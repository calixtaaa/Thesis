import os
import sys
import re
import subprocess
import time
import json
import math
import datetime
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk

from touch_scroll import install_ctk_scroll_support

import prediction_runtime
from customer import checkout_ui, main_menu_ui, status_ui
from chatbot.chatbot_ui import build_chatbot_screen

from admin.admin import AdminMixin
from admin.reports import get_reports_dir
from staff.staff import (
    StaffMixin,
)
from database import (
    init_db,
    get_admin_credentials,
    update_admin_credentials,
    get_all_products,
    get_product_by_id,
    decrement_stock,
    record_transaction,
    get_user_by_uid,
    create_user,
    update_user_balance,
    adjust_user_balance,
    get_all_rfid_users,
    update_rfid_user,
    delete_rfid_user,
    update_rfid_user_role,
    reset_transactions,
    get_hardware_setting,
    set_hardware_setting,
    restock_product,
    export_sales_report,
    get_admin_overview_stats,
    get_ir_confirmation_stats,
    get_sales_trend_data,
    get_monthly_sales_data,
    get_top_selling_products,
    get_low_stock_chart_data,
)
from patchNotes import get_patch_notes_text, VERSION

install_ctk_scroll_support(ctk)

try:
    from mfrc522 import SimpleMFRC522, MFRC522  # type: ignore
except Exception:
    SimpleMFRC522 = None
    MFRC522 = None

# ======================
#  ENV & GPIO HANDLING
# ======================

# MockGPIO defined at module level so it can be used as a fallback
# both at import time (Windows) and at runtime (Pi 5 compatibility).
class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    PUD_UP = "PUD_UP"
    FALLING = "FALLING"
    RISING = "RISING"
    BOTH = "BOTH"

    def setmode(self, *_a, **_k): pass
    def setwarnings(self, *_a, **_k): pass
    def setup(self, *_a, **_k): pass
    def output(self, *_a, **_k): pass
    def input(self, *_a, **_k): return self.HIGH
    def cleanup(self): pass
    def add_event_detect(self, *_a, **_k): pass

ON_RPI = False
try:
    import RPi.GPIO as GPIO  # type: ignore
    ON_RPI = True
except ImportError:
    GPIO = MockGPIO()  # type: ignore

# ======================
#  CONFIG & CONSTANTS
# ======================

BASE_DIR = Path(__file__).resolve().parent
DEBUG_LOGS_DIR = BASE_DIR / "debug_logs"

# Base layout size (matches current design)
BASE_APP_W = 800
BASE_APP_H = 480

# ──────────────────────────────────────────────
#  Brand palette: Emerald Green · Plum · Creamy White
# ──────────────────────────────────────────────
THEMES = {
    "light": {
        "bg": "#F9F9FB",              # Creamy white
        "fg": "#1E1E2F",              # Deep charcoal text
        "button_bg": "#F0EFF4",       # Soft lavender-gray
        "button_fg": "#1E1E2F",
        "accent": "#50C878",          # Emerald green (primary CTA)
        "accent_hover": "#3DA863",    # Darker emerald on hover
        "card_bg": "#FFFFFF",
        "card_border": "#E8E5F0",     # Subtle plum-tinted border
        "search_bg": "#F0EFF4",
        "search_border": "#D1CDE0",
        "muted": "#7A7491",           # Muted plum-gray
        "nav_bg": "#8E4585",          # Plum (navigation / header)
        "nav_fg": "#FFFFFF",
        "nav_hover": "#723670",       # Darker plum on hover
        "on_accent": "#FFFFFF",
        "status_error": "#C0392B",
        "status_success": "#27AE60",
        "success_bg": "#50C878",
        "success_hover": "#3DA863",
        "chart_line": "#50C878",
        "chart_fill": "#D5F5E3",
        "chart_grid": "#E8E5F0",
        "btn_add": "#50C878",
        "btn_add_hover": "#3DA863",
        "btn_remove": "#E74C3C",
        "btn_remove_hover": "#C0392B",
        "price_color": "#8E4585",     # Plum price tag
        "selected_bg": "#D5F5E3",     # Light emerald tint
        "selected_border": "#50C878",
    },
    "dark": {
        "bg": "#1A1A2E",              # Deep navy/charcoal
        "fg": "#F0EFF4",
        "button_bg": "#242440",
        "button_fg": "#F0EFF4",
        "accent": "#6AEAA0",          # Bright mint-emerald
        "accent_hover": "#50C878",
        "card_bg": "#242440",
        "card_border": "#3D3A5C",
        "search_bg": "#242440",
        "search_border": "#4A4670",
        "muted": "#A09BB8",
        "nav_bg": "#B06AAB",          # Lighter plum
        "nav_fg": "#FFFFFF",
        "nav_hover": "#8E4585",
        "on_accent": "#1A1A2E",
        "status_error": "#F1948A",
        "status_success": "#82E0AA",
        "success_bg": "#6AEAA0",
        "success_hover": "#50C878",
        "chart_line": "#6AEAA0",
        "chart_fill": "#1E3A2F",
        "chart_grid": "#3D3A5C",
        "btn_add": "#6AEAA0",
        "btn_add_hover": "#50C878",
        "btn_remove": "#F1948A",
        "btn_remove_hover": "#E74C3C",
        "price_color": "#D7A0D3",     # Soft plum price
        "selected_bg": "#1E3A2F",
        "selected_border": "#6AEAA0",
    },
}

# Poppins first, fall back to Segoe UI if not installed
UI_FONT = "Poppins"
UI_FONT_BOLD = (UI_FONT, 22, "bold")
UI_FONT_TITLE = (UI_FONT, 20, "bold")
UI_FONT_BODY = (UI_FONT, 13)
UI_FONT_SMALL = (UI_FONT, 11)
UI_FONT_BUTTON = (UI_FONT, 13, "bold")


def _hover_scale_btn(btn, normal_padx=10, normal_pady=6, hover_padx=14, hover_pady=10):
    """Make button appear to scale up on hover by increasing padding."""
    def on_enter(_e):
        if btn.winfo_exists():
            btn.configure(padx=hover_padx, pady=hover_pady)
    def on_leave(_e):
        if btn.winfo_exists():
            btn.configure(padx=normal_padx, pady=normal_pady)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# Raspberry Pi 5 (BCM numbering) pin map.
# NOTE: Single shared MFRC522 reader on SPI0 CE0 for payment/reload/door auth flows.
RFID_PINS = {
    "spi_sclk": 11,              # Physical pin 23
    "spi_mosi": 10,              # Physical pin 19
    "spi_miso": 9,               # Physical pin 21
    "reader_cs": 8,              # Physical pin 24 (CE0)
    "reader_rst": 5,             # Physical pin 29
}

# ULN2003 IN1..IN4 mapping per tray motor (28BYJ-48), keyed by DB `slot_number` (1..10).
# Primary mode uses three MCP23017 expanders so every slot can have its own 4 control lines.
# Fallback mode keeps legacy native GPIO bank wiring for development or transition setups.
_STEPPER_BANK_A = {"backend": "native_gpio", "in1": 17, "in2": 27, "in3": 22, "in4": 23}
_STEPPER_BANK_B = {"backend": "native_gpio", "in1": 4, "in2": 18, "in3": 15, "in4": 14}


def _build_native_stepper_map() -> dict[int, dict]:
    return {
        slot: (_STEPPER_BANK_A if slot % 2 == 1 else _STEPPER_BANK_B).copy() for slot in range(1, 11)
    }

STEPPER_BACKEND = os.getenv("STEPPER_BACKEND", "mcp23017" if ON_RPI else "native_gpio").strip().lower()
STEPPER_I2C_BUS = int(os.getenv("STEPPER_I2C_BUS", "1"))
MCP23017_ADDRESSES = [
    int(part.strip(), 0)
    for part in os.getenv("MCP23017_ADDRESSES", "0x20,0x21,0x22").split(",")
    if part.strip()
]


def _build_mcp23017_stepper_map() -> dict[int, dict]:
    mapping: dict[int, dict] = {}
    slot = 1
    for address in MCP23017_ADDRESSES:
        for base_pin in (0, 4, 8, 12):
            if slot > 10:
                return mapping
            mapping[slot] = {
                "backend": "mcp23017",
                "address": address,
                "in1": base_pin,
                "in2": base_pin + 1,
                "in3": base_pin + 2,
                "in4": base_pin + 3,
            }
            slot += 1
    return mapping


if STEPPER_BACKEND == "mcp23017":
    PRODUCT_STEPPER_PINS = _build_mcp23017_stepper_map()
else:
    PRODUCT_STEPPER_PINS = _build_native_stepper_map()

SOLENOID_PINS = {
    "restock": 16,          # Physical pin 36
    "troubleshoot": 20,     # Physical pin 38
}

PAYMENT_INPUT_PINS = {
    "coin_acceptor": 19,    # Physical pin 35
}

# Coin acceptor relay control (enable when user selects cash payment)
COIN_ACCEPTOR_RELAY_PIN = 6   # Physical pin 31

IR_BREAK_BEAM_PIN = 26        # Physical pin 37
STEPS_PER_PRODUCT = 4096      # 28BYJ-48 output-shaft revolution (8-phase half-step)
STEP_DELAY = 0.002
SOLENOID_UNLOCK_SECONDS = 3.0
# Most low-cost 5V relay modules are active-low (IN=LOW energizes relay).
# Set to False if your relay board is active-high.
SOLENOID_ACTIVE_LOW = True


def set_coin_acceptor_relay(enabled: bool) -> None:
    global _coin_pulse_ignore_until
    # Coin acceptor relay: active-low (LOW energizes, HIGH de-energizes)
    GPIO.output(COIN_ACCEPTOR_RELAY_PIN, GPIO.LOW if enabled else GPIO.HIGH)

    # Clear pending counts and ignore startup transients after relay enable.
    if enabled:
        _payment_pulse_counts["coin_acceptor"] = 0
        _coin_pulse_ignore_until = time.monotonic() + (COIN_ACCEPTOR_ENABLE_IGNORE_MS / 1000.0)
    else:
        _coin_pulse_ignore_until = 0.0
        _payment_pulse_counts["coin_acceptor"] = 0

COINS_PER_SECOND = {
    1: 5,                     # 1-peso hopper fallback rate when no pulse feedback
    5: 5,                     # 5-peso hopper fallback rate when no pulse feedback
}

COIN_ACCEPTOR_PULSE_VALUE = 1.0
PAYMENT_PULSE_EDGE_DEFAULT = "falling"  # supported: falling, rising
PAYMENT_PULSE_BOUNCETIME_MS = 50
COIN_ACCEPTOR_ENABLE_IGNORE_MS = 350

_payment_pulse_counts = {
    "coin_acceptor": 0,
}

_coin_pulse_ignore_until = 0.0


def get_payment_pulse_counts() -> dict:
    return {
        "coin_acceptor": int(_payment_pulse_counts["coin_acceptor"]),
    }


def _payment_pulse_callback(channel: int):
    if channel == PAYMENT_INPUT_PINS["coin_acceptor"]:
        if time.monotonic() < _coin_pulse_ignore_until:
            return
        _payment_pulse_counts["coin_acceptor"] += 1


def consume_payment_pulse_amount() -> float:
    coin_pulses = _payment_pulse_counts["coin_acceptor"]
    _payment_pulse_counts["coin_acceptor"] = 0
    return coin_pulses * COIN_ACCEPTOR_PULSE_VALUE


def _normalize_payment_edge_name(value) -> str:
    edge = str(value or PAYMENT_PULSE_EDGE_DEFAULT).strip().lower()
    if edge in {"falling", "rising"}:
        return edge
    return PAYMENT_PULSE_EDGE_DEFAULT


def _payment_pulse_edge_gpio_constant(edge_name: str):
    if edge_name == "rising":
        return getattr(GPIO, "RISING", GPIO.FALLING)
    return GPIO.FALLING


def _solenoid_idle_level():
    return GPIO.HIGH if SOLENOID_ACTIVE_LOW else GPIO.LOW


def _solenoid_active_level():
    return GPIO.LOW if SOLENOID_ACTIVE_LOW else GPIO.HIGH


# ======================
#  HARDWARE ABSTRACTION
# ======================


class NativeGPIOStepperBackend:
    def setup(self, product_pins: dict[int, dict]) -> None:
        for cfg in product_pins.values():
            for key in ("in1", "in2", "in3", "in4"):
                pin = cfg[key]
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

    def set_phase(self, pins: dict, phase: tuple[int, int, int, int]) -> None:
        GPIO.output(pins["in1"], GPIO.HIGH if phase[0] else GPIO.LOW)
        GPIO.output(pins["in2"], GPIO.HIGH if phase[1] else GPIO.LOW)
        GPIO.output(pins["in3"], GPIO.HIGH if phase[2] else GPIO.LOW)
        GPIO.output(pins["in4"], GPIO.HIGH if phase[3] else GPIO.LOW)

    def cleanup(self) -> None:
        pass


class MCP23017StepperBackend:
    IODIRA = 0x00
    IODIRB = 0x01
    OLATA = 0x14
    OLATB = 0x15

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
                raise RuntimeError("Install smbus2 (or smbus) for MCP23017 stepper mode.") from exc

    def setup(self, product_pins: dict[int, dict]) -> None:
        SMBus = self._import_bus()
        self.bus = SMBus(self.bus_id)

        detected: list[int] = []
        missing: list[int] = []
        for addr in self.addresses:
            try:
                _ = self.bus.read_byte_data(addr, self.IODIRA)
                detected.append(addr)
            except Exception:
                missing.append(addr)

        if not detected:
            raise RuntimeError(
                "No configured MCP23017 addresses responded on I2C bus "
                f"{self.bus_id}: {', '.join(f'0x{x:02X}' for x in self.addresses)}"
            )

        if missing:
            print(
                "[HW] MCP23017 addresses not detected: "
                + ", ".join(f"0x{x:02X}" for x in missing)
            )

        self.addresses = detected
        self.olat_cache = {addr: {"A": 0x00, "B": 0x00} for addr in detected}

        for addr in self.addresses:
            self.bus.write_byte_data(addr, self.IODIRA, 0x00)
            self.bus.write_byte_data(addr, self.IODIRB, 0x00)
            self.bus.write_byte_data(addr, self.OLATA, 0x00)
            self.bus.write_byte_data(addr, self.OLATB, 0x00)

        disabled_slots: list[int] = []
        for slot, cfg in list(product_pins.items()):
            if cfg.get("backend") != "mcp23017":
                continue
            if int(cfg.get("address", -1)) not in self.addresses:
                disabled_slots.append(slot)
                product_pins.pop(slot, None)
        if disabled_slots:
            print(
                "[HW] Disabled MCP slots due to missing expanders: "
                + ", ".join(str(slot) for slot in sorted(disabled_slots))
            )

    def _set_pin_value(self, address: int, pin: int, value: int) -> None:
        port = "A" if pin < 8 else "B"
        bit = pin if pin < 8 else pin - 8
        current = self.olat_cache[address][port]
        if value:
            current |= 1 << bit
        else:
            current &= ~(1 << bit)
        self.olat_cache[address][port] = current & 0xFF

    def set_phase(self, pins: dict, phase: tuple[int, int, int, int]) -> None:
        if self.bus is None:
            raise RuntimeError("MCP23017 backend is not initialized.")

        address = int(pins["address"])
        for key, value in zip(("in1", "in2", "in3", "in4"), phase):
            self._set_pin_value(address, int(pins[key]), int(value))

        self.bus.write_byte_data(address, self.OLATA, self.olat_cache[address]["A"])
        self.bus.write_byte_data(address, self.OLATB, self.olat_cache[address]["B"])

    def cleanup(self) -> None:
        if self.bus is None:
            return
        try:
            for addr in self.addresses:
                self.bus.write_byte_data(addr, self.OLATA, 0x00)
                self.bus.write_byte_data(addr, self.OLATB, 0x00)
        except Exception:
            pass
        try:
            self.bus.close()
        except Exception:
            pass
        self.bus = None


_stepper_backend = None


def _create_stepper_backend():
    if STEPPER_BACKEND == "mcp23017":
        return MCP23017StepperBackend(STEPPER_I2C_BUS, MCP23017_ADDRESSES)
    return NativeGPIOStepperBackend()


def _describe_stepper_backend() -> str:
    i2c_ready = Path("/dev/i2c-1").exists()
    if STEPPER_BACKEND == "mcp23017":
        return "MCP23017 preferred (I2C ready)" if i2c_ready else "MCP23017 preferred (I2C missing, native GPIO test mode)"
    return "native GPIO stepper mode"


def _switch_to_native_stepper_backend(reason: str) -> None:
    global STEPPER_BACKEND, PRODUCT_STEPPER_PINS, _stepper_backend
    STEPPER_BACKEND = "native_gpio"
    PRODUCT_STEPPER_PINS = _build_native_stepper_map()
    _stepper_backend = NativeGPIOStepperBackend()
    print(f"[HW] {reason}")
    print("[HW] Falling back to native GPIO stepper bank mode.")

def gpio_init():
    global _stepper_backend
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    payment_edge_name = _normalize_payment_edge_name(
        get_hardware_setting("payment_pulse_edge", PAYMENT_PULSE_EDGE_DEFAULT)
    )
    payment_edge = _payment_pulse_edge_gpio_constant(payment_edge_name)

    # Stepper outputs (native GPIO or MCP23017 via I2C)
    _stepper_backend = _create_stepper_backend()
    try:
        _stepper_backend.setup(PRODUCT_STEPPER_PINS)
    except Exception as exc:
        if isinstance(_stepper_backend, MCP23017StepperBackend):
            _switch_to_native_stepper_backend(f"MCP23017 stepper backend unavailable: {exc}")
            _stepper_backend.setup(PRODUCT_STEPPER_PINS)
        else:
            raise

    # Solenoid outputs (through relay or MOSFET driver)
    for pin in SOLENOID_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, _solenoid_idle_level())

    # Coin acceptor relay output (active-high: HIGH enables, LOW disables)
    GPIO.setup(COIN_ACCEPTOR_RELAY_PIN, GPIO.OUT)
    set_coin_acceptor_relay(False)  # Start disabled (LOW)

    # Shared RFID reader reset line
    GPIO.setup(RFID_PINS["reader_rst"], GPIO.OUT)
    GPIO.output(RFID_PINS["reader_rst"], GPIO.HIGH)

    # Pulse inputs from coin acceptor
    for pin in PAYMENT_INPUT_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        try:
            GPIO.add_event_detect(
                pin,
                payment_edge,
                callback=_payment_pulse_callback,
                bouncetime=PAYMENT_PULSE_BOUNCETIME_MS,
            )
        except Exception:
            pass

    # IR break-beam receiver output (usually active-low)
    GPIO.setup(IR_BREAK_BEAM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def _describe_gpio_owners() -> str:
    device_paths = ["/dev/gpiochip0", "/dev/gpiochip4", "/dev/gpiomem0"]
    try:
        result = subprocess.run(
            ["fuser", "-v", *device_paths],
            capture_output=True,
            text=True,
            check=False,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        pid_set = set()
        for pid_text in re.findall(r"\b\d+\b", output):
            pid = int(pid_text)
            if pid != os.getpid():
                pid_set.add(pid)

        lines = []
        if output:
            lines.append(output)

        if pid_set:
            ps = subprocess.run(
                ["ps", "-p", ",".join(str(pid) for pid in sorted(pid_set)), "-o", "pid=,comm=,args="],
                capture_output=True,
                text=True,
                check=False,
            )
            if ps.stdout.strip():
                lines.append("Process details:")
                lines.append(ps.stdout.strip())

        return "\n".join(lines).strip()
    except Exception as detail_error:
        return f"Unable to inspect GPIO ownership: {detail_error}"


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


def _set_stepper_phase(pins: dict, phase: tuple[int, int, int, int]):
    if _stepper_backend is None:
        if not ON_RPI:
            return
        raise RuntimeError("Stepper backend is not initialized.")
    _stepper_backend.set_phase(pins, phase)

def dispense_from_slot(slot_number: int, quantity: int = 1):
    pins = PRODUCT_STEPPER_PINS.get(slot_number)
    print(f"[HW] Dispensing from slot {slot_number} x{quantity}")
    if not pins:
        if not ON_RPI:
            print(f"[HW] (Simulated – no pins for slot {slot_number})")
        else:
            print(f"[HW] WARNING: No stepper pins for slot {slot_number}, skipping")
        return

    steps = STEPS_PER_PRODUCT * quantity
    if _stepper_backend is None and not ON_RPI:
        time.sleep(steps * STEP_DELAY)
        return

    for i in range(steps):
        _set_stepper_phase(pins, ULN2003_SEQUENCE[i % len(ULN2003_SEQUENCE)])
        time.sleep(STEP_DELAY)

    # De-energize coils at end to reduce heat.
    _set_stepper_phase(pins, (0, 0, 0, 0))


def wait_for_vend_confirmation(timeout_s: float = 3.0) -> bool:
    """Return True when IR beam is broken within timeout (active-low sensor)."""
    if not ON_RPI:
        return True

    deadline = time.time() + max(0.1, timeout_s)
    while time.time() < deadline:
        if GPIO.input(IR_BREAK_BEAM_PIN) == GPIO.LOW:
            return True
        time.sleep(0.01)
    return False


def unlock_access_door(door: str):
    pin = SOLENOID_PINS.get(door)
    if pin is None:
        raise ValueError(f"Unknown door '{door}'")

    print(f"[HW] Unlocking {door} door for {SOLENOID_UNLOCK_SECONDS:.1f}s")
    GPIO.output(pin, _solenoid_active_level())
    time.sleep(SOLENOID_UNLOCK_SECONDS)
    GPIO.output(pin, _solenoid_idle_level())


# ======================
#  SIMPLE CASH SESSION
#  (Simulated for now)
# ======================

class CashSession:
    """
    For now: simulated cash input using "+" buttons on GUI.
    On real machine, replace with pulse‑based reader.
    """
    def __init__(self):
        self.total_amount = 0.0

    def reset(self):
        self.total_amount = 0.0

    def add(self, value: float):
        self.total_amount += value

    def get_amount(self) -> float:
        return self.total_amount

cash_session = CashSession()


# ======================
#  TKINTER GUI
# ======================

class MainApp(AdminMixin, StaffMixin, ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Hygiene Vending Machine  {VERSION}")

        # Set CTk appearance based on default theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # Fill the display by default; set APP_WINDOWED=1 for a fixed dev window.
        self._fill_screen = os.getenv("APP_WINDOWED", "").strip().lower() not in {"1", "true", "yes"}
        if self._fill_screen:
            if ON_RPI:
                self.attributes("-fullscreen", True)
            else:
                try:
                    self.state("zoomed")
                except Exception:
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self.minsize(640, 400)
            self.resizable(True, True)
        else:
            self.geometry(f"{BASE_APP_W}x{BASE_APP_H}")
            self.minsize(640, 400)
            self.resizable(True, True)

        # Auto-fit scale for different LCD resolutions (keeps layout consistent)
        try:
            self.after(50, lambda: self._apply_lcd_fit(profile="customer"))
        except Exception:
            pass
        try:
            self.after(250, self._report_window_state)
        except Exception:
            pass

        self.current_product = None
        self.current_quantity = 1

        # Last known user context (for offline personalization: Hygiene Hero advice, etc.)
        self._last_rfid_user_id = None
        self._last_rfid_uid = None

        # Theme state
        self.current_theme_name = "light"
        self.current_theme = THEMES[self.current_theme_name]
        self.configure(bg=self.current_theme["bg"])
        # UI scaling hints (used by customer/admin screens). Default 1.0 for desktop dev.
        self._lcd_scale = 1.0
        self._ui_font_name = UI_FONT
        self._ui_font_bold = UI_FONT_BOLD
        self._ui_font_title = UI_FONT_TITLE
        self._ui_font_body = UI_FONT_BODY
        self._ui_font_small = UI_FONT_SMALL
        self._ui_font_button = UI_FONT_BUTTON
        self.cash_session = cash_session
        self._cash_poll_after_id = None
        self.coin_pulse_value = COIN_ACCEPTOR_PULSE_VALUE

        try:
            self.coin_pulse_value = float(self.get_hardware_setting_data("coin_pulse_value", str(COIN_ACCEPTOR_PULSE_VALUE)))
        except Exception:
            self.coin_pulse_value = COIN_ACCEPTOR_PULSE_VALUE

        # Icon images (loaded lazily if files exist)
        self.staff_icon = None
        self.admin_icon = None
        self.menu_icon = None
        self.search_icon = None
        self.light_theme_icon = None
        self.dark_theme_icon = None

        # Small thumbnail cache (reduces UI lag on receipt/order summary renders)
        self._thumb_cache = {}

        # Staff icon
        try:
            for name in ("staff.png", "staff_icon.png"):
                staff_path = BASE_DIR / "images" / name
                if staff_path.exists():
                    self.staff_icon = tk.PhotoImage(file=str(staff_path))
                    break
        except Exception:
            self.staff_icon = None

        # Admin icon
        try:
            for name in ("admin.png", "admin_icon.png"):
                admin_path = BASE_DIR / "images" / name
                if admin_path.exists():
                    self.admin_icon = tk.PhotoImage(file=str(admin_path))
                    break
        except Exception:
            self.admin_icon = None

        # Hamburger / menu icon (subsample 4x for compact size, matches dark mode text size)
        try:
            menu_path = BASE_DIR / "images" / "hamburger.png"
            if menu_path.exists():
                img = tk.PhotoImage(file=str(menu_path))
                self.menu_icon = img.subsample(4, 4)
        except Exception:
            self.menu_icon = None

        # Search / magnifying glass icon
        try:
            search_path = BASE_DIR / "images" / "magnifying glass.png"
            if search_path.exists():
                img = tk.PhotoImage(file=str(search_path))
                self.search_icon = img.subsample(4, 4)
        except Exception:
            self.search_icon = None

        # Theme icons for light/dark toggle
        try:
            theme_path = BASE_DIR / "images" / "light-mode.png"
            if theme_path.exists():
                img = tk.PhotoImage(file=str(theme_path))
                self.light_theme_icon = img.subsample(5, 5)
        except Exception:
            self.light_theme_icon = None
        try:
            theme_path = BASE_DIR / "images" / "darkMode.png"
            if theme_path.exists():
                img = tk.PhotoImage(file=str(theme_path))
                self.dark_theme_icon = img.subsample(5, 5)
        except Exception:
            self.dark_theme_icon = None

        # Backspace icon for clearing search text
        self.backspace_icon = None
        try:
            backspace_path = BASE_DIR / "images" / "backspace.png"
            if backspace_path.exists():
                img = tk.PhotoImage(file=str(backspace_path))
                self.backspace_icon = img.subsample(4, 4)
        except Exception:
            self.backspace_icon = None

        # Welcome screen logo (medal/icon); optional
        self.welcome_icon = None
        try:
            for name in ("welcome.png", "logo.png", "welcome_icon.png"):
                welcome_path = BASE_DIR / "images" / name
                if welcome_path.exists():
                    self.welcome_icon = tk.PhotoImage(file=str(welcome_path))
                    break
        except Exception:
            self.welcome_icon = None

        # Sidebar / navbar state
        self.role_menu = None
        self.sidebar_frame = None
        self.sidebar_holder = None  # Persistent right teal sidebar (created in main menu)

        # Cart: list of {"product": p, "quantity": int} for order panel
        self.cart = []
        # Checkout snapshot (so totals stay consistent after leaving main menu)
        self.checkout_items = []  # list of {"product": p, "quantity": int}

        self.search_var = tk.StringVar()
        self.theme_animating = False
        self._pending_theme_apply_id = None
        self._current_screen_builder = None  # callable to rebuild the active screen

        # Receipt screen only (no QR/download)

        # Prediction Analysis cache (run once per session unless forced)
        self._prediction_results = None
        self._prediction_summary = None
        self._prediction_ran = False

        # Main content lives here; sidebar (when shown) is a sibling on the right
        self.content_holder = ctk.CTkFrame(self, fg_color=self.current_theme["bg"], corner_radius=0)
        self.content_holder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_welcome_screen()

    def run_prediction_analysis_once(self, force: bool = False):
        """
        Run lightweight prediction analysis using SQLite data.
        Runs once per session unless force=True.
        """
        if self._prediction_ran and not force and self._prediction_results is not None:
            return self._prediction_results, self._prediction_summary
        try:
            results, summary = prediction_runtime.run_prediction_analysis(db_path=BASE_DIR / "vending.db")
            self._prediction_results = results
            self._prediction_summary = summary
            self._prediction_ran = True
            return results, summary
        except Exception as e:
            messagebox.showerror("Prediction Analysis", f"Failed to run prediction.\n\n{e}")
            return None, None

    def _apply_lcd_fit(self, profile: str = "customer"):
        """
        Fit the app window to the current display size.
        On Raspberry Pi the window is already fullscreen.
        On Windows / LCD, centre and size to fill most of the screen.
        """
        if getattr(self, "_fill_screen", False):
            try:
                if ON_RPI:
                    self.attributes("-fullscreen", True)
                else:
                    try:
                        self.state("zoomed")
                    except Exception:
                        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            except Exception:
                pass
            return

        if ON_RPI:
            return
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            target_w = min(BASE_APP_W, screen_w)
            target_h = min(BASE_APP_H, screen_h)
            if screen_w <= 1024 or screen_h <= 600:
                target_w = screen_w
                target_h = screen_h
                try:
                    self.attributes("-fullscreen", True)
                except Exception:
                    self.state("zoomed")
            else:
                x = max(0, (screen_w - target_w) // 2)
                y = max(0, (screen_h - target_h) // 2)
                self.geometry(f"{target_w}x{target_h}+{x}+{y}")
        except Exception:
            pass

        # Font + widget scaling for small 7-inch LCDs (800x480/1024x600): bump sizes for readability.
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            is_small_lcd = screen_w <= 1024 or screen_h <= 600
            scale = 1.25 if is_small_lcd else 1.0
            self._lcd_scale = scale

            # CustomTkinter global scaling (keeps paddings/controls readable).
            try:
                ctk.set_widget_scaling(scale)
            except Exception:
                pass

            if scale > 1.0:
                # Keep font family, bump point sizes.
                self._ui_font_bold = (UI_FONT, 26, "bold")
                self._ui_font_title = (UI_FONT, 24, "bold")
                self._ui_font_body = (UI_FONT, 16)
                self._ui_font_small = (UI_FONT, 13)
                self._ui_font_button = (UI_FONT, 16, "bold")
            else:
                self._ui_font_bold = UI_FONT_BOLD
                self._ui_font_title = UI_FONT_TITLE
                self._ui_font_body = UI_FONT_BODY
                self._ui_font_small = UI_FONT_SMALL
                self._ui_font_button = UI_FONT_BUTTON
        except Exception:
            pass

    def _report_window_state(self):
        try:
            self.update_idletasks()
        except Exception:
            pass

        try:
            actual_state = self.state()
        except Exception:
            actual_state = "unknown"

        try:
            fullscreen_enabled = bool(self.attributes("-fullscreen"))
        except Exception:
            fullscreen_enabled = actual_state == "zoomed"

        try:
            geometry = self.winfo_geometry()
        except Exception:
            geometry = "unknown"

        requested_mode = "fullscreen" if self._fill_screen else "windowed"
        accepted_text = "accepted" if fullscreen_enabled else "not fullscreen"
        print(
            f"[HW] Main window state: requested={requested_mode}, actual={actual_state}, "
            f"fullscreen={accepted_text}, geometry={geometry}"
        )

    # ---------- Screen helpers ----------

    def clear_screen(self):
        # Close any right-side sidebars (not children of content_holder)
        try:
            if self.sidebar_frame is not None and self.sidebar_frame.winfo_exists():
                self.sidebar_frame.destroy()
        except Exception:
            pass
        self.sidebar_frame = None
        try:
            if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
                self.sidebar_holder.destroy()
        except Exception:
            pass
        self.sidebar_holder = None

        # Cancel any pending focus callbacks before destroying widgets
        for after_id in getattr(self, "_pending_focus_ids", []):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._pending_focus_ids = []
        if getattr(self, "_cash_poll_after_id", None):
            try:
                self.after_cancel(self._cash_poll_after_id)
            except Exception:
                pass
            self._cash_poll_after_id = None
        for w in self.content_holder.winfo_children():
            w.destroy()
        # Reset any per-screen background colour changes (e.g. LOGIN_PAGE_BG)
        try:
            self.content_holder.configure(fg_color=self.current_theme["bg"])
        except Exception:
            pass

    def _debug_log(self, hypothesis_id: str, location: str, message: str, data: dict):
        DEBUG_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": "14d174",
            "runId": "initial",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOGS_DIR / "debug-14d174.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
        # Keep a compatibility copy in the project root for existing tooling.
        with open(BASE_DIR / "debug-14d174.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")

    # Data wrappers for extracted admin/staff modules
    def get_user_by_uid_data(self, rfid_uid: str):
        return get_user_by_uid(rfid_uid)

    def get_all_products_data(self):
        return get_all_products()

    def restock_product_data(self, product_id: int, amount: int, new_price: float | None = None):
        return restock_product(product_id, amount, new_price)

    def get_all_rfid_users_data(self):
        return get_all_rfid_users()

    def create_rfid_user_data(
        self,
        rfid_uid: str,
        name: str | None = None,
        is_staff: int = 0,
        initial_balance: float = 0.0,
        role: str = "customer",
    ):
        return create_user(rfid_uid, name=name, is_staff=is_staff, initial_balance=initial_balance, role=role)

    def update_rfid_user_role_data(self, user_id: int, role: str):
        return update_rfid_user_role(user_id, role)

    def update_rfid_user_data(self, user_id: int, rfid_uid: str, name: str | None, balance: float, role: str):
        return update_rfid_user(user_id, rfid_uid, name, balance, role)

    def delete_rfid_user_data(self, user_id: int):
        return delete_rfid_user(user_id)

    def get_hardware_setting_data(self, key: str, default: str | None = None):
        return get_hardware_setting(key, default)

    def set_hardware_setting_data(self, key: str, value: str):
        return set_hardware_setting(key, value)

    def get_payment_pulse_counts_data(self):
        return get_payment_pulse_counts()

    def get_payment_pulse_edge_data(self):
        return _normalize_payment_edge_name(
            self.get_hardware_setting_data("payment_pulse_edge", PAYMENT_PULSE_EDGE_DEFAULT)
        )

    def format_payment_pulse_debug_text(self) -> str:
        counts = self.get_payment_pulse_counts_data()
        edge = self.get_payment_pulse_edge_data()
        return f"Pulse debug  coin(GPIO19): {counts['coin_acceptor']}  edge: {edge}"

    def _create_mfrc522_reader(self):
        if MFRC522 is None:
            return None

        ctor_attempts = (
            {"bus": 0, "device": 0},
            {"dev": 0},
            {"device": 0},
            {"bus": 0, "dev": 0},
            {},
        )
        for kwargs in ctor_attempts:
            try:
                return MFRC522(**kwargs)
            except TypeError:
                continue
            except Exception:
                continue
        return None

    def _close_mfrc522_spi(self, reader) -> None:
        try:
            spi_obj = getattr(reader, "spi", None)
            if spi_obj is not None and hasattr(spi_obj, "close"):
                spi_obj.close()
        except Exception:
            pass

    def _read_mfrc522_register(self, reader, reg_addr: int) -> int | None:
        method_names = ("Read_MFRC522", "MFRC522_Read", "ReadReg", "read")
        for name in method_names:
            fn = getattr(reader, name, None)
            if fn is None:
                continue
            try:
                value = fn(reg_addr)
                if isinstance(value, (tuple, list)) and value:
                    value = value[0]
                return int(value) & 0xFF
            except Exception:
                continue
        return None

    def probe_rfid_spi_link(self) -> tuple[bool, str]:
        """Probe MFRC522 SPI link by reading VersionReg over CE0."""
        if not ON_RPI:
            return False, "SPI probe unavailable in simulation mode."
        if MFRC522 is None:
            return False, "MFRC522 backend is not available."

        try:
            GPIO.output(RFID_PINS["reader_rst"], GPIO.LOW)
            time.sleep(0.01)
            GPIO.output(RFID_PINS["reader_rst"], GPIO.HIGH)
            time.sleep(0.01)
        except Exception:
            pass

        reader = self._create_mfrc522_reader()
        if reader is None:
            return False, "Could not initialize MFRC522 reader on SPI0 CE0."

        try:
            version_reg = int(getattr(reader, "VersionReg", 0x37))
            value = self._read_mfrc522_register(reader, version_reg)
            if value is None:
                return False, "Reader API does not expose a known register-read method."
            if value in {0x00, 0xFF}:
                return False, (
                    f"SPI probe FAIL: VersionReg=0x{value:02X}. "
                    "Check CE0/SCK/MOSI/MISO wiring, power, and SPI enablement."
                )
            return True, f"SPI probe PASS: VersionReg=0x{value:02X}."
        except Exception as exc:
            return False, f"SPI probe error: {exc}"
        finally:
            self._close_mfrc522_spi(reader)

    def _read_rfid_uid_from_hardware(self, reader_name: str) -> str | None:
        if not ON_RPI:
            return None

        uid = self._read_rfid_uid_shared_backend(reader_name)
        if uid:
            return uid

        if SimpleMFRC522 is None:
            return None

        # Most SimpleMFRC522 setups map to CE0; this still enables live tap reads.
        # Kept as fallback when low-level backend is unavailable.
        _ = reader_name
        try:
            reader = SimpleMFRC522()
            uid_int, _text = reader.read_no_block()
            if uid_int:
                return str(uid_int).strip().upper()
        except Exception:
            return None
        return None

    def _read_rfid_uid_shared_backend(self, reader_name: str) -> str | None:
        """Read RFID UID from the single shared MFRC522 reader on CE0."""
        if MFRC522 is None:
            return None

        _ = reader_name
        spi_device = 0
        rst_pin = RFID_PINS["reader_rst"]

        try:
            # Reset shared reader before each poll.
            GPIO.output(rst_pin, GPIO.LOW)
            time.sleep(0.01)
            GPIO.output(rst_pin, GPIO.HIGH)
            time.sleep(0.1)  # MFRC522 needs ~100ms to stabilize after reset
        except Exception:
            pass

        reader = self._create_mfrc522_reader()

        if reader is None:
            return None

        try:
            # Initialize firmware and set antenna gain if available
            for init_method in ("PCD_Init", "InitRC522", "init"):
                if hasattr(reader, init_method):
                    try:
                        getattr(reader, init_method)()
                        break
                    except Exception:
                        pass
            
            # Ensure antenna is enabled if method exists
            if hasattr(reader, "PCD_SetAntennaGain"):
                try:
                    reader.PCD_SetAntennaGain(0x07)  # Max gain
                except Exception:
                    pass
            
            # Common MFRC522 low-level API used by several Python wrappers.
            if hasattr(reader, "MFRC522_Request") and hasattr(reader, "MFRC522_Anticoll"):
                req_cmd = getattr(reader, "PICC_REQIDL", 0x26)
                mi_ok = getattr(reader, "MI_OK", 0)
                status, _tag_type = reader.MFRC522_Request(req_cmd)
                if status != mi_ok:
                    return None
                status, uid = reader.MFRC522_Anticoll()
                if status == mi_ok and uid:
                    return "".join(f"{int(part) & 0xFF:02X}" for part in uid[:4])

            # Alternate API shape fallback.
            if hasattr(reader, "read_id_no_block"):
                uid_int = reader.read_id_no_block()
                if uid_int:
                    return str(uid_int).strip().upper()
        except Exception:
            return None
        finally:
            # Close SPI if the backend exposes it.
            self._close_mfrc522_spi(reader)

        return None

    def read_rfid_uid(self, reader_name: str) -> str | None:
        return self._read_rfid_uid_from_hardware(reader_name)

    def start_cash_pulse_monitor(self, amount_var, remaining_var, total_amount: float, change_var=None, on_update=None):
        def tick():
            if not self.winfo_exists():
                return
            delta = self.consume_payment_pulse_amount_with_values(self.coin_pulse_value)
            if delta > 0:
                self.cash_session.add(delta)
                current = self.cash_session.get_amount()
                amount_var.set(current)
                remaining_var.set(max(0.0, total_amount - current))
                if change_var is not None:
                    change_var.set(max(0.0, current - total_amount))
                if callable(on_update):
                    try:
                        on_update()
                    except Exception:
                        pass
                if round(float(current), 2) >= round(float(total_amount), 2):
                    try:
                        set_coin_acceptor_relay(False)
                        print("[HW] Coin acceptor relay disabled: amount due reached")
                    except Exception as relay_error:
                        print(f"[HW] Warning: Failed to disable coin acceptor relay: {relay_error}")
            self._cash_poll_after_id = self.after(120, tick)

        self._cash_poll_after_id = self.after(120, tick)

    def consume_payment_pulse_amount_with_values(self, coin_value: float) -> float:
        coin_pulses = _payment_pulse_counts["coin_acceptor"]
        _payment_pulse_counts["coin_acceptor"] = 0
        return coin_pulses * float(coin_value)

    def is_user_authorized_for_door(self, user, door: str) -> bool:
        role = (user["role"] or "").strip().lower() if "role" in user.keys() else ""

        if role == "admin":
            return True
        if door == "restock":
            return role == "restocker"
        if door == "troubleshoot":
            return False
        return False

    def unlock_access_door(self, door: str):
        unlock_access_door(door)

    def get_admin_credentials_data(self):
        return get_admin_credentials()

    def update_admin_credentials_data(self, new_username: str, new_password: str):
        return update_admin_credentials(new_username, new_password)

    def get_admin_overview_stats_data(self):
        return get_admin_overview_stats()

    def get_ir_confirmation_stats_data(self):
        return get_ir_confirmation_stats()

    def reset_transactions_data(self):
        return reset_transactions()

    def get_sales_trend_data_points(self, days: int = 15):
        return get_sales_trend_data(days)

    def get_monthly_sales_data_points(self, months: int = 6):
        return get_monthly_sales_data(months)

    def get_top_selling_products_data(self, limit: int | None = None):
        return get_top_selling_products(limit)

    def get_low_stock_chart_data_points(self, limit: int = 5):
        return get_low_stock_chart_data(limit)

    def apply_theme_to_widget(self, widget, _depth=0):
        """Apply current theme colors to a widget and its children (recursive)."""
        if _depth > 80:
            return
        try:
            if not widget.winfo_exists():
                return
            widget.configure(bg=self.current_theme["bg"])
        except Exception:
            pass
        for child in list(widget.winfo_children()):
            try:
                if isinstance(child, tk.Button):
                    if getattr(child, "_sidebar_nav", False):
                        nav_bg = self.current_theme.get("nav_bg", "#6366f1")
                        nav_fg = self.current_theme.get("nav_fg", "#ffffff")
                        child.configure(bg=nav_bg, fg=nav_fg, activebackground=self.current_theme.get("nav_hover", "#4f46e5"), activeforeground=nav_fg)
                        child._sidebar_nav_bg = nav_bg
                        child._sidebar_nav_fg = nav_fg
                    elif getattr(child, "_staff_exit_btn", False):
                        exit_bg = self.current_theme.get("button_bg", "#f1f5f9")
                        exit_fg = self.current_theme.get("button_fg", "#0f172a")
                        child.configure(bg=exit_bg, fg=exit_fg)
                        child._staff_exit_bg = exit_bg
                        child._staff_exit_fg = exit_fg
                    elif getattr(child, "_hamburger_btn", False):
                        child.configure(text="☰", image="", font=(UI_FONT, 16, "bold"), bg=self.current_theme["bg"], fg=self.current_theme["fg"])
                        if hasattr(child, "image"):
                            child.image = None
                    elif getattr(child, "_restock_btn", False):
                        acc = self.current_theme.get("accent", "#10b981")
                        child.configure(bg=acc, fg=self.current_theme.get("on_accent", "#ffffff"))
                        child._hover_normal = acc
                        child._hover_hover = self.current_theme.get("accent_hover", "#059669")
                    elif getattr(child, "_product_add_btn", False):
                        acc = self.current_theme.get("btn_add", self.current_theme.get("accent", "#10b981"))
                        child.configure(
                            fg=self.current_theme.get("on_accent", "#ffffff"),
                            bg=acc,
                            activeforeground=self.current_theme.get("on_accent", "#ffffff"),
                            activebackground=self.current_theme.get("btn_add_hover", self.current_theme.get("accent_hover", "#059669")),
                        )
                    else:
                        child.configure(
                            bg=self.current_theme["button_bg"],
                            fg=self.current_theme["button_fg"],
                            activebackground=self.current_theme["button_bg"],
                            activeforeground=self.current_theme["button_fg"],
                        )
                    if getattr(child, "_is_theme_toggle", False):
                        child.configure(text=f"Theme: {self.current_theme_name.capitalize()}")
                elif isinstance(child, tk.Label):
                    if getattr(child, "_datetime_label", False):
                        # Datetime uses a "badge" background for visibility
                        badge_bg = self.current_theme.get("button_bg", self.current_theme["bg"])
                        fg = self.current_theme["fg"]
                        child.configure(bg=badge_bg, fg=fg)
                    elif getattr(child, "_admin_metric_value", False):
                        acc = self.current_theme.get("accent", "#10b981")
                        child.configure(bg=self.current_theme.get("card_bg", "#ffffff"), fg=acc)
                    else:
                        child.configure(bg=self.current_theme["bg"], fg=self.current_theme["fg"])
                elif isinstance(child, tk.Radiobutton) and getattr(child, "_bug_report", False):
                    try:
                        parent_bg = child.master.cget("bg")
                    except Exception:
                        parent_bg = self.current_theme.get("card_bg", self.current_theme["bg"])
                    child.configure(
                        bg=parent_bg,
                        fg=self.current_theme["fg"],
                        activebackground=parent_bg,
                        activeforeground=self.current_theme["fg"],
                        selectcolor=self.current_theme.get("card_bg", "#ffffff"),
                    )
                elif isinstance(child, tk.Text) and getattr(child, "_bug_report", False):
                    try:
                        parent_bg = child.master.cget("bg")
                    except Exception:
                        parent_bg = self.current_theme.get("card_bg", self.current_theme["bg"])
                    child.configure(
                        bg=self.current_theme.get("search_bg", self.current_theme.get("card_bg", "#ffffff")),
                        fg=self.current_theme["fg"],
                        insertbackground=self.current_theme["fg"],
                        highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
                    )
                elif isinstance(child, tk.Frame):
                    if getattr(child, "_datetime_badge", False):
                        badge_bg = self.current_theme.get("button_bg", self.current_theme["bg"])
                        child.configure(
                            bg=badge_bg,
                            highlightbackground=self.current_theme.get("card_border", "#e2e8f0"),
                        )
                    else:
                        child.configure(bg=self.current_theme["bg"])
                    self.apply_theme_to_widget(child, _depth + 1)
                elif isinstance(child, tk.Canvas):
                    try:
                        child.configure(bg=self.current_theme.get("card_bg", self.current_theme["bg"]))
                    except Exception:
                        pass
                    self.apply_theme_to_widget(child, _depth + 1)
            except tk.TclError:
                pass

    def _do_deferred_theme_apply(self):
        self._pending_theme_apply_id = None
        try:
            self.apply_theme_to_widget(self)
        except Exception:
            pass

    def _rebuild_current_screen_after_theme_change(self):
        """Rebuild active screen after a theme toggle to avoid stale widget colors."""
        builder = getattr(self, "_current_screen_builder", None)
        if not callable(builder):
            return
        try:
            self.clear_screen()
        except Exception:
            return
        try:
            builder()
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Fallback: keep app usable even if a specific screen rebuild fails.
            try:
                self.apply_theme_to_widget(self)
            except Exception:
                pass

    def _translate_theme_color(self, value, old_theme, new_theme):
        """Map known old-theme color values to their new-theme equivalents."""
        if isinstance(value, str):
            for key, old_val in old_theme.items():
                if value == old_val and key in new_theme:
                    return new_theme[key]
            return value
        if isinstance(value, tuple):
            mapped = tuple(self._translate_theme_color(v, old_theme, new_theme) for v in value)
            return mapped
        if isinstance(value, list):
            mapped = [self._translate_theme_color(v, old_theme, new_theme) for v in value]
            return mapped
        return value

    def _apply_theme_to_ctk_widget_tree(self, widget, old_theme, new_theme, _depth=0):
        """Update CTk widget explicit color options in-place without rebuilding the screen."""
        if _depth > 80:
            return
        option_names = (
            "fg_color",
            "hover_color",
            "text_color",
            "border_color",
            "button_color",
            "button_hover_color",
            "progress_color",
        )
        for child in list(widget.winfo_children()):
            try:
                for opt in option_names:
                    try:
                        current = child.cget(opt)
                    except Exception:
                        continue
                    updated = self._translate_theme_color(current, old_theme, new_theme)
                    if updated != current:
                        try:
                            child.configure(**{opt: updated})
                        except Exception:
                            pass
            except Exception:
                pass
            self._apply_theme_to_ctk_widget_tree(child, old_theme, new_theme, _depth + 1)

    def _safe_focus(self, widget):
        """Focus widget only if it still exists (prevents async focus TclError)."""
        try:
            exists = widget is not None and widget.winfo_exists()
        except Exception:
            return
        if not exists:
            return
        try:
            # CTkEntry wraps a native tk.Entry in ._entry; focus that directly
            # so we never touch a destroyed inner widget path.
            inner = getattr(widget, "_entry", None)
            if inner is not None:
                inner.focus_set()
            else:
                widget.focus_set()
        except Exception:
            pass

    def _apply_theme_change(self, next_theme_name):
        """Core logic to switch the theme (no animation)."""
        old_theme = dict(self.current_theme)
        self.current_theme_name = next_theme_name
        self.current_theme = THEMES[next_theme_name]
        ctk.set_appearance_mode(self.current_theme_name)
        try:
            self.configure(fg_color=self.current_theme["bg"])
        except Exception:
            pass
        try:
            self.content_holder.configure(fg_color=self.current_theme["bg"])
        except Exception:
            pass
        try:
            self._apply_theme_to_ctk_widget_tree(self, old_theme, self.current_theme)
        except Exception:
            pass
        try:
            self.apply_theme_to_widget(self)
        except Exception:
            pass
        self._rebuild_current_screen_after_theme_change()

    def _circle_reveal_theme_change(self, next_theme_name, cx=None, cy=None):
        """Animate an expanding circle to reveal the new theme."""
        next_theme = THEMES[next_theme_name]
        circle_color = next_theme["bg"]

        win_w = max(self.winfo_width(), 100)
        win_h = max(self.winfo_height(), 100)

        if cx is None:
            cx = win_w // 2
        if cy is None:
            cy = win_h // 2

        # Calculate the radius needed to cover the entire window from (cx, cy)
        max_radius = int(math.sqrt(
            max(cx, win_w - cx) ** 2 + max(cy, win_h - cy) ** 2
        )) + 50

        # Create a fullscreen canvas overlay on top of everything
        overlay = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0,
        )
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.tkraise(overlay)

        # Draw the expanding circle in the new theme's background color
        circle = overlay.create_oval(
            cx, cy, cx, cy,
            fill=circle_color,
            outline="",
        )

        total_steps = 20
        step_duration = 12  # milliseconds per frame

        def _animate(step=0):
            try:
                if not overlay.winfo_exists():
                    self._apply_theme_change(next_theme_name)
                    self.theme_animating = False
                    return
            except Exception:
                self._apply_theme_change(next_theme_name)
                self.theme_animating = False
                return

            if step >= total_steps:
                # Circle covers the screen — apply theme underneath and remove overlay
                self._apply_theme_change(next_theme_name)
                try:
                    overlay.destroy()
                except Exception:
                    pass
                self.theme_animating = False
                return

            # Cubic ease-out for smooth deceleration
            progress = (step + 1) / total_steps
            eased = 1 - (1 - progress) ** 3
            radius = int(max_radius * eased)

            try:
                overlay.coords(
                    circle,
                    cx - radius, cy - radius,
                    cx + radius, cy + radius,
                )
            except Exception:
                self._apply_theme_change(next_theme_name)
                try:
                    overlay.destroy()
                except Exception:
                    pass
                self.theme_animating = False
                return

            overlay.after(step_duration, lambda: _animate(step + 1))

        _animate()

    def toggle_theme(self):
        """Switch between light and dark modes with expanding circle animation."""
        if getattr(self, "theme_animating", False):
            return
        self.theme_animating = True
        next_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self._circle_reveal_theme_change(next_theme_name)

    def animate_button_press(self, button, callback):
        """Play a quick press animation before running a button action."""
        normal_bg = button.cget("bg")
        normal_relief = button.cget("relief")
        normal_bd = button.cget("bd")

        pressed_bg = self.current_theme.get("accent_hover", self.current_theme.get("accent", "#10b981"))

        try:
            button.configure(bg=pressed_bg, relief=tk.SUNKEN, bd=3)
        except tk.TclError:
            callback()
            return

        def finish():
            if button.winfo_exists():
                try:
                    button.configure(bg=normal_bg, relief=normal_relief, bd=normal_bd)
                except tk.TclError:
                    pass
            callback()

        button.after(100, finish)

    def create_theme_slider(self, parent):
        """Create a small animated theme slider near the hamburger icon."""
        width = 64
        height = 30
        padding = 3
        knob_size = height - (padding * 2)

        track_light = "#e2e8f0"
        track_dark = "#334155"
        knob_fill = "#FFFFFF"
        border_light = "#cbd5e1"
        border_dark = "#475569"

        is_dark = self.current_theme_name == "dark"
        start_x = width - padding - knob_size if is_dark else padding

        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=self.current_theme["bg"],
            highlightthickness=0,
            bd=0,
        )

        track = canvas.create_oval(
            padding,
            padding,
            width - padding,
            height - padding,
            fill=track_dark if is_dark else track_light,
            outline=border_dark if is_dark else border_light,
        )
        knob = canvas.create_oval(
            start_x,
            padding,
            start_x + knob_size,
            padding + knob_size,
            fill=knob_fill,
            outline="",
        )

        # No icon inside knob – avoids black line artifacts (reference: clean white knob)

        def _finish_toggle(target_dark):
            """Start the expanding circle reveal after the knob animation finishes."""
            next_name = "dark" if target_dark else "light"
            try:
                cx = canvas.winfo_rootx() + canvas.winfo_width() // 2 - self.winfo_rootx()
                cy = canvas.winfo_rooty() + canvas.winfo_height() // 2 - self.winfo_rooty()
            except Exception:
                cx, cy = None, None
            self._circle_reveal_theme_change(next_name, cx, cy)

        def animate_toggle(_event=None):
            if self.theme_animating:
                return

            self.theme_animating = True
            target_dark = self.current_theme_name != "dark"
            end_x = width - padding - knob_size if target_dark else padding
            try:
                current_coords = canvas.coords(knob)
                current_x = current_coords[0]
            except Exception:
                self.theme_animating = False
                return
            step_count = 8
            delta = (end_x - current_x) / step_count if step_count else 0

            def step(index=0):
                try:
                    if not canvas.winfo_exists():
                        raise RuntimeError("canvas gone")
                except Exception:
                    _finish_toggle(target_dark)
                    return

                if index >= step_count:
                    _finish_toggle(target_dark)
                    return

                try:
                    canvas.move(knob, delta, 0)
                    progress = (index + 1) / step_count
                    if progress > 0.5:
                        canvas.itemconfigure(
                            track,
                            fill=track_dark if target_dark else track_light,
                            outline=border_dark if target_dark else border_light,
                        )
                    canvas.after(14, lambda: step(index + 1))
                except Exception:
                    _finish_toggle(target_dark)

            step()

        canvas.bind("<Button-1>", animate_toggle)
        return canvas

    def add_theme_toggle_footer(self):
        """Add a bottom bar with a theme toggle button to the current screen."""
        bottom = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        ctk.CTkLabel(
            bottom,
            text=f"SyntaxError  ·  {VERSION}",
            font=UI_FONT_SMALL,
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
        ).pack(side=tk.LEFT, padx=12)
        self.add_ph_datetime_label(bottom)
        icon_text = "☀" if self.current_theme_name == "dark" else "☾"
        label_text = f"{icon_text}  {self.current_theme_name.capitalize()}"
        theme_btn = ctk.CTkButton(
            bottom,
            text=label_text,
            command=self.toggle_theme,
            font=(UI_FONT, 12, "bold"),
            fg_color=self.current_theme.get("nav_bg", "#1c1c1e"),
            hover_color=self.current_theme.get("nav_hover", "#333333"),
            text_color=self.current_theme.get("nav_fg", "#ffffff"),
            corner_radius=980,
            height=34,
        )
        theme_btn._is_theme_toggle = True
        theme_btn.pack(side=tk.RIGHT, padx=12)

    def add_ph_datetime_label(self, parent):
        """Show a live Philippine date/time label inside the given parent."""
        badge_bg = self.current_theme.get("button_bg", self.current_theme["bg"])
        badge = ctk.CTkFrame(
            parent,
            fg_color=badge_bg,
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=8,
        )
        badge._datetime_badge = True
        badge.pack(side=tk.RIGHT, padx=8, pady=2)

        label = ctk.CTkLabel(
            badge,
            font=(UI_FONT, 10),
            text_color=self.current_theme.get("muted", self.current_theme["fg"]),
            text="",
        )
        label._datetime_label = True
        label.pack(padx=10, pady=4)

        ph_tz = datetime.timezone(datetime.timedelta(hours=8))

        def _refresh():
            if not label.winfo_exists():
                return
            now = datetime.datetime.now(ph_tz)
            # Compact format so the datetime badge doesn't crowd footer buttons.
            label.configure(text=now.strftime("%I:%M %p"))
            label.after(1000, _refresh)

        _refresh()
        return label

    def show_patch_notes_dialog(self):
        """In-app Patch Notes screen (no external pop-up)."""
        self._current_screen_builder = self.show_patch_notes_dialog
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        # Top bar with back button for easier navigation
        top_bar = ctk.CTkFrame(frame, fg_color=self.current_theme["bg"], corner_radius=0)
        top_bar.pack(side=tk.TOP, fill=tk.X, pady=(8, 0), padx=10)
        ctk.CTkButton(
            top_bar,
            text="← Back to Dashboard",
            font=UI_FONT_BODY,
            command=self.build_main_menu,
            fg_color=self.current_theme.get("nav_bg", "#1c1c1e"),
            hover_color=self.current_theme.get("nav_hover", "#333333"),
            text_color=self.current_theme.get("nav_fg", "#ffffff"),
            corner_radius=980,
            height=36,
        ).pack(side=tk.LEFT)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.place(relx=0.5, rely=0.55, anchor="center", relwidth=0.9, relheight=0.72)

        ctk.CTkLabel(
            card,
            text=f"Patch Notes  ·  {VERSION}",
            font=(UI_FONT, 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=24, pady=(20, 8))

        txt = ctk.CTkTextbox(
            card,
            font=UI_FONT_SMALL,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            text_color=self.current_theme["fg"],
            corner_radius=8,
        )
        txt.pack(expand=True, fill=tk.BOTH, padx=24, pady=(4, 20))
        txt.insert("1.0", get_patch_notes_text())
        txt.configure(state="disabled")

        self.add_theme_toggle_footer()

    def show_help_dialog(self):
        """In-app 'How to use' page (no external pop-up)."""
        self._current_screen_builder = self.show_help_dialog
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        card = ctk.CTkFrame(
            frame,
            fg_color=self.current_theme.get("card_bg", "#ffffff"),
            border_width=1,
            border_color=self.current_theme.get("card_border", "#e2e8f0"),
            corner_radius=12,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text="How to Use the Vending Machine",
            font=(UI_FONT, 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(20, 10), padx=32)

        steps = (
            "1. Select Product – Tap the item you want on the main menu.\n"
            "2. Set Quantity – Use the + and − buttons to choose how many pieces you need.\n"
            "3. Choose Payment – Pay with Cash or RFID Card.\n"
            "4. Take Products – Wait for the machine to dispense your items.\n\n"
            "You can also use the buttons at the bottom of the main menu to reload an existing RFID card "
            "or buy a new RFID card."
        )
        ctk.CTkLabel(
            card,
            text=steps,
            font=UI_FONT_BODY,
            text_color=self.current_theme["fg"],
            justify="left",
            wraplength=480,
        ).pack(pady=(4, 18), padx=32)

        ctk.CTkButton(
            card,
            text="Back to Dashboard",
            font=UI_FONT_BUTTON,
            command=self.build_main_menu,
            fg_color=self.current_theme.get("nav_bg", "#1c1c1e"),
            hover_color=self.current_theme.get("nav_hover", "#333333"),
            text_color=self.current_theme.get("nav_fg", "#ffffff"),
            corner_radius=980,
            width=220,
            height=42,
        ).pack(pady=(0, 20), padx=32)

        self.add_theme_toggle_footer()

    def show_role_menu(self):
        """Toggle a right-side teal sidebar for Dashboard / Staff / Admin (hamburger menu)."""
        # region agent log
        self._debug_log(
            "H3",
            "main.py:show_role_menu",
            "hamburger action invoked",
            {
                "sidebar_exists_before": bool(self.sidebar_frame and self.sidebar_frame.winfo_exists()),
                "current_theme": self.current_theme_name,
            },
        )
        # endregion
        # If sidebar already open, close it
        if self.sidebar_frame is not None and self.sidebar_frame.winfo_exists():
            self.sidebar_frame.destroy()
            self.sidebar_frame = None
            return

        sidebar_width = 240
        sidebar_bg = self.current_theme.get("card_bg", "#ffffff")
        sidebar_border = self.current_theme.get("card_border", "#d1d1d6")
        sidebar = ctk.CTkFrame(self, fg_color=sidebar_bg, width=sidebar_width, corner_radius=0,
                               border_width=1, border_color=sidebar_border)
        sidebar.place(relx=1.0, x=0, y=0, anchor="ne", relheight=1.0)

        top_row = ctk.CTkFrame(sidebar, fg_color=sidebar_bg)
        top_row.pack(fill=tk.X, padx=14, pady=(14, 8))
        ctk.CTkLabel(
            top_row,
            text="Menu",
            font=(UI_FONT, 14, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            top_row,
            text="×",
            width=32,
            height=32,
            font=(UI_FONT, 14, "bold"),
            fg_color="transparent",
            hover_color=self.current_theme.get("search_bg", "#f2f2f7"),
            text_color=self.current_theme["fg"],
            corner_radius=8,
            command=self.show_role_menu,
        ).pack(side=tk.RIGHT)

        nav_bg = self.current_theme.get("nav_bg", "#1c1c1e")
        nav_fg = self.current_theme.get("nav_fg", "#ffffff")
        nav_hover = self.current_theme.get("nav_hover", "#333333")

        def make_nav_button(text, command):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                anchor="w",
                font=(UI_FONT, 12, "bold"),
                command=command,
                fg_color=nav_bg,
                hover_color=nav_hover,
                text_color=nav_fg,
                corner_radius=980,
                height=42,
            )
            btn.pack(fill=tk.X, padx=14, pady=3)
            return btn

        # Dashboard – close sidebar and stay on current screen
        make_nav_button("Dashboard", lambda: self.show_role_menu())

        # Staff restock screen
        make_nav_button(
            "Staff",
            lambda: (self.show_role_menu(), self.enter_restock_mode()),
        )

        # Admin dashboard
        make_nav_button(
            "Admin",
            lambda: (self.show_role_menu(), self.enter_admin_dashboard()),
        )

        # Hygiene Hero chatbot
        make_nav_button(
            "🤖 Hygiene Hero",
            lambda: (self.show_role_menu(), self.show_chatbot_screen()),
        )

        # Back to main screen: show thank-you in-app then return to welcome screen
        def go_back_to_welcome():
            self.show_role_menu()
            self.show_thank_you_screen()

        make_nav_button("Back to main screen", go_back_to_welcome)

        self.sidebar_frame = sidebar
        # region agent log
        self._debug_log(
            "H3",
            "main.py:show_role_menu",
            "sidebar created",
            {
                "sidebar_width": sidebar_width,
                "sidebar_exists_after": bool(self.sidebar_frame and self.sidebar_frame.winfo_exists()),
            },
        )
        # endregion

    # ---------- Chatbot Screen ----------

    def show_chatbot_screen(self):
        """Open the Hygiene Hero chatbot interface."""
        build_chatbot_screen(self)

    # ---------- Welcome Screen ----------

    def build_welcome_screen(self):
        """Show welcome page (icon, Welcome / Syntaxer, Start Order) before dashboard."""
        self._current_screen_builder = self.build_welcome_screen
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="customer")
            except Exception:
                pass
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.configure(fg_color=self.current_theme["bg"])
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        # Centered container (inside content_holder)
        center = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Optional logo / icon at top
        if self.welcome_icon is not None:
            icon_label = tk.Label(
                center,
                image=self.welcome_icon,
                bg=self.current_theme["bg"],
            )
            icon_label.pack(pady=(0, 16))
            icon_label.image = self.welcome_icon

        # "Welcome" line
        ctk.CTkLabel(
            center,
            text="Welcome",
            font=(UI_FONT, 28, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 2))

        # "Syntaxer" line
        ctk.CTkLabel(
            center,
            text="Syntaxer",
            font=(UI_FONT, 24, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 28))

        # Start Order button – iOS pill style
        start_btn = ctk.CTkButton(
            center,
            text="Start Order",
            font=(UI_FONT, 15, "bold"),
            fg_color=self.current_theme.get("nav_bg", "#1c1c1e"),
            hover_color=self.current_theme.get("nav_hover", "#333333"),
            text_color=self.current_theme.get("nav_fg", "#ffffff"),
            corner_radius=980,
            width=220,
            height=50,
            command=self.build_main_menu,
        )
        start_btn.pack(pady=0)

    def show_thank_you_screen(self):
        """Show 'Thank you, come again!' in-app, then return to welcome screen."""
        self._current_screen_builder = self.show_thank_you_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=self.current_theme["bg"])

        center = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center,
            text="Thank you, come again!",
            font=(UI_FONT, 22, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(pady=(0, 24))

        def go_welcome():
            self.build_welcome_screen()

        ctk.CTkButton(
            center,
            text="OK",
            font=(UI_FONT, 13, "bold"),
            command=go_welcome,
            fg_color=self.current_theme.get("nav_bg", "#1c1c1e"),
            hover_color=self.current_theme.get("nav_hover", "#333333"),
            text_color=self.current_theme.get("nav_fg", "#ffffff"),
            corner_radius=980,
            width=140,
            height=42,
        ).pack(pady=0)
        self.after(3500, go_welcome)

    # ---------- Main Menu ----------

    def build_main_menu(self):
        self._current_screen_builder = self.build_main_menu
        if hasattr(self, "_apply_lcd_fit"):
            try:
                self._apply_lcd_fit(profile="customer")
            except Exception:
                pass
        self.clear_screen()
        # UI ordering should match physical tray layout:
        # show highest slot at the top so the bottom-most/heaviest (slot 1) appears last.
        all_products = sorted(get_all_products(), key=lambda p: int(p["slot_number"]), reverse=True)

        # Destroy any existing sidebar
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None

        # Note: The right-side menu is shown only via the hamburger (☰),
        # not automatically on the main menu.

        # Left + order panel area (inside content_holder)
        main_row = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        main_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._main_row = main_row

        left_part = ctk.CTkFrame(main_row, fg_color=self.current_theme["bg"], corner_radius=0)
        left_part.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_main_menu_header(left_part)
        self._build_main_menu_products(left_part, all_products)

        # Order panel (dark green) – right of left_part, only when cart has items
        self._build_order_panel(main_row)

        self._build_main_menu_footer()

    def _build_main_menu_header(self, parent):
        """Main menu top bar: title, menu button, and theme slider."""
        main_menu_ui.build_main_menu_header(
            self,
            parent,
            ui_font=UI_FONT,
            ui_font_title=UI_FONT_TITLE,
            ui_font_small=UI_FONT_SMALL,
        )

    def _build_main_menu_products(self, parent, products):
        """Scrollable product grid for the customer main menu."""
        main_menu_ui.build_main_menu_products(self, parent, products)

    def _build_product_card(self, grid, product, idx):
        """Single product card in the main menu grid."""
        main_menu_ui.build_product_card(self, grid, product, idx)

    def _build_product_card_button(self, card, product, in_cart):
        """Add/remove button for a product card."""
        return main_menu_ui.build_product_card_button(self, card, product, in_cart)

    def _build_main_menu_footer(self):
        """Footer actions and info row for the main menu."""
        main_menu_ui.build_main_menu_footer(self, version=VERSION, hover_scale_btn=_hover_scale_btn)

    def _cart_has_product(self, product):
        return any(entry["product"]["id"] == product["id"] for entry in self.cart)

    def _add_product_to_cart(self, product):
        if product["current_stock"] <= 0:
            return
        self.cart.append({"product": product, "quantity": 1})
        ref = self._product_card_refs.get(product["id"])
        if ref:
            try:
                ref["card"].configure(fg_color=self._cart_selected_bg, border_color=self._cart_selected_border)
                ref["btn"].configure(
                    text="×  Remove",
                    fg_color=self.current_theme.get("btn_remove", "#ef4444"),
                    hover_color=self.current_theme.get("btn_remove_hover", "#dc2626"),
                    command=lambda prod=product: self._remove_product_from_cart(prod),
                )
            except Exception:
                pass
        self._refresh_order_panel()

    def _remove_product_from_cart(self, product):
        self.cart = [entry for entry in self.cart if entry["product"]["id"] != product["id"]]
        ref = self._product_card_refs.get(product["id"])
        if ref:
            try:
                ref["card"].configure(fg_color=self._cart_card_bg, border_color=self._cart_card_border)
                ref["btn"].configure(
                    text="+",
                    fg_color=self.current_theme.get("btn_add", "#10b981"),
                    hover_color=self.current_theme.get("btn_add_hover", "#059669"),
                    state=tk.NORMAL if product["current_stock"] > 0 else tk.DISABLED,
                    command=ref["add_cmd"],
                )
            except Exception:
                pass
        self._refresh_order_panel()

    def _cancel_cart(self):
        """Clear the cart and reset every product card button in-place — no full screen rebuild."""
        self.cart.clear()
        card_bg = getattr(self, "_cart_card_bg", None)
        card_border = getattr(self, "_cart_card_border", None)
        for ref in getattr(self, "_product_card_refs", {}).values():
            p = ref["product"]
            try:
                if ref["card"].winfo_exists() and card_bg:
                    ref["card"].configure(fg_color=card_bg, border_color=card_border)
                if ref["btn"].winfo_exists():
                    ref["btn"].configure(
                        text="+",
                        fg_color=self.current_theme.get("btn_add", "#10b981"),
                        hover_color=self.current_theme.get("btn_add_hover", "#059669"),
                        state=tk.NORMAL if p["current_stock"] > 0 else tk.DISABLED,
                        command=ref["add_cmd"],
                    )
            except Exception:
                pass
        self._refresh_order_panel()

    def _build_order_panel(self, main_row):
        """Build (or rebuild) only the order panel inside main_row."""
        order_panel_width = 260
        panel_bg = self.current_theme.get("nav_bg", "#6366f1")
        if not self.cart:
            self._order_panel = None
            self._order_qty_vars = {}
            return
        self._order_panel = ctk.CTkFrame(main_row, fg_color=panel_bg, width=order_panel_width, corner_radius=0)
        self._order_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
        self._order_panel.pack_propagate(False)
        order_panel = self._order_panel
        self._order_qty_vars = {}

        ctk.CTkButton(
            order_panel,
            text="Cancel",
            font=(UI_FONT, 11, "bold"),
            text_color=self.current_theme.get("nav_fg", "#ffffff"),
            fg_color=panel_bg,
            hover_color=self.current_theme.get("nav_hover", "#4f46e5"),
            corner_radius=8,
            height=36,
            command=self._cancel_cart,
        ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 8))

        items_frame = ctk.CTkScrollableFrame(
            order_panel,
            fg_color=panel_bg,
            corner_radius=0,
            scrollbar_button_color=self.current_theme.get("search_border", "#cbd5e1"),
            scrollbar_button_hover_color=self.current_theme.get("accent", "#10b981"),
        )
        items_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        for entry in self.cart:
            prod = entry["product"]
            qty_var = tk.IntVar(value=entry["quantity"])
            self._order_qty_vars[prod["id"]] = qty_var

            row = ctk.CTkFrame(items_frame, fg_color=panel_bg, corner_radius=0)
            row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)

            ctk.CTkLabel(
                row,
                text=prod["name"][:18] + ("…" if len(prod["name"]) > 18 else ""),
                font=UI_FONT_SMALL,
                text_color=self.current_theme.get("nav_fg", "#ffffff"),
            ).pack(anchor="center")

            ctrl = ctk.CTkFrame(row, fg_color=panel_bg, corner_radius=0)
            ctrl.pack(anchor="center", pady=2)

            ctk.CTkButton(
                ctrl,
                text="-",
                font=(UI_FONT, 12, "bold"),
                text_color=self.current_theme.get("nav_fg", "#ffffff"),
                fg_color=panel_bg,
                hover_color=self.current_theme.get("nav_hover", "#4f46e5"),
                # Ensure the qty buttons still read as "buttons" on both themes.
                border_width=1,
                border_color=self.current_theme.get("button_fg", self.current_theme.get("nav_fg", "#ffffff")),
                width=32,
                height=28,
                corner_radius=6,
                command=lambda pid=prod["id"]: self._change_cart_quantity(pid, -1),
            ).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(ctrl, textvariable=qty_var, font=(UI_FONT, 12, "bold"), bg=panel_bg, fg=self.current_theme.get("nav_fg", "#ffffff"), width=3).pack(side=tk.LEFT, padx=(0, 6))
            ctk.CTkButton(
                ctrl,
                text="+",
                font=(UI_FONT, 12, "bold"),
                text_color=self.current_theme.get("nav_fg", "#ffffff"),
                fg_color=panel_bg,
                hover_color=self.current_theme.get("nav_hover", "#4f46e5"),
                border_width=1,
                border_color=self.current_theme.get("button_fg", self.current_theme.get("nav_fg", "#ffffff")),
                width=32,
                height=28,
                corner_radius=6,
                command=lambda pid=prod["id"]: self._change_cart_quantity(pid, 1),
            ).pack(side=tk.LEFT)

        ctk.CTkButton(
            order_panel,
            text="Confirm Order",
            font=(UI_FONT, 12, "bold"),
            text_color=self.current_theme.get("on_accent", "#ffffff"),
            fg_color=self.current_theme.get("accent", "#10b981"),
            hover_color=self.current_theme.get("accent_hover", "#059669"),
            corner_radius=10,
            height=44,
            command=lambda: self._confirm_cart_order(),
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(8, 12))

    def _refresh_order_panel(self):
        """Destroy and rebuild only the order panel, leaving the product grid untouched."""
        if hasattr(self, "_order_panel") and self._order_panel is not None and self._order_panel.winfo_exists():
            self._order_panel.destroy()
            self._order_panel = None
        if hasattr(self, "_main_row") and self._main_row is not None and self._main_row.winfo_exists():
            self._build_order_panel(self._main_row)

    def _change_cart_quantity(self, product_id: int, delta: int):
        """Update a single cart item's quantity, removing it when it reaches zero."""
        for entry in self.cart:
            if entry["product"]["id"] != product_id:
                continue
            old_qty = int(entry["quantity"] if entry["quantity"] is not None else 1)
            product = entry["product"]
            # `product` is typically a sqlite3.Row; use indexing (not `.get`) and guard None.
            try:
                max_stock = int(product["current_stock"]) if product["current_stock"] is not None else old_qty
            except Exception:
                max_stock = old_qty
            try:
                cap = int(product["capacity"]) if product["capacity"] is not None else 0
                if cap > 0:
                    max_stock = min(max_stock, cap)
            except Exception:
                pass
            new_qty = min(max_stock, old_qty + int(delta))
            if new_qty <= 0:
                self._remove_product_from_cart(product)
                return
            if new_qty == old_qty:
                return
            entry["quantity"] = new_qty
            var = getattr(self, "_order_qty_vars", {}).get(product_id)
            if var is not None:
                try:
                    var.set(new_qty)
                except Exception:
                    pass
            return

    def _confirm_cart_order(self):
        """Proceed to review/quantity/payment based on current cart."""
        if not self.cart:
            return
        # snapshot the cart so later screens reflect what was confirmed
        items = [{"product": e["product"], "quantity": int(e.get("quantity", 1) or 1)} for e in self.cart]
        # clamp to current stock (defensive)
        for it in items:
            try:
                it["quantity"] = max(1, min(int(it["product"]["current_stock"]), int(it["quantity"])))
            except Exception:
                it["quantity"] = max(1, int(it["quantity"]))

        self.checkout_items = items
        if len(items) == 1:
            self.current_product = items[0]["product"]
            self.current_quantity = items[0]["quantity"]
            # Quantity is already adjustable in the order panel for cart-based checkout.
            # Go directly to payment for a single selected product.
            self.show_payment_method_screen()
        else:
            self.show_order_review_screen()

    def select_product(self, product_row):
        self.current_product = product_row
        self.current_quantity = 1
        self.checkout_items = []
        self.show_quantity_screen()

    def _get_checkout_items(self):
        """Return a stable list of items for checkout screens and payment flows."""
        if getattr(self, "checkout_items", None):
            return self.checkout_items
        if self.current_product is not None:
            return [{"product": self.current_product, "quantity": int(self.current_quantity or 1)}]
        return []

    def _get_checkout_total(self, items):
        return sum((float(it["product"]["price"]) * int(it["quantity"])) for it in items)

    def _reset_checkout_state(self):
        self.cart.clear()
        self.checkout_items = []
        self.current_product = None
        self.current_quantity = 1

    def show_order_review_screen(self):
        """Step 2 of 3 for multi-item carts: review order & totals."""
        self._current_screen_builder = self.show_order_review_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()

        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return

        accent = self.current_theme.get("accent", "#10b981")
        accent_hover = self.current_theme.get("accent_hover", "#059669")
        total = self._get_checkout_total(items)

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)
        self._build_order_review_content(frame, items, total, accent, accent_hover)
        self.add_theme_toggle_footer()

    def _build_checkout_back_bar(self, parent, text, command):
        """Bottom back/cancel bar shared by checkout-related screens."""
        checkout_ui.build_checkout_back_bar(self, parent, text, command)

    def _build_order_review_content(self, parent, items, total, accent, accent_hover):
        """Order review title, item list, and continue button."""
        checkout_ui.build_order_review_content(self, parent, items, total, accent, accent_hover)

    # ---------- Quantity Screen ----------

    def show_quantity_screen(self):
        self._current_screen_builder = self.show_quantity_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        p = self.current_product
        accent = self.current_theme.get("accent", "#10b981")
        accent_hover = self.current_theme.get("accent_hover", "#059669")

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_checkout_back_bar(
            frame,
            text="Back to products",
            command=lambda: (self.checkout_items.clear(), self.build_main_menu()),
        )
        self._build_quantity_content(frame, p, accent, accent_hover)
        self.add_theme_toggle_footer()

    def _build_quantity_content(self, parent, product, accent, accent_hover):
        """Single-product quantity selector card."""
        checkout_ui.build_quantity_content(self, parent, product, accent, accent_hover)

    # ---------- Payment Method ----------

    def show_payment_method_screen(self):
        self._current_screen_builder = self.show_payment_method_screen
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        
        # Disable coin acceptor relay when navigating back to payment method selector
        try:
            set_coin_acceptor_relay(False)
            print("[HW] Coin acceptor relay disabled")
        except Exception as e:
            print(f"[HW] Warning: Failed to disable coin acceptor relay: {e}")
        
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        total = self._get_checkout_total(items)

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_payment_method_content(frame, items, total)
        self.add_theme_toggle_footer()

    def _build_payment_method_content(self, parent, items, total):
        """Payment method chooser with order summary."""
        checkout_ui.build_payment_method_content(self, parent, items, total)

    def go_back_from_payment_method(self):
        """Back action for payment method screen.

        Multi-item checkout returns to order review.
        Single-item checkout returns to main menu with the order panel quantity editor.
        """
        # Disable coin acceptor relay when user cancels
        try:
            set_coin_acceptor_relay(False)
            print("[HW] Coin acceptor relay disabled")
        except Exception as e:
            print(f"[HW] Warning: Failed to disable coin acceptor relay: {e}")
        
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return

        if len(items) > 1:
            self.show_order_review_screen()
            return

        single = items[0]
        product = single["product"]
        qty = int(single.get("quantity", 1) or 1)

        self.current_product = product
        self.current_quantity = qty
        self.checkout_items = [{"product": product, "quantity": qty}]
        self.cart = [{"product": product, "quantity": qty}]
        self.build_main_menu()

    # ---------- Cash Payment Flow ----------

    def cash_payment_flow(self, total_amount: float):
        self._current_screen_builder = lambda: self.cash_payment_flow(total_amount)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()
        
        # Enable coin acceptor relay when user selects cash payment
        try:
            set_coin_acceptor_relay(True)
            print("[HW] Coin acceptor relay enabled")
        except Exception as e:
            print(f"[HW] Warning: Failed to enable coin acceptor relay: {e}")

        frame = ctk.CTkFrame(self.content_holder, fg_color=self.current_theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_cash_payment_content(frame, total_amount)
        self.add_theme_toggle_footer()

    def _build_cash_payment_content(self, parent, total_amount: float):
        """Cash payment screen with coin-only pulse/simulation support."""
        checkout_ui.build_cash_payment_content(self, parent, total_amount)

    def complete_purchase_cash(self, total_amount: float, inserted: float):
        items = self._get_checkout_items()
        if not items:
            self.build_main_menu()
            return
        change = max(0.0, inserted - total_amount)
        self._show_dispensing_screen()
        # Run the blocking dispense + DB writes off the UI thread (keeps UI responsive).
        threading.Thread(target=self._do_dispense_cash, args=(items, change), daemon=True).start()

    def _do_dispense_cash(self, items, change):
        try:
            for it in items:
                p = it["product"]
                q = int(it["quantity"])
                line_total = float(p["price"]) * q
                decrement_stock(p["id"], q)
                dispense_from_slot(p["slot_number"], q)
                ir_ok = wait_for_vend_confirmation(timeout_s=3.0)
                if not ir_ok:
                    print(f"[HW] WARNING: No IR vend confirmation for slot {p['slot_number']}")
                record_transaction(p["id"], q, line_total, "cash", ir_confirmed=ir_ok)
            
            # Disable coin acceptor relay after payment is complete
            try:
                set_coin_acceptor_relay(False)
                print("[HW] Coin acceptor relay disabled after payment")
            except Exception as relay_error:
                print(f"[HW] Warning: Failed to disable coin acceptor relay: {relay_error}")
            
            change_note = ""
            if change > 0:
                change_note = (
                    f"\n\nInserted above total: Php{change:.2f}. "
                    "Automatic coin change hopper is disabled in this build."
                )
            total = self._get_checkout_total(items)
            footer = "Please take your products." + change_note
            self.after(
                0,
                lambda: self.show_receipt_screen(
                    items,
                    total=total,
                    payment_method="cash",
                    footer_note=footer,
                ),
            )
        except Exception as e:
            # Disable relay on error too
            try:
                GPIO.output(COIN_ACCEPTOR_RELAY_PIN, GPIO.LOW)
            except Exception:
                pass
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: (self._reset_checkout_state(), self.build_main_menu()))

    # ---------- Utility Screens ----------

    def show_wait_screen(self, text: str):
        """In-app styled wait screen (no pop-up)."""
        # Don't update _current_screen_builder for transient screens
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_wait_screen_content(text)
        self.add_theme_toggle_footer()

    def _build_wait_screen_content(self, text: str):
        """Centered wait/status card used for transient wait states."""
        status_ui.build_wait_screen_content(self, text)


    def _show_dispensing_screen(self):
        """Full-screen dispensing overlay - shown before the blocking hardware call."""
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_dispensing_screen_content()
        self.update_idletasks()

    def _build_dispensing_screen_content(self):
        """Centered dispensing status card."""
        status_ui.build_dispensing_screen_content(self)

    def _do_dispense_rfid(self, items, rfid_user_id, new_balance):
        try:
            self._last_rfid_user_id = rfid_user_id
            for it in items:
                p = it["product"]
                q = int(it["quantity"])
                line_total = float(p["price"]) * q
                decrement_stock(p["id"], q)
                dispense_from_slot(p["slot_number"], q)
                ir_ok = wait_for_vend_confirmation(timeout_s=3.0)
                if not ir_ok:
                    print(f"[HW] WARNING: No IR vend confirmation for slot {p['slot_number']}")
                record_transaction(
                    product_id=p["id"],
                    quantity=q,
                    total_amount=line_total,
                    payment_method="rfid_purchase",
                    rfid_user_id=rfid_user_id,
                    ir_confirmed=ir_ok,
                )
            total = self._get_checkout_total(items)
            footer = f"Remaining balance: ₱{new_balance:.2f}\nPlease take your products."
            self.after(
                0,
                lambda: self.show_receipt_screen(
                    items,
                    total=total,
                    payment_method="RFID",
                    footer_note=footer,
                ),
            )
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: (self._reset_checkout_state(), self.build_main_menu()))

    def show_success_screen(self, title: str, message: str, on_ok=None):
        """In-app success screen (no messagebox pop-up)."""
        # Keep this screen active so theme toggles do not revert to the previous flow.
        self._current_screen_builder = lambda: self.show_success_screen(title, message, on_ok)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_success_screen_content(title, message, on_ok)
        self.add_theme_toggle_footer()

    def _build_success_screen_content(self, title: str, message: str, on_ok=None):
        """Centered success/result card with OK action."""
        status_ui.build_success_screen_content(self, title, message, on_ok)

    # ---------- Receipt (after dispensing) ----------

    def show_receipt_screen(self, items, total: float, *, payment_method: str, footer_note: str = ""):
        """Receipt view shown after dispensing. Includes optional QR download of a receipt image."""
        self._current_screen_builder = lambda: self.show_receipt_screen(items, total, payment_method=payment_method, footer_note=footer_note)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self._build_receipt_screen_content(items, total, payment_method=payment_method, footer_note=footer_note)
        self.add_theme_toggle_footer()

    def _build_receipt_screen_content(self, items, total: float, *, payment_method: str, footer_note: str = ""):
        theme = self.current_theme
        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"], corner_radius=0)
        frame.pack(expand=True, fill=tk.BOTH)

        card = ctk.CTkFrame(
            frame,
            fg_color=theme.get("card_bg", theme["button_bg"]),
            border_width=2,
            border_color=theme.get("accent", "#1A948E"),
            corner_radius=16,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(card, fg_color=theme.get("card_bg", theme["button_bg"]))
        inner.pack(padx=32, pady=24)

        ts = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        ctk.CTkLabel(inner, text="Receipt", font=self._ui_font_title, text_color=theme.get("accent", "#1A948E")).pack(pady=(0, 4))
        ctk.CTkLabel(inner, text=ts, font=self._ui_font_small, text_color=theme.get("muted", theme["fg"])).pack(pady=(0, 12))

        list_frame = ctk.CTkScrollableFrame(
            inner,
            fg_color=theme.get("card_bg", theme["button_bg"]),
            corner_radius=0,
            height=170,
            scrollbar_button_color=theme.get("search_border", "#cbd5e1"),
            scrollbar_button_hover_color=theme.get("accent", "#10b981"),
        )
        list_frame.pack(fill=tk.BOTH, expand=False, padx=6, pady=(0, 10))
        list_frame.grid_columnconfigure(0, weight=0)
        list_frame.grid_columnconfigure(1, weight=1)
        list_frame.grid_columnconfigure(2, weight=0)
        list_frame.grid_columnconfigure(3, weight=0)

        # Use same image loader as product cards/order summary
        try:
            import customer.main_menu_ui as mm  # type: ignore
        except Exception:
            mm = None

        for r, it in enumerate(items):
            p = it["product"]
            q = int(it.get("quantity", 1) or 1)
            try:
                name = str(p["name"])
            except Exception:
                name = str(getattr(p, "name", "") or "")
            try:
                price = float(p["price"])
            except Exception:
                price = float(getattr(p, "price", 0) or 0)
            line_total = price * q

            placed = False
            thumb_key = (name, 40)
            if thumb_key in self._thumb_cache:
                try:
                    cached = self._thumb_cache.get(thumb_key)
                    if cached is not None:
                        # Cached can be CTkImage or tk.PhotoImage, depending on loader.
                        if isinstance(cached, ctk.CTkImage):
                            img_lbl = ctk.CTkLabel(list_frame, text="", image=cached, fg_color="transparent")
                            img_lbl._ctk_img_ref = cached
                            img_lbl.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
                            placed = True
                        else:
                            lbl = tk.Label(
                                list_frame,
                                image=cached,
                                bd=0,
                                bg=theme.get("card_bg", theme["button_bg"]),
                                highlightthickness=0,
                            )
                            lbl.tk_img_ref = cached
                            lbl.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
                            placed = True
                except Exception:
                    placed = False

            if not placed and mm is not None and getattr(mm, "_HAS_PIL", False):
                try:
                    # Prefer the shared cached loader when available.
                    if hasattr(mm, "_load_uniform_image"):
                        # returns a cached Tk image (ImageTk.PhotoImage)
                        tk_img = mm._load_uniform_image(name, size=40)
                        if tk_img is not None:
                            lbl = tk.Label(list_frame, image=tk_img, bd=0, bg=theme.get("card_bg", theme["button_bg"]), highlightthickness=0)
                            lbl.tk_img_ref = tk_img
                            lbl.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
                            self._thumb_cache[thumb_key] = tk_img
                            placed = True
                    if not placed:
                        img_path = mm._resolve_product_image_path(name)
                        if img_path:
                            pil_img = mm.Image.open(str(img_path)).convert("RGBA")
                            ctk_img = mm._pil_square_rgba_to_ctk(pil_img, 40)
                        img_lbl = ctk.CTkLabel(list_frame, text="", image=ctk_img, fg_color="transparent")
                        img_lbl._ctk_img_ref = ctk_img
                        img_lbl.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
                        self._thumb_cache[thumb_key] = ctk_img
                        placed = True
                except Exception:
                    placed = False
            if not placed and mm is not None:
                try:
                    tkph = mm._load_product_image_tk(name, 40)
                except Exception:
                    tkph = None
                if tkph is not None:
                    lbl = tk.Label(list_frame, image=tkph, bd=0, bg=theme.get("card_bg", theme["button_bg"]), highlightthickness=0)
                    lbl.tk_img_ref = tkph
                    lbl.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
                    self._thumb_cache[thumb_key] = tkph
                    placed = True
            if not placed:
                ctk.CTkLabel(list_frame, text="", width=40).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))

            ctk.CTkLabel(list_frame, text=name, font=self._ui_font_body, text_color=theme["button_fg"], anchor="w", wraplength=360).grid(row=r, column=1, sticky="w", pady=4)
            ctk.CTkLabel(list_frame, text=f"x{q}", font=(self._ui_font_name, 12, "bold"), text_color=theme.get("muted", theme["button_fg"])).grid(row=r, column=2, sticky="e", padx=(10, 0))
            ctk.CTkLabel(list_frame, text=f"₱{line_total:.2f}", font=(self._ui_font_name, 12, "bold"), text_color=theme["button_fg"]).grid(row=r, column=3, sticky="e", padx=(16, 0))

        ctk.CTkLabel(inner, text=f"Total: ₱{total:.2f}", font=(self._ui_font_name, 16, "bold"), text_color=theme["button_fg"]).pack(pady=(2, 2))
        ctk.CTkLabel(inner, text=f"Paid via: {payment_method}", font=self._ui_font_small, text_color=theme.get("muted", theme["fg"])).pack(pady=(0, 8))
        if footer_note:
            ctk.CTkLabel(inner, text=footer_note, font=self._ui_font_small, text_color=theme.get("muted", theme["fg"]), wraplength=520, justify="center").pack(pady=(0, 10))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill=tk.X, pady=(6, 0))

        ctk.CTkButton(
            btn_row,
            text="Done",
            font=self._ui_font_button,
            fg_color=theme.get("accent", "#1A948E"),
            hover_color=theme.get("accent_hover", "#15857B"),
            text_color=theme.get("on_accent", "#ffffff"),
            corner_radius=10,
            height=40,
            command=lambda: (self._reset_checkout_state(), self.build_main_menu()),
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)

    # ---------- RFID Card Purchase ----------

    def buy_card_flow(self):
        """Card dispensing is unavailable in this build."""
        messagebox.showinfo(
            "Card Purchase Unavailable",
            "This machine cannot dispense RFID cards right now.\n"
            "Please buy a card at the office.",
        )
        self.build_main_menu()

    # ---------- RFID Reload ----------

    def reload_card_flow(self):
        """Customer reloads an existing RFID card balance."""
        self._current_screen_builder = self.reload_card_flow
        theme = self.current_theme
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_reload_card_content(frame, theme)
        self.add_theme_toggle_footer()

    def _build_reload_card_content(self, parent, theme):
        """RFID reload card lookup screen."""
        panel = ctk.CTkFrame(
            parent,
            fg_color=theme["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=theme["card_border"],
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)
        ctk.CTkLabel(inner, text="Reload RFID Card", font=(UI_FONT, 18, "bold"), text_color=theme["fg"]).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text="Tap RFID card now. Reader is always listening (or type card ID manually):",
            font=UI_FONT_SMALL,
            text_color=theme["muted"],
        ).pack(anchor="w", pady=(0, 6))

        scan_hint = ctk.CTkLabel(
            inner,
            text="Waiting for RFID tap...",
            font=(UI_FONT, 12, "bold"),
            text_color=theme.get("accent", "#22c55e"),
        )
        scan_hint.pack(anchor="w", pady=(0, 8))

        uid_entry = ctk.CTkEntry(inner, font=UI_FONT_BODY, width=280, fg_color=theme["search_bg"], text_color=theme["fg"], border_color=theme["search_border"], corner_radius=8, height=40)
        uid_entry.pack(pady=(0, 8))

        last_uid = {"value": None}
        lookup_in_progress = {"value": False}

        def read_from_reader():
            uid = self.read_rfid_uid("payment")
            if not uid:
                error_lbl.configure(text="No RFID tap detected. You can type card ID manually.")
                scan_hint.configure(text="Waiting for RFID tap...")
                return
            uid_entry.delete(0, tk.END)
            uid_entry.insert(0, uid.strip().upper())
            scan_hint.configure(text=f"RFID {uid.strip().upper()} detected. Verifying card...")
            error_lbl.configure(text="")
            proceed_to_amount(uid)

        ctk.CTkButton(
            inner,
            text="Read from RFID Reader",
            font=UI_FONT_SMALL,
            command=read_from_reader,
            fg_color=theme["accent"],
            hover_color=theme["accent_hover"],
            text_color=theme.get("on_accent", "#ffffff"),
            corner_radius=8,
            height=32,
            width=180,
        ).pack(anchor="w", pady=(0, 8))

        error_lbl = ctk.CTkLabel(inner, text="", font=UI_FONT_SMALL, text_color=theme.get("status_error", "#b91c1c"))
        error_lbl.pack(pady=(0, 4))

        def proceed_to_amount(uid_override: str | None = None):
            if lookup_in_progress["value"]:
                return

            uid = (uid_override or uid_entry.get()).strip().upper()
            if not uid:
                error_lbl.configure(text="Please enter or tap a card ID.")
                scan_hint.configure(text="Waiting for RFID tap...")
                return

            lookup_in_progress["value"] = True
            user = get_user_by_uid(uid)
            if not user:
                error_lbl.configure(text="Card not found. Please buy a new card at the office.")
                scan_hint.configure(text="Waiting for RFID tap...")
                lookup_in_progress["value"] = False
                return

            scan_hint.configure(text=f"RFID {uid} accepted. Opening reload amount...")
            self._reload_amount_screen(uid, user)

        def poll_rfid():
            if not inner.winfo_exists() or lookup_in_progress["value"]:
                return

            try:
                uid = self.read_rfid_uid("payment")
            except Exception:
                uid = None

            if uid:
                uid = uid.strip().upper()
                if uid != last_uid["value"]:
                    last_uid["value"] = uid
                    uid_entry.delete(0, tk.END)
                    uid_entry.insert(0, uid)
                    scan_hint.configure(text=f"RFID {uid} detected. Verifying card...")
                    error_lbl.configure(text="")
                    proceed_to_amount(uid)
            else:
                last_uid["value"] = None

            if inner.winfo_exists() and not lookup_in_progress["value"] and self._current_screen_builder == self.reload_card_flow:
                self.after(250, poll_rfid)

        btn_row = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ctk.CTkButton(btn_row, text="OK", font=(UI_FONT, 11, "bold"), command=lambda: proceed_to_amount(None), fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color=theme.get("on_accent", "#ffffff"), corner_radius=8, height=38).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(btn_row, text="Cancel", font=(UI_FONT, 11, "bold"), command=self.build_main_menu, fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=38).pack(side=tk.LEFT)
        uid_entry.bind("<Return>", lambda _e: proceed_to_amount(None))

        self.after(250, poll_rfid)

    def _reload_amount_screen(self, uid, user):
        """Second step for reload – choose amount, still in-app."""
        self._current_screen_builder = lambda: self._reload_amount_screen(uid, user)
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        cash_session.reset()

        theme = self.current_theme
        self.content_holder.configure(fg_color=theme["bg"])
        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_reload_amount_content(frame, uid, user, theme)
        self.add_theme_toggle_footer()

    def _build_reload_amount_content(self, parent, uid, user, theme):
        """RFID reload amount entry screen."""
        ctk.CTkLabel(parent, text="Reload RFID Card", font=UI_FONT_BOLD, text_color=theme["fg"]).pack(pady=10)
        card = ctk.CTkFrame(parent, fg_color=theme["button_bg"], corner_radius=12, border_width=1, border_color=theme.get("card_border", "#94a3b8"))
        card.pack(padx=24, pady=10)
        card_inner = ctk.CTkFrame(card, fg_color=theme["button_bg"])
        card_inner.pack(padx=20, pady=18)
        ctk.CTkLabel(card_inner, text=f"Card ID: {uid}", font=UI_FONT_BODY, text_color=theme["button_fg"]).pack(pady=(0, 4))
        ctk.CTkLabel(card_inner, text=f"Current Balance: ₱{user['balance']:.2f}", font=UI_FONT_BODY, text_color=theme["button_fg"]).pack(pady=(0, 10))

        amount_var = tk.DoubleVar(value=0.0)
        ctk.CTkLabel(card_inner, text="Amount to Load:", font=UI_FONT_BODY, text_color=theme["button_fg"]).pack(pady=5)
        tk.Label(card_inner, textvariable=amount_var, font=(UI_FONT, 22, "bold"), bg=theme["button_bg"], fg=theme["button_fg"]).pack()
        pulse_debug_var = tk.StringVar(value=self.format_payment_pulse_debug_text())
        tk.Label(
            card_inner,
            textvariable=pulse_debug_var,
            font=UI_FONT_SMALL,
            bg=theme["button_bg"],
            fg=theme.get("muted", theme["button_fg"]),
            wraplength=380,
            justify="left",
        ).pack(pady=(8, 0), anchor="w")

        ctk.CTkLabel(
            card_inner,
            text="Insert coins into the coin acceptor to add balance.",
            font=UI_FONT_SMALL,
            text_color=theme.get("muted", theme["button_fg"]),
            justify="left",
            wraplength=380,
        ).pack(pady=(10, 8), anchor="w")

        def _refresh_pulse_debug():
            pulse_debug_var.set(self.format_payment_pulse_debug_text())

        # Monitor coin-acceptor pulses while this screen is open.
        self.start_cash_pulse_monitor(amount_var, tk.DoubleVar(value=0.0), 0.0, on_update=_refresh_pulse_debug)

        def confirm_reload():
            amount = cash_session.get_amount()
            if amount <= 0:
                messagebox.showwarning("No amount", "Please add some amount to reload.")
                return
            new_balance = user["balance"] + amount
            self._last_rfid_user_id = user["id"]
            self._last_rfid_uid = str(user.get("rfid_uid") or uid).strip().upper()
            update_user_balance(user["id"], new_balance)
            record_transaction(product_id=None, quantity=None, total_amount=amount, payment_method="rfid_reload", rfid_user_id=user["id"])
            self.show_success_screen("Reload Successful", f"New balance: ₱{new_balance:.2f}", on_ok=self.build_main_menu)

        ctk.CTkButton(card_inner, text="Add balance", font=UI_FONT_BUTTON, command=confirm_reload, fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color=theme.get("on_accent", "#ffffff"), corner_radius=8, height=44).pack(pady=(10, 8), fill=tk.X)
        ctk.CTkButton(parent, text="Cancel and go back", font=UI_FONT_BODY, command=self.build_main_menu, fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=36).pack(pady=5)

    # ---------- RFID Purchase Payment ----------

    def rfid_payment_flow(self, total_amount: float):
        """Purchase products using RFID card balance – in-app card ID entry."""
        self._current_screen_builder = lambda: self.rfid_payment_flow(total_amount)
        theme = self.current_theme
        if self.sidebar_holder is not None and self.sidebar_holder.winfo_exists():
            self.sidebar_holder.destroy()
            self.sidebar_holder = None
        self.clear_screen()
        self.content_holder.configure(fg_color=theme["bg"])

        frame = ctk.CTkFrame(self.content_holder, fg_color=theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        self._build_rfid_payment_content(frame, total_amount, theme)
        self.add_theme_toggle_footer()

    def _build_rfid_payment_content(self, parent, total_amount: float, theme):
        """RFID payment entry and validation screen with live RFID listening."""
        panel = ctk.CTkFrame(
            parent,
            fg_color=theme["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=theme["card_border"],
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(panel, fg_color=theme["card_bg"])
        inner.pack(padx=40, pady=28)
        ctk.CTkLabel(inner, text="RFID Payment", font=(UI_FONT, 18, "bold"), text_color=theme["fg"]).pack(pady=(0, 6))
        ctk.CTkLabel(inner, text=f"Total: ₱{total_amount:.2f}", font=(UI_FONT, 16), text_color=theme["muted"]).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text="Tap RFID card now. Reader is always listening (or type card ID manually):",
            font=UI_FONT_SMALL,
            text_color=theme["muted"],
        ).pack(anchor="w", pady=(0, 6))

        scan_hint = ctk.CTkLabel(
            inner,
            text="Waiting for RFID tap...",
            font=(UI_FONT, 12, "bold"),
            text_color=theme.get("accent", "#22c55e"),
        )
        scan_hint.pack(anchor="w", pady=(0, 8))

        uid_entry = ctk.CTkEntry(inner, font=UI_FONT_BODY, width=280, fg_color=theme["search_bg"], text_color=theme["fg"], border_color=theme["search_border"], corner_radius=8, height=40)
        uid_entry.pack(pady=(0, 8))

        last_uid = {"value": None}
        payment_in_progress = {"value": False}

        error_lbl = ctk.CTkLabel(inner, text="", font=UI_FONT_SMALL, text_color=theme.get("status_error", "#b91c1c"))
        error_lbl.pack(pady=(0, 4))

        def process_rfid(uid_override: str | None = None):
            if payment_in_progress["value"]:
                return

            uid = (uid_override or uid_entry.get()).strip().upper()
            if not uid:
                error_lbl.configure(text="Please enter or tap a card ID.")
                scan_hint.configure(text="Waiting for RFID tap...")
                return

            user = get_user_by_uid(uid)
            if not user:
                error_lbl.configure(text="Card not found. Please buy a new card at the office.")
                scan_hint.configure(text="Waiting for RFID tap...")
                return
            if user["balance"] < total_amount:
                error_lbl.configure(text="Insufficient card balance.")
                scan_hint.configure(text="Waiting for RFID tap...")
                return

            payment_in_progress["value"] = True
            scan_hint.configure(text=f"RFID {uid} accepted. Processing payment...")
            error_lbl.configure(text="")

            self._last_rfid_user_id = user["id"]
            self._last_rfid_uid = uid
            new_balance = user["balance"] - total_amount
            update_user_balance(user["id"], new_balance)
            items = self._get_checkout_items()
            if not items:
                self.build_main_menu()
                return
            self._show_dispensing_screen()
            self.after(50, lambda i=items, uid=user["id"], nb=new_balance: self._do_dispense_rfid(i, uid, nb))

        def read_from_reader():
            uid = self.read_rfid_uid("payment")
            if not uid:
                error_lbl.configure(text="No RFID tap detected. You can type card ID manually.")
                scan_hint.configure(text="Waiting for RFID tap...")
                return
            uid_entry.delete(0, tk.END)
            uid_entry.insert(0, uid.strip().upper())
            scan_hint.configure(text=f"RFID {uid.strip().upper()} detected. Verifying card...")
            error_lbl.configure(text="")
            process_rfid(uid)

        ctk.CTkButton(
            inner,
            text="Read from RFID Reader",
            font=UI_FONT_SMALL,
            command=read_from_reader,
            fg_color=theme["accent"],
            hover_color=theme["accent_hover"],
            text_color=theme.get("on_accent", "#ffffff"),
            corner_radius=8,
            height=32,
            width=180,
        ).pack(anchor="w", pady=(0, 8))

        def poll_rfid():
            if not inner.winfo_exists() or payment_in_progress["value"]:
                return

            try:
                uid = self.read_rfid_uid("payment")
            except Exception:
                uid = None

            if uid:
                uid = uid.strip().upper()
                if uid != last_uid["value"]:
                    last_uid["value"] = uid
                    uid_entry.delete(0, tk.END)
                    uid_entry.insert(0, uid)
                    scan_hint.configure(text=f"RFID {uid} detected. Verifying...")
                    error_lbl.configure(text="")
                    process_rfid(uid)
            else:
                last_uid["value"] = None

            if inner.winfo_exists() and not payment_in_progress["value"]:
                self.after(250, poll_rfid)

        btn_row = ctk.CTkFrame(inner, fg_color=theme["card_bg"])
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ctk.CTkButton(btn_row, text="Pay Now", font=(UI_FONT, 11, "bold"), command=lambda: process_rfid(None), fg_color=theme["accent"], hover_color=theme["accent_hover"], text_color=theme.get("on_accent", "#ffffff"), corner_radius=8, height=38).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(btn_row, text="Cancel", font=(UI_FONT, 11, "bold"), command=self.show_payment_method_screen, fg_color=theme["button_bg"], hover_color=theme["card_border"], text_color=theme["button_fg"], corner_radius=8, height=38).pack(side=tk.LEFT)
        uid_entry.bind("<Return>", lambda _e: process_rfid(None))

        self.after(250, poll_rfid)

    # ---------- Sales Report Export ----------

    def export_sales_report_ui(self):
        """Generate an Excel file with transaction, daily, and monthly sales."""
        def _run():
            try:
                path = export_sales_report()
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Export Complete",
                        f"Sales report saved as:\n{path}",
                    ),
                )
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Export Failed", str(e)))

        threading.Thread(target=_run, daemon=True).start()


# ======================
#  MAIN ENTRYPOINT
# ======================

_SUPABASE_BRIDGE_PROC = None


def _stop_supabase_bridge():
    """Terminate background SQLite→Supabase sync started by _start_supabase_bridge_if_configured."""
    global _SUPABASE_BRIDGE_PROC
    proc = _SUPABASE_BRIDGE_PROC
    _SUPABASE_BRIDGE_PROC = None
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=6)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _start_supabase_bridge_if_configured():
    """POST new local transactions/products to Supabase so the website Realtime feed updates."""
    global _SUPABASE_BRIDGE_PROC
    try:
        from sync.machine_supabase_bridge import env_configured
    except ImportError:
        print("[Supabase] Could not import sync.machine_supabase_bridge.")
        return

    if not env_configured():
        print("[Supabase] Cloud sync off: add supabase.env next to main.py (see supabase.env.example).")
        return
    script = BASE_DIR / "sync" / "machine_supabase_bridge.py"
    if not script.exists():
        return
    try:
        _SUPABASE_BRIDGE_PROC = subprocess.Popen(
            [sys.executable, "-u", str(script)],
            cwd=str(BASE_DIR),
        )
        print("[Supabase] Background bridge started (local DB → Supabase → website Realtime).")
    except Exception as e:
        print(f"[Supabase] Could not start bridge process: {e}")


def main():
    global ON_RPI, GPIO
    init_db()
    _start_supabase_bridge_if_configured()
    if ON_RPI:
        print(f"[HW] GPIO backend module: {getattr(GPIO, '__file__', 'unknown')}")
        print(f"[HW] GPIO backend version: {getattr(GPIO, 'VERSION', 'unknown')}")
    else:
        print("[HW] GPIO backend: simulation (RPi.GPIO import unavailable)")
    print(f"[HW] Stepper backend: {_describe_stepper_backend()}")
    try:
        gpio_init()
        print("[HW] GPIO mode: live (RPi.GPIO)")
    except Exception as e:
        # GPIO init can fail on unsupported backends or when the chip is not available.
        # Fall back to simulation mode so the app still runs.
        print(f"[HW] GPIO init failed: {e}")
        error_text = str(e).lower()
        if STEPPER_BACKEND == "mcp23017" and (
            "/dev/i2c-1" in error_text or "i2c" in error_text or "smbus" in error_text
        ):
            print("[HW] MCP23017 stepper backend unavailable; switching to native GPIO stepper bank mode.")
        if "busy" in error_text or "not allocated" in error_text:
            owner_details = _describe_gpio_owners()
            print("[HW] GPIO pins appear to be in use by another process.")
            if owner_details:
                print("[HW] GPIO ownership details:\n" + owner_details)
        print("[HW] Tip: On Raspberry Pi 5, install rpi-lgpio and ensure GPIO access is available.")
        print("[HW] Falling back to simulation mode.")
        ON_RPI = False
        GPIO = MockGPIO()
        print("[HW] GPIO mode: simulation")
        print(f"[HW] Stepper backend: {_describe_stepper_backend()}")

    app = MainApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")
    finally:
        _stop_supabase_bridge()
        try:
            if _stepper_backend is not None:
                _stepper_backend.cleanup()
        except Exception:
            pass
        try:
            GPIO.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    main()