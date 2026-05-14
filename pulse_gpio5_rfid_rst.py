#!/usr/bin/env python3
"""
Drive RFID reader reset (BCM GPIO5): output LOW briefly, then HIGH.

Default timing matches a typical MFRC522 hard-reset pulse. Run on the Pi only.

Examples:
  python3 pulse_gpio5_rfid_rst.py
  python3 pulse_gpio5_rfid_rst.py --low-ms 15 --high-hold-ms 120
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO not available. Run this on a Raspberry Pi.")
    sys.exit(1)

BCM_PIN = 5


def main() -> int:
    p = argparse.ArgumentParser(description="Pulse GPIO5 LOW then HIGH (RFID RST)")
    p.add_argument("--low-ms", type=float, default=10.0, help="Time LOW in ms (default: 10)")
    p.add_argument(
        "--high-hold-ms",
        type=float,
        default=50.0,
        help="Time HIGH before exit in ms (default: 50)",
    )
    args = p.parse_args()

    low_s = max(0.001, args.low_ms / 1000.0)
    high_s = max(0.001, args.high_hold_ms / 1000.0)

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BCM_PIN, GPIO.OUT)
        GPIO.output(BCM_PIN, GPIO.HIGH)
        time.sleep(0.01)

        GPIO.output(BCM_PIN, GPIO.LOW)
        time.sleep(low_s)
        GPIO.output(BCM_PIN, GPIO.HIGH)
        time.sleep(high_s)

        print(f"GPIO{BCM_PIN}: LOW {args.low_ms:g} ms, then HIGH {args.high_hold_ms:g} ms.")
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
