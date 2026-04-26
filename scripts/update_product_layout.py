"""
One-time helper to update an existing local SQLite DB (`vending.db`)
to the latest physical tray slot → product placement.

This does NOT change any machine functions—only product rows (name/price) by slot_number.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "vending.db"


LATEST_LAYOUT = {
    1: {"name": "Alcohol", "details": "Green Cross Isopropyl Alcohol 70% Solution, 60mL", "price": 25.00},
    2: {"name": "Soap", "details": "Soap, 10grams", "price": 5.00},
    3: {"name": "Deodorant", "details": "Rexona Shower Clean, 3ml*12packs", "price": 10.00},
    4: {"name": "Mouthwash", "details": "Scoban Mint Flavor, 10ml*10 packs", "price": 8.00},
    5: {"name": "Tissues", "details": "Sanicare Hankies, 6 packs", "price": 8.00},
    6: {"name": "Wet Wipes", "details": "Sanicare Mini Wipes, 6 packs x 8 sheets", "price": 18.00},
    7: {"name": "Panty Liners", "details": "Charmee Breathable, 20 liners", "price": 5.00},
    8: {"name": "All Night Pads", "details": "Charmee All Night Plus, 4 pads", "price": 10.00},
    9: {"name": "Regular W/ Wings Pads", "details": "Charmee Dry Net with wings, 8 pads", "price": 7.00},
    10: {"name": "Non-Wing Pads", "details": "Charmee Cottony without wings, 8 pads", "price": 7.00},
}


def main() -> int:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cur.fetchone():
            raise SystemExit("Table 'products' not found. Run the app once to initialize the DB.")

        for slot, data in LATEST_LAYOUT.items():
            cur.execute(
                """
                UPDATE products
                SET name = ?, details = ?, price = ?
                WHERE slot_number = ?
                """,
                (data["name"], data.get("details"), float(data["price"]), int(slot)),
            )

        conn.commit()
    finally:
        conn.close()

    print("Updated product layout successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

