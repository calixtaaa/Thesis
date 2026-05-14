#!/usr/bin/env python3
"""
Recover / re-initialize the MFRC522 RFID path after SPI or the reader appears stuck.

Typical use: run this alone after solenoid or relay activity left the reader
returning VersionReg 0x00/0xFF or timing out. It does not drive actuators.

Wiring (same as main.py / rfid_single_reader_test.py):
  SPI0 CE0 GPIO8, RST GPIO5, SCK 11, MOSI 10, MISO 9

Examples:
  python3 test_rfid_spi_reinit.py
  python3 test_rfid_spi_reinit.py --rst-pulses 5 --retry 10 --retry-delay 0.25
  python3 test_rfid_spi_reinit.py --try-read-uid
"""

from __future__ import annotations

import argparse
import sys
import time

from rfid_single_reader_test import (
    RFID_RST_PIN,
    _init_gpio,
    _probe_mfrc522_spi_link,
    _pulse_reader_reset,
    _read_uid,
)


def reinit_spi_path(*, rst_pulses: int, settle_s: float) -> tuple[bool, str]:
    """Hardware reset line + fresh SPI session (probe opens/closes MFRC522)."""
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
    parser = argparse.ArgumentParser(description="MFRC522 SPI / reader re-init helper")
    parser.add_argument(
        "--rst-pulses",
        type=int,
        default=3,
        help="Number of RST low/high cycles on GPIO5 (default: 3)",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.05,
        help="Seconds to hold RST high each half-cycle / extra settle after pulse (default: 0.05)",
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=1,
        help="Retry reinit+probe until pass or attempts exhausted (default: 1)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=0.2,
        help="Seconds between retries (default: 0.2)",
    )
    parser.add_argument(
        "--try-read-uid",
        action="store_true",
        help="After a passing SPI probe, attempt one non-blocking UID read",
    )
    args = parser.parse_args()

    ok, err = _init_gpio()
    if not ok:
        print(err or "GPIO init failed.")
        print(
            "If GPIO init failed on Pi 5, see hints printed by rfid_single_reader_test "
            "(rpi-lgpio, SPI enable)."
        )
        return 1

    print(f"RFID RST on GPIO{RFID_RST_PIN}. Re-initializing reader path…")

    last_ok = False
    last_msg = ""
    attempts = max(1, args.retry)
    for attempt in range(1, attempts + 1):
        last_ok, last_msg = reinit_spi_path(rst_pulses=args.rst_pulses, settle_s=args.settle)
        print(f"[{attempt}/{attempts}] {last_msg}")
        if last_ok:
            break
        if attempt < attempts:
            time.sleep(max(0.0, args.retry_delay))

    if args.try_read_uid and last_ok:
        uid = _read_uid()
        if uid:
            print(f"UID read after reinit: {uid}")
        else:
            print("UID read after reinit: (none this pass — tap card and rerun with --try-read-uid)")

    return 0 if last_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
