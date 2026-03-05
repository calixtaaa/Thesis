## Personal Hygiene Vending Machine with Machine Learning (Prototype)

This Thesis is a Raspberry Pi–based **personal hygiene vending machine** with:

- 7" touchscreen GUI (Tkinter)
- Cash and RFID wallet payments
- Basic inventory & staff restock mode
- SQLite logging of sales
- Excel export for sales reporting (daily / monthly summaries)
- Light / Dark **theme toggle** on the main screen

> Current status: **single‑file prototype** in `main.py` implementing core vending and reporting logic. Hardware is partially simulated so it can run on Windows for development.

---

## Features

- **Product vending**
  - Product list with available stock and price
  - Greyed‑out / disabled buttons if product is out of stock
  - Quantity selection per product
  - Cash payment (simulated buttons; later replace with coin/bill acceptors)
  - RFID cashless payment (balance deducted from card)

- **RFID wallet**
  - Buy new RFID card (fixed price, e.g. ₱50)
  - Reload existing RFID card using cash
  - Link transactions to RFID UID

- **Staff restock mode**
  - Staff login using RFID card ID (simulated)
  - Shows all product trays, capacities, and current stock
  - Restock a tray (with optional price change)
  - Updates inventory in SQLite

- **Database & reports**
  - SQLite DB `vending.db` (automatically created)
  - Tables:
    - `products`
    - `rfid_users`
    - `transactions`
  - Excel export (`.xlsx`) with:
    - All transactions (with product, amount, method, RFID UID)
    - Daily sales summary
    - Monthly sales summary

- **Hardware abstraction & UI**
  - Stepper motors per slot (GPIO pins configurable)
  - Coin hopper (for change)
  - All GPIO access mocked automatically when running on Windows
  - Light / Dark theme toggle

---

## Project Structure

Currently, the prototype is **single file**:

- `main.py` – GUI, database, hardware abstraction, RFID wallet logic, restock mode, and Excel export.

The SQLite database file is created automatically:

- `vending.db` – stores products, users, and transactions.

Generated reports:

- `sales_report_YYYYMMDD_HHMMSS.xlsx` – Excel sales reports.

---

## Requirements

### Software

- Python 3.10+ (recommended)
- Packages:
  - `openpyxl` (for Excel export)
  - `RPi.GPIO` (on Raspberry Pi only; auto‑mocked on Windows)

Install dependencies:

```bash
pip install openpyxl
# On Raspberry Pi:
# sudo apt-get install python3-rpi.gpio
```

Tkinter is usually bundled with Python; if not, install it from your OS package manager.

---

## How It Works (Summary)

- At startup, `main.py` creates / migrates `vending.db`, seeds:
  - Sample products (slots 1–2).
  - A default staff RFID card (`rfid_uid="STAFF001"`).
- Main screen shows product grid and bottom actions:
  - `Restock (Staff)`, `Reload (RFID)`, `Buy RFID Card`, `Export Sales (Excel)`, and **Theme toggle**.
- Flows implemented:
  - **Cash purchase** (simulated buttons).
  - **RFID purchase**, **Buy RFID Card**, **Reload RFID Card**.
  - **Staff restock mode** with per‑tray restocking and price update.
  - **Excel export** with all transactions, daily and monthly sales.
  - **Light/Dark mode** toggle that changes the whole UI theme.