"""Compatibility entry point: python -m ai_logic.mqtt_ai_subscriber --broker localhost"""
import argparse
from tp8 import run_mqtt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--tls", action="store_true")
    args = parser.parse_args()
    run_mqtt(args.broker, args.port, args.tls)
