#!/usr/bin/env python3
"""Standalone IR break-beam sensor test utility for Raspberry Pi.

This script reads the shared vending-machine IR break-beam receiver on GPIO 26
using an internal pull-up. The sensor is treated as active-low:
- beam clear  -> GPIO HIGH
- beam broken -> GPIO LOW
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:
    GPIO = None  # type: ignore


DEFAULT_PIN = 26


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IR break-beam sensor tester")
    parser.add_argument("--pin", type=int, default=DEFAULT_PIN, help="BCM GPIO pin for the beam sensor (default: 26)")
    parser.add_argument("--interval", type=float, default=0.05, help="Poll interval in seconds (default: 0.05)")
    parser.add_argument("--duration", type=float, default=0.0, help="Optional run duration in seconds; 0 means run until Ctrl+C")
    parser.add_argument("--once", action="store_true", help="Print the current state once and exit")
    return parser.parse_args(argv)


def gpio_state_to_text(raw_value: int) -> str:
    return "BROKEN" if raw_value == GPIO.LOW else "CLEAR"


def init_gpio(pin: int) -> tuple[bool, str | None]:
    if GPIO is None:
        return False, "[ERR] RPi.GPIO is not available. Run this on Raspberry Pi OS."

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    except Exception as exc:
        return False, f"[ERR] Failed to initialize GPIO{pin}: {exc}"

    return True, None


def read_sensor(pin: int) -> tuple[int, str]:
    raw_value = GPIO.input(pin)
    return raw_value, gpio_state_to_text(raw_value)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    ok, error = init_gpio(args.pin)
    if not ok:
        print(error)
        return 1

    print(f"[INFO] Monitoring IR break-beam sensor on GPIO{args.pin} (active-low).")
    print("[INFO] Press Ctrl+C to stop.")

    try:
        last_state: str | None = None
        start_time = time.monotonic()

        while True:
            raw_value, state = read_sensor(args.pin)
            if state != last_state:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] GPIO{args.pin} = {raw_value} -> {state}")
                last_state = state

            if args.once:
                break

            if args.duration > 0 and (time.monotonic() - start_time) >= args.duration:
                break

            time.sleep(max(0.01, args.interval))
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))