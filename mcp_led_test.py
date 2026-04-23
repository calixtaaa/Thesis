#!/usr/bin/env python3
"""Standalone MCP23017 LED test utility for Raspberry Pi.

Use this script to quickly verify MCP23017 output pins by turning LEDs on/off,
blinking selected pins, running a chase pattern, or spinning stepper motors.

Examples:
  python mcp_led_test.py --on --address 0x20 --pins 0 1 2 3
  python mcp_led_test.py --blink --pins 0 1 2 3 --iterations 10 --interval 0.2
  python mcp_led_test.py --chase --pins 0 1 2 3 4 5 6 7 --iterations 5 --interval 0.12
  python mcp_led_test.py --spin-slot 1 --steps 4096 --step-delay 0.002
  python mcp_led_test.py --ui --address 0x20
"""

from __future__ import annotations

import argparse
import sys
import time
import tkinter as tk
from tkinter import messagebox
from typing import Iterable


IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

ULN2003_SEQUENCE = [
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
]

DEFAULT_ADDRESSES = [0x20, 0x21, 0x22]
DEFAULT_PINS = [0, 1, 2, 3]

# Slot mapping mirrors main.py/hardware_pin_connections.txt defaults:
# slot 1..4 -> 0x20 GP0..15 in groups of 4
# slot 5..8 -> 0x21 GP0..15 in groups of 4
# slot 9..10 -> 0x22 GP0..7 in groups of 4
SLOT_TO_MCP_GROUP = {
    1: (0x20, [0, 1, 2, 3]),
    2: (0x20, [4, 5, 6, 7]),
    3: (0x20, [8, 9, 10, 11]),
    4: (0x20, [12, 13, 14, 15]),
    5: (0x21, [0, 1, 2, 3]),
    6: (0x21, [4, 5, 6, 7]),
    7: (0x21, [8, 9, 10, 11]),
    8: (0x21, [12, 13, 14, 15]),
    9: (0x22, [0, 1, 2, 3]),
    10: (0x22, [4, 5, 6, 7]),
}


class MCPError(Exception):
    """Raised for MCP configuration and I2C interaction failures."""


class MCP23017Controller:
    def __init__(self, bus_id: int, addresses: list[int]):
        self.bus_id = bus_id
        self.addresses = addresses
        self.bus = None
        self.olat_cache: dict[int, dict[str, int]] = {
            addr: {"A": 0x00, "B": 0x00} for addr in self.addresses
        }

    def _import_bus(self):
        try:
            from smbus2 import SMBus  # type: ignore

            return SMBus
        except Exception:
            try:
                from smbus import SMBus  # type: ignore

                return SMBus
            except Exception as exc:
                raise MCPError("Install smbus2 (or smbus) to use MCP23017 LED tests.") from exc

    def open(self) -> None:
        SMBus = self._import_bus()
        try:
            self.bus = SMBus(self.bus_id)
        except Exception as exc:
            raise MCPError(f"Failed to open I2C bus {self.bus_id}: {exc}") from exc

    def close(self) -> None:
        if self.bus is None:
            return
        try:
            self.bus.close()
        except Exception:
            pass
        self.bus = None

    def setup_outputs(self) -> None:
        if self.bus is None:
            raise MCPError("I2C bus is not open.")

        detected, missing = self.probe_addresses(self.addresses)
        if not detected:
            wanted = ", ".join(f"0x{x:02X}" for x in self.addresses)
            raise MCPError(
                "No MCP23017 devices responded on bus "
                f"{self.bus_id} for addresses [{wanted}]. "
                "Run `i2cdetect -y 1` and verify wiring (SDA/SCL/GND/VDD), RESET pull-up, and A0/A1/A2 address straps."
            )
        if missing:
            print(
                "[WARN] Some configured MCP addresses did not respond: "
                + ", ".join(f"0x{x:02X}" for x in missing)
            )

        for addr in self.addresses:
            try:
                self.bus.write_byte_data(addr, IODIRA, 0x00)
                self.bus.write_byte_data(addr, IODIRB, 0x00)
                self.bus.write_byte_data(addr, OLATA, 0x00)
                self.bus.write_byte_data(addr, OLATB, 0x00)
            except Exception as exc:
                raise MCPError(
                    f"Failed to initialize MCP23017 at 0x{addr:02X}. Check wiring/address: {exc}"
                ) from exc

            self.olat_cache[addr]["A"] = 0x00
            self.olat_cache[addr]["B"] = 0x00

    def probe_addresses(self, addresses: list[int]) -> tuple[list[int], list[int]]:
        """Return (detected, missing) address lists based on I2C ACK/read response."""
        if self.bus is None:
            raise MCPError("I2C bus is not open.")

        detected: list[int] = []
        missing: list[int] = []
        for addr in addresses:
            try:
                _ = self.bus.read_byte_data(addr, IODIRA)
                detected.append(addr)
            except Exception:
                missing.append(addr)
        return detected, missing

    def _validate_pin(self, pin: int) -> None:
        if not (0 <= pin <= 15):
            raise MCPError(f"Invalid MCP pin {pin}. Valid range is 0..15.")

    def write_pin(self, address: int, pin: int, value: int) -> None:
        if self.bus is None:
            raise MCPError("I2C bus is not open.")
        self._validate_pin(pin)

        if address not in self.olat_cache:
            raise MCPError(f"Address 0x{address:02X} was not configured.")

        port = "A" if pin < 8 else "B"
        bit = pin if pin < 8 else pin - 8
        current = self.olat_cache[address][port]

        if value:
            current |= 1 << bit
        else:
            current &= ~(1 << bit)

        self.olat_cache[address][port] = current & 0xFF

        reg = OLATA if port == "A" else OLATB
        try:
            self.bus.write_byte_data(address, reg, self.olat_cache[address][port])
        except Exception as exc:
            raise MCPError(
                f"I2C write failed at 0x{address:02X} pin {pin} ({port}{bit}): {exc}"
            ) from exc

    def write_many(self, pin_map: list[tuple[int, int]], value: int) -> None:
        for address, pin in pin_map:
            self.write_pin(address, pin, value)

    def all_off(self) -> None:
        if self.bus is None:
            return
        for addr in self.addresses:
            try:
                self.bus.write_byte_data(addr, OLATA, 0x00)
                self.bus.write_byte_data(addr, OLATB, 0x00)
            except Exception:
                pass
            self.olat_cache[addr]["A"] = 0x00
            self.olat_cache[addr]["B"] = 0x00


def parse_int_auto(text: str) -> int:
    return int(text, 0)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCP23017 LED on/off and blink tester")
    parser.add_argument(
        "--bus",
        type=int,
        default=1,
        help="I2C bus number (default: 1)",
    )
    parser.add_argument(
        "--addresses",
        nargs="+",
        type=parse_int_auto,
        default=DEFAULT_ADDRESSES,
        help="MCP23017 I2C addresses (supports decimal or hex like 0x20)",
    )
    parser.add_argument(
        "--address",
        type=parse_int_auto,
        default=None,
        help="Single MCP address to test (overrides --addresses)",
    )
    parser.add_argument(
        "--pins",
        nargs="+",
        type=int,
        default=DEFAULT_PINS,
        help="MCP pin numbers 0..15 to test (default: 0 1 2 3)",
    )
    parser.add_argument(
        "--slots",
        nargs="+",
        type=int,
        default=None,
        help="Slot presets 1..10 from project wiring map (overrides --address/--addresses/--pins)",
    )

    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument("--on", action="store_true", help="Turn selected pins on")
    mode.add_argument("--off", action="store_true", help="Turn selected pins off")
    mode.add_argument("--blink", action="store_true", help="Blink selected pins together")
    mode.add_argument("--chase", action="store_true", help="Chase one pin at a time")
    mode.add_argument("--spin-slot", type=int, default=None, help="Spin one slot using slot mapping")
    mode.add_argument("--all-off", action="store_true", help="Force all configured addresses off")
    parser.add_argument(
        "--list-slots",
        action="store_true",
        help="Print slot-to-MCP address/pin mapping. Can be used alone or before a test run.",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Open a simple UI for manual pin ON/OFF, blink, and pulse tests.",
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Blink/chase cycle count (default: 10)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Delay in seconds for blink/chase timing (default: 0.2)",
    )
    parser.add_argument(
        "--leave-on",
        action="store_true",
        help="Do not auto-clear pins when command finishes",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=4096,
        help="Stepper step count for --spin-slot (default: 4096 = ~1 revolution)",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.002,
        help="Delay per step for --spin-slot in seconds (default: 0.002)",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse direction for --spin-slot",
    )

    return parser.parse_args(argv)


def normalize_addresses(addresses: Iterable[int]) -> list[int]:
    unique = []
    seen = set()
    for addr in addresses:
        if not (0x03 <= addr <= 0x77):
            raise MCPError(f"Invalid I2C address {addr}. Expected 0x03..0x77.")
        if addr not in seen:
            unique.append(addr)
            seen.add(addr)
    if not unique:
        raise MCPError("At least one MCP address is required.")
    return unique


def normalize_pins(pins: Iterable[int]) -> list[int]:
    unique = []
    seen = set()
    for pin in pins:
        if not (0 <= pin <= 15):
            raise MCPError(f"Invalid pin {pin}. Valid range is 0..15.")
        if pin not in seen:
            unique.append(pin)
            seen.add(pin)
    if not unique:
        raise MCPError("At least one MCP pin is required.")
    return unique


def normalize_slots(slots: Iterable[int]) -> list[int]:
    unique = []
    seen = set()
    for slot in slots:
        if slot not in SLOT_TO_MCP_GROUP:
            raise MCPError(f"Invalid slot {slot}. Valid range is 1..10.")
        if slot not in seen:
            unique.append(slot)
            seen.add(slot)
    if not unique:
        raise MCPError("At least one slot is required when using --slots.")
    return unique


def build_pin_map(addresses: list[int], pins: list[int]) -> list[tuple[int, int]]:
    return [(addr, pin) for addr in addresses for pin in pins]


def build_pin_map_from_slots(slots: list[int]) -> tuple[list[int], list[tuple[int, int]]]:
    addresses: list[int] = []
    seen_addr = set()
    pin_map: list[tuple[int, int]] = []
    for slot in slots:
        address, pins = SLOT_TO_MCP_GROUP[slot]
        if address not in seen_addr:
            addresses.append(address)
            seen_addr.add(address)
        for pin in pins:
            pin_map.append((address, pin))
    return addresses, pin_map


def print_slot_map() -> None:
    print("[MCP] Slot mapping (default project wiring):")
    for slot in sorted(SLOT_TO_MCP_GROUP):
        address, pins = SLOT_TO_MCP_GROUP[slot]
        print(f"  slot {slot:>2}: 0x{address:02X} pins {pins}")


def print_quick_start() -> None:
    print("[MCP] Quick start examples:")
    print("  python mcp_led_test.py --list-slots")
    print("  python mcp_led_test.py --ui --address 0x20")
    print("  python mcp_led_test.py --blink --slots 1 --iterations 6 --interval 0.2")
    print("  python mcp_led_test.py --spin-slot 1 --steps 4096 --step-delay 0.002")
    print("  python mcp_led_test.py --all-off --address 0x20")


def resolve_targets(args: argparse.Namespace) -> tuple[list[int], list[tuple[int, int]], str]:
    if args.slots:
        slots = normalize_slots(args.slots)
        addresses, pin_map = build_pin_map_from_slots(slots)
        target_desc = f"slots {slots}"
        return addresses, pin_map, target_desc

    addresses = normalize_addresses([args.address] if args.address is not None else args.addresses)
    pins = normalize_pins(args.pins)
    pin_map = build_pin_map(addresses, pins)
    target_desc = f"pins {pins}"
    return addresses, pin_map, target_desc


def do_blink(ctrl: MCP23017Controller, pin_map: list[tuple[int, int]], iterations: int, interval: float) -> None:
    for _ in range(max(1, iterations)):
        ctrl.write_many(pin_map, 1)
        time.sleep(max(0.01, interval))
        ctrl.write_many(pin_map, 0)
        time.sleep(max(0.01, interval))


def do_chase(ctrl: MCP23017Controller, pin_map: list[tuple[int, int]], iterations: int, interval: float) -> None:
    steps = max(1, iterations)
    delay = max(0.01, interval)
    ctrl.write_many(pin_map, 0)

    for _ in range(steps):
        for address, pin in pin_map:
            ctrl.write_many(pin_map, 0)
            ctrl.write_pin(address, pin, 1)
            time.sleep(delay)

    ctrl.write_many(pin_map, 0)


def do_stepper_steps(
    ctrl: MCP23017Controller,
    address: int,
    slot_pins: list[int],
    steps: int,
    step_delay: float,
    reverse: bool = False,
) -> None:
    if len(slot_pins) != 4:
        raise MCPError("Slot mapping must contain exactly 4 pins for stepper sequence.")

    sequence = list(reversed(ULN2003_SEQUENCE)) if reverse else ULN2003_SEQUENCE
    total_steps = max(1, int(steps))
    delay = max(0.0005, float(step_delay))

    for idx in range(total_steps):
        phase = sequence[idx % len(sequence)]
        for pin, value in zip(slot_pins, phase):
            ctrl.write_pin(address, pin, int(value))
        time.sleep(delay)

    for pin in slot_pins:
        ctrl.write_pin(address, pin, 0)


class MCPTestUI:
    def __init__(self, ctrl: MCP23017Controller, addresses: list[int]):
        self.ctrl = ctrl
        self.addresses = addresses
        self.root = tk.Tk()
        self.root.title("MCP23017 Pin Test UI")
        self.root.geometry("860x620")
        self.root.configure(bg="#f4f6f8")

        self.status_var = tk.StringVar(value="Ready")
        self.detect_var = tk.StringVar(value="Detected: (not scanned)")
        self.address_var = tk.StringVar(value=f"0x{addresses[0]:02X}")
        self.slot_var = tk.StringVar(value="1")
        self.iterations_var = tk.StringVar(value="6")
        self.interval_var = tk.StringVar(value="0.2")
        self.pulse_var = tk.StringVar(value="0.3")
        self.step_delay_var = tk.StringVar(value="0.002")
        self.step_dir_var = tk.StringVar(value="forward")

        self.pin_selected: dict[int, tk.BooleanVar] = {pin: tk.BooleanVar(value=(pin in DEFAULT_PINS)) for pin in range(16)}
        self.pin_state_labels: dict[int, tk.Label] = {}

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        top = tk.Frame(self.root, bg="#f4f6f8")
        top.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(top, text="Address", bg="#f4f6f8", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        tk.OptionMenu(top, self.address_var, *[f"0x{a:02X}" for a in self.addresses]).pack(side=tk.LEFT, padx=(8, 14))

        tk.Label(top, text="Blink count", bg="#f4f6f8").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.iterations_var, width=6).pack(side=tk.LEFT, padx=(6, 12))

        tk.Label(top, text="Interval (s)", bg="#f4f6f8").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.interval_var, width=6).pack(side=tk.LEFT, padx=(6, 12))

        tk.Label(top, text="Pulse (s)", bg="#f4f6f8").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.pulse_var, width=6).pack(side=tk.LEFT, padx=(6, 12))

        tk.Label(top, text="Step delay (s)", bg="#f4f6f8").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.step_delay_var, width=7).pack(side=tk.LEFT, padx=(6, 12))

        slot_row = tk.Frame(self.root, bg="#f4f6f8")
        slot_row.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Label(slot_row, text="Slot", bg="#f4f6f8", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        tk.OptionMenu(slot_row, self.slot_var, *[str(slot) for slot in sorted(SLOT_TO_MCP_GROUP)]).pack(
            side=tk.LEFT, padx=(8, 10)
        )
        tk.Button(slot_row, text="Load slot pins", width=14, command=lambda: self._run_async(self._load_slot_selection)).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        tk.Label(
            slot_row,
            text="Loads mapped address and selects the 4 pins for that slot",
            bg="#f4f6f8",
            fg="#4b5563",
        ).pack(side=tk.LEFT)

        tk.OptionMenu(slot_row, self.step_dir_var, "forward", "reverse").pack(side=tk.LEFT, padx=(8, 8))
        tk.Button(
            slot_row,
            text="Spin 1 rev (4096)",
            width=15,
            command=lambda: self._run_async(self._spin_slot_one_rev),
        ).pack(side=tk.LEFT, padx=(0, 8))

        detect_row = tk.Frame(self.root, bg="#f4f6f8")
        detect_row.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Button(
            detect_row,
            text="Detect MCP",
            width=14,
            command=lambda: self._run_async(self._detect_addresses),
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(
            detect_row,
            textvariable=self.detect_var,
            bg="#f4f6f8",
            fg="#374151",
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        actions = tk.Frame(self.root, bg="#f4f6f8")
        actions.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Button(actions, text="ON selected", width=14, command=lambda: self._run_async(self._on_selected)).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="OFF selected", width=14, command=lambda: self._run_async(self._off_selected)).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="Blink selected", width=14, command=lambda: self._run_async(self._blink_selected)).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="Pulse selected", width=14, command=lambda: self._run_async(self._pulse_selected)).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="All OFF", width=12, command=lambda: self._run_async(self._all_off)).pack(side=tk.LEFT, padx=4)

        pins_wrap = tk.Frame(self.root, bg="#f4f6f8")
        pins_wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        for pin in range(16):
            row = pin // 4
            col = pin % 4
            card = tk.Frame(pins_wrap, bd=1, relief=tk.RIDGE, bg="#ffffff", padx=8, pady=6)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

            tk.Label(card, text=f"Pin {pin}", bg="#ffffff", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Checkbutton(card, text="Select", variable=self.pin_selected[pin], bg="#ffffff").pack(anchor="w")

            state = tk.Label(card, text="OFF", bg="#d1d5db", fg="#111827", width=8)
            state.pack(anchor="w", pady=(2, 4))
            self.pin_state_labels[pin] = state

            row_btn = tk.Frame(card, bg="#ffffff")
            row_btn.pack(anchor="w")
            tk.Button(row_btn, text="ON", width=6, command=lambda p=pin: self._run_async(lambda: self._set_single(p, 1))).pack(side=tk.LEFT, padx=(0, 4))
            tk.Button(row_btn, text="OFF", width=6, command=lambda p=pin: self._run_async(lambda: self._set_single(p, 0))).pack(side=tk.LEFT)

        for idx in range(4):
            pins_wrap.grid_columnconfigure(idx, weight=1)

        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#111827",
            fg="#f9fafb",
            anchor="w",
            padx=10,
            pady=8,
        )
        status.pack(fill=tk.X, side=tk.BOTTOM)

    def _get_address(self) -> int:
        return int(self.address_var.get(), 0)

    def _selected_pin_list(self) -> list[int]:
        pins = [p for p, var in self.pin_selected.items() if var.get()]
        if not pins:
            raise MCPError("Select at least one pin in the UI.")
        return pins

    def _read_float(self, value: str, name: str, minimum: float) -> float:
        try:
            parsed = float(value)
        except Exception as exc:
            raise MCPError(f"Invalid {name}: {value}") from exc
        if parsed < minimum:
            raise MCPError(f"{name} must be >= {minimum}.")
        return parsed

    def _read_int(self, value: str, name: str, minimum: int) -> int:
        try:
            parsed = int(value)
        except Exception as exc:
            raise MCPError(f"Invalid {name}: {value}") from exc
        if parsed < minimum:
            raise MCPError(f"{name} must be >= {minimum}.")
        return parsed

    def _set_state_label(self, pin: int, value: int) -> None:
        label = self.pin_state_labels[pin]
        if value:
            label.config(text="ON", bg="#34d399", fg="#052e16")
        else:
            label.config(text="OFF", bg="#d1d5db", fg="#111827")

    def _load_slot_selection(self) -> None:
        slot = int(self.slot_var.get())
        if slot not in SLOT_TO_MCP_GROUP:
            raise MCPError(f"Invalid slot {slot}.")

        address, pins = SLOT_TO_MCP_GROUP[slot]
        if address not in self.addresses:
            raise MCPError(
                f"Slot {slot} maps to 0x{address:02X}, but UI addresses are limited to "
                f"{', '.join(f'0x{x:02X}' for x in self.addresses)}"
            )

        self.address_var.set(f"0x{address:02X}")
        for pin in range(16):
            self.pin_selected[pin].set(pin in pins)
        self.status_var.set(f"Loaded slot {slot}: address 0x{address:02X}, pins {pins}")

    def _spin_slot_one_rev(self) -> None:
        slot = int(self.slot_var.get())
        if slot not in SLOT_TO_MCP_GROUP:
            raise MCPError(f"Invalid slot {slot}.")

        address, pins = SLOT_TO_MCP_GROUP[slot]
        if address not in self.addresses:
            raise MCPError(
                f"Slot {slot} maps to 0x{address:02X}, but UI addresses are limited to "
                f"{', '.join(f'0x{x:02X}' for x in self.addresses)}"
            )

        step_delay = self._read_float(self.step_delay_var.get().strip(), "step delay", 0.0005)
        reverse = self.step_dir_var.get().strip().lower() == "reverse"

        self.address_var.set(f"0x{address:02X}")
        for pin in range(16):
            self.pin_selected[pin].set(pin in pins)

        do_stepper_steps(self.ctrl, address, pins, 4096, step_delay, reverse=reverse)
        for pin in pins:
            self._set_state_label(pin, 0)
        self.status_var.set(
            f"Slot {slot} spin complete (4096 steps, {'reverse' if reverse else 'forward'})"
        )

    def _set_single(self, pin: int, value: int) -> None:
        self.ctrl.write_pin(self._get_address(), pin, value)
        self._set_state_label(pin, value)
        self.status_var.set(f"Set pin {pin} {'ON' if value else 'OFF'} on {self.address_var.get()}")

    def _detect_addresses(self) -> None:
        detected, missing = self.ctrl.probe_addresses(self.addresses)
        if detected:
            self.detect_var.set("Detected: " + ", ".join(f"0x{x:02X}" for x in detected))
            if missing:
                self.status_var.set("Missing: " + ", ".join(f"0x{x:02X}" for x in missing))
            else:
                self.status_var.set("All configured MCP addresses detected")
        else:
            self.detect_var.set("Detected: none")
            self.status_var.set("No configured MCP address responded")

    def _on_selected(self) -> None:
        address = self._get_address()
        for pin in self._selected_pin_list():
            self.ctrl.write_pin(address, pin, 1)
            self._set_state_label(pin, 1)
        self.status_var.set(f"Selected pins ON at {self.address_var.get()}")

    def _off_selected(self) -> None:
        address = self._get_address()
        for pin in self._selected_pin_list():
            self.ctrl.write_pin(address, pin, 0)
            self._set_state_label(pin, 0)
        self.status_var.set(f"Selected pins OFF at {self.address_var.get()}")

    def _blink_selected(self) -> None:
        address = self._get_address()
        pins = self._selected_pin_list()
        iterations = self._read_int(self.iterations_var.get().strip(), "blink count", 1)
        interval = self._read_float(self.interval_var.get().strip(), "interval", 0.01)

        for _ in range(iterations):
            for pin in pins:
                self.ctrl.write_pin(address, pin, 1)
                self._set_state_label(pin, 1)
            time.sleep(interval)
            for pin in pins:
                self.ctrl.write_pin(address, pin, 0)
                self._set_state_label(pin, 0)
            time.sleep(interval)

        self.status_var.set(f"Blink complete on {self.address_var.get()} for pins {pins}")

    def _pulse_selected(self) -> None:
        address = self._get_address()
        pins = self._selected_pin_list()
        pulse_s = self._read_float(self.pulse_var.get().strip(), "pulse seconds", 0.01)

        for pin in pins:
            self.ctrl.write_pin(address, pin, 1)
            self._set_state_label(pin, 1)
        time.sleep(pulse_s)
        for pin in pins:
            self.ctrl.write_pin(address, pin, 0)
            self._set_state_label(pin, 0)

        self.status_var.set(f"Pulse complete on {self.address_var.get()} for pins {pins}")

    def _all_off(self) -> None:
        self.ctrl.all_off()
        for pin in range(16):
            self._set_state_label(pin, 0)
        self.status_var.set("All configured MCP addresses forced OFF")

    def _run_async(self, fn) -> None:
        try:
            fn()
        except Exception as exc:
            messagebox.showerror("MCP test error", str(exc))
            self.status_var.set(f"Error: {exc}")

    def _on_close(self) -> None:
        try:
            self.ctrl.all_off()
            self.ctrl.close()
        except Exception:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run_ui(args: argparse.Namespace) -> int:
    addresses = normalize_addresses([args.address] if args.address is not None else args.addresses)
    ctrl = MCP23017Controller(bus_id=args.bus, addresses=addresses)
    ctrl.open()

    detected, missing = ctrl.probe_addresses(addresses)
    if not detected:
        wanted = ", ".join(f"0x{x:02X}" for x in addresses)
        ctrl.close()
        raise MCPError(
            "No MCP23017 devices responded for UI startup on "
            f"bus {args.bus} for addresses [{wanted}]."
        )

    if missing:
        print(
            "[WARN] UI fallback: only using detected MCP addresses: "
            + ", ".join(f"0x{x:02X}" for x in detected)
        )

    ctrl.addresses = detected
    ctrl.olat_cache = {addr: {"A": 0x00, "B": 0x00} for addr in detected}
    ctrl.setup_outputs()
    print(f"[MCP] UI ready on bus {args.bus}, addresses: {', '.join(f'0x{x:02X}' for x in detected)}")
    ui = MCPTestUI(ctrl=ctrl, addresses=detected)
    ui.run()
    return 0


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)

        if args.list_slots:
            print_slot_map()

        selected_mode = any((args.on, args.off, args.blink, args.chase, args.all_off, args.spin_slot is not None))

        if args.ui:
            return run_ui(args)

        if not selected_mode:
            if args.list_slots:
                return 0
            print_slot_map()
            print_quick_start()
            return 0

        if args.spin_slot is not None:
            spin_slot = normalize_slots([args.spin_slot])[0]
            spin_address, spin_pins = SLOT_TO_MCP_GROUP[spin_slot]
            addresses = [spin_address]
            pin_map = [(spin_address, pin) for pin in spin_pins]
            target_desc = f"spin slot {spin_slot}"
        else:
            addresses, pin_map, target_desc = resolve_targets(args)

        ctrl = MCP23017Controller(bus_id=args.bus, addresses=addresses)
        ctrl.open()
        ctrl.setup_outputs()

        print(
            f"[MCP] Bus {args.bus}, addresses: {', '.join(f'0x{x:02X}' for x in addresses)}, "
            f"target: {target_desc}"
        )

        if args.all_off:
            ctrl.all_off()
            print("[MCP] All configured outputs forced OFF.")
            ctrl.close()
            return 0

        if args.on:
            ctrl.write_many(pin_map, 1)
            print("[MCP] Selected pins are ON.")
        elif args.off:
            ctrl.write_many(pin_map, 0)
            print("[MCP] Selected pins are OFF.")
        elif args.blink:
            do_blink(ctrl, pin_map, args.iterations, args.interval)
            print("[MCP] Blink test complete.")
        elif args.chase:
            do_chase(ctrl, pin_map, args.iterations, args.interval)
            print("[MCP] Chase test complete.")
        elif args.spin_slot is not None:
            do_stepper_steps(
                ctrl,
                spin_address,
                spin_pins,
                args.steps,
                args.step_delay,
                reverse=args.reverse,
            )
            print(
                f"[MCP] Slot {spin_slot} spin complete ({max(1, int(args.steps))} steps, "
                f"{'reverse' if args.reverse else 'forward'})."
            )

        if not args.leave_on:
            ctrl.write_many(pin_map, 0)
            print("[MCP] Auto-cleared selected pins to OFF.")

        ctrl.close()
        return 0

    except KeyboardInterrupt:
        print("\n[MCP] Interrupted by user.")
        return 130
    except MCPError as exc:
        print(f"[ERR] {exc}")
        return 1
    except Exception as exc:
        print(f"[ERR] Unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
