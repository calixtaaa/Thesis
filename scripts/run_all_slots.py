#!/usr/bin/env python3
"""Run all slots from the terminal: 3 revolutions each,
then 2 cycles of energizing the coin acceptor relay for 5s each.

Usage: (from repo root)
    source venv/bin/activate
    python scripts/run_all_slots.py

WARNING: This will move motors and toggle relays. Ensure it's safe.
"""
import time
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import main` works when this script
# is executed from the repo root using `python scripts/run_all_slots.py`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    # Import hardware helpers from main (shared code)
    from main import gpio_init, dispense_from_slot, set_coin_acceptor_relay, PRODUCT_STEPPER_PINS, GPIO
except Exception as e:
    print(f"Failed to import hardware helpers: {e}")
    sys.exit(1)


def run_all_slots(revolutions: int = 3, relay_cycles: int = 2, relay_on_seconds: float = 5.0):
    print("Initializing GPIO and stepper backend...")
    gpio_init()

    slots = sorted(PRODUCT_STEPPER_PINS.keys())
    if not slots:
        print("No configured slots found. Exiting.")
        return

    try:
        for slot in slots:
            print(f"\n=== Slot {slot} — running {revolutions} revolutions ===")
            dispense_from_slot(slot, quantity=revolutions)
            # short pause between slots
            time.sleep(0.5)

            # Relay cycles (active on when True)
            for cycle in range(1, relay_cycles + 1):
                print(f"Slot {slot}: relay cycle {cycle} — energize for {relay_on_seconds}s")
                try:
                    set_coin_acceptor_relay(True)
                except Exception as e:
                    print(f"Warning: failed to energize relay: {e}")
                time.sleep(relay_on_seconds)
                try:
                    set_coin_acceptor_relay(False)
                except Exception as e:
                    print(f"Warning: failed to de-energize relay: {e}")
                time.sleep(1.0)

        print("\nAll slots processed.")
    finally:
        try:
            print("Cleaning up GPIO...")
            GPIO.cleanup()
        except Exception:
            pass


def main():
    run_all_slots()


if __name__ == "__main__":
    main()
