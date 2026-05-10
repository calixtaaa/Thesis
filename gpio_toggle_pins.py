#!/usr/bin/env python3
"""Toggle GPIO26, GPIO16, GPIO6 HIGH/LOW for 3 repetitions, then set to HIGH."""

import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("[ERR] RPi.GPIO not available. Run this script on Raspberry Pi OS.")
    sys.exit(1)

PINS = [26, 16, 6]
REPETITIONS = 3
PULSE_DURATION = 1.0  # seconds
DEFAULT_STATE = GPIO.HIGH


def init_gpio():
    """Initialize GPIO and set all pins as outputs."""
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, DEFAULT_STATE)
        print("[INFO] GPIO initialized. Pins set to default state (HIGH).")
    except Exception as exc:
        print(f"[ERR] Failed to initialize GPIO: {exc}")
        sys.exit(1)


def toggle_pins():
    """Toggle GPIO26, GPIO16, GPIO6 HIGH/LOW for 3 repetitions."""
    print(f"\n[INFO] Starting {REPETITIONS} repetitions of toggle cycle...")
    
    try:
        for rep in range(1, REPETITIONS + 1):
            print(f"\n--- Repetition {rep}/{REPETITIONS} ---")
            
            # Set LOW
            print(f"Setting pins to LOW...")
            for pin in PINS:
                GPIO.output(pin, GPIO.LOW)
            print(f"  GPIO{PINS[0]}, GPIO{PINS[1]}, GPIO{PINS[2]} → LOW")
            time.sleep(PULSE_DURATION)
            
            # Set HIGH
            print(f"Setting pins to HIGH...")
            for pin in PINS:
                GPIO.output(pin, GPIO.HIGH)
            print(f"  GPIO{PINS[0]}, GPIO{PINS[1]}, GPIO{PINS[2]} → HIGH")
            time.sleep(PULSE_DURATION)
        
        print(f"\n[INFO] {REPETITIONS} repetitions complete.")
        print(f"[INFO] All pins set to default state (HIGH).")
        
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
    print("GPIO Toggle Test — GPIO26, GPIO16, GPIO6")
    print("=" * 50)
    
    init_gpio()
    toggle_pins()
    cleanup()
    
    print("\n[OK] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
