"""
GPIO Pin Testing Tool
Simple utility to test input and output pins for the vending machine hardware.
Not part of the main app - for development/testing only.
"""

import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import csv
from datetime import datetime
import time
import threading
from pathlib import Path

# GPIO handling - try real hardware first, then mock
try:
    from gpiozero import OutputDevice, DigitalInputDevice, LED
    ON_RPI = True
    GPIO_LIBRARY = "gpiozero"
except ImportError:
    try:
        import RPi.GPIO as GPIO
        ON_RPI = True
        GPIO_LIBRARY = "RPi.GPIO"
    except ImportError:
        ON_RPI = False
        GPIO_LIBRARY = "mock"

# Global device storage for gpiozero
_output_devices = {}
_input_devices = {}

# Debounce for input pulse lines (seconds).
# Keep this low for fast pulse bursts from coin/bill acceptors.
GPIOZERO_INPUT_BOUNCE_S = 0.002

def setup_gpiozero_output(pin):
    """Create and store gpiozero OutputDevice for a pin."""
    if GPIO_LIBRARY != "gpiozero":
        return
    try:
        _output_devices[pin] = OutputDevice(pin)
    except Exception as e:
        print(f"[GPIO] Failed to create output device for pin {pin}: {e}")

def setup_gpiozero_input(pin):
    """Create and store gpiozero InputDevice for a pin."""
    if GPIO_LIBRARY != "gpiozero":
        return
    try:
        device = DigitalInputDevice(pin, pull_up=True, bounce_time=GPIOZERO_INPUT_BOUNCE_S)
        device.when_activated = lambda pin_num=pin: _on_gpiozero_input_edge(pin_num)
        _input_devices[pin] = device
    except Exception as e:
        print(f"[GPIO] Failed to create input device for pin {pin}: {e}")

def gpiozero_output(pin, state):
    """Set pin HIGH (state=1) or LOW (state=0)."""
    if pin not in _output_devices:
        return
    _output_devices[pin].value = bool(state)

def gpiozero_input(pin):
    """Read pin value (0=LOW/active, 1=HIGH/inactive with pull_up)."""
    if pin not in _input_devices:
        return 1
    return 0 if _input_devices[pin].is_active else 1

def _on_gpiozero_input_edge(pin_num):
    """Internal gpiozero activation callback for pulse counting."""
    try:
        app = _gpio_app_ref[0]
    except Exception:
        return

    if app is not None:
        app._on_input_edge(pin_num)


_gpio_app_ref = [None]

def gpiozero_cleanup():
    """Close all GPIO devices."""
    for dev in list(_output_devices.values()):
        try:
            dev.close()
        except:
            pass
    _output_devices.clear()
    
    for dev in list(_input_devices.values()):
        try:
            dev.close()
        except:
            pass
    _input_devices.clear()


def gpiozero_is_output_ready(pin):
    return pin in _output_devices


def gpiozero_is_input_ready(pin):
    return pin in _input_devices

# Pin configuration from main.py
RFID_PINS = {
    "spi_sclk": 11,
    "spi_mosi": 10,
    "spi_miso": 9,
    "reader_cs": 8,
    "reader_rst": 5,
}

_STEPPER_BANK_A = {"in1": 17, "in2": 27, "in3": 22, "in4": 23}
_STEPPER_BANK_B = {"in1": 4, "in2": 18, "in3": 15, "in4": 14}
PRODUCT_STEPPER_PINS = {
    slot: (_STEPPER_BANK_A if slot % 2 == 1 else _STEPPER_BANK_B).copy() for slot in range(1, 11)
}

SOLENOID_PINS = {
    "restock": 16,
    "troubleshoot": 20,
}

PAYMENT_INPUT_PINS = {
    "coin_acceptor": 19,
}

IR_BREAK_BEAM_PIN = 26

# Combine all pins for easy reference
ALL_OUTPUT_PINS = {
    "RFID SPI SCLK (11)": 11,
    "RFID SPI MOSI (10)": 10,
    "RFID Reader RST (5)": 5,
    "Motor bank A (slots 1,3,5,7,9) IN1 (17)": 17,
    "Motor bank A (slots 1,3,5,7,9) IN2 (27)": 27,
    "Motor bank A (slots 1,3,5,7,9) IN3 (22)": 22,
    "Motor bank A (slots 1,3,5,7,9) IN4 (23)": 23,
    "Motor bank B (slots 2,4,6,8,10) IN1 (4)": 4,
    "Motor bank B (slots 2,4,6,8,10) IN2 (18)": 18,
    "Motor bank B (slots 2,4,6,8,10) IN3 (15)": 15,
    "Motor bank B (slots 2,4,6,8,10) IN4 (14)": 14,
    "Solenoid Restock (16)": 16,
    "Solenoid Troubleshoot (20)": 20,
}

# Reserved by the SPI driver for MFRC522 CE0. Do not toggle as a generic GPIO output.
RESERVED_PINS = {
    "RFID Reader CS (8)": 8,
}

ALL_INPUT_PINS = {
    "Coin Acceptor Pulse (19)": 19,
    "IR Break Beam (26)": 26,
    "RFID SPI MISO (9)": 9,
}

OUTPUT_PIN_TO_LABEL = {pin: label for label, pin in ALL_OUTPUT_PINS.items()}
INPUT_PIN_TO_LABEL = {pin: label for label, pin in ALL_INPUT_PINS.items()}

DEFAULT_LOOPBACK_TESTS = []

STEPPER_BACKEND = os.getenv("STEPPER_BACKEND", "mcp23017" if Path("/dev/i2c-1").exists() else "native_gpio").strip().lower()


def _describe_stepper_backend() -> str:
    i2c_ready = Path("/dev/i2c-1").exists()
    if STEPPER_BACKEND == "mcp23017":
        return "MCP23017 preferred (I2C ready)" if i2c_ready else "MCP23017 preferred (I2C missing, native GPIO test mode)"
    return "native GPIO stepper mode"

UI_FONT = "Segoe UI"
UI_FONT_BOLD = (UI_FONT, 12, "bold")
UI_FONT_BODY = (UI_FONT, 11)
UI_FONT_SMALL = (UI_FONT, 9)

THEMES = {
    "light": {
        "bg": "#f8fafc",
        "fg": "#0f172a",
        "card_bg": "#ffffff",
        "card_border": "#e2e8f0",
        "accent": "#10b981",
        "accent_hover": "#059669",
        "button_bg": "#f1f5f9",
        "nav_bg": "#6366f1",
        "nav_fg": "#ffffff",
        "status_active": "#10b981",
        "status_inactive": "#cbd5e1",
    },
    "dark": {
        "bg": "#0f172a",
        "fg": "#f1f5f9",
        "card_bg": "#1e293b",
        "card_border": "#334155",
        "accent": "#22d3ee",
        "accent_hover": "#06b6d4",
        "button_bg": "#1e293b",
        "nav_bg": "#8b5cf6",
        "nav_fg": "#ffffff",
        "status_active": "#22d3ee",
        "status_inactive": "#475569",
    },
}


class GPIOTestTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GPIO Pin Testing Tool")
        self._fill_screen = os.getenv("APP_WINDOWED", "").strip().lower() not in {"1", "true", "yes"}
        if self._fill_screen:
            try:
                self.attributes("-fullscreen", True)
            except Exception:
                try:
                    self.state("zoomed")
                except Exception:
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        else:
            self.geometry("1000x700")
        self.minsize(640, 400)
        self.resizable(True, True)
        
        self.current_theme_name = "light"
        self.current_theme = THEMES[self.current_theme_name]
        ctk.set_appearance_mode(self.current_theme_name)
        ctk.set_default_color_theme("green")
        
        self.configure(fg_color=self.current_theme["bg"])
        
        # Pin states tracking
        self.output_pin_states = {pin: False for pin in ALL_OUTPUT_PINS.values()}
        self.input_pin_states = {pin: False for pin in ALL_INPUT_PINS.values()}
        self.last_raw_input_states = {pin: None for pin in ALL_INPUT_PINS.values()}
        self.input_pulse_counts = {pin: 0 for pin in ALL_INPUT_PINS.values()}
        self.input_last_change = {pin: "never" for pin in ALL_INPUT_PINS.values()}
        self.edge_detection_enabled = {pin: False for pin in ALL_INPUT_PINS.values()}
        self.input_state_labels = {}
        self.input_count_labels = {}
        self.input_last_labels = {}
        self.output_toggle_buttons = {}
        self.test_status_label = None
        self.initialized_output_pins = set()
        self.initialized_input_pins = set()

        _gpio_app_ref[0] = self

        self.loopback_test_pairs = []
        for output_label, input_label in DEFAULT_LOOPBACK_TESTS:
            output_pin = ALL_OUTPUT_PINS.get(output_label)
            input_pin = ALL_INPUT_PINS.get(input_label)
            if output_pin is not None and input_pin is not None:
                self.loopback_test_pairs.append((output_pin, input_pin))

        self.event_log_path = Path(__file__).resolve().parent / "debug_logs" / "pin_test_events.csv"
        self.event_log_lock = threading.Lock()
        self._setup_event_log()
        
        # Setup GPIO
        self.gpio_ready = self.setup_gpio()
        if self.gpio_ready:
            print(f"[GPIO Test Tool] GPIO mode: live ({GPIO_LIBRARY})")
        else:
            print("[GPIO Test Tool] GPIO mode: simulation")
        print(f"[GPIO Test Tool] Stepper backend: {_describe_stepper_backend()}")
        print(f"[GPIO Test Tool] Window mode: {'fullscreen' if self._fill_screen else 'windowed'}")
        
        # Build UI
        self.build_ui()

        if not ON_RPI:
            messagebox.showwarning(
                "Mock Mode",
                "Running without RPi.GPIO.\n\n"
                "Input/output changes are simulated only and do not verify electrical signals.\n"
                "Run this tool on a Raspberry Pi to test actual pin signals.",
            )
        
        # Start input monitoring thread
        self.monitoring = self.gpio_ready
        if self.gpio_ready:
            self.monitor_thread = threading.Thread(target=self.monitor_input_pins, daemon=True)
            self.monitor_thread.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        if not ON_RPI:
            print("[GPIO Test Tool] Running in mock mode (not on Raspberry Pi)")
            return False
        
        print(f"[GPIO Test Tool] Initializing GPIO using {GPIO_LIBRARY}...")
        
        try:
            # Setup output pins
            for pin in ALL_OUTPUT_PINS.values():
                try:
                    if GPIO_LIBRARY == "gpiozero":
                        setup_gpiozero_output(pin)
                        if gpiozero_is_output_ready(pin):
                            self.initialized_output_pins.add(pin)
                    else:
                        GPIO.setup(pin, GPIO.OUT)
                        GPIO.output(pin, GPIO.LOW)
                        self.initialized_output_pins.add(pin)
                except Exception as e:
                    print(f"[GPIO] Failed to setup output pin {pin}: {e}")
            
            # Setup input pins
            for pin in ALL_INPUT_PINS.values():
                try:
                    if GPIO_LIBRARY == "gpiozero":
                        setup_gpiozero_input(pin)
                        if gpiozero_is_input_ready(pin):
                            self.edge_detection_enabled[pin] = True
                            self.initialized_input_pins.add(pin)
                    else:
                        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                        GPIO.add_event_detect(pin, GPIO.BOTH, callback=self._on_input_edge, bouncetime=20)
                        self.edge_detection_enabled[pin] = True
                        self.initialized_input_pins.add(pin)
                except Exception as e:
                    print(f"[GPIO] Failed to setup input pin {pin}: {e}")
            
            print(
                f"[GPIO Test Tool] GPIO setup complete: "
                f"outputs={len(self.initialized_output_pins)}/{len(ALL_OUTPUT_PINS)}, "
                f"inputs={len(self.initialized_input_pins)}/{len(ALL_INPUT_PINS)}"
            )
            return bool(self.initialized_output_pins or self.initialized_input_pins)
        except Exception as e:
            messagebox.showerror("GPIO Setup Error", f"Failed to initialize GPIO: {e}")
            return False

    def _setup_event_log(self):
        """Create CSV log file for pin events if it does not exist."""
        try:
            self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.event_log_path.exists():
                with self.event_log_path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "event", "pin", "label", "state", "details"])
        except Exception as e:
            print(f"[GPIO Log] Failed to initialize event log: {e}")

    def log_event(self, event_name, pin_num=None, state=None, details=""):
        """Append a pin event entry to CSV log."""
        label = ""
        if pin_num in OUTPUT_PIN_TO_LABEL:
            label = OUTPUT_PIN_TO_LABEL[pin_num]
        elif pin_num in INPUT_PIN_TO_LABEL:
            label = INPUT_PIN_TO_LABEL[pin_num]

        row = [
            datetime.now().isoformat(timespec="seconds"),
            event_name,
            "" if pin_num is None else pin_num,
            label,
            "" if state is None else state,
            details,
        ]

        try:
            with self.event_log_lock:
                with self.event_log_path.open("a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
        except Exception as e:
            print(f"[GPIO Log] Failed to write event: {e}")

    def _on_input_edge(self, pin_num):
        """Edge callback for input pins on Raspberry Pi."""
        if not self.gpio_ready:
            return

        if pin_num not in self.input_pulse_counts:
            return

        self.input_pulse_counts[pin_num] += 1
        self.input_last_change[pin_num] = time.strftime("%H:%M:%S")
        state = gpiozero_input(pin_num) if GPIO_LIBRARY == "gpiozero" else GPIO.input(pin_num)
        self.log_event("input_edge", pin_num=pin_num, state=state)

        # GPIO callbacks run outside Tk mainloop; schedule UI updates safely.
        self.after(0, self._refresh_input_aux_labels, pin_num)

    def _refresh_input_aux_labels(self, pin_num):
        """Refresh pulse count and last-change labels for an input pin."""
        if pin_num in self.input_count_labels:
            self.input_count_labels[pin_num].configure(text=str(self.input_pulse_counts[pin_num]))
        if pin_num in self.input_last_labels:
            self.input_last_labels[pin_num].configure(text=self.input_last_change[pin_num])
    
    def build_ui(self):
        """Build the main UI"""
        # Top header
        header = ctk.CTkFrame(self, fg_color=self.current_theme["nav_bg"], corner_radius=0, height=60)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🔌 GPIO Pin Testing Tool",
            font=(UI_FONT, 16, "bold"),
            text_color=self.current_theme["nav_fg"],
        ).pack(side=tk.LEFT, padx=16, pady=12)
        
        status_text = "🟢 Live Mode (RPi - " + GPIO_LIBRARY + ")" if ON_RPI else "🟡 Mock Mode (Development)"
        ctk.CTkLabel(
            header,
            text=status_text,
            font=UI_FONT_SMALL,
            text_color=self.current_theme["nav_fg"],
        ).pack(side=tk.RIGHT, padx=16, pady=12)
        
        # Main content area
        main_frame = ctk.CTkFrame(self, fg_color=self.current_theme["bg"], corner_radius=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Two column layout
        left_col = ctk.CTkFrame(main_frame, fg_color=self.current_theme["bg"])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        
        right_col = ctk.CTkFrame(main_frame, fg_color=self.current_theme["bg"])
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))
        
        # OUTPUT PINS SECTION
        self.build_output_section(left_col)
        
        # INPUT PINS SECTION
        self.build_input_section(right_col)
    
    def build_output_section(self, parent):
        """Build output pins testing section"""
        # Card container
        card = ctk.CTkFrame(
            parent,
            fg_color=self.current_theme["card_bg"],
            border_width=1,
            border_color=self.current_theme["card_border"],
            corner_radius=12,
        )
        card.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ctk.CTkLabel(
            card,
            text="📤 OUTPUT PINS (Control LEDs / Hardware)",
            font=UI_FONT_BOLD,
            text_color=self.current_theme["accent"],
        ).pack(anchor="w", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            card,
            text="Toggle steady states or send 200ms pulse outputs to verify hardware response.",
            font=UI_FONT_SMALL,
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=16, pady=(0, 12))

        action_row = ctk.CTkFrame(card, fg_color="transparent")
        action_row.pack(fill=tk.X, padx=12, pady=(0, 8))

        ctk.CTkButton(
            action_row,
            text="Run All Pin Tests",
            font=UI_FONT_SMALL,
            width=130,
            height=30,
            fg_color=self.current_theme["accent"],
            hover_color=self.current_theme["accent_hover"],
            command=self.run_all_pin_tests,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ctk.CTkButton(
            action_row,
            text="Reset Input Counters",
            font=UI_FONT_SMALL,
            width=140,
            height=30,
            fg_color=self.current_theme["button_bg"],
            text_color=self.current_theme["fg"],
            hover_color=self.current_theme["card_border"],
            command=self.reset_input_counters,
        ).pack(side=tk.LEFT)

        self.test_status_label = ctk.CTkLabel(
            action_row,
            text="Ready",
            font=UI_FONT_SMALL,
            text_color=self.current_theme["fg"],
        )
        self.test_status_label.pack(side=tk.RIGHT, padx=4)
        
        # Scrollable frame for pins
        scroll_frame = ctk.CTkScrollableFrame(
            card,
            fg_color=self.current_theme["card_bg"],
            corner_radius=0,
        )
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Pin buttons
        for pin_label, pin_num in ALL_OUTPUT_PINS.items():
            pin_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            pin_row.pack(fill=tk.X, pady=4)
            
            # Pin info
            ctk.CTkLabel(
                pin_row,
                text=pin_label,
                font=UI_FONT_BODY,
                text_color=self.current_theme["fg"],
                width=200,
            ).pack(side=tk.LEFT, padx=4)
            
            # Toggle button
            btn = ctk.CTkButton(
                pin_row,
                text="LOW",
                font=UI_FONT_SMALL,
                width=80,
                height=28,
                fg_color=self.current_theme["status_inactive"],
                hover_color=self.current_theme["accent_hover"],
                command=lambda p=pin_num: self.toggle_output_pin(p),
            )
            btn.pack(side=tk.RIGHT, padx=4)
            self.output_toggle_buttons[pin_num] = btn

            pulse_btn = ctk.CTkButton(
                pin_row,
                text="Pulse 200ms",
                font=UI_FONT_SMALL,
                width=110,
                height=28,
                fg_color=self.current_theme["button_bg"],
                text_color=self.current_theme["fg"],
                hover_color=self.current_theme["card_border"],
                command=lambda p=pin_num: self.pulse_output_pin(p, 0.2),
            )
            pulse_btn.pack(side=tk.RIGHT, padx=4)

            if GPIO_LIBRARY == "gpiozero" and pin_num not in self.initialized_output_pins:
                btn.configure(state="disabled")
                pulse_btn.configure(state="disabled")
    
    def build_input_section(self, parent):
        """Build input pins monitoring section"""
        # Card container
        card = ctk.CTkFrame(
            parent,
            fg_color=self.current_theme["card_bg"],
            border_width=1,
            border_color=self.current_theme["card_border"],
            corner_radius=12,
        )
        card.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ctk.CTkLabel(
            card,
            text="📥 INPUT PINS (Read Sensors / Signals)",
            font=UI_FONT_BOLD,
            text_color=self.current_theme["accent"],
        ).pack(anchor="w", padx=16, pady=(12, 8))
        
        ctk.CTkLabel(
            card,
            text="Live state plus edge counts and last-change timestamps.",
            font=UI_FONT_SMALL,
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=16, pady=(0, 12))
        
        # Scrollable frame for pins
        scroll_frame = ctk.CTkScrollableFrame(
            card,
            fg_color=self.current_theme["card_bg"],
            corner_radius=0,
        )
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        header_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header_row.pack(fill=tk.X, pady=(0, 6))
        ctk.CTkLabel(header_row, text="Pin", font=UI_FONT_SMALL, text_color=self.current_theme["fg"], width=200).pack(side=tk.LEFT, padx=4)
        ctk.CTkLabel(header_row, text="State", font=UI_FONT_SMALL, text_color=self.current_theme["fg"], width=70).pack(side=tk.LEFT, padx=4)
        ctk.CTkLabel(header_row, text="Edges", font=UI_FONT_SMALL, text_color=self.current_theme["fg"], width=70).pack(side=tk.LEFT, padx=4)
        ctk.CTkLabel(header_row, text="Last Change", font=UI_FONT_SMALL, text_color=self.current_theme["fg"], width=120).pack(side=tk.LEFT, padx=4)
        
        # Pin status indicators
        for pin_label, pin_num in ALL_INPUT_PINS.items():
            pin_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            pin_row.pack(fill=tk.X, pady=4)
            
            # Pin info
            ctk.CTkLabel(
                pin_row,
                text=pin_label,
                font=UI_FONT_BODY,
                text_color=self.current_theme["fg"],
                width=200,
            ).pack(side=tk.LEFT, padx=4)
            
            # Status indicator
            status_label = ctk.CTkLabel(
                pin_row,
                text="LOW",
                font=(UI_FONT, 11, "bold"),
                text_color="#cbd5e1",
                width=70,
            )
            status_label.pack(side=tk.LEFT, padx=4)
            self.input_state_labels[pin_num] = status_label

            count_label = ctk.CTkLabel(
                pin_row,
                text="0",
                font=UI_FONT_BODY,
                text_color=self.current_theme["fg"],
                width=70,
            )
            count_label.pack(side=tk.LEFT, padx=4)
            self.input_count_labels[pin_num] = count_label

            last_label = ctk.CTkLabel(
                pin_row,
                text="never",
                font=UI_FONT_BODY,
                text_color=self.current_theme["fg"],
                width=120,
            )
            last_label.pack(side=tk.LEFT, padx=4)
            self.input_last_labels[pin_num] = last_label

    def pulse_output_pin(self, pin_num, duration_sec=0.2):
        """Pulse an output pin HIGH for duration_sec, then return LOW."""
        if pin_num not in self.output_pin_states:
            return

        def _pulse():
            try:
                self._pulse_output_blocking(pin_num, duration_sec)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("GPIO Error", f"Failed to pulse pin {pin_num}: {e}"))

        threading.Thread(target=_pulse, daemon=True).start()

    def _pulse_output_blocking(self, pin_num, duration_sec):
        """Pulse an output pin synchronously; safe to call from worker threads."""
        if GPIO_LIBRARY == "gpiozero":
            gpiozero_output(pin_num, 1)
        else:
            GPIO.output(pin_num, 1)
        self.output_pin_states[pin_num] = True
        self.log_event("output_pulse_start", pin_num=pin_num, state="HIGH")
        self.after(0, lambda: self._set_output_button_state(pin_num, True))
        time.sleep(duration_sec)
        if GPIO_LIBRARY == "gpiozero":
            gpiozero_output(pin_num, 0)
        else:
            GPIO.output(pin_num, 0)
        self.output_pin_states[pin_num] = False
        self.log_event("output_pulse_end", pin_num=pin_num, state="LOW")
        self.after(0, lambda: self._set_output_button_state(pin_num, False))

    def _set_test_status(self, text):
        """Update run-all test status text."""
        if self.test_status_label:
            self.test_status_label.configure(text=text)

    def reset_input_counters(self):
        """Reset edge counters and last-change markers for all inputs."""
        for pin in self.input_pulse_counts:
            self.input_pulse_counts[pin] = 0
            self.input_last_change[pin] = "never"

        self._apply_input_updates([
            (
                pin,
                "LOW" if not self.input_pin_states.get(pin, False) else "HIGH",
                self.current_theme["status_active"] if not self.input_pin_states.get(pin, False) else self.current_theme["status_inactive"],
                "0",
                "never",
            )
            for pin in self.input_state_labels
        ])
        self.log_event("input_counters_reset", details="All input counters reset")

    def run_all_pin_tests(self):
        """Run automated output sweep plus configured loopback pass/fail checks."""
        if not ON_RPI:
            messagebox.showwarning("Mock Mode", "Run All Pin Tests requires Raspberry Pi GPIO hardware.")
            return

        threading.Thread(target=self._run_all_pin_tests_worker, daemon=True).start()

    def _run_all_pin_tests_worker(self):
        """Worker that performs output pulse sweep and loopback validation."""
        self.after(0, self._set_test_status, "Running tests...")
        self.log_event("test_run_start", details="Run All Pin Tests started")

        pulse_failures = 0
        loopback_pass = 0
        loopback_fail = 0

        for output_pin in ALL_OUTPUT_PINS.values():
            try:
                self._pulse_output_blocking(output_pin, 0.12)
                time.sleep(0.08)
            except Exception as e:
                pulse_failures += 1
                self.log_event("output_pulse_error", pin_num=output_pin, details=str(e))

        for output_pin, input_pin in self.loopback_test_pairs:
            before = self.input_pulse_counts.get(input_pin, 0)
            result_details = f"OUT {output_pin} -> IN {input_pin}"
            try:
                self._pulse_output_blocking(output_pin, 0.2)
                deadline = time.time() + 0.7
                detected = False
                while time.time() < deadline:
                    if self.input_pulse_counts.get(input_pin, 0) > before:
                        detected = True
                        break
                    time.sleep(0.02)

                if detected:
                    loopback_pass += 1
                    self.log_event("loopback_pass", pin_num=input_pin, details=result_details)
                else:
                    loopback_fail += 1
                    self.log_event("loopback_fail", pin_num=input_pin, details=result_details)
            except Exception as e:
                loopback_fail += 1
                self.log_event("loopback_error", pin_num=input_pin, details=f"{result_details} | {e}")

        summary = (
            f"Done: pulse failures={pulse_failures}, "
            f"loopback pass={loopback_pass}, fail={loopback_fail}"
        )
        self.log_event("test_run_end", details=summary)
        self.after(0, self._set_test_status, summary)

    def _set_output_button_state(self, pin_num, is_high):
        """Update output button visuals based on logical pin state."""
        btn = self.output_toggle_buttons.get(pin_num)
        if not btn:
            return

        if is_high:
            btn.configure(text="HIGH", fg_color=self.current_theme["status_active"])
        else:
            btn.configure(text="LOW", fg_color=self.current_theme["status_inactive"])
    
    def toggle_output_pin(self, pin_num):
        """Toggle an output pin HIGH/LOW and update button"""
        if pin_num not in self.output_pin_states:
            return
        
        # Toggle state
        new_state = not self.output_pin_states[pin_num]
        self.output_pin_states[pin_num] = new_state
        
        # Set GPIO
        try:
            gpio_state = 1 if new_state else 0
            if GPIO_LIBRARY == "gpiozero":
                gpiozero_output(pin_num, gpio_state)
            else:
                GPIO.output(pin_num, gpio_state)
            print(f"[GPIO] Pin {pin_num} set to {'HIGH' if new_state else 'LOW'}")
            self.log_event("output_toggle", pin_num=pin_num, state=gpio_state)
        except Exception as e:
            messagebox.showerror("GPIO Error", f"Failed to set pin {pin_num}: {e}")
            self.output_pin_states[pin_num] = not new_state
            return
        
        # Update button appearance
        self._set_output_button_state(pin_num, new_state)
    
    def monitor_input_pins(self):
        """Background thread to monitor input pins"""
        while self.monitoring:
            try:
                ui_updates = []
                for pin_num in self.input_state_labels:
                    if not self.edge_detection_enabled.get(pin_num, False):
                        continue

                    try:
                        if GPIO_LIBRARY == "gpiozero":
                            state = gpiozero_input(pin_num)
                        else:
                            state = GPIO.input(pin_num)
                        self.input_pin_states[pin_num] = bool(state)

                        previous_state = self.last_raw_input_states[pin_num]
                        if previous_state is None:
                            self.last_raw_input_states[pin_num] = state
                        elif previous_state != state:
                            self.last_raw_input_states[pin_num] = state
                            # Fallback edge counting when callbacks are unavailable.
                            if not self.edge_detection_enabled.get(pin_num, False):
                                self.input_pulse_counts[pin_num] += 1
                                self.input_last_change[pin_num] = time.strftime("%H:%M:%S")
                                self.log_event("input_edge_polling", pin_num=pin_num, state=state)
                        
                        # Update label color based on state
                        if state == 0:  # LOW (active on most sensors)
                            text = "LOW"
                            color = self.current_theme["status_active"]
                        else:  # HIGH
                            text = "HIGH"
                            color = self.current_theme["status_inactive"]

                        ui_updates.append(
                            (pin_num, text, color, str(self.input_pulse_counts[pin_num]), self.input_last_change[pin_num])
                        )
                    except Exception as e:
                        print(f"[GPIO Monitor] Error reading pin {pin_num}: {e}")

                self.after(0, self._apply_input_updates, ui_updates)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"[GPIO Monitor] Error: {e}")

    def _apply_input_updates(self, updates):
        """Apply input label updates on Tk main thread."""
        for pin_num, state_text, state_color, count_text, last_change_text in updates:
            state_label = self.input_state_labels.get(pin_num)
            if state_label:
                state_label.configure(text=state_text, text_color=state_color)

            count_label = self.input_count_labels.get(pin_num)
            if count_label:
                count_label.configure(text=count_text)

            last_label = self.input_last_labels.get(pin_num)
            if last_label:
                last_label.configure(text=last_change_text)
    
    def on_closing(self):
        """Cleanup on window close"""
        print("[GPIO Test Tool] Shutting down...")
        self.monitoring = False
        _gpio_app_ref[0] = None
        
        # Reset all output pins to LOW
        try:
            for pin in ALL_OUTPUT_PINS.values():
                if GPIO_LIBRARY == "gpiozero":
                    gpiozero_output(pin, 0)
                else:
                    GPIO.output(pin, 0)
        except Exception:
            pass
        
        # Cleanup GPIO
        try:
            if ON_RPI:
                if GPIO_LIBRARY == "gpiozero":
                    gpiozero_cleanup()
                else:
                    GPIO.cleanup()
        except Exception:
            pass
        
        self.destroy()


if __name__ == "__main__":
    app = GPIOTestTool()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[GPIO Test Tool] Interrupted by user")
        app.on_closing()
