#!/usr/bin/env python3
"""
Stress MFRC522 SPI against solenoid unlocks and coin-acceptor relay toggles.

Use this on the Pi to reproduce "RFID SPI dies after lock/unlock or relay noise"
and to see whether a software re-init restores VersionReg reads.

Pin map matches main.py:
  RFID RST: GPIO 5
  Restock solenoid: GPIO 16
  Troubleshoot solenoid: GPIO 20
  Coin acceptor relay: GPIO 21 (LOW = enabled, HIGH = disabled — same as main)

Examples:
  python3 test_rfid_spi_actuator_stress.py --cycles 8
  python3 test_rfid_spi_actuator_stress.py --cycles 5 --apply-reinit
  python3 test_rfid_spi_actuator_stress.py --solenoid-active-high
"""

from __future__ import annotations

import argparse
import os
import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO not available. Run this script on a Raspberry Pi.")
    sys.exit(1)

from rfid_single_reader_test import (
    _init_gpio,
    _probe_mfrc522_spi_link,
    _pulse_reader_reset,
)

# Mirrors main.py
SOLENOID_PINS = {
    "restock": 16,
    "troubleshoot": 20,
}
COIN_ACCEPTOR_RELAY_PIN = 21


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _solenoid_idle_level(active_low: bool):
    return GPIO.HIGH if active_low else GPIO.LOW


def _solenoid_active_level(active_low: bool):
    return GPIO.LOW if active_low else GPIO.HIGH


def _set_coin_relay(enabled: bool) -> None:
    GPIO.output(COIN_ACCEPTOR_RELAY_PIN, GPIO.LOW if enabled else GPIO.HIGH)


def _setup_actuator_outputs(active_low: bool) -> None:
    for pin in SOLENOID_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, _solenoid_idle_level(active_low))
    GPIO.setup(COIN_ACCEPTOR_RELAY_PIN, GPIO.OUT)
    _set_coin_relay(False)


def _unlock_pulse(pin: int, seconds: float, active_low: bool) -> None:
    GPIO.output(pin, _solenoid_active_level(active_low))
    time.sleep(max(0.0, seconds))
    GPIO.output(pin, _solenoid_idle_level(active_low))


def _relay_chatter(cycles: int, dwell_s: float) -> None:
    for _ in range(max(0, cycles)):
        _set_coin_relay(True)
        time.sleep(max(0.0, dwell_s))
        _set_coin_relay(False)
        time.sleep(max(0.0, dwell_s))


def _probe_line(label: str) -> tuple[bool, str]:
    ok, msg = _probe_mfrc522_spi_link()
    print(f"  [{label}] {msg}")
    return ok, msg


def _reinit_after_stress(rst_pulses: int, settle_s: float) -> tuple[bool, str]:
    ok_pulse, pulse_msg = _pulse_reader_reset(
        pulses=max(1, rst_pulses),
        low_s=0.02,
        high_s=max(0.02, settle_s),
    )
    if not ok_pulse:
        return False, pulse_msg
    time.sleep(max(0.0, settle_s))
    return _probe_mfrc522_spi_link()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Solenoid + coin relay stress with MFRC522 SPI probes",
    )
    parser.add_argument("--cycles", type=int, default=5, help="Stress cycles (default: 5)")
    parser.add_argument(
        "--unlock-s",
        type=float,
        default=0.35,
        help="Per-door energize time in seconds (default: 0.35)",
    )
    parser.add_argument(
        "--relay-bursts",
        type=int,
        default=6,
        help="Full on/off relay cycles per stress pass (default: 6)",
    )
    parser.add_argument(
        "--relay-dwell",
        type=float,
        default=0.08,
        help="Seconds on each relay state (default: 0.08)",
    )
    parser.add_argument(
        "--apply-reinit",
        action="store_true",
        help="After each cycle, pulse RST and probe again (recovery check)",
    )
    parser.add_argument(
        "--rst-pulses",
        type=int,
        default=3,
        help="RST pulses when --apply-reinit is used (default: 3)",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.05,
        help="Settle time for RST when --apply-reinit is used (default: 0.05)",
    )
    parser.add_argument(
        "--solenoid-active-high",
        action="store_true",
        help="Set if relays are active-HIGH (default follows main.py: active-LOW)",
    )
    args = parser.parse_args()

    active_low = not args.solenoid_active_high
    if os.environ.get("SOLENOID_ACTIVE_LOW", "").strip() != "":
        active_low = _env_bool("SOLENOID_ACTIVE_LOW", active_low)

    ok, err = _init_gpio()
    if not ok:
        print(err or "GPIO init failed.")
        return 1

    try:
        _setup_actuator_outputs(active_low)
    except Exception as exc:
        print(f"Failed to configure actuator GPIOs: {exc}")
        GPIO.cleanup()
        return 1

    print("Baseline SPI probe (before stress):")
    before_ok, _ = _probe_line("baseline")

    fails_after_stress = 0
    recovery_ok = 0

    for n in range(1, max(1, args.cycles) + 1):
        print(f"\n--- Cycle {n}/{args.cycles}: solenoid + relay chatter ---")
        _unlock_pulse(SOLENOID_PINS["restock"], args.unlock_s, active_low)
        time.sleep(0.02)
        _unlock_pulse(SOLENOID_PINS["troubleshoot"], args.unlock_s, active_low)
        _relay_chatter(args.relay_bursts, args.relay_dwell)

        post_ok, post_msg = _probe_line("post-stress")
        if not post_ok:
            fails_after_stress += 1

        if args.apply_reinit:
            r_ok, r_msg = _reinit_after_stress(args.rst_pulses, args.settle)
            tag = "post-reinit"
            print(f"  [{tag}] {r_msg}")
            if r_ok:
                recovery_ok += 1
            elif not post_ok:
                print("    (SPI still failing after reinit this cycle)")

    print("\n=== Summary ===")
    print(f"  Baseline probe OK: {before_ok}")
    print(f"  Post-stress probe failures (count): {fails_after_stress} / {args.cycles}")
    if args.apply_reinit:
        print(f"  Cycles where post-reinit probe OK: {recovery_ok} / {args.cycles}")
    print("\nDone. GPIO cleaned up.")

    GPIO.cleanup()
    return 0 if fails_after_stress == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
