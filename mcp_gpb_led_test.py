#!/usr/bin/env python3
"""Dedicated MCP23017 LED test tool for GPA/GPB validation.

This utility is intentionally simple so you can verify that the Raspberry Pi can
directly command MCP23017 GPIO pins on both ports.

Examples:
  python mcp_gpb_led_test.py --address 0x20 --pin 8 --on
  python mcp_gpb_led_test.py --address 0x20 --pin 8 --blink --count 6 --interval 0.25
  python mcp_gpb_led_test.py --address 0x20 --walk --count 3 --interval 0.2
    python mcp_gpb_led_test.py --address 0x20 --walk-all --count 2 --interval 0.2
    python mcp_gpb_led_test.py --address 0x20 --all-on
    python mcp_gpb_led_test.py --address 0x20 --all-off
"""

from __future__ import annotations

import argparse
import sys
import time


IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

GPB_PIN_MIN = 8
GPB_PIN_MAX = 15


class MCPError(Exception):
    pass


class MCPController:
    def __init__(self, bus_id: int, address: int):
        self.bus_id = bus_id
        self.address = address
        self.bus = None
        self.olat_a = 0x00
        self.olat_b = 0x00

    def _import_bus(self):
        try:
            from smbus2 import SMBus  # type: ignore

            return SMBus
        except Exception:
            try:
                from smbus import SMBus  # type: ignore

                return SMBus
            except Exception as exc:
                raise MCPError("Install smbus2 (or smbus) to use this tool.") from exc

    def open(self):
        SMBus = self._import_bus()
        try:
            self.bus = SMBus(self.bus_id)
        except Exception as exc:
            raise MCPError(f"Failed to open I2C bus {self.bus_id}: {exc}") from exc

    def close(self):
        if self.bus is None:
            return
        try:
            self.bus.close()
        except Exception:
            pass
        self.bus = None

    def probe(self):
        if self.bus is None:
            raise MCPError("I2C bus is not open.")
        try:
            _ = self.bus.read_byte_data(self.address, IODIRA)
        except Exception as exc:
            raise MCPError(
                f"No response from MCP at 0x{self.address:02X} on bus {self.bus_id}: {exc}"
            ) from exc

    def setup_outputs(self):
        if self.bus is None:
            raise MCPError("I2C bus is not open.")
        self.bus.write_byte_data(self.address, IODIRA, 0x00)
        self.bus.write_byte_data(self.address, IODIRB, 0x00)
        self.bus.write_byte_data(self.address, OLATA, 0x00)
        self.bus.write_byte_data(self.address, OLATB, 0x00)
        self.olat_a = 0x00
        self.olat_b = 0x00

    def _validate_gpb_pin(self, pin: int):
        if not (GPB_PIN_MIN <= pin <= GPB_PIN_MAX):
            raise MCPError(f"Pin {pin} is not a GPB pin. Use {GPB_PIN_MIN}..{GPB_PIN_MAX}.")

    def write_pin(self, pin: int, value: int):
        if self.bus is None:
            raise MCPError("I2C bus is not open.")
        if not (0 <= pin <= 15):
            raise MCPError("Pin must be in range 0..15")

        if pin < 8:
            bit = pin
            if value:
                self.olat_a |= 1 << bit
            else:
                self.olat_a &= ~(1 << bit)
            self.olat_a &= 0xFF
            self.bus.write_byte_data(self.address, OLATA, self.olat_a)
        else:
            bit = pin - 8
            if value:
                self.olat_b |= 1 << bit
            else:
                self.olat_b &= ~(1 << bit)
            self.olat_b &= 0xFF
            self.bus.write_byte_data(self.address, OLATB, self.olat_b)

    def all_off(self):
        if self.bus is None:
            return
        self.olat_a = 0x00
        self.olat_b = 0x00
        self.bus.write_byte_data(self.address, OLATA, 0x00)
        self.bus.write_byte_data(self.address, OLATB, 0x00)

    def all_on(self):
        if self.bus is None:
            return
        self.olat_a = 0xFF
        self.olat_b = 0xFF
        self.bus.write_byte_data(self.address, OLATA, 0xFF)
        self.bus.write_byte_data(self.address, OLATB, 0xFF)


def pin_label(pin: int) -> str:
    if 0 <= pin <= 7:
        return f"GPA{pin} (pin {pin})"
    if 8 <= pin <= 15:
        return f"GPB{pin - 8} (pin {pin})"
    return f"pin {pin}"


def parse_int_auto(value: str) -> int:
    return int(value, 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test MCP23017 pins (0..15) with an LED")
    parser.add_argument("--bus", type=int, default=1, help="I2C bus number (default: 1)")
    parser.add_argument(
        "--address",
        type=parse_int_auto,
        default=0x20,
        help="MCP23017 address (default: 0x20)",
    )
    parser.add_argument(
        "--pin",
        type=int,
        default=8,
        help="Target MCP pin number (0..15, default: 8 = GPB0)",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--on", action="store_true", help="Turn selected GPB pin ON")
    mode.add_argument("--off", action="store_true", help="Turn selected GPB pin OFF")
    mode.add_argument("--blink", action="store_true", help="Blink selected GPB pin")
    mode.add_argument(
        "--walk",
        action="store_true",
        help="Walk a single ON bit across GPB0..GPB7 and print the active pin name",
    )
    mode.add_argument(
        "--walk-all",
        action="store_true",
        help="Walk a single ON bit across GPA0..GPA7 and GPB0..GPB7",
    )
    mode.add_argument("--all-on", action="store_true", help="Turn all GPB pins ON")
    mode.add_argument("--all-off", action="store_true", help="Turn all GPB pins OFF")

    parser.add_argument("--count", type=int, default=6, help="Blink/walk cycles (default: 6)")
    parser.add_argument("--interval", type=float, default=0.2, help="Delay seconds (default: 0.2)")
    parser.add_argument(
        "--keep-state",
        action="store_true",
        help="Do not auto-clear GPB outputs at command end",
    )
    return parser


def do_blink(ctrl: MCPController, pin: int, count: int, interval: float):
    loops = max(1, int(count))
    delay = max(0.01, float(interval))
    for _ in range(loops):
        ctrl.write_pin(pin, 1)
        time.sleep(delay)
        ctrl.write_pin(pin, 0)
        time.sleep(delay)


def do_walk(ctrl: MCPController, count: int, interval: float):
    loops = max(1, int(count))
    delay = max(0.01, float(interval))
    for loop_idx in range(loops):
        print(f"[MCP-GPB] Walk cycle {loop_idx + 1}/{loops}")
        for pin in range(8, 16):
            gpb_index = pin - 8
            print(f"[MCP-GPB] Lighting GPB{gpb_index} (pin {pin})")
            ctrl.all_off()
            ctrl.write_pin(pin, 1)
            time.sleep(delay)
    ctrl.all_off()


def do_walk_all(ctrl: MCPController, count: int, interval: float):
    loops = max(1, int(count))
    delay = max(0.01, float(interval))
    for loop_idx in range(loops):
        print(f"[MCP-ALL] Walk cycle {loop_idx + 1}/{loops}")
        for pin in range(0, 16):
            print(f"[MCP-ALL] Lighting {pin_label(pin)}")
            ctrl.all_off()
            ctrl.write_pin(pin, 1)
            time.sleep(delay)
    ctrl.all_off()


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not (0x03 <= args.address <= 0x77):
        print(f"[ERR] Invalid I2C address 0x{args.address:02X}")
        return 1

    ctrl = MCPController(bus_id=args.bus, address=args.address)

    try:
        ctrl.open()
        ctrl.probe()
        ctrl.setup_outputs()

        print(f"[MCP] bus={args.bus}, address=0x{args.address:02X}, pin={args.pin}")

        if args.on:
            ctrl.write_pin(args.pin, 1)
            print(f"[MCP] {pin_label(args.pin)} set ON")
        elif args.off:
            ctrl.write_pin(args.pin, 0)
            print(f"[MCP] {pin_label(args.pin)} set OFF")
        elif args.blink:
            do_blink(ctrl, args.pin, args.count, args.interval)
            print(f"[MCP] Blink complete on {pin_label(args.pin)}")
        elif args.walk:
            do_walk(ctrl, args.count, args.interval)
            print("[MCP] GPB walk test complete")
        elif args.walk_all:
            do_walk_all(ctrl, args.count, args.interval)
            print("[MCP] All-pin walk test complete")
        elif args.all_on:
            ctrl.all_on()
            print("[MCP] GPA+GPB all ON")
        elif args.all_off:
            ctrl.all_off()
            print("[MCP] GPA+GPB all OFF")

        if not args.keep_state and not args.all_on:
            ctrl.all_off()
            print("[MCP] Auto-cleared outputs to OFF")

        ctrl.close()
        return 0

    except KeyboardInterrupt:
        print("\n[MCP] Interrupted")
        try:
            ctrl.all_off()
        except Exception:
            pass
        ctrl.close()
        return 130
    except MCPError as exc:
        print(f"[ERR] {exc}")
        return 1
    except Exception as exc:
        print(f"[ERR] Unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))