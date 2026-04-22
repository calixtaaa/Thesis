#!/usr/bin/env python3
"""Hardware regression checklist runner for Raspberry Pi 5 vending machine integration.

This script performs a repeatable set of hardware-facing smoke checks and writes
run artifacts to debug_logs for traceability.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_REPORT_DIR = BASE_DIR / "debug_logs"


@dataclass
class CheckResult:
    name: str
    status: str
    details: str
    duration_s: float


class ChecklistError(Exception):
    """Raised when a required checklist precondition is not met."""


class StepperDriver:
    """Minimal stepper driver for ULN2003 test pulses without opening UI tools."""

    def __init__(self, pins: dict[str, int]):
        self.pins = pins
        self.backend = None
        self.devices = {}
        self.gpio = None

    def setup(self) -> None:
        try:
            from gpiozero import OutputDevice  # type: ignore

            self.backend = "gpiozero"
            for pin in self.pins.values():
                self.devices[pin] = OutputDevice(pin)
            return
        except Exception:
            pass

        try:
            import RPi.GPIO as GPIO  # type: ignore

            self.backend = "RPi.GPIO"
            self.gpio = GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for pin in self.pins.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
        except Exception as exc:
            raise ChecklistError(f"Stepper GPIO setup failed: {exc}") from exc

    def set_phase(self, phase: tuple[int, int, int, int]) -> None:
        if self.backend == "gpiozero":
            for pin_name, value in zip(("in1", "in2", "in3", "in4"), phase):
                self.devices[self.pins[pin_name]].value = bool(value)
            return

        if self.backend == "RPi.GPIO" and self.gpio is not None:
            self.gpio.output(self.pins["in1"], self.gpio.HIGH if phase[0] else self.gpio.LOW)
            self.gpio.output(self.pins["in2"], self.gpio.HIGH if phase[1] else self.gpio.LOW)
            self.gpio.output(self.pins["in3"], self.gpio.HIGH if phase[2] else self.gpio.LOW)
            self.gpio.output(self.pins["in4"], self.gpio.HIGH if phase[3] else self.gpio.LOW)
            return

        raise ChecklistError("Stepper backend is not initialized.")

    def deenergize(self) -> None:
        self.set_phase((0, 0, 0, 0))

    def cleanup(self) -> None:
        try:
            if self.backend == "gpiozero":
                for dev in self.devices.values():
                    try:
                        dev.close()
                    except Exception:
                        pass
                self.devices.clear()
            elif self.backend == "RPi.GPIO" and self.gpio is not None:
                try:
                    for pin in self.pins.values():
                        self.gpio.output(pin, self.gpio.LOW)
                except Exception:
                    pass
                self.gpio.cleanup()
        except Exception:
            pass


def run_check(name: str, fn) -> CheckResult:
    started = time.time()
    try:
        status, details = fn()
        if status not in {"PASS", "WARN", "FAIL", "SKIP"}:
            status = "FAIL"
            details = f"Invalid status from check: {status}"
    except ChecklistError as exc:
        status = "FAIL"
        details = str(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        status = "FAIL"
        details = f"Unexpected error: {exc}"
    elapsed = time.time() - started
    return CheckResult(name=name, status=status, details=details, duration_s=round(elapsed, 3))


def check_runtime_environment() -> tuple[str, str]:
    info = (
        f"python={platform.python_version()} "
        f"platform={platform.system()}-{platform.machine()} "
        f"hostname={platform.node()}"
    )
    return "PASS", info


def check_spi_device_present() -> tuple[str, str]:
    spi0 = Path("/dev/spidev0.0")
    spi1 = Path("/dev/spidev0.1")
    if spi0.exists() and spi1.exists():
        return "PASS", "Found /dev/spidev0.0 and /dev/spidev0.1."
    if spi0.exists():
        return "WARN", "Found /dev/spidev0.0 only. CE1 may be disabled or unused."
    return "FAIL", "SPI device /dev/spidev0.0 not found. Enable SPI in raspi-config."


def check_gpio_stack() -> tuple[str, str]:
    backends = []
    try:
        import gpiozero  # type: ignore  # noqa: F401

        backends.append("gpiozero")
    except Exception:
        pass

    try:
        import RPi.GPIO  # type: ignore  # noqa: F401

        backends.append("RPi.GPIO")
    except Exception:
        pass

    if not backends:
        return "FAIL", "No GPIO backend importable (gpiozero or RPi.GPIO)."
    return "PASS", f"Available GPIO backends: {', '.join(backends)}"


def check_rfid_probe(skip: bool) -> tuple[str, str]:
    if skip:
        return "SKIP", "RFID probe skipped by flag."

    try:
        import rfid_single_reader_test as rfid_test
    except Exception as exc:
        return "FAIL", f"Could not import rfid_single_reader_test: {exc}"

    ok, err = rfid_test._init_gpio()
    if not ok:
        return "FAIL", str(err)

    try:
        ok, msg = rfid_test._probe_mfrc522_spi_link()
        return ("PASS" if ok else "FAIL"), msg
    finally:
        try:
            if getattr(rfid_test, "GPIO", None) is not None:
                rfid_test.GPIO.cleanup()
        except Exception:
            pass


def parse_slots(slot_text: str) -> list[int]:
    slots = []
    for chunk in slot_text.split(","):
        item = chunk.strip()
        if not item:
            continue
        value = int(item)
        if value < 1 or value > 10:
            raise ChecklistError(f"Invalid slot {value}. Allowed range is 1..10.")
        slots.append(value)
    if not slots:
        raise ChecklistError("No slot numbers supplied for stepper test.")
    return slots


def stepper_spin(slot: int, steps: int, delay_s: float) -> tuple[str, str]:
    try:
        from stepper import PRODUCT_STEPPER_PINS, ULN2003_SEQUENCE
    except Exception as exc:
        return "FAIL", f"Could not import stepper mappings: {exc}"

    pins = PRODUCT_STEPPER_PINS.get(slot)
    if not pins:
        return "FAIL", f"No pin mapping found for slot {slot}."

    driver = StepperDriver(pins)
    phase_index = 0
    try:
        driver.setup()
        for _ in range(steps):
            phase_index = (phase_index + 1) % len(ULN2003_SEQUENCE)
            driver.set_phase(ULN2003_SEQUENCE[phase_index])
            time.sleep(max(0.0005, delay_s))
        driver.deenergize()
        return "PASS", f"Stepper slot {slot} pulsed for {steps} steps using {driver.backend}."
    except ChecklistError as exc:
        return "FAIL", str(exc)
    except Exception as exc:
        return "FAIL", f"Stepper drive failed on slot {slot}: {exc}"
    finally:
        driver.cleanup()


def check_stepper(skip: bool, slots: Iterable[int], steps: int, delay_s: float) -> tuple[str, str]:
    if skip:
        return "SKIP", "Stepper test skipped by flag."

    outcomes = []
    for slot in slots:
        outcomes.append(stepper_spin(slot=slot, steps=steps, delay_s=delay_s))

    failures = [msg for status, msg in outcomes if status == "FAIL"]
    if failures:
        return "FAIL", " | ".join(failures)

    messages = [msg for _status, msg in outcomes]
    return "PASS", " | ".join(messages)


def parse_loopback_pairs(pair_text: str) -> list[tuple[int, int]]:
    pairs = []
    for chunk in pair_text.split(","):
        item = chunk.strip()
        if not item:
            continue
        left, right = item.split(":", 1)
        pairs.append((int(left.strip()), int(right.strip())))
    return pairs


def read_input_state(pin: int, backend: str, gpio=None, device=None) -> int:
    if backend == "gpiozero":
        return 0 if device.is_active else 1
    return int(gpio.input(pin))


def check_loopback(enable: bool, pair_text: str, pulses: int, pulse_s: float) -> tuple[str, str]:
    if not enable:
        return "SKIP", "GPIO loopback skipped (enable with --enable-loopback)."

    pairs = parse_loopback_pairs(pair_text)
    if not pairs:
        return "FAIL", "No GPIO loopback pairs configured."

    backend = None
    gpio = None
    output_devices = {}
    input_devices = {}

    try:
        try:
            from gpiozero import DigitalInputDevice, OutputDevice  # type: ignore

            backend = "gpiozero"
            for out_pin, in_pin in pairs:
                if out_pin not in output_devices:
                    output_devices[out_pin] = OutputDevice(out_pin)
                if in_pin not in input_devices:
                    input_devices[in_pin] = DigitalInputDevice(in_pin, pull_up=True)
        except Exception:
            import RPi.GPIO as GPIO  # type: ignore

            backend = "RPi.GPIO"
            gpio = GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for out_pin, in_pin in pairs:
                GPIO.setup(out_pin, GPIO.OUT)
                GPIO.output(out_pin, GPIO.LOW)
                GPIO.setup(in_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        failures = []
        checks = []

        for out_pin, in_pin in pairs:
            observed_edges = 0
            previous = None
            for _ in range(max(1, pulses)):
                if backend == "gpiozero":
                    output_devices[out_pin].on()
                    time.sleep(pulse_s)
                    state_high = read_input_state(in_pin, backend, device=input_devices[in_pin])
                    output_devices[out_pin].off()
                    time.sleep(pulse_s)
                    state_low = read_input_state(in_pin, backend, device=input_devices[in_pin])
                else:
                    gpio.output(out_pin, gpio.HIGH)
                    time.sleep(pulse_s)
                    state_high = read_input_state(in_pin, backend, gpio=gpio)
                    gpio.output(out_pin, gpio.LOW)
                    time.sleep(pulse_s)
                    state_low = read_input_state(in_pin, backend, gpio=gpio)

                for state in (state_high, state_low):
                    if previous is not None and state != previous:
                        observed_edges += 1
                    previous = state

            checks.append(f"{out_pin}->{in_pin} edges={observed_edges}")
            if observed_edges < 1:
                failures.append(f"No edge detected for pair {out_pin}->{in_pin}")

        if failures:
            return "FAIL", " | ".join(failures + checks)
        return "PASS", " | ".join(checks)
    except Exception as exc:
        return "FAIL", f"Loopback setup/test failed: {exc}"
    finally:
        try:
            for dev in output_devices.values():
                try:
                    dev.off()
                    dev.close()
                except Exception:
                    pass
            for dev in input_devices.values():
                try:
                    dev.close()
                except Exception:
                    pass
            if backend == "RPi.GPIO" and gpio is not None:
                gpio.cleanup()
        except Exception:
            pass


def build_report_paths(report_dir: Path) -> tuple[Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_txt = report_dir / f"hardware_regression_{stamp}.txt"
    report_ndjson = report_dir / f"hardware_regression_{stamp}.ndjson"
    return report_txt, report_ndjson


def write_reports(report_txt: Path, report_ndjson: Path, results: list[CheckResult], argv: list[str]) -> None:
    report_txt.parent.mkdir(parents=True, exist_ok=True)

    status_counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

    with report_txt.open("w", encoding="utf-8") as handle:
        handle.write("Hardware Regression Checklist Report\n")
        handle.write(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        handle.write(f"Command: {' '.join(argv)}\n")
        handle.write("\n")
        handle.write("Summary\n")
        handle.write(f"PASS={status_counts['PASS']} WARN={status_counts['WARN']} ")
        handle.write(f"FAIL={status_counts['FAIL']} SKIP={status_counts['SKIP']}\n")
        handle.write("\n")
        handle.write("Checks\n")
        for result in results:
            handle.write(f"- {result.name}: {result.status} ({result.duration_s:.3f}s)\n")
            handle.write(f"  {result.details}\n")

    with report_ndjson.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(asdict(result), ensure_ascii=True) + "\n")


def print_console_summary(results: list[CheckResult], report_txt: Path, report_ndjson: Path) -> int:
    print("\nHardware Regression Checklist")
    print("=" * 34)
    fail_count = 0
    for result in results:
        print(f"{result.status:>4} | {result.name:<28} | {result.details}")
        if result.status == "FAIL":
            fail_count += 1

    print("\nArtifacts")
    print(f"- Text report:   {report_txt}")
    print(f"- NDJSON report: {report_ndjson}")

    return 1 if fail_count else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run hardware regression checklist on Raspberry Pi 5.")
    parser.add_argument("--skip-rfid", action="store_true", help="Skip RFID SPI probe.")
    parser.add_argument("--skip-stepper", action="store_true", help="Skip stepper pulse test.")
    parser.add_argument(
        "--slots",
        default="2",
        help="Comma-separated slot numbers for stepper pulse test (default: 2).",
    )
    parser.add_argument(
        "--stepper-steps",
        type=int,
        default=16,
        help="Number of step pulses per test slot (default: 16).",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.002,
        help="Stepper phase delay in seconds (default: 0.002).",
    )
    parser.add_argument(
        "--enable-loopback",
        action="store_true",
        help="Enable GPIO loopback checks (requires wired output->input pairs).",
    )
    parser.add_argument(
        "--loopback-pairs",
        default="12:24,21:25",
        help="Output:input comma list for loopback, e.g. 12:24,21:25.",
    )
    parser.add_argument(
        "--loopback-pulses",
        type=int,
        default=4,
        help="Pulse count per loopback pair (default: 4).",
    )
    parser.add_argument(
        "--loopback-pulse-s",
        type=float,
        default=0.04,
        help="Pulse high/low hold time in seconds for loopback tests.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory for generated reports (default: debug_logs).",
    )
    args = parser.parse_args(argv)

    if args.stepper_steps < 1:
        raise ChecklistError("--stepper-steps must be >= 1")

    slots = parse_slots(args.slots)
    report_dir = Path(args.report_dir).expanduser().resolve()

    checks = [
        ("Runtime environment", check_runtime_environment),
        ("SPI device presence", check_spi_device_present),
        ("GPIO backend availability", check_gpio_stack),
        ("RFID SPI probe", lambda: check_rfid_probe(skip=args.skip_rfid)),
        (
            "Stepper pulse test",
            lambda: check_stepper(
                skip=args.skip_stepper,
                slots=slots,
                steps=int(args.stepper_steps),
                delay_s=float(args.step_delay),
            ),
        ),
        (
            "GPIO loopback test",
            lambda: check_loopback(
                enable=args.enable_loopback,
                pair_text=args.loopback_pairs,
                pulses=int(args.loopback_pulses),
                pulse_s=float(args.loopback_pulse_s),
            ),
        ),
    ]

    results = [run_check(name, fn) for name, fn in checks]
    report_txt, report_ndjson = build_report_paths(report_dir)
    write_reports(report_txt, report_ndjson, results, argv=sys.argv)
    return print_console_summary(results, report_txt, report_ndjson)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ChecklistError as exc:
        print(f"[ERR] {exc}")
        raise SystemExit(2)
