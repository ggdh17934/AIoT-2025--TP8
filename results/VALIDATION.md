# Validation

- All 6 notebook code cells executed successfully; genuine outputs are saved.
- Notebook format validated with nbformat.
- Python solution/support modules pass syntax compilation.
- Report and Arabic explanation are included.
- Actual subscriber passed a real localhost MQTT round trip via AMQTT: 5.689 ms.
- Temporary broker and clients were stopped after testing.
- This host MQTT result excludes ESP32/WiFi latency.
- GitHub Actions builds the ESP32 firmware on push; local toolchain unpacking exceeded available disk space and task-only downloads were removed.
- No real-board runtime measurements or Wokwi observations are claimed.

## GitHub firmware build

**PASSED**: [Build run](https://github.com/ggdh17934/AIoT-2025--TP8/actions/runs/38261469050).

The included firmware and pinned platform configuration compiled successfully on GitHub's Linux runner.
This proves compilation; board execution, sensor/LCD behavior and runtime timing remain separate observations.
