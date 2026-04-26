#!/usr/bin/env python3
"""
Interactive wiring visual guide showing detailed component pinouts.
Click components to view connections, use Details panel to hide/show.
"""

import customtkinter as ctk
import tkinter as tk
from dataclasses import dataclass
from typing import Optional


# Colors - simple dark scheme
COLORS = {
    "bg_main": "#0a0e27",
    "bg_panel": "#111b2e",
    "bg_canvas": "#0f1419",
    "text": "#e0e0e0",
    "text_muted": "#888888",
    "border": "#333333",
    "grid": "#1a1f2e",
}

WIRE_COLORS = {
    "power": "#dc2626",
    "rfid": "#0369a1",
    "motor": "#059669",
    "lock": "#b45309",
    "sensor": "#7c3aed",
}


@dataclass
class Node:
    key: str
    title: str
    x: float
    y: float
    width: float
    height: float
    pinout: dict  # pin_name: description
    connections: list  # wire categories this connects to


@dataclass
class WirePoint:
    x: float
    y: float


class WiringVisualGuide(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wiring Guide - Component Pinouts")
        self.geometry("1600x900")
        
        self.scale = 1.0
        self.details_visible = False
        self.node_canvas_ids = {}
        self.selected_key: Optional[str] = None
        
        self._build_components()
        self._build_layout()
        self._redraw()

    def _build_components(self):
        """Define all components with pinout details"""
        self.nodes = {
            "pi5": Node(
                key="pi5",
                title="Raspberry Pi 5",
                x=800, y=400,
                width=200, height=180,
                pinout={
                    "GPIO2": "I2C SDA",
                    "GPIO3": "I2C SCL",
                    "GPIO5": "RFID RST",
                    "GPIO8": "SPI CE0",
                    "GPIO9": "SPI MISO",
                    "GPIO10": "SPI MOSI",
                    "GPIO11": "SPI SCK",
                    "GPIO16": "Relay IN1",
                    "GPIO20": "Relay IN2",
                    "GPIO19": "Coin Pulse",
                    "GPIO26": "IR Sensor",
                    "5V": "Power Rail",
                    "3.3V": "Logic Power",
                    "GND": "Ground",
                },
                connections=["power", "rfid", "motor", "lock", "sensor"]
            ),
            "rfid": Node(
                key="rfid",
                title="MFRC522 RFID",
                x=1150, y=150,
                width=180, height=140,
                pinout={
                    "SCK": "SPI Clock (GPIO11)",
                    "MOSI": "SPI Data In (GPIO10)",
                    "MISO": "SPI Data Out (GPIO9)",
                    "SDA/SS": "Chip Select (GPIO8)",
                    "RST": "Reset (GPIO5)",
                    "GND": "Ground",
                    "3.3V": "Power (Pi 3.3V)",
                },
                connections=["rfid", "power"]
            ),
            "mcp20": Node(
                key="mcp20",
                title="MCP23017 #1\n(Addr: 0x20)",
                x=200, y=150,
                width=170, height=140,
                pinout={
                    "SDA": "I2C Data (GPIO2)",
                    "SCL": "I2C Clock (GPIO3)",
                    "A0-A2": "Address 0x20",
                    "GPA0-7": "GPIO Port A",
                    "GPB0-3": "Motor Slots 1-4",
                    "RST": "Reset",
                    "GND": "Ground",
                    "VDD": "3.3V Power",
                },
                connections=["motor", "power"]
            ),
            "mcp21": Node(
                key="mcp21",
                title="MCP23017 #2\n(Addr: 0x21)",
                x=200, y=330,
                width=170, height=140,
                pinout={
                    "SDA": "I2C Data (GPIO2)",
                    "SCL": "I2C Clock (GPIO3)",
                    "A0-A2": "Address 0x21",
                    "GPA0-7": "GPIO Port A",
                    "GPB0-3": "Motor Slots 5-8",
                    "RST": "Reset",
                    "GND": "Ground",
                    "VDD": "3.3V Power",
                },
                connections=["motor", "power"]
            ),
            "mcp22": Node(
                key="mcp22",
                title="MCP23017 #3\n(Addr: 0x22)",
                x=200, y=510,
                width=170, height=140,
                pinout={
                    "SDA": "I2C Data (GPIO2)",
                    "SCL": "I2C Clock (GPIO3)",
                    "A0-A2": "Address 0x22",
                    "GPA0-7": "GPIO Port A",
                    "GPB0-1": "Motor Slots 9-10",
                    "RST": "Reset",
                    "GND": "Ground",
                    "VDD": "3.3V Power",
                },
                connections=["motor", "power"]
            ),
            "motors": Node(
                key="motors",
                title="ULN2003 + 28BYJ-48\nSteppers (10x)",
                x=50, y=300,
                width=140, height=200,
                pinout={
                    "IN1-4": "Motor Coil Ctrl",
                    "GND": "Ground",
                    "12V": "Motor Power",
                },
                connections=["motor", "power"]
            ),
            "relay": Node(
                key="relay",
                title="Songle 2-Channel\nRelay Module",
                x=1150, y=350,
                width=180, height=120,
                pinout={
                    "IN1": "GPIO16 Signal",
                    "IN2": "GPIO20 Signal",
                    "GND": "Ground",
                    "VCC": "5V Power",
                    "COM": "Relay Common",
                    "NO1": "Restock Solenoid",
                    "NO2": "Troubleshoot Solenoid",
                },
                connections=["lock", "power"]
            ),
            "solenoid_r": Node(
                key="solenoid_r",
                title="Solenoid Lock\n(Restock)",
                x=1380, y=300,
                width=160, height=100,
                pinout={
                    "+": "12V from Relay NO1",
                    "-": "12V PSU Ground",
                    "Coil": "Electromagnetic",
                    "Flyback": "Protection Diode",
                },
                connections=["lock", "power"]
            ),
            "solenoid_t": Node(
                key="solenoid_t",
                title="Solenoid Lock\n(Troubleshoot)",
                x=1380, y=440,
                width=160, height=100,
                pinout={
                    "+": "12V from Relay NO2",
                    "-": "12V PSU Ground",
                    "Coil": "Electromagnetic",
                    "Flyback": "Protection Diode",
                },
                connections=["lock", "power"]
            ),
            "coin": Node(
                key="coin",
                title="Coin Acceptor\nWEIYU 1239",
                x=500, y=700,
                width=160, height=100,
                pinout={
                    "Pulse": "GPIO19 Signal",
                    "GND": "Ground",
                    "12V": "Input Power",
                },
                connections=["sensor", "power"]
            ),
            "ir": Node(
                key="ir",
                title="IR Break-Beam\nSensor",
                x=750, y=700,
                width=160, height=100,
                pinout={
                    "Signal": "GPIO26 (Active Low)",
                    "VCC": "5V Power",
                    "GND": "Ground",
                },
                connections=["sensor", "power"]
            ),
            "psu_12v": Node(
                key="psu_12v",
                title="12V PSU",
                x=50, y=700,
                width=140, height=100,
                pinout={
                    "+": "12V Output",
                    "-": "GND (tied to Pi GND)",
                },
                connections=["power"]
            ),
        }

        self.edges = [
            ("pi5", "rfid", "SPI: GPIO11/10/9/8 + GPIO5 RST", "rfid"),
            ("pi5", "mcp20", "I2C: GPIO2/3", "motor"),
            ("pi5", "mcp21", "I2C: GPIO2/3", "motor"),
            ("pi5", "mcp22", "I2C: GPIO2/3", "motor"),
            ("mcp20", "motors", "Motor Slots 1-4", "motor"),
            ("mcp21", "motors", "Motor Slots 5-8", "motor"),
            ("mcp22", "motors", "Motor Slots 9-10", "motor"),
            ("pi5", "relay", "GPIO16 + GPIO20", "lock"),
            ("relay", "solenoid_r", "Relay CH1 → 12V", "lock"),
            ("relay", "solenoid_t", "Relay CH2 → 12V", "lock"),
            ("pi5", "coin", "GPIO19", "sensor"),
            ("pi5", "ir", "GPIO26", "sensor"),
            ("psu_12v", "motors", "12V Power", "power"),
            ("psu_12v", "solenoid_r", "12V Power", "power"),
            ("psu_12v", "solenoid_t", "12V Power", "power"),
            ("pi5", "relay", "5V from Pi", "power"),
        ]

    def _build_layout(self):
        """Build main UI with collapsible details panel"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar with controls
        top_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_panel"], height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        ctk.CTkLabel(top_frame, text="Zoom:", text_color=COLORS["text"]).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(top_frame, text="-", width=40, command=lambda: self._zoom(0.9)).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(top_frame, text="+", width=40, command=lambda: self._zoom(1.1)).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(top_frame, text="Reset", width=60, command=self._reset_zoom).pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ctk.CTkLabel(top_frame, text="100%", text_color=COLORS["text_muted"])
        self.zoom_label.pack(side=tk.LEFT, padx=10)
        
        # Toggle details button
        ctk.CTkButton(
            top_frame, text="▼ Show Details", width=120,
            command=self._toggle_details
        ).pack(side=tk.LEFT, padx=20)
        
        # Content frame (canvas + details)
        content_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_main"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        canvas_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_canvas"])
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=COLORS["bg_canvas"],
            highlightthickness=0,
            cursor="cross"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_zoom_wheel)
        self.canvas.bind("<Button-4>", self._on_zoom_wheel)
        self.canvas.bind("<Button-5>", self._on_zoom_wheel)
        
        # Details panel (initially hidden)
        self.details_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_panel"], width=350)
        self.details_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            self.details_frame,
            text="Component Pinouts",
            text_color=COLORS["text"],
            font=("Segoe UI", 12, "bold")
        ).pack(padx=10, pady=10)
        
        self.details_text = ctk.CTkTextbox(
            self.details_frame,
            text_color=COLORS["text"],
            fg_color=COLORS["bg_canvas"],
            border_color=COLORS["border"],
            border_width=1,
            font=("Courier", 9)
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Legend
        ctk.CTkLabel(
            self.details_frame,
            text="Wire Categories",
            text_color=COLORS["text"],
            font=("Segoe UI", 10, "bold")
        ).pack(padx=10, pady=(10, 5))
        
        for cat, color in WIRE_COLORS.items():
            row = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row.pack(fill=tk.X, padx=10, pady=2)
            
            canvas_box = tk.Canvas(row, width=20, height=3, bg=COLORS["bg_panel"], highlightthickness=0)
            canvas_box.pack(side=tk.LEFT)
            canvas_box.create_line(0, 1, 20, 1, fill=color, width=2)
            
            ctk.CTkLabel(row, text=cat.capitalize(), text_color=COLORS["text_muted"], font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)

    def _toggle_details(self):
        """Toggle details panel visibility"""
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        else:
            self.details_frame.pack_forget()

    def _on_canvas_click(self, event):
        """Handle component click"""
        for key, node in self.nodes.items():
            x1 = node.x * self.scale
            y1 = node.y * self.scale
            x2 = x1 + node.width * self.scale
            y2 = y1 + node.height * self.scale
            
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.selected_key = key
                self._show_pinout(node)
                self._redraw()
                return

    def _show_pinout(self, node: Node):
        """Display component pinout in details panel"""
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        
        text = f"{node.title}\n" + "=" * 40 + "\n\n"
        text += "PINOUT:\n"
        text += "-" * 40 + "\n"
        
        for pin, desc in node.pinout.items():
            text += f"  {pin:15} → {desc}\n"
        
        text += "\n\nCONNECTIONS:\n"
        text += "-" * 40 + "\n"
        for conn in node.connections:
            text += f"  • {conn.upper()}\n"
        
        self.details_text.insert("1.0", text)
        self.details_text.configure(state=tk.DISABLED)

    def _redraw(self):
        """Redraw entire canvas"""
        self.canvas.delete("all")
        self.node_canvas_ids.clear()
        
        # Grid
        for x in range(0, 2000, 50):
            self.canvas.create_line(x, 0, x, 1000, fill=COLORS["grid"], dash=(2, 4))
        for y in range(0, 1000, 50):
            self.canvas.create_line(0, y, 2000, y, fill=COLORS["grid"], dash=(2, 4))
        
        # Edges
        for src_key, dst_key, label, cat in self.edges:
            self._draw_edge(src_key, dst_key, label, cat)
        
        # Nodes
        for node in self.nodes.values():
            self._draw_node(node)

    def _draw_edge(self, src_key: str, dst_key: str, label: str, category: str):
        """Draw connection between components"""
        src = self.nodes[src_key]
        dst = self.nodes[dst_key]
        
        src_x = (src.x + src.width / 2) * self.scale
        src_y = (src.y + src.height / 2) * self.scale
        dst_x = (dst.x + dst.width / 2) * self.scale
        dst_y = (dst.y + dst.height / 2) * self.scale
        
        color = WIRE_COLORS.get(category, "#999999")
        
        # Routed path with bend
        mid_x = (src_x + dst_x) / 2
        self.canvas.create_line(src_x, src_y, mid_x, src_y, mid_x, dst_y, dst_x, dst_y,
                               fill=color, width=2, smooth=True)
        
        # Label
        label_x = (src_x + dst_x) / 2
        label_y = (src_y + dst_y) / 2
        self.canvas.create_text(label_x, label_y - 10, text=label, fill=color,
                               font=("Segoe UI", 8, "bold"))

    def _draw_node(self, node: Node):
        """Draw component box with title"""
        x = node.x * self.scale
        y = node.y * self.scale
        w = node.width * self.scale
        h = node.height * self.scale
        
        # Highlight if selected
        outline = "#4a9eff" if node.key == self.selected_key else COLORS["border"]
        width = 3 if node.key == self.selected_key else 1
        
        # Component box
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=COLORS["bg_panel"],
                                     outline=outline, width=width)
        
        # Header
        self.canvas.create_rectangle(x, y, x + w, y + 25,
                                     fill=COLORS["border"], outline=outline, width=1)
        
        # Title
        self.canvas.create_text(x + w / 2, y + 12, text=node.title,
                               fill=COLORS["text"], font=("Segoe UI", 9, "bold"))
        
        # Pin summary (first few pins)
        y_offset = y + 30
        pin_list = list(node.pinout.items())[:4]
        for pin, desc in pin_list:
            self.canvas.create_text(x + 5, y_offset, text=f"{pin}: {desc[:20]}", 
                                   fill=COLORS["text_muted"], font=("Segoe UI", 7), anchor="nw")
            y_offset += 12
        
        if len(node.pinout) > 4:
            self.canvas.create_text(x + 5, y_offset, 
                                   text=f"+{len(node.pinout) - 4} pins...",
                                   fill=COLORS["text_muted"], font=("Segoe UI", 7, "italic"))

    def _zoom(self, factor: float):
        """Adjust zoom"""
        self.scale *= factor
        self.scale = max(0.5, min(2.0, self.scale))
        self.zoom_label.configure(text=f"{int(self.scale * 100)}%")
        self._redraw()

    def _reset_zoom(self):
        """Reset to 100%"""
        self.scale = 1.0
        self.zoom_label.configure(text="100%")
        self._redraw()

    def _on_zoom_wheel(self, event):
        """Handle mouse wheel zoom"""
        if event.state & 0x4:  # Ctrl key
            factor = 1.1 if event.num == 4 or event.delta > 0 else 0.9
            self._zoom(factor)


def main():
    app = WiringVisualGuide()
    app.mainloop()


if __name__ == "__main__":
    main()
