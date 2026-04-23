"""
Standalone MCP23017 stepper motor test utility for the vending machine.

This tool mirrors the existing stepper.py experience but drives ULN2003 inputs
through MCP23017 GPIO expander pins over I2C.
"""

from __future__ import annotations

import threading
import time
import tkinter as tk
from datetime import date
from tkinter import messagebox

import customtkinter as ctk


IODIRA = 0x00
IODIRB = 0x01
OLATA = 0x14
OLATB = 0x15

DEFAULT_STEPS_PER_REV = 4096
DEFAULT_STEP_DELAY = 0.002
DEFAULT_I2C_BUS = 1
DEFAULT_ADDRESSES = [0x20, 0x21, 0x22]

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


class MCPError(Exception):
    pass


class MCP23017Controller:
    def __init__(self, bus_id: int, addresses: list[int]):
        self.bus_id = bus_id
        self.addresses = addresses
        self.bus = None
        self.olat_cache = {addr: {"A": 0x00, "B": 0x00} for addr in addresses}

    def _import_bus(self):
        try:
            from smbus2 import SMBus  # type: ignore

            return SMBus
        except Exception:
            try:
                from smbus import SMBus  # type: ignore

                return SMBus
            except Exception as exc:
                raise MCPError("Install smbus2 (or smbus) for MCP23017 stepper mode.") from exc

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
            self.all_off()
        except Exception:
            pass
        try:
            self.bus.close()
        except Exception:
            pass
        self.bus = None

    def probe_addresses(self, addresses: list[int]) -> tuple[list[int], list[int]]:
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

    def setup_outputs(self):
        if self.bus is None:
            raise MCPError("I2C bus is not open.")

        detected, missing = self.probe_addresses(self.addresses)
        if not detected:
            wanted = ", ".join(f"0x{x:02X}" for x in self.addresses)
            raise MCPError(
                "No MCP23017 devices responded on I2C bus "
                f"{self.bus_id} for addresses [{wanted}]"
            )

        self.addresses = detected
        self.olat_cache = {addr: {"A": 0x00, "B": 0x00} for addr in detected}

        for addr in self.addresses:
            self.bus.write_byte_data(addr, IODIRA, 0x00)
            self.bus.write_byte_data(addr, IODIRB, 0x00)
            self.bus.write_byte_data(addr, OLATA, 0x00)
            self.bus.write_byte_data(addr, OLATB, 0x00)

        return missing

    def write_pin(self, address: int, pin: int, value: int):
        if self.bus is None:
            raise MCPError("I2C bus is not open.")
        if address not in self.olat_cache:
            raise MCPError(f"Address 0x{address:02X} is not initialized.")
        if not (0 <= pin <= 15):
            raise MCPError(f"Invalid pin {pin}; expected 0..15")

        port = "A" if pin < 8 else "B"
        bit = pin if pin < 8 else pin - 8
        current = self.olat_cache[address][port]
        if value:
            current |= 1 << bit
        else:
            current &= ~(1 << bit)
        self.olat_cache[address][port] = current & 0xFF

        register = OLATA if port == "A" else OLATB
        self.bus.write_byte_data(address, register, self.olat_cache[address][port])

    def write_phase(self, address: int, pins: list[int], phase: tuple[int, int, int, int]):
        if len(pins) != 4:
            raise MCPError("Stepper slot must map to 4 pins.")
        for pin, value in zip(pins, phase):
            self.write_pin(address, pin, int(value))

    def all_off(self):
        if self.bus is None:
            return
        for addr in self.addresses:
            try:
                self.bus.write_byte_data(addr, OLATA, 0x00)
                self.bus.write_byte_data(addr, OLATB, 0x00)
            except Exception:
                pass
            if addr in self.olat_cache:
                self.olat_cache[addr]["A"] = 0x00
                self.olat_cache[addr]["B"] = 0x00


def build_slot_map(addresses: list[int]) -> dict[int, dict]:
    mapping: dict[int, dict] = {}
    slot = 1
    for address in addresses:
        for base_pin in (0, 4, 8, 12):
            if slot > 10:
                return mapping
            mapping[slot] = {
                "backend": "mcp23017",
                "address": address,
                "pins": [base_pin, base_pin + 1, base_pin + 2, base_pin + 3],
            }
            slot += 1
    return mapping


class StepperMCPTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stepper MCP23017 Test Tool")
        self.geometry("980x700")
        self.minsize(760, 520)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.current_theme = {
            "bg": "#f8fafc",
            "fg": "#0f172a",
            "card_bg": "#ffffff",
            "card_border": "#e2e8f0",
            "accent": "#10b981",
            "accent_hover": "#059669",
            "button_bg": "#f1f5f9",
            "button_fg": "#0f172a",
            "nav_bg": "#0f172a",
            "nav_fg": "#ffffff",
            "muted": "#475569",
            "status_ok": "#059669",
            "status_warn": "#d97706",
            "status_error": "#b91c1c",
        }

        self.i2c_bus = tk.IntVar(value=DEFAULT_I2C_BUS)
        self.configured_addresses = DEFAULT_ADDRESSES.copy()
        self.detected_addresses: list[int] = []
        self.slot_map: dict[int, dict] = {}

        self.current_slot = tk.StringVar(value="1")
        self.steps_per_rev = tk.IntVar(value=DEFAULT_STEPS_PER_REV)
        self.step_delay_ms = tk.DoubleVar(value=DEFAULT_STEP_DELAY * 1000)
        self.custom_steps = tk.IntVar(value=512)
        self.direction = tk.StringVar(value="forward")
        self.status_text = tk.StringVar(value="MCP backend: initializing")
        self.detect_text = tk.StringVar(value="Detected MCP: (not scanned)")
        self.calibration_counter_text = tk.StringVar(value="Calibration jog counter: 0 steps")
        self.snippet_status_text = tk.StringVar(value="Snippet output: not generated")

        self.running = False
        self.stop_requested = False
        self._phase_index = 0
        self._calibration_steps = 0

        self.ctrl: MCP23017Controller | None = None

        self._build_ui()
        self.current_slot.trace_add("write", self._on_slot_change)
        self._setup_mcp()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=self.current_theme["nav_bg"], corner_radius=0, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side=tk.LEFT, padx=22, pady=14)
        ctk.CTkLabel(
            title_box,
            text="Stepper MCP23017 Test Tool",
            font=("Segoe UI", 22, "bold"),
            text_color=self.current_theme["nav_fg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Standalone 28BYJ-48 + ULN2003 test via MCP23017 I2C expander",
            font=("Segoe UI", 11),
            text_color=self.current_theme["nav_fg"],
        ).pack(anchor="w")

        status_chip = ctk.CTkLabel(
            header,
            textvariable=self.status_text,
            font=("Segoe UI", 11, "bold"),
            text_color=self.current_theme["nav_fg"],
            fg_color="#334155",
            corner_radius=12,
            padx=14,
            pady=8,
        )
        status_chip.pack(side=tk.RIGHT, padx=22, pady=16)

        main = ctk.CTkFrame(self, fg_color=self.current_theme["bg"], corner_radius=0)
        main.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        left = ctk.CTkScrollableFrame(
            main,
            fg_color=self.current_theme["bg"],
            corner_radius=0,
            scrollbar_button_color=self.current_theme["card_border"],
            scrollbar_button_hover_color="#cbd5e1",
        )
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = ctk.CTkFrame(main, fg_color=self.current_theme["bg"], corner_radius=0, width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right.pack_propagate(False)

        control_card = self._card(left)
        control_card.pack(fill=tk.BOTH, expand=True)

        ctk.CTkLabel(
            control_card,
            text="Motor Controls",
            font=("Segoe UI", 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=18, pady=(18, 4))
        ctk.CTkLabel(
            control_card,
            text="Slot mapping follows main.py: slot 1..4 on 0x20, 5..8 on 0x21, 9..10 on 0x22.",
            font=("Segoe UI", 11),
            text_color=self.current_theme["muted"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 12))

        bus_row = ctk.CTkFrame(control_card, fg_color="transparent")
        bus_row.pack(fill=tk.X, padx=18, pady=(0, 8))
        ctk.CTkLabel(
            bus_row,
            text="I2C bus",
            font=("Segoe UI", 11, "bold"),
            text_color=self.current_theme["fg"],
            width=150,
            anchor="w",
        ).pack(side=tk.LEFT)
        ctk.CTkEntry(
            bus_row,
            textvariable=self.i2c_bus,
            fg_color=self.current_theme["button_bg"],
            text_color=self.current_theme["fg"],
            border_color=self.current_theme["card_border"],
            corner_radius=8,
            width=90,
            height=36,
        ).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(
            bus_row,
            text="Detect MCP",
            command=self.detect_mcp,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            width=140,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT)

        ctk.CTkLabel(
            control_card,
            textvariable=self.detect_text,
            font=("Consolas", 11),
            text_color=self.current_theme["fg"],
            justify="left",
            anchor="w",
        ).pack(fill=tk.X, padx=18, pady=(0, 10))

        form = ctk.CTkFrame(control_card, fg_color="transparent")
        form.pack(fill=tk.X, padx=18, pady=(0, 10))
        form.grid_columnconfigure(1, weight=1)

        self._field(form, 0, "Slot number", self.current_slot, input_widget="spin")
        self._field(form, 1, "Steps per revolution", self.steps_per_rev)
        self._field(form, 2, "Step delay (ms)", self.step_delay_ms)
        self._field(form, 3, "Custom steps", self.custom_steps)

        dir_row = ctk.CTkFrame(control_card, fg_color="transparent")
        dir_row.pack(fill=tk.X, padx=18, pady=(0, 14))
        ctk.CTkLabel(
            dir_row,
            text="Direction",
            font=("Segoe UI", 11, "bold"),
            text_color=self.current_theme["fg"],
            width=150,
            anchor="w",
        ).pack(side=tk.LEFT)
        ctk.CTkOptionMenu(
            dir_row,
            values=["forward", "reverse"],
            variable=self.direction,
            fg_color=self.current_theme["button_bg"],
            button_color=self.current_theme["accent"],
            button_hover_color=self.current_theme["accent_hover"],
            text_color=self.current_theme["button_fg"],
            dropdown_fg_color=self.current_theme["card_bg"],
            dropdown_text_color=self.current_theme["fg"],
            width=180,
        ).pack(side=tk.LEFT)

        button_row = ctk.CTkFrame(control_card, fg_color="transparent")
        button_row.pack(fill=tk.X, padx=18, pady=(0, 10))
        ctk.CTkButton(
            button_row,
            text="Spin 1 revolution",
            command=self.spin_one_revolution,
            fg_color=self.current_theme["accent"],
            hover_color=self.current_theme["accent_hover"],
            text_color="#ffffff",
            height=42,
            corner_radius=10,
        ).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        ctk.CTkButton(
            button_row,
            text="Run custom steps",
            command=self.run_custom_steps,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            height=42,
            corner_radius=10,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        stop_row = ctk.CTkFrame(control_card, fg_color="transparent")
        stop_row.pack(fill=tk.X, padx=18, pady=(0, 16))
        ctk.CTkButton(
            stop_row,
            text="Stop motor",
            command=self.stop_motor,
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color="#ffffff",
            height=40,
            corner_radius=10,
        ).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        ctk.CTkButton(
            stop_row,
            text="All coils OFF",
            command=self.all_coils_off,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            height=40,
            corner_radius=10,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_label = ctk.CTkLabel(
            control_card,
            text="Idle",
            font=("Segoe UI", 12, "bold"),
            text_color=self.current_theme["status_ok"],
        )
        self.progress_label.pack(anchor="w", padx=18, pady=(0, 16))

        calibration_card = self._card(left)
        calibration_card.pack(fill=tk.X, pady=(10, 0))
        ctk.CTkLabel(
            calibration_card,
            text="Calibration Mode",
            font=("Segoe UI", 16, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(
            calibration_card,
            text="Use jog buttons to measure one dispenser cycle, then generate a snippet for main.py.",
            font=("Segoe UI", 11),
            text_color=self.current_theme["muted"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 10))

        self.calibration_counter_label = ctk.CTkLabel(
            calibration_card,
            textvariable=self.calibration_counter_text,
            font=("Consolas", 12),
            text_color=self.current_theme["fg"],
        )
        self.calibration_counter_label.pack(anchor="w", padx=18, pady=(0, 8))

        jog_forward_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        jog_forward_row.pack(fill=tk.X, padx=18, pady=(0, 8))
        ctk.CTkButton(jog_forward_row, text="Jog +1", command=lambda: self.calibration_jog(1), fg_color=self.current_theme["accent"], hover_color=self.current_theme["accent_hover"], text_color="#ffffff", width=100, height=36, corner_radius=8).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(jog_forward_row, text="Jog +8", command=lambda: self.calibration_jog(8), fg_color=self.current_theme["accent"], hover_color=self.current_theme["accent_hover"], text_color="#ffffff", width=100, height=36, corner_radius=8).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(jog_forward_row, text="Jog +64", command=lambda: self.calibration_jog(64), fg_color=self.current_theme["accent"], hover_color=self.current_theme["accent_hover"], text_color="#ffffff", width=100, height=36, corner_radius=8).pack(side=tk.LEFT)

        jog_reverse_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        jog_reverse_row.pack(fill=tk.X, padx=18, pady=(0, 10))
        ctk.CTkButton(jog_reverse_row, text="Jog -1", command=lambda: self.calibration_jog(-1), fg_color=self.current_theme["button_bg"], hover_color=self.current_theme["card_border"], text_color=self.current_theme["button_fg"], width=100, height=36, corner_radius=8).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(jog_reverse_row, text="Jog -8", command=lambda: self.calibration_jog(-8), fg_color=self.current_theme["button_bg"], hover_color=self.current_theme["card_border"], text_color=self.current_theme["button_fg"], width=100, height=36, corner_radius=8).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(jog_reverse_row, text="Jog -64", command=lambda: self.calibration_jog(-64), fg_color=self.current_theme["button_bg"], hover_color=self.current_theme["card_border"], text_color=self.current_theme["button_fg"], width=100, height=36, corner_radius=8).pack(side=tk.LEFT)

        calibration_action_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        calibration_action_row.pack(fill=tk.X, padx=18, pady=(0, 14))
        ctk.CTkButton(calibration_action_row, text="Reset counter", command=self.reset_calibration_counter, fg_color=self.current_theme["button_bg"], hover_color=self.current_theme["card_border"], text_color=self.current_theme["button_fg"], width=170, height=38, corner_radius=8).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(calibration_action_row, text="Apply counter to steps/rev", command=self.apply_calibration_to_steps, fg_color="#0ea5e9", hover_color="#0284c7", text_color="#ffffff", width=230, height=38, corner_radius=8).pack(side=tk.LEFT)

        export_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        export_row.pack(fill=tk.X, padx=18, pady=(0, 10))
        ctk.CTkButton(export_row, text="Generate main.py snippet", command=self.generate_main_snippet, fg_color="#111827", hover_color="#1f2937", text_color="#ffffff", width=220, height=38, corner_radius=8).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(export_row, text="Copy snippet", command=self.copy_generated_snippet, fg_color=self.current_theme["button_bg"], hover_color=self.current_theme["card_border"], text_color=self.current_theme["button_fg"], width=140, height=38, corner_radius=8).pack(side=tk.LEFT)

        ctk.CTkLabel(
            calibration_card,
            textvariable=self.snippet_status_text,
            font=("Segoe UI", 10),
            text_color=self.current_theme["muted"],
        ).pack(anchor="w", padx=18, pady=(0, 6))

        self.snippet_box = ctk.CTkTextbox(
            calibration_card,
            height=140,
            fg_color="#0b1220",
            text_color="#e2e8f0",
            border_color=self.current_theme["card_border"],
            border_width=1,
            corner_radius=10,
            font=("Consolas", 11),
            wrap="none",
        )
        self.snippet_box.pack(fill=tk.X, padx=18, pady=(0, 14))
        self.snippet_box.insert(
            "1.0",
            "# Generate a calibration snippet after jogging one full dispense cycle.\n"
            "# Then paste it near STEPS_PER_PRODUCT in main.py.\n",
        )
        self.snippet_box.configure(state="disabled")

        info_card = self._card(right)
        info_card.pack(fill=tk.BOTH, expand=True)
        ctk.CTkLabel(
            info_card,
            text="MCP Wiring Summary",
            font=("Segoe UI", 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=18, pady=(18, 8))

        info_text = (
            "MCP23017 GPIO -> ULN2003 IN1..IN4\n"
            "Pi GPIO2/GPIO3 -> MCP SDA/SCL\n"
            "Pi 3.3V -> MCP VDD, Pi GND -> MCP VSS\n"
            "RESET needs pull-up to 3.3V\n\n"
            "Slot map:\n"
            "1-4 => 0x20\n"
            "5-8 => 0x21\n"
            "9-10 => 0x22"
        )
        ctk.CTkLabel(
            info_card,
            text=info_text,
            font=("Segoe UI", 11),
            text_color=self.current_theme["muted"],
            justify="left",
            wraplength=280,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        self.pin_preview = ctk.CTkLabel(
            info_card,
            text="Selected slot: 1\nMCP 0x20\nIN1 GP0\nIN2 GP1\nIN3 GP2\nIN4 GP3",
            font=("Consolas", 11),
            text_color=self.current_theme["fg"],
            justify="left",
            anchor="w",
        )
        self.pin_preview.pack(fill=tk.X, padx=18, pady=(0, 14))

        self._refresh_preview()

    def _card(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=self.current_theme["card_bg"],
            border_width=1,
            border_color=self.current_theme["card_border"],
            corner_radius=16,
        )

    def _field(self, parent, row, label_text, variable, input_widget="entry"):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=("Segoe UI", 11, "bold"),
            text_color=self.current_theme["fg"],
            width=170,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        if input_widget == "spin":
            widget = ctk.CTkOptionMenu(
                row_frame,
                values=[str(i) for i in range(1, 11)],
                variable=variable,
                command=self._slot_changed,
                fg_color=self.current_theme["button_bg"],
                button_color=self.current_theme["accent"],
                button_hover_color=self.current_theme["accent_hover"],
                text_color=self.current_theme["button_fg"],
                dropdown_fg_color=self.current_theme["card_bg"],
                dropdown_text_color=self.current_theme["fg"],
                width=220,
            )
            widget.grid(row=0, column=1, sticky="ew")
        else:
            widget = ctk.CTkEntry(
                row_frame,
                textvariable=variable,
                fg_color=self.current_theme["button_bg"],
                text_color=self.current_theme["fg"],
                border_color=self.current_theme["card_border"],
                corner_radius=8,
                height=36,
            )
            widget.grid(row=0, column=1, sticky="ew")

    def _setup_mcp(self):
        self._cleanup_mcp()
        bus_id = int(self.i2c_bus.get())
        self.ctrl = MCP23017Controller(bus_id=bus_id, addresses=self.configured_addresses.copy())
        try:
            self.ctrl.open()
            missing = self.ctrl.setup_outputs()
            self.detected_addresses = self.ctrl.addresses.copy()
            self.slot_map = build_slot_map(self.detected_addresses)
            self.detect_text.set(
                "Detected MCP: " + ", ".join(f"0x{x:02X}" for x in self.detected_addresses)
            )
            if missing:
                self.status_text.set(
                    "Ready (missing: " + ", ".join(f"0x{x:02X}" for x in missing) + ")"
                )
            else:
                self.status_text.set(f"Ready on I2C bus {bus_id}")
            self.progress_label.configure(text="Idle", text_color=self.current_theme["status_ok"])
        except Exception as exc:
            self.detected_addresses = []
            self.slot_map = {}
            self.status_text.set(f"MCP setup failed: {exc}")
            self.detect_text.set("Detected MCP: none")
            messagebox.showerror("MCP setup failed", str(exc))
        finally:
            self._refresh_preview()

    def _cleanup_mcp(self):
        if self.ctrl is None:
            return
        try:
            self.ctrl.close()
        except Exception:
            pass
        self.ctrl = None

    def detect_mcp(self):
        self._setup_mcp()

    def _get_slot_number(self):
        try:
            return int(self.current_slot.get())
        except Exception:
            return 1

    def _slot_changed(self, value):
        self.current_slot.set(str(value))
        self._on_slot_change()

    def _on_slot_change(self, *_args):
        self._refresh_preview()
        self.reset_calibration_counter(update_status=False)

    def _refresh_preview(self):
        slot = self._get_slot_number()
        cfg = self.slot_map.get(slot)
        if not cfg:
            self.pin_preview.configure(text=f"Selected slot: {slot}\nNo MCP mapping available")
            return
        address = int(cfg["address"])
        pins = cfg["pins"]
        self.pin_preview.configure(
            text=(
                f"Selected slot: {slot}\n"
                f"MCP 0x{address:02X}\n"
                f"IN1 GP{pins[0]}\n"
                f"IN2 GP{pins[1]}\n"
                f"IN3 GP{pins[2]}\n"
                f"IN4 GP{pins[3]}"
            )
        )

    def _slot_config(self, slot: int):
        cfg = self.slot_map.get(slot)
        if not cfg:
            raise MCPError(
                f"No MCP mapping for slot {slot}. Detected addresses: "
                f"{', '.join(f'0x{x:02X}' for x in self.detected_addresses) or 'none'}"
            )
        return cfg

    def _rotate(self, steps, slot=None):
        if self.running:
            return
        if self.ctrl is None:
            raise MCPError("MCP backend is not ready.")

        slot_number = slot if slot is not None else self._get_slot_number()
        cfg = self._slot_config(slot_number)
        address = int(cfg["address"])
        pins = cfg["pins"]

        try:
            step_delay = max(0.0005, float(self.step_delay_ms.get()) / 1000.0)
        except Exception:
            step_delay = DEFAULT_STEP_DELAY

        sequence = ULN2003_SEQUENCE if self.direction.get() == "forward" else list(reversed(ULN2003_SEQUENCE))
        total_steps = max(1, int(steps))

        def worker():
            self.running = True
            self.stop_requested = False
            self.progress_label.configure(text="Running", text_color=self.current_theme["status_warn"])
            try:
                for index in range(total_steps):
                    if self.stop_requested:
                        break
                    phase = sequence[index % len(sequence)]
                    self.ctrl.write_phase(address, pins, phase)
                    time.sleep(step_delay)

                self.ctrl.write_phase(address, pins, (0, 0, 0, 0))
                final_text = "Stopped" if self.stop_requested else f"Completed {total_steps} steps"
                color = self.current_theme["status_warn"] if self.stop_requested else self.current_theme["status_ok"]
                self.after(0, lambda: self.progress_label.configure(text=final_text, text_color=color))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Stepper error", str(exc)))
                self.after(0, lambda: self.progress_label.configure(text="Error", text_color=self.current_theme["status_error"]))
            finally:
                try:
                    self.ctrl.write_phase(address, pins, (0, 0, 0, 0))
                except Exception:
                    pass
                self.running = False

        threading.Thread(target=worker, daemon=True).start()

    def spin_one_revolution(self):
        self._refresh_preview()
        try:
            steps = int(self.steps_per_rev.get())
            self._rotate(steps)
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc))

    def run_custom_steps(self):
        self._refresh_preview()
        try:
            steps = int(self.custom_steps.get())
        except Exception:
            messagebox.showerror("Invalid input", "Custom steps must be a number.")
            return
        if steps <= 0:
            messagebox.showerror("Invalid input", "Custom steps must be greater than zero.")
            return
        try:
            self._rotate(steps)
        except Exception as exc:
            messagebox.showerror("Stepper error", str(exc))

    def stop_motor(self):
        self.stop_requested = True
        self.progress_label.configure(text="Stop requested", text_color=self.current_theme["status_warn"])

    def all_coils_off(self):
        if self.ctrl is None:
            return
        try:
            self.ctrl.all_off()
            self.progress_label.configure(text="All coils OFF", text_color=self.current_theme["status_ok"])
        except Exception as exc:
            messagebox.showerror("MCP error", str(exc))

    def reset_calibration_counter(self, update_status=True):
        self._calibration_steps = 0
        self._phase_index = 0
        self.calibration_counter_text.set("Calibration jog counter: 0 steps")
        if update_status:
            self.progress_label.configure(text="Calibration counter reset", text_color=self.current_theme["status_ok"])

    def _jog_steps_blocking(self, cfg, delta_steps, step_delay):
        if self.ctrl is None:
            raise MCPError("MCP backend is not ready.")
        address = int(cfg["address"])
        pins = cfg["pins"]
        count = abs(int(delta_steps))
        direction = 1 if delta_steps >= 0 else -1
        for _ in range(count):
            if direction > 0:
                self._phase_index = (self._phase_index + 1) % len(ULN2003_SEQUENCE)
            else:
                self._phase_index = (self._phase_index - 1) % len(ULN2003_SEQUENCE)
            self.ctrl.write_phase(address, pins, ULN2003_SEQUENCE[self._phase_index])
            time.sleep(step_delay)
        self.ctrl.write_phase(address, pins, (0, 0, 0, 0))

    def calibration_jog(self, delta_steps):
        if self.running:
            return
        try:
            cfg = self._slot_config(self._get_slot_number())
        except Exception as exc:
            messagebox.showerror("Invalid slot", str(exc))
            return

        try:
            step_delay = max(0.001, float(self.step_delay_ms.get()) / 1000.0)
        except Exception:
            step_delay = DEFAULT_STEP_DELAY

        self.progress_label.configure(text=f"Jogging {delta_steps:+d} steps", text_color=self.current_theme["status_warn"])
        try:
            self._jog_steps_blocking(cfg, int(delta_steps), step_delay)
            self._calibration_steps += int(delta_steps)
            self.calibration_counter_text.set(f"Calibration jog counter: {self._calibration_steps:+d} steps")
            self.progress_label.configure(text="Jog complete", text_color=self.current_theme["status_ok"])
        except Exception as exc:
            messagebox.showerror("Calibration jog error", str(exc))
            self.progress_label.configure(text="Calibration error", text_color=self.current_theme["status_error"])

    def apply_calibration_to_steps(self):
        if self._calibration_steps == 0:
            messagebox.showwarning("No calibration data", "Jog the motor first, then apply the counter.")
            return

        calibrated_steps = abs(int(self._calibration_steps))
        self.steps_per_rev.set(calibrated_steps)
        self.progress_label.configure(
            text=f"Steps per revolution updated to {calibrated_steps}",
            text_color=self.current_theme["status_ok"],
        )

    def _format_main_snippet(self):
        slot = self._get_slot_number()
        calibrated_steps = abs(int(self.steps_per_rev.get()))
        today = date.today().isoformat()
        return (
            f"# Calibrated with stepper_mcp.py on {today}\\n"
            f"# Slot {slot} tested via MCP23017 + ULN2003\\n"
            "# Optional per-slot calibration in main.py:\\n"
            "CALIBRATED_STEPS_PER_SLOT = {\\n"
            f"    {slot}: {calibrated_steps},\\n"
            "}\\n\\n"
            "# In dispense_from_slot(), replace fixed step count with:\\n"
            "# steps_per_cycle = CALIBRATED_STEPS_PER_SLOT.get(slot_number, STEPS_PER_PRODUCT)\\n"
            "# steps = steps_per_cycle * quantity\\n"
        )

    def generate_main_snippet(self):
        try:
            snippet = self._format_main_snippet()
        except Exception as exc:
            messagebox.showerror("Snippet error", str(exc))
            return

        self.snippet_box.configure(state="normal")
        self.snippet_box.delete("1.0", "end")
        self.snippet_box.insert("1.0", snippet)
        self.snippet_box.configure(state="disabled")
        self.snippet_status_text.set("Snippet output: generated for current slot")
        self.progress_label.configure(text="Snippet generated", text_color=self.current_theme["status_ok"])

    def copy_generated_snippet(self):
        snippet = self.snippet_box.get("1.0", "end").strip()
        if not snippet or snippet.startswith("# Generate a calibration snippet"):
            messagebox.showwarning("No snippet yet", "Generate the snippet first, then copy.")
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(snippet)
            self.update_idletasks()
            self.snippet_status_text.set("Snippet output: copied to clipboard")
            self.progress_label.configure(text="Snippet copied", text_color=self.current_theme["status_ok"])
        except Exception as exc:
            messagebox.showerror("Clipboard error", str(exc))

    def _on_close(self):
        self.stop_requested = True
        self._cleanup_mcp()
        self.destroy()


if __name__ == "__main__":
    app = StepperMCPTestApp()
    app.mainloop()