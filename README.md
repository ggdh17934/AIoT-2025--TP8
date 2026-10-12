# AIoT-2025--TP8 — MQTT image inference offloading

Simple, documented solution to [the course TP8](https://github.com/ahmed3991/AIoT-2025/tree/main/TP8).

[Open notebook in Colab](https://colab.research.google.com/github/ggdh17934/AIoT-2025--TP8/blob/main/TP8-Ghanabzia.ipynb)

This repository is **private**. Sign in with your GitHub account when Colab asks
for access. You can also download the notebook and use Colab's **Upload** option.

## Run locally

Use Python 3.11 or newer (TensorFlow builds depend on the supported Python version).
From this project folder:

```sh
python -m pip install -r requirements.txt
python tp8.py
```

## Run the notebook

Run all and upload models/cnn_int8.tflite when prompted. The notebook runs the real JSON image inference demo. Use the Python MQTT mode on your computer and the ESP32 sketch for the network/board demonstration.

The first notebook cell installs missing dependencies. TP2/TP4 also ensure the
versions used for their pickle models. All notebooks contain the actual solution
code; they do not require downloading the Python script just to execute cells.
Saved outputs come from the local run; rerunning generates your own measurements.

## Files

- `TP8-Ghanabzia.ipynb`: notebook with code, outputs, and report display.
- `tp8.py`: Python solution.
- `EXPLICATION_AR.md`: Arabic explanation of the code, concepts and limitations.
- `results/REPORT.md`: measured results and conclusions.
- `results/VALIDATION.md`: what was actually checked.
- `requirements.txt`: runtime dependencies.

## Embedded part

The notebook demonstrates the host-side work. The assignment also requires
`src/main.cpp`, `platformio.ini`, and `diagram.json` for the board/simulator.
Install PlatformIO, open this folder and build:

```sh
pio run -e esp32dev
```

Run the included Wokwi project from VS Code, or upload the sketch to the matching
board. No hardware measurements are invented; see `results/VALIDATION.md` and
GitHub Actions for the actual build status.


## MQTT mode

```sh
python tp8.py --mqtt --broker localhost
```

For Wokwi's public classroom default use `--broker broker.mqtt.cool`.
Keep TP4 and TP8 subscribers in different sessions: both use the assignment
topics `esp32/data` and `esp32/control` but different schemas. Python supports
`--tls --port 8883` and broker credentials through environment variables.

## Sources and attribution

Assignment and original wiring: Ahmed Ghenabzia,
[ahmed3991/AIoT-2025](https://github.com/ahmed3991/AIoT-2025).
Solution Python and firmware are implemented for this project; diagrams are
adapted from the course starter files. Smoke data source:
[Kaggle Smoke Detection](https://www.kaggle.com/datasets/deepcontractor/smoke-detection-dataset).
Fashion-MNIST is loaded through the official Keras dataset loader; source:
[Fashion-MNIST](https://github.com/zalandoresearch/fashion-mnist).
