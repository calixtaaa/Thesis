"""
GPIO Pin Testing Tool
Simple utility to test input and output pins for the vending machine hardware.
Not part of the main app - for development/testing only.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pathlib import Path
import time
import threading

# GPIO mock for development
try:
    import RPi.GPIO as GPIO
    ON_RPI = True
except ImportError:
    ON_RPI = False
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
        def output(self, pin, state): 
            print(f"[GPIO Mock] Pin {pin} set to {state}")
        def input(self, pin): 
            return self.HIGH
        def cleanup(self): pass
        def add_event_detect(self, *_a, **_k): pass

    GPIO = MockGPIO()

# Pin configuration from main.py
RFID_PINS = {
    "spi_sclk": 11,
    "spi_mosi": 10,
    "spi_miso": 9,
    "payment_reader_cs": 8,
    "door_reader_cs": 7,
    "payment_reader_rst": 5,
    "door_reader_rst": 19,
}

PRODUCT_STEPPER_PINS = {
    1: {"in1": 17, "in2": 27, "in3": 22, "in4": 23},
    2: {"in1": 4, "in2": 18, "in3": 15, "in4": 14},
}

SOLENOID_PINS = {
    "restock": 16,
    "troubleshoot": 20,
}

PAYMENT_INPUT_PINS = {
    "bill_acceptor": 6,
    "coin_acceptor": 13,
}

COIN_HOPPER_PINS = {
    1: 12,
    5: 21,
}

HOPPER_FEEDBACK_PINS = {
    1: 24,
    5: 25,
}

IR_BREAK_BEAM_PIN = 26

# Combine all pins for easy reference
ALL_OUTPUT_PINS = {
    "RFID SPI SCLK (11)": 11,
    "RFID SPI MOSI (10)": 10,
    "RFID Payment CS (8)": 8,
    "RFID Door CS (7)": 7,
    "RFID Payment RST (5)": 5,
    "RFID Door RST (19)": 19,
    "Stepper 1 - IN1 (17)": 17,
    "Stepper 1 - IN2 (27)": 27,
    "Stepper 1 - IN3 (22)": 22,
    "Stepper 1 - IN4 (23)": 23,
    "Stepper 2 - IN1 (4)": 4,
    "Stepper 2 - IN2 (18)": 18,
    "Stepper 2 - IN3 (15)": 15,
    "Stepper 2 - IN4 (14)": 14,
    "Solenoid Restock (16)": 16,
    "Solenoid Troubleshoot (20)": 20,
    "Coin Hopper 1-peso (12)": 12,
    "Coin Hopper 5-peso (21)": 21,
}

ALL_INPUT_PINS = {
    "Bill Acceptor Pulse (6)": 6,
    "Coin Acceptor Pulse (13)": 13,
    "Hopper 1-peso Feedback (24)": 24,
    "Hopper 5-peso Feedback (25)": 25,
    "IR Break Beam (26)": 26,
    "RFID SPI MISO (9)": 9,
}

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
        self.geometry("1000x700")
        
        self.current_theme_name = "light"
        self.current_theme = THEMES[self.current_theme_name]
        ctk.set_appearance_mode(self.current_theme_name)
        ctk.set_default_color_theme("green")
        
        self.configure(fg_color=self.current_theme["bg"])
        
        # Pin states tracking
        self.output_pin_states = {pin: False for pin in ALL_OUTPUT_PINS.values()}
        self.input_pin_states = {pin: False for pin in ALL_INPUT_PINS.values()}
        self.input_state_labels = {}
        self.output_toggle_buttons = {}
        
        # Setup GPIO
        self.setup_gpio()
        
        # Build UI
        self.build_ui()
        
        # Start input monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_input_pins, daemon=True)
        self.monitor_thread.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        if not ON_RPI:
            print("[GPIO Test Tool] Running in mock mode (not on Raspberry Pi)")
            return
        
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            
            # Setup output pins
            for pin in ALL_OUTPUT_PINS.values():
                try:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
                except Exception as e:
                    print(f"[GPIO] Failed to setup output pin {pin}: {e}")
            
            # Setup input pins
            for pin in ALL_INPUT_PINS.values():
                try:
                    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                except Exception as e:
                    print(f"[GPIO] Failed to setup input pin {pin}: {e}")
            
            print("[GPIO Test Tool] GPIO setup complete")
        except Exception as e:
            messagebox.showerror("GPIO Setup Error", f"Failed to initialize GPIO: {e}")
    
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
        
        status_text = "🟢 Live Mode (RPi)" if ON_RPI else "🟡 Mock Mode (Development)"
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
            text="Click buttons to toggle OUTPUT pins HIGH/LOW. Connect an LED to verify signals.",
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
            text="Real-time monitoring - Apply 3V or 5V signals to test. Updates automatically.",
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
                width=80,
            )
            status_label.pack(side=tk.RIGHT, padx=4)
            self.input_state_labels[pin_num] = status_label
    
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
            GPIO.output(pin_num, gpio_state)
            print(f"[GPIO] Pin {pin_num} set to {'HIGH' if new_state else 'LOW'}")
        except Exception as e:
            messagebox.showerror("GPIO Error", f"Failed to set pin {pin_num}: {e}")
            self.output_pin_states[pin_num] = not new_state
            return
        
        # Update button appearance
        btn = self.output_toggle_buttons[pin_num]
        if new_state:
            btn.configure(
                text="HIGH",
                fg_color=self.current_theme["status_active"],
            )
        else:
            btn.configure(
                text="LOW",
                fg_color=self.current_theme["status_inactive"],
            )
    
    def monitor_input_pins(self):
        """Background thread to monitor input pins"""
        while self.monitoring:
            try:
                for pin_num, label_widget in self.input_state_labels.items():
                    try:
                        state = GPIO.input(pin_num)
                        self.input_pin_states[pin_num] = bool(state)
                        
                        # Update label color based on state
                        if state == 0:  # LOW (active on most sensors)
                            text = "LOW"
                            color = self.current_theme["status_active"]
                        else:  # HIGH
                            text = "HIGH"
                            color = self.current_theme["status_inactive"]
                        
                        label_widget.configure(text=text, text_color=color)
                    except Exception as e:
                        print(f"[GPIO Monitor] Error reading pin {pin_num}: {e}")
                
                time.sleep(0.1)
            except Exception as e:
                print(f"[GPIO Monitor] Error: {e}")
    
    def on_closing(self):
        """Cleanup on window close"""
        print("[GPIO Test Tool] Shutting down...")
        self.monitoring = False
        
        # Reset all output pins to LOW
        try:
            for pin in ALL_OUTPUT_PINS.values():
                GPIO.output(pin, 0)
        except Exception:
            pass
        
        # Cleanup GPIO
        try:
            if ON_RPI:
                GPIO.cleanup()
        except Exception:
            pass
        
        self.destroy()


if __name__ == "__main__":
    app = GPIOTestTool()
    app.mainloop()
