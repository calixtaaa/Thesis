#!/usr/bin/env python3
"""Toggle a single GPIO pin HIGH/LOW for 3 repetitions, then set to HIGH."""

import sys
import time
import argparse

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("[ERR] RPi.GPIO not available. Run this script on Raspberry Pi OS.")
    sys.exit(1)

REPETITIONS = 3
PULSE_DURATION = 1.0  # seconds
DEFAULT_STATE = GPIO.HIGH


def init_gpio(pin):
    """Initialize GPIO and set pin as output."""
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, DEFAULT_STATE)
        print(f"[INFO] GPIO{pin} initialized. Pin set to default state (HIGH).")
    except Exception as exc:
        print(f"[ERR] Failed to initialize GPIO{pin}: {exc}")
        sys.exit(1)


def toggle_pin(pin):
    """Toggle GPIO pin HIGH/LOW for 3 repetitions."""
    print(f"\n[INFO] Starting {REPETITIONS} repetitions of toggle cycle for GPIO{pin}...")
    
    try:
        for rep in range(1, REPETITIONS + 1):
            print(f"\n--- Repetition {rep}/{REPETITIONS} ---")
            
            # Set LOW
            print(f"Setting GPIO{pin} to LOW...")
            GPIO.output(pin, GPIO.LOW)
            print(f"  GPIO{pin} → LOW")
            time.sleep(PULSE_DURATION)
            
            # Set HIGH
            print(f"Setting GPIO{pin} to HIGH...")
            GPIO.output(pin, GPIO.HIGH)
            print(f"  GPIO{pin} → HIGH")
            time.sleep(PULSE_DURATION)
        
        print(f"\n[INFO] {REPETITIONS} repetitions complete.")
        print(f"[INFO] GPIO{pin} set to default state (HIGH).")
        
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user (Ctrl+C).")
        sys.exit(130)
    except Exception as exc:
        print(f"[ERR] Toggle operation failed: {exc}")
        sys.exit(1)


def cleanup():
    """Clean up GPIO on exit."""
    try:
        GPIO.cleanup()
        print("[INFO] GPIO cleaned up.")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Toggle a single GPIO pin HIGH/LOW.")
    parser.add_argument("pin", type=int, help="GPIO pin number (e.g., 26, 16, 6)")
    args = parser.parse_args()
    
    pin = args.pin
    print(f"GPIO Toggle Test — GPIO{pin}")
    print("=" * 50)
    
    init_gpio(pin)
    toggle_pin(pin)
    cleanup()
    
    print("\n[OK] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
