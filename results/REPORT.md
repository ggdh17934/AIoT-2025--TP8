# TP8 report

The firmware sends a 784-element signed int8 array under encoded_image.
The Python subscriber validates length/range, reshapes to the actual
[1, 28, 28, 1] tensor, invokes the real TP6 CNN, and returns
class_name plus device/request IDs on esp32/control. The LCD displays the name.
No unnecessary scaler or extra /255 is applied to already quantized int8 data.

The local JSON round-trip demo used the first real Fashion-MNIST test image:
true label **Ankle boot**, predicted
**Ankle boot**, confidence 0.9961.
The JSON inference result matches a direct interpreter call. Invalid out-of-range
pixel values are rejected. Local encode/decode/inference time: 0.532 ms;
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
