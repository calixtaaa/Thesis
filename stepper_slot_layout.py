"""
Shared MCP23017 stepper slot layout for main.py, stepper_mcp.py, and hardware tools.

Adjacent pairs (1↔2, 3↔4, 5↔6, 7↔8) swap MCP pin blocks vs sequential wiring so
logical slot numbers match the physical tray (and stepper_mcp test UI).
"""

from __future__ import annotations

# slot -> (MCP I2C address, IN1..IN4 logical pin indices 0..15)
SLOT_LAYOUT: dict[int, tuple[int, tuple[int, int, int, int]]] = {
    1: (0x20, (4, 5, 6, 7)),
    2: (0x20, (0, 1, 2, 3)),
    3: (0x20, (12, 13, 14, 15)),
    4: (0x20, (8, 9, 10, 11)),
    5: (0x21, (4, 5, 6, 7)),
    6: (0x21, (0, 1, 2, 3)),
    7: (0x21, (12, 13, 14, 15)),
    8: (0x21, (8, 9, 10, 11)),
    9: (0x22, (0, 1, 2, 3)),
    10: (0x22, (4, 5, 6, 7)),
}


def build_mcp23017_stepper_map() -> dict[int, dict]:
    mapping: dict[int, dict] = {}
    for slot, (address, pins) in SLOT_LAYOUT.items():
        p1, p2, p3, p4 = pins
        mapping[slot] = {
            "backend": "mcp23017",
            "address": address,
            "in1": p1,
            "in2": p2,
            "in3": p3,
            "in4": p4,
        }
    return mapping
