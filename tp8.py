"""TP8: receive int8 images, run real TFLite inference, return class labels."""
# %% 1. Imports, model, and tensor metadata
import argparse
import json
import logging
import os
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
MODEL_PATH = ROOT / "models" / "cnn_int8.tflite"
if not MODEL_PATH.exists():
    try:
        from google.colab import files
    except ImportError as error:
        raise FileNotFoundError("Copy TP6 cnn_int8.tflite into models/.") from error
    print("Upload cnn_int8.tflite from TP6")
    uploaded = files.upload()
    if "cnn_int8.tflite" not in uploaded:
        raise FileNotFoundError("cnn_int8.tflite was not uploaded.")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_bytes(uploaded["cnn_int8.tflite"])

interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH), num_threads=1)
interpreter.allocate_tensors()
input_info = interpreter.get_input_details()[0]
output_info = interpreter.get_output_details()[0]
if input_info["dtype"] != np.int8 or int(np.prod(input_info["shape"])) != 784:
    raise ValueError("The model must accept one 28x28 int8 image.")
class_names = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
               "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]

# %% 2. Parse the payload and use the actual model input shape
def infer_image(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object.")
    pixels = payload.get("encoded_image")
    if not isinstance(pixels, list) or len(pixels) != 784:
        raise ValueError("encoded_image must contain exactly 784 int8 pixels.")
    if any(isinstance(value, bool) or not isinstance(value, int)
           or value < -128 or value > 127 for value in pixels):
        raise ValueError("All pixels must be integers between -128 and 127.")
    # A CNN has shape [1,28,28,1], unlike the MLP's [1,28,28].
    image = np.asarray(pixels, dtype=np.int8).reshape(input_info["shape"])
    started = time.perf_counter()
    interpreter.set_tensor(input_info["index"], image)
    interpreter.invoke()
    scores = interpreter.get_tensor(output_info["index"])[0]
    index = int(np.argmax(scores))
    output_scale, output_zero_point = output_info["quantization"]
    probability = float((int(scores[index]) - output_zero_point) * output_scale)
    return {
        "device_id": payload.get("device_id", "demo"),
        "request_id": payload.get("request_id", 0),
        "class_index": index, "class_name": class_names[index],
        "probability": probability,
        "server_inference_ms": (time.perf_counter() - started) * 1000,
    }

# %% 3. MQTT subscriber with reconnect, input validation, and returned labels
def run_mqtt(broker="localhost", port=1883, tls=False):
    import paho.mqtt.client as mqtt
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logging.error("Connection rejected: %s", reason_code)
            return
        client.subscribe("esp32/data", qos=1)
        logging.info("Ready for encoded_image messages")

    def on_message(client, userdata, message):
        try:
            response = infer_image(json.loads(message.payload))
            # Returning device/request IDs prevents a different ESP32 using this reply.
            client.publish("esp32/control", json.dumps(response), qos=1, retain=False)
            logging.info("%s", response)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError) as error:
            logging.warning("Ignored malformed image: %s", error)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ghanabzia-tp8-ai")
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    if tls:
        client.tls_set()
    if os.environ.get("MQTT_USERNAME"):
        client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ.get("MQTT_PASSWORD"))
    client.connect_async(broker, port, keepalive=30)
    try:
        client.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:
        client.disconnect()

# %% 4. Local/Colab demo with one actual Fashion-MNIST test image
def run_demo():
    from tensorflow import keras
    (_, _), (test_images, test_labels) = keras.datasets.fashion_mnist.load_data()
    scale, zero_point = input_info["quantization"]
    image = test_images[0].astype(np.float32) / 255.0
    encoded = np.clip(np.rint(image / scale + zero_point), -128, 127).astype(np.int8)
    payload = {"device_id": "esp-demo", "request_id": 1,
               "encoded_image": encoded.flatten().astype(int).tolist()}
    started = time.perf_counter()
    # Serialize and decode exactly the JSON format used over MQTT.
    response = infer_image(json.loads(json.dumps(payload)))
    local_ms = (time.perf_counter() - started) * 1000
    try:
        infer_image({"encoded_image": [200] * 784})
    except ValueError:
        print("Invalid int8 pixels rejected correctly.")
    else:
        raise AssertionError("Invalid pixels were accepted.")
    direct_input = encoded.reshape(input_info["shape"])
    interpreter.set_tensor(input_info["index"], direct_input)
    interpreter.invoke()
    direct_index = int(interpreter.get_tensor(output_info["index"])[0].argmax())
    assert direct_index == response["class_index"]
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (ROOT / "sample_payload.json").write_text(json.dumps(payload), encoding="utf-8")
    (out / "demo_response.json").write_text(json.dumps(response, indent=2), encoding="utf-8")
    report = f"""# TP8 report

The firmware sends a 784-element signed int8 array under encoded_image.
The Python subscriber validates length/range, reshapes to the actual
{input_info['shape'].tolist()} tensor, invokes the real TP6 CNN, and returns
class_name plus device/request IDs on esp32/control. The LCD displays the name.
No unnecessary scaler or extra /255 is applied to already quantized int8 data.

The local JSON round-trip demo used the first real Fashion-MNIST test image:
true label **{class_names[int(test_labels[0])]}**, predicted
**{response['class_name']}**, confidence {response['probability']:.4f}.
The JSON inference result matches a direct interpreter call. Invalid out-of-range
pixel values are rejected. Local encode/decode/inference time: {local_ms:.3f} ms;
this excludes broker/WiFi/board delays and is not network latency.

MQTT defaults to a local broker, with configurable broker/port, TLS and credentials
from environment variables. The classroom Wokwi firmware defaults to
broker.mqtt.cool; start Python with --broker broker.mqtt.cool to match it.
Keep TP4 and TP8 subscribers in separate sessions because their assignment
topics match while their message schemas differ. Input images generated in
TP7 use exactly the same CNN quantization parameters.

Offloading reduces the ESP32's model/runtime memory requirement, while adding
network latency, connectivity dependency, and transmission bandwidth.
On-device inference works without a broker and keeps images on the board.
The board measures round-trip time from send to the matched reply and prints it;
actual hardware/MQTT observations must be recorded when that system is run.

Source: https://github.com/ahmed3991/AIoT-2025/blob/main/TP8/TP8.md
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")
    print("True class:", class_names[int(test_labels[0])])
    print(json.dumps(response, indent=2))
    print("Desktop JSON round trip (ms):", local_ms)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mqtt", action="store_true", help="Run the network subscriber instead of the demo")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--tls", action="store_true")
    args = parser.parse_args()
    if args.mqtt:
        run_mqtt(args.broker, args.port, args.tls)
    else:
        run_demo()
