"""
Embedded hardware test tool UI builders for diagnostics dashboard.
Extracts UI logic from standalone test scripts and adapts them for tabbed display.
"""

import tkinter as tk
import time
import threading
from tkinter import messagebox
import customtkinter as ctk

try:
    import RPi.GPIO as GPIO
    ON_RPI = True
except ImportError:
    GPIO = None
    ON_RPI = False

try:
    from smbus2 import SMBus
except ImportError:
    try:
        from smbus import SMBus
    except ImportError:
        SMBus = None

UI_FONT = "Segoe UI"
UI_FONT_SMALL = (UI_FONT, 10)
UI_FONT_BODY = (UI_FONT, 12)

# Pin mappings from main system
RFID_PINS = {"spi_sclk": 11, "spi_mosi": 10, "spi_miso": 9, "reader_cs": 8, "reader_rst": 5}
_STEPPER_BANK_A = {"in1": 17, "in2": 27, "in3": 22, "in4": 23}
_STEPPER_BANK_B = {"in1": 4, "in2": 18, "in3": 15, "in4": 14}
PRODUCT_STEPPER_PINS = {
    slot: (_STEPPER_BANK_A if slot % 2 == 1 else _STEPPER_BANK_B).copy() for slot in range(1, 11)
}
SOLENOID_PINS = {"restock": 16, "troubleshoot": 20}
PAYMENT_INPUT_PINS = {"coin_acceptor": 19}
IR_BREAK_BEAM_PIN = 26

# Output pins for GPIO test
ALL_OUTPUT_PINS = {
    "RFID SPI SCLK (11)": 11,
    "RFID SPI MOSI (10)": 10,
    "RFID Reader RST (5)": 5,
    "Motor A IN1 (17)": 17,
    "Motor A IN2 (27)": 27,
    "Motor A IN3 (22)": 22,
    "Motor A IN4 (23)": 23,
    "Motor B IN1 (4)": 4,
    "Motor B IN2 (18)": 18,
    "Motor B IN3 (15)": 15,
    "Motor B IN4 (14)": 14,
    "Solenoid Restock (16)": 16,
    "Solenoid Troubleshoot (20)": 20,
}

# Input pins for GPIO test
ALL_INPUT_PINS = {
    "Coin Acceptor (19)": 19,
    "IR Break Beam (26)": 26,
    "RFID SPI MISO (9)": 9,
}


def build_stepper_tab(parent_frame, theme):
    """Build stepper motor test UI tab."""
    inner = ctk.CTkScrollableFrame(parent_frame, fg_color=theme["bg"])
    inner.pack(fill=tk.BOTH, expand=True)

    # Controls card
    card = ctk.CTkFrame(
        inner,
        fg_color=theme.get("card_bg", theme["button_bg"]),
        corner_radius=10,
        border_width=1,
        border_color=theme.get("card_border", "#d1d1d6"),
    )
    card.pack(fill=tk.X, padx=8, pady=8)

    ctk.CTkLabel(
        card,
        text="Stepper Motor Control",
        font=(UI_FONT, 13, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w", padx=14, pady=(12, 4))

    ctk.CTkLabel(
        card,
        text="Select slot, configure steps and delay, then run test",
        font=UI_FONT_SMALL,
        text_color=theme.get("muted", theme["fg"]),
    ).pack(anchor="w", padx=14, pady=(0, 10))

    # Form fields
    form_frame = ctk.CTkFrame(card, fg_color=theme.get("card_bg", theme["button_bg"]))
    form_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    slot_var = tk.StringVar(value="1")
    steps_var = tk.IntVar(value=512)
    delay_var = tk.DoubleVar(value=2.0)
    direction_var = tk.StringVar(value="forward")

    def make_field(label_text, var, input_type="entry"):
        row = ctk.CTkFrame(form_frame, fg_color="transparent")
        row.pack(fill=tk.X, pady=4)
        ctk.CTkLabel(row, text=label_text, font=UI_FONT_SMALL, text_color=theme["fg"], width=120, anchor="w").pack(
            side=tk.LEFT
        )
        if input_type == "entry":
            entry = ctk.CTkEntry(
                row,
                textvariable=var,
                font=UI_FONT_BODY,
                width=150,
                fg_color=theme.get("search_bg", "#f2f2f7"),
                text_color=theme["fg"],
            )
            entry.pack(side=tk.LEFT, padx=(0, 8))
        elif input_type == "spinbox":
            spinbox = tk.Spinbox(
                row,
                from_=1,
                to=10,
                textvariable=var,
                font=UI_FONT_BODY,
                width=10,
                bg=theme.get("search_bg", "#f2f2f7"),
                fg=theme["fg"],
            )
            spinbox.pack(side=tk.LEFT, padx=(0, 8))

    make_field("Slot (1-10):", slot_var, "spinbox")
    make_field("Steps per rev:", steps_var)
    make_field("Step delay (ms):", delay_var)

    dir_row = ctk.CTkFrame(form_frame, fg_color="transparent")
    dir_row.pack(fill=tk.X, pady=4)
    ctk.CTkLabel(dir_row, text="Direction:", font=UI_FONT_SMALL, text_color=theme["fg"], width=120, anchor="w").pack(
        side=tk.LEFT
    )
    ctk.CTkOptionMenu(
        dir_row,
        values=["forward", "reverse"],
        variable=direction_var,
        fg_color=theme.get("button_bg", "#f1f5f9"),
        button_color=theme.get("accent", "#22c55e"),
        text_color=theme["fg"],
    ).pack(side=tk.LEFT)

    # Buttons
    btn_frame = ctk.CTkFrame(card, fg_color="transparent")
    btn_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    status_label = ctk.CTkLabel(card, text="Ready", font=UI_FONT_SMALL, text_color=theme.get("accent", "#22c55e"))
    status_label.pack(anchor="w", padx=14, pady=(0, 8))

    def run_stepper():
        if not ON_RPI:
            messagebox.showwarning("Not on RPi", "Stepper test requires Raspberry Pi GPIO")
            return
        # Start/Stop behavior using an event flag
        status_label.configure(text="Starting...", text_color=theme.get("accent", "#22c55e"))
        inner.update_idletasks()

        stop_event = threading.Event()

        def _run():
            try:
                slot = int(slot_var.get())
                steps = int(steps_var.get())
                delay = float(delay_var.get()) / 1000.0
                is_reverse = direction_var.get() == "reverse"

                if slot < 1 or slot > 10:
                    status_label.configure(text="Invalid slot (1-10)", text_color=theme.get("status_error", "#ef4444"))
                    return

                pins = PRODUCT_STEPPER_PINS.get(slot)
                if not pins:
                    status_label.configure(text="Slot not found", text_color=theme.get("status_error", "#ef4444"))
                    return

                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                for pin in pins.values():
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)

                phases = [(1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1), (1, 0, 0, 1)]

                count = 0
                while count < steps and not stop_event.is_set():
                    for phase in reversed(phases) if is_reverse else phases:
                        for pin_name, pin_num in pins.items():
                            idx = ["in1", "in2", "in3", "in4"].index(pin_name)
                            GPIO.output(pin_num, GPIO.HIGH if phase[idx] else GPIO.LOW)
                        time.sleep(delay)
                        count += 1
                        if stop_event.is_set() or count >= steps:
                            break

                for pin in pins.values():
                    GPIO.output(pin, GPIO.LOW)
                try:
                    GPIO.cleanup()
                except Exception:
                    pass

                if stop_event.is_set():
                    status_label.configure(text="Stopped", text_color=theme.get("status_error", "#ef4444"))
                else:
                    status_label.configure(text="Complete!", text_color=theme.get("accent", "#22c55e"))
            except Exception as e:
                status_label.configure(text=f"Error: {str(e)[:30]}", text_color=theme.get("status_error", "#ef4444"))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return stop_event, thread

    # Start/Stop toggle button
    running_state = {"stop_event": None, "thread": None}

    def toggle_start_stop():
        if running_state["thread"] and running_state["thread"].is_alive():
            # Stop
            if running_state["stop_event"]:
                running_state["stop_event"].set()
            start_btn.configure(text="Start", fg_color=theme.get("accent", "#22c55e"))
        else:
            # Start
            ev, th = run_stepper()
            running_state["stop_event"] = ev
            running_state["thread"] = th
            start_btn.configure(text="Stop", fg_color=theme.get("status_error", "#ef4444"))

    start_btn = ctk.CTkButton(
        btn_frame,
        text="Start",
        font=(UI_FONT, 11, "bold"),
        command=toggle_start_stop,
        fg_color=theme.get("accent", "#22c55e"),
        hover_color=theme.get("accent_hover", "#16a34a"),
        text_color="#ffffff",
        corner_radius=8,
        height=36,
    )
    start_btn.pack(side=tk.LEFT, padx=(0, 8))


def build_gpio_tab(parent_frame, theme):
    """Build GPIO pin test UI tab."""
    inner = ctk.CTkScrollableFrame(parent_frame, fg_color=theme["bg"])
    inner.pack(fill=tk.BOTH, expand=True)

    # Output pins
    out_card = ctk.CTkFrame(
        inner,
        fg_color=theme.get("card_bg", theme["button_bg"]),
        corner_radius=10,
        border_width=1,
        border_color=theme.get("card_border", "#d1d1d6"),
    )
    out_card.pack(fill=tk.X, padx=8, pady=8)

    ctk.CTkLabel(
        out_card,
        text="Output Pins (Toggle)",
        font=(UI_FONT, 13, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w", padx=14, pady=(12, 8))

    output_states = {}
    for label, pin in list(ALL_OUTPUT_PINS.items())[:6]:  # Show first 6
        row = ctk.CTkFrame(out_card, fg_color="transparent")
        row.pack(fill=tk.X, padx=14, pady=4)

        output_states[pin] = tk.BooleanVar(value=False)

        def toggle_output(p=pin, var=output_states[pin]):
            if not ON_RPI:
                messagebox.showinfo("GPIO Info", f"Pin {p} would toggle (mock mode)")
                return
            try:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(p, GPIO.OUT)
                GPIO.output(p, GPIO.HIGH if var.get() else GPIO.LOW)
            except Exception as e:
                messagebox.showerror("GPIO Error", str(e))

        ctk.CTkLabel(row, text=label, font=UI_FONT_SMALL, text_color=theme["fg"], width=180, anchor="w").pack(side=tk.LEFT)
        ctk.CTkCheckBox(
            row,
            text="ON",
            variable=output_states[pin],
            command=lambda p=pin: toggle_output(p),
            fg_color=theme.get("accent", "#22c55e"),
        ).pack(side=tk.LEFT)

    # Input pins
    inp_card = ctk.CTkFrame(
        inner,
        fg_color=theme.get("card_bg", theme["button_bg"]),
        corner_radius=10,
        border_width=1,
        border_color=theme.get("card_border", "#d1d1d6"),
    )
    inp_card.pack(fill=tk.X, padx=8, pady=8)

    ctk.CTkLabel(
        inp_card,
        text="Input Pins (Monitor)",
        font=(UI_FONT, 13, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w", padx=14, pady=(12, 8))

    input_labels = {}
    for label, pin in ALL_INPUT_PINS.items():
        row = ctk.CTkFrame(inp_card, fg_color="transparent")
        row.pack(fill=tk.X, padx=14, pady=4)

        ctk.CTkLabel(row, text=label, font=UI_FONT_SMALL, text_color=theme["fg"], width=180, anchor="w").pack(side=tk.LEFT)
        status = ctk.CTkLabel(row, text="---", font=UI_FONT_SMALL, text_color=theme.get("muted", theme["fg"]))
        status.pack(side=tk.LEFT)
        input_labels[pin] = status

    def monitor_inputs():
        if not ON_RPI or GPIO is None:
            return
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for pin in ALL_INPUT_PINS.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            while inp_card.winfo_exists():
                for pin in ALL_INPUT_PINS.values():
                    state = GPIO.input(pin)
                    label_text = "HIGH" if state else "LOW"
                    if pin in input_labels and input_labels[pin].winfo_exists():
                        color = theme.get("accent", "#22c55e") if state else theme.get("status_error", "#ef4444")
                        input_labels[pin].configure(text=label_text, text_color=color)
                time.sleep(0.1)
        except Exception:
            pass

    thread = threading.Thread(target=monitor_inputs, daemon=True)
    thread.start()


def build_mcp_led_tab(parent_frame, theme):
    """Build MCP23017 LED test UI tab."""
    inner = ctk.CTkScrollableFrame(parent_frame, fg_color=theme["bg"])
    inner.pack(fill=tk.BOTH, expand=True)

    card = ctk.CTkFrame(
        inner,
        fg_color=theme.get("card_bg", theme["button_bg"]),
        corner_radius=10,
        border_width=1,
        border_color=theme.get("card_border", "#d1d1d6"),
    )
    card.pack(fill=tk.X, padx=8, pady=8)

    ctk.CTkLabel(
        card,
        text="MCP23017 LED Control",
        font=(UI_FONT, 13, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w", padx=14, pady=(12, 4))

    ctk.CTkLabel(
        card,
        text="Select address and pins to control LEDs via I2C",
        font=UI_FONT_SMALL,
        text_color=theme.get("muted", theme["fg"]),
    ).pack(anchor="w", padx=14, pady=(0, 10))

    # Address selector
    form_frame = ctk.CTkFrame(card, fg_color="transparent")
    form_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    address_var = tk.StringVar(value="0x20")
    ctk.CTkLabel(form_frame, text="MCP Address:", font=UI_FONT_SMALL, text_color=theme["fg"], width=120, anchor="w").pack(
        side=tk.LEFT
    )
    ctk.CTkOptionMenu(
        form_frame,
        values=["0x20", "0x21", "0x22"],
        variable=address_var,
        fg_color=theme.get("button_bg", "#f1f5f9"),
        button_color=theme.get("accent", "#22c55e"),
        text_color=theme["fg"],
    ).pack(side=tk.LEFT)

    # Pin selector (16 pins for MCP23017)
    pin_frame = ctk.CTkFrame(card, fg_color="transparent")
    pin_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    ctk.CTkLabel(pin_frame, text="Pins (0-15):", font=UI_FONT_SMALL, text_color=theme["fg"]).pack(side=tk.LEFT, padx=(0, 8))
    selected_pins = tk.StringVar(value="0,1,2,3")
    ctk.CTkEntry(
        pin_frame,
        textvariable=selected_pins,
        font=UI_FONT_SMALL,
        width=200,
        fg_color=theme.get("search_bg", "#f2f2f7"),
        text_color=theme["fg"],
    ).pack(side=tk.LEFT)

    # Buttons
    btn_frame = ctk.CTkFrame(card, fg_color="transparent")
    btn_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    status_label = ctk.CTkLabel(card, text="Ready", font=UI_FONT_SMALL, text_color=theme.get("accent", "#22c55e"))
    status_label.pack(anchor="w", padx=14, pady=(0, 8))

    def send_mcp_command(action):
        if SMBus is None:
            status_label.configure(text="SMBus not available", text_color=theme.get("status_error", "#ef4444"))
            return

        try:
            addr = int(address_var.get(), 16)
            pins = [int(p.strip()) for p in selected_pins.get().split(",")]
            bus = SMBus(1)
            bus.write_byte_data(addr, 0x00, 0x00)  # IODIRA
            bus.write_byte_data(addr, 0x01, 0x00)  # IODIRB

            # Build mask for selected pins
            mask_a = 0
            mask_b = 0
            for p in pins:
                if 0 <= p <= 7:
                    mask_a |= 1 << p
                elif 8 <= p <= 15:
                    mask_b |= 1 << (p - 8)

            if action == "on":
                bus.write_byte_data(addr, 0x14, mask_a)  # OLATA
                bus.write_byte_data(addr, 0x15, mask_b)  # OLATB
            else:
                bus.write_byte_data(addr, 0x14, 0x00)
                bus.write_byte_data(addr, 0x15, 0x00)

            bus.close()

            status_label.configure(text=f"Sent {action}", text_color=theme.get("accent", "#22c55e"))
        except Exception as e:
            status_label.configure(text=f"Error: {str(e)[:25]}", text_color=theme.get("status_error", "#ef4444"))
    # Replace ON/OFF buttons with a single toggle switch
    mcp_on_var = tk.BooleanVar(value=False)

    def on_toggle():
        if mcp_on_var.get():
            threading.Thread(target=lambda: send_mcp_command("on"), daemon=True).start()
        else:
            threading.Thread(target=lambda: send_mcp_command("off"), daemon=True).start()

    ctk.CTkSwitch(
        btn_frame,
        text="Pins ON",
        variable=mcp_on_var,
        command=on_toggle,
        fg_color=theme.get("accent", "#22c55e"),
    ).pack(side=tk.LEFT)


def build_stepper_mcp_tab(parent_frame, theme):
    """Build MCP23017-based stepper motor test UI tab."""
    inner = ctk.CTkScrollableFrame(parent_frame, fg_color=theme["bg"])
    inner.pack(fill=tk.BOTH, expand=True)

    card = ctk.CTkFrame(
        inner,
        fg_color=theme.get("card_bg", theme["button_bg"]),
        corner_radius=10,
        border_width=1,
        border_color=theme.get("card_border", "#d1d1d6"),
    )
    card.pack(fill=tk.X, padx=8, pady=8)

    ctk.CTkLabel(
        card,
        text="Stepper Motor (via MCP23017)",
        font=(UI_FONT, 13, "bold"),
        text_color=theme["fg"],
    ).pack(anchor="w", padx=14, pady=(12, 4))

    ctk.CTkLabel(
        card,
        text="Control stepper motors through I2C MCP23017 expanders",
        font=UI_FONT_SMALL,
        text_color=theme.get("muted", theme["fg"]),
    ).pack(anchor="w", padx=14, pady=(0, 10))

    form_frame = ctk.CTkFrame(card, fg_color="transparent")
    form_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    slot_var = tk.IntVar(value=1)
    steps_var = tk.IntVar(value=512)
    delay_var = tk.DoubleVar(value=2.0)

    def make_field(label_text, var):
        row = ctk.CTkFrame(form_frame, fg_color="transparent")
        row.pack(fill=tk.X, pady=4)
        ctk.CTkLabel(row, text=label_text, font=UI_FONT_SMALL, text_color=theme["fg"], width=120, anchor="w").pack(side=tk.LEFT)
        ctk.CTkEntry(
            row, textvariable=var, font=UI_FONT_BODY, width=150, fg_color=theme.get("search_bg", "#f2f2f7"), text_color=theme["fg"]
        ).pack(side=tk.LEFT)

    make_field("Slot (1-10):", slot_var)
    make_field("Steps:", steps_var)
    make_field("Delay (ms):", delay_var)

    btn_frame = ctk.CTkFrame(card, fg_color="transparent")
    btn_frame.pack(fill=tk.X, padx=14, pady=(0, 10))

    status_label = ctk.CTkLabel(card, text="Ready", font=UI_FONT_SMALL, text_color=theme.get("accent", "#22c55e"))
    status_label.pack(anchor="w", padx=14, pady=(0, 8))

    def run_mcp_stepper():
        if SMBus is None:
            status_label.configure(text="SMBus not available", text_color=theme.get("status_error", "#ef4444"))
            return

        status_label.configure(text="Starting...", text_color=theme.get("accent", "#22c55e"))
        inner.update_idletasks()

        stop_event = threading.Event()

        def _run():
            try:
                slot = slot_var.get()
                steps = steps_var.get()
                delay = delay_var.get() / 1000.0

                bus = SMBus(1)
                addr = 0x20
                bus.write_byte_data(addr, 0x00, 0x00)
                bus.write_byte_data(addr, 0x01, 0x00)

                count = 0
                while count < steps and not stop_event.is_set():
                    for val in [0xFF, 0x00]:
                        bus.write_byte_data(addr, 0x14, val)
                        time.sleep(delay)
                        count += 1
                        if stop_event.is_set() or count >= steps:
                            break

                try:
                    bus.close()
                except Exception:
                    pass

                if stop_event.is_set():
                    status_label.configure(text="Stopped", text_color=theme.get("status_error", "#ef4444"))
                else:
                    status_label.configure(text="Complete!", text_color=theme.get("accent", "#22c55e"))
            except Exception as e:
                status_label.configure(text=f"Error: {str(e)[:30]}", text_color=theme.get("status_error", "#ef4444"))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return stop_event, thread

    # Start/Stop toggle for MCP stepper
    mcp_running = {"stop_event": None, "thread": None}

    def toggle_mcp():
        if mcp_running["thread"] and mcp_running["thread"].is_alive():
            if mcp_running["stop_event"]:
                mcp_running["stop_event"].set()
            mcp_start_btn.configure(text="Start", fg_color=theme.get("accent", "#22c55e"))
        else:
            ev, th = run_mcp_stepper()
            mcp_running["stop_event"] = ev
            mcp_running["thread"] = th
            mcp_start_btn.configure(text="Stop", fg_color=theme.get("status_error", "#ef4444"))

    mcp_start_btn = ctk.CTkButton(
        btn_frame,
        text="Start",
        font=(UI_FONT, 11, "bold"),
        command=toggle_mcp,
        fg_color=theme.get("accent", "#22c55e"),
        hover_color=theme.get("accent_hover", "#16a34a"),
        text_color="#ffffff",
        corner_radius=8,
        height=36,
    )
    mcp_start_btn.pack(side=tk.LEFT)
