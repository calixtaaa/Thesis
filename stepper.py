"""
Standalone stepper motor test utility for the vending machine.

Use this tool to verify a 28BYJ-48 stepper with a ULN2003AN driver board,
including one full revolution and custom jog tests from a small UI.
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox
from datetime import date

import customtkinter as ctk

try:
    from gpiozero import OutputDevice
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


_STEPPER_BANK_A = {"in1": 17, "in2": 27, "in3": 22, "in4": 23}
_STEPPER_BANK_B = {"in1": 4, "in2": 18, "in3": 15, "in4": 14}
PRODUCT_STEPPER_PINS = {
    slot: (_STEPPER_BANK_A if slot % 2 == 1 else _STEPPER_BANK_B).copy() for slot in range(1, 11)
}

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

DEFAULT_STEPS_PER_REV = 4096
DEFAULT_STEP_DELAY = 0.002


class StepperTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stepper Test Tool")
        self.geometry("920x620")
        self.minsize(820, 560)

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

        self.current_slot = tk.StringVar(value="2")
        self.steps_per_rev = tk.IntVar(value=DEFAULT_STEPS_PER_REV)
        self.step_delay_ms = tk.DoubleVar(value=DEFAULT_STEP_DELAY * 1000)
        self.custom_steps = tk.IntVar(value=512)
        self.direction = tk.StringVar(value="forward")
        self.status_text = tk.StringVar(value=self._startup_status())
        self.calibration_counter_text = tk.StringVar(value="Calibration jog counter: 0 steps")
        self.snippet_status_text = tk.StringVar(value="Snippet output: not generated")
        self.running = False
        self.stop_requested = False
        self._phase_index = 0
        self._calibration_steps = 0

        self._gpio_ready = False
        self._motor_pins = None
        self._gpiozero_devices = {}

        self._build_ui()
        self.current_slot.trace_add("write", self._on_slot_change)
        self._setup_gpio()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _startup_status(self):
        if ON_RPI:
            return f"GPIO backend: {GPIO_LIBRARY}"
        return "GPIO backend: simulation"

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=self.current_theme["nav_bg"], corner_radius=0, height=72)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side=tk.LEFT, padx=22, pady=14)
        ctk.CTkLabel(
            title_box,
            text="Stepper Test Tool",
            font=("Segoe UI", 22, "bold"),
            text_color=self.current_theme["nav_fg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Standalone 28BYJ-48 + ULN2003AN test window",
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

        left = ctk.CTkFrame(main, fg_color=self.current_theme["bg"], corner_radius=0)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = ctk.CTkFrame(main, fg_color=self.current_theme["bg"], corner_radius=0, width=310)
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
            text="Use slot 2 first if that is the bank you already verified on the ULN2003 board.",
            font=("Segoe UI", 11),
            text_color=self.current_theme["muted"],
            wraplength=540,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        form = ctk.CTkFrame(control_card, fg_color="transparent")
        form.pack(fill=tk.X, padx=18, pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)

        self._field(form, 0, "Slot number", self.current_slot, input_widget="spin")
        self._field(form, 1, "Steps per revolution", self.steps_per_rev, input_widget="entry")
        self._field(form, 2, "Step delay (ms)", self.step_delay_ms, input_widget="entry")
        self._field(form, 3, "Custom steps", self.custom_steps, input_widget="entry")

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
            text="Test selected slot bank",
            command=self.preview_selected_slot,
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
            text="Use jog buttons to move until exactly one dispenser cycle, then apply the counter to steps per revolution.",
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
        ctk.CTkButton(
            jog_forward_row,
            text="Jog +1",
            command=lambda: self.calibration_jog(1),
            fg_color=self.current_theme["accent"],
            hover_color=self.current_theme["accent_hover"],
            text_color="#ffffff",
            width=100,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            jog_forward_row,
            text="Jog +8",
            command=lambda: self.calibration_jog(8),
            fg_color=self.current_theme["accent"],
            hover_color=self.current_theme["accent_hover"],
            text_color="#ffffff",
            width=100,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            jog_forward_row,
            text="Jog +64",
            command=lambda: self.calibration_jog(64),
            fg_color=self.current_theme["accent"],
            hover_color=self.current_theme["accent_hover"],
            text_color="#ffffff",
            width=100,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT)

        jog_reverse_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        jog_reverse_row.pack(fill=tk.X, padx=18, pady=(0, 10))
        ctk.CTkButton(
            jog_reverse_row,
            text="Jog -1",
            command=lambda: self.calibration_jog(-1),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            width=100,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            jog_reverse_row,
            text="Jog -8",
            command=lambda: self.calibration_jog(-8),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            width=100,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            jog_reverse_row,
            text="Jog -64",
            command=lambda: self.calibration_jog(-64),
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            width=100,
            height=36,
            corner_radius=8,
        ).pack(side=tk.LEFT)

        calibration_action_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        calibration_action_row.pack(fill=tk.X, padx=18, pady=(0, 14))
        ctk.CTkButton(
            calibration_action_row,
            text="Reset counter",
            command=self.reset_calibration_counter,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            width=170,
            height=38,
            corner_radius=8,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            calibration_action_row,
            text="Apply counter to steps/rev",
            command=self.apply_calibration_to_steps,
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            text_color="#ffffff",
            width=230,
            height=38,
            corner_radius=8,
        ).pack(side=tk.LEFT)

        export_row = ctk.CTkFrame(calibration_card, fg_color="transparent")
        export_row.pack(fill=tk.X, padx=18, pady=(0, 10))
        ctk.CTkButton(
            export_row,
            text="Generate main.py snippet",
            command=self.generate_main_snippet,
            fg_color="#111827",
            hover_color="#1f2937",
            text_color="#ffffff",
            width=220,
            height=38,
            corner_radius=8,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            export_row,
            text="Copy snippet",
            command=self.copy_generated_snippet,
            fg_color=self.current_theme["button_bg"],
            hover_color=self.current_theme["card_border"],
            text_color=self.current_theme["button_fg"],
            width=140,
            height=38,
            corner_radius=8,
        ).pack(side=tk.LEFT)

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
            text="Wiring Summary",
            font=("Segoe UI", 18, "bold"),
            text_color=self.current_theme["fg"],
        ).pack(anchor="w", padx=18, pady=(18, 8))
        info_text = (
            "ULN2003 IN1-IN4 -> Raspberry Pi GPIO.\n\n"
            "Bank A (odd slots): 17, 27, 22, 23\n"
            "Bank B (even slots): 4, 18, 15, 14\n\n"
            "Motor power must come from the external 12V supply.\n"
            "Share ground between Pi, PSU, and driver board.\n\n"
            "This tool rotates a selected slot bank using the same sequence as main.py."
        )
        ctk.CTkLabel(
            info_card,
            text=info_text,
            font=("Segoe UI", 11),
            text_color=self.current_theme["muted"],
            justify="left",
            wraplength=260,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        self.pin_preview = ctk.CTkLabel(
            info_card,
            text="Selected bank: slot 2\nIN1  GPIO4\nIN2  GPIO18\nIN3  GPIO15\nIN4  GPIO14",
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

    def _refresh_preview(self):
        slot = self._get_slot_number()
        pins = PRODUCT_STEPPER_PINS.get(slot)
        if not pins:
            self.pin_preview.configure(text=f"Selected slot {slot}\nNo pin mapping")
            return
        self.pin_preview.configure(
            text=(
                f"Selected bank: slot {slot}\n"
                f"IN1  GPIO{pins['in1']}\n"
                f"IN2  GPIO{pins['in2']}\n"
                f"IN3  GPIO{pins['in3']}\n"
                f"IN4  GPIO{pins['in4']}"
            )
        )

    def _get_slot_number(self):
        try:
            return int(self.current_slot.get())
        except Exception:
            return 2

    def _slot_changed(self, value):
        self.current_slot.set(str(value))
        self._on_slot_change()

    def _on_slot_change(self, *_args):
        self._motor_pins = PRODUCT_STEPPER_PINS.get(self._get_slot_number())
        self._refresh_preview()
        self.reset_calibration_counter(update_status=False)
        if self._gpio_ready and ON_RPI:
            self._cleanup_gpio()
            self._gpio_ready = False
            self._setup_gpio()

    def _setup_gpio(self):
        slot = self._get_slot_number()
        self._motor_pins = PRODUCT_STEPPER_PINS.get(slot)
        if not self._motor_pins:
            self.status_text.set(f"No motor pins for slot {slot}")
            return

        if not ON_RPI:
            self.status_text.set("Simulation mode: GPIO not available")
            return

        try:
            if GPIO_LIBRARY == "gpiozero":
                for pin in self._motor_pins.values():
                    self._gpiozero_devices[pin] = OutputDevice(pin)
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                for pin in self._motor_pins.values():
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
            self._gpio_ready = True
            self.status_text.set(f"Ready on slot {slot} using {GPIO_LIBRARY}")
        except Exception as exc:
            self.status_text.set(f"GPIO setup failed: {exc}")
            messagebox.showerror("GPIO setup failed", str(exc))

    def _cleanup_gpio(self):
        try:
            if GPIO_LIBRARY == "gpiozero":
                for dev in self._gpiozero_devices.values():
                    try:
                        dev.close()
                    except Exception:
                        pass
                self._gpiozero_devices.clear()
            elif ON_RPI:
                for pin in self._motor_pins.values():
                    try:
                        GPIO.output(pin, GPIO.LOW)
                    except Exception:
                        pass
                GPIO.cleanup()
        except Exception:
            pass

    def _set_phase(self, pins, phase):
        if GPIO_LIBRARY == "gpiozero":
            for pin_name, value in zip(("in1", "in2", "in3", "in4"), phase):
                self._gpiozero_devices[pins[pin_name]].value = bool(value)
        else:
            GPIO.output(pins["in1"], GPIO.HIGH if phase[0] else GPIO.LOW)
            GPIO.output(pins["in2"], GPIO.HIGH if phase[1] else GPIO.LOW)
            GPIO.output(pins["in3"], GPIO.HIGH if phase[2] else GPIO.LOW)
            GPIO.output(pins["in4"], GPIO.HIGH if phase[3] else GPIO.LOW)

    def _deenergize(self, pins):
        self._set_phase(pins, (0, 0, 0, 0))

    def _jog_steps_blocking(self, pins, delta_steps, step_delay):
        count = abs(int(delta_steps))
        direction = 1 if delta_steps >= 0 else -1
        for _ in range(count):
            if direction > 0:
                self._phase_index = (self._phase_index + 1) % len(ULN2003_SEQUENCE)
            else:
                self._phase_index = (self._phase_index - 1) % len(ULN2003_SEQUENCE)
            self._set_phase(pins, ULN2003_SEQUENCE[self._phase_index])
            time.sleep(step_delay)
        self._deenergize(pins)

    def _rotate(self, steps, slot=None):
        if self.running:
            return

        slot_number = slot if slot is not None else self._get_slot_number()
        pins = PRODUCT_STEPPER_PINS.get(slot_number)
        if not pins:
            messagebox.showerror("Invalid slot", f"No stepper mapping for slot {slot_number}")
            return

        if not self._gpio_ready and ON_RPI:
            self._setup_gpio()
            pins = PRODUCT_STEPPER_PINS.get(slot_number)
            if not self._gpio_ready:
                return

        try:
            step_delay = max(0.0005, float(self.step_delay_ms.get()) / 1000.0)
        except Exception:
            step_delay = DEFAULT_STEP_DELAY
        direction = self.direction.get()
        phase_sequence = ULN2003_SEQUENCE if direction == "forward" else list(reversed(ULN2003_SEQUENCE))

        def worker():
            self.running = True
            self.stop_requested = False
            self.progress_label.configure(text="Running", text_color=self.current_theme["status_warn"])
            try:
                for i in range(int(steps)):
                    if self.stop_requested:
                        break
                    self._set_phase(pins, phase_sequence[i % len(phase_sequence)])
                    time.sleep(step_delay)
                self._deenergize(pins)
                final_text = "Stopped" if self.stop_requested else f"Completed {int(steps)} steps"
                color = self.current_theme["status_warn"] if self.stop_requested else self.current_theme["status_ok"]
                self.after(0, lambda: self.progress_label.configure(text=final_text, text_color=color))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Stepper error", str(exc)))
                self.after(0, lambda: self.progress_label.configure(text="Error", text_color=self.current_theme["status_error"]))
            finally:
                try:
                    self._deenergize(pins)
                except Exception:
                    pass
                self.running = False

        threading.Thread(target=worker, daemon=True).start()

    def spin_one_revolution(self):
        self._refresh_preview()
        try:
            steps = int(self.steps_per_rev.get())
        except Exception:
            messagebox.showerror("Invalid input", "Steps per revolution must be a number.")
            return
        self._rotate(steps)

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
        self._rotate(steps)

    def preview_selected_slot(self):
        self._refresh_preview()
        slot = self._get_slot_number()
        if messagebox.askyesno(
            "Preview slot",
            f"Run one revolution on slot {slot}?\n\nThis uses the current steps per revolution value.",
        ):
            self.spin_one_revolution()

    def stop_motor(self):
        self.stop_requested = True
        self.progress_label.configure(text="Stop requested", text_color=self.current_theme["status_warn"])

    def reset_calibration_counter(self, update_status=True):
        self._calibration_steps = 0
        self._phase_index = 0
        self.calibration_counter_text.set("Calibration jog counter: 0 steps")
        if update_status:
            self.progress_label.configure(text="Calibration counter reset", text_color=self.current_theme["status_ok"])

    def calibration_jog(self, delta_steps):
        if self.running:
            return

        slot_number = self._get_slot_number()
        pins = PRODUCT_STEPPER_PINS.get(slot_number)
        if not pins:
            messagebox.showerror("Invalid slot", f"No stepper mapping for slot {slot_number}")
            return

        if not self._gpio_ready and ON_RPI:
            self._setup_gpio()
            if not self._gpio_ready:
                return

        try:
            step_delay = max(0.001, float(self.step_delay_ms.get()) / 1000.0)
        except Exception:
            step_delay = DEFAULT_STEP_DELAY

        self.progress_label.configure(text=f"Jogging {delta_steps:+d} steps", text_color=self.current_theme["status_warn"])
        try:
            self._jog_steps_blocking(pins, int(delta_steps), step_delay)
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
        bank = "A" if slot % 2 == 1 else "B"
        calibrated_steps = abs(int(self.steps_per_rev.get()))
        today = date.today().isoformat()
        return (
            f"# Calibrated with stepper.py on {today}\\n"
            f"# Slot {slot} (bank {bank}) tested with 28BYJ-48 + ULN2003AN\\n"
            f"CALIBRATED_STEPS_PER_SLOT = {{\\n"
            f"    {slot}: {calibrated_steps},\\n"
            f"}}\\n\\n"
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
        self._cleanup_gpio()
        self.destroy()


if __name__ == "__main__":
    app = StepperTestApp()
    app.after(100, app._on_slot_change)
    app.mainloop()
