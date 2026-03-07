## Personal Hygiene Vending Machine (Raspberry Pi Prototype)

This Thesis is a Raspberry Pi–based **personal hygiene vending machine** with:

- 7" touchscreen GUI (Tkinter)
- Cash and RFID wallet payments
- Product search bar with icons & backspace
- Basic inventory & staff restock mode
- Admin dashboard (overview metrics + reports)
- SQLite logging of sales
- Excel export for sales reporting (daily / monthly summaries)
- Light / Dark **theme toggle** on all main screens

> Current status: **single‑file prototype** in `main.py` implementing core vending, admin dashboard, search UI, and reporting logic. Hardware is partially simulated so it can run on Windows for development, and uses real GPIO when deployed on a Raspberry Pi.

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

Currently, the prototype is **mostly single file**:

- `main.py` – GUI, database, hardware abstraction, RFID wallet logic, product search, sidebar navigation, admin dashboard, restock mode, and Excel export.
- `admin/` – package reserved for admin‑related helpers (`reports.py` etc.).
- `images/` – PNG assets for icons (hamburger, search, backspace, staff/admin).

The SQLite database file is created automatically:

- `vending.db` – stores products, users, and transactions.

Generated reports:

- `sales_report_YYYYMMDD_HHMMSS.xlsx` – Excel sales reports.

---

## Requirements

### Software (Windows dev OR Raspberry Pi)

- Python **3.10+** (3.11+ OK)
- System packages:
  - Tkinter (for GUI)
  - SQLite (usually bundled with Python)
  - `RPi.GPIO` **only on Raspberry Pi**
- Python packages:
  - `openpyxl` (for Excel export)

Install Python packages (on both Windows and Raspberry Pi):

```bash
pip install openpyxl
```

### Extra setup on Raspberry Pi (recommended)

On Raspberry Pi OS / Debian‑based distros:

```bash
sudo apt update

# Core Python and Tkinter (if not already installed)
sudo apt install -y python3 python3-pip python3-tk

# GPIO library used by the prototype
sudo apt install -y python3-rpi.gpio
```

Tkinter is required for the touchscreen GUI; `python3-tk` ensures it is available.  
`python3-rpi.gpio` enables real stepper motors / coin hopper control. On Windows, GPIO is automatically mocked, so you can still run and test the UI.

---

## How It Works (Summary)

- At startup, `main.py` creates / migrates `vending.db`, seeds:
  - 10 hygiene / convenience products (slots 1–10) with approximate Philippine SRP prices.
  - A default staff RFID card (`rfid_uid="STAFF001"`, marked as staff).
- Main screen shows:
  - Product grid (scrollable, responsive layout).
  - Search bar with magnifying‑glass icon, placeholder **“Search for products”**, and backspace icon to delete characters.
  - Bottom actions: `Reload (RFID)`, `Buy RFID Card`, **How to use?**, theme toggle, and `SyntaxError™` trademark footer.
- Hidden admin/staff controls are accessed via a **hamburger icon** that opens a left sidebar:
  - Staff restock mode (RFID‑based).
  - Admin dashboard (overview metrics + links to reports and credentials).
- Flows implemented:
  - **Cash purchase** (simulated buttons, then hardware GPIO for dispensing).
  - **RFID purchase**, **Buy RFID Card**, **Reload RFID Card**.
  - **Staff restock mode** with per‑tray restocking and optional price update.
  - **Admin dashboard** with total sales, order count, active customers, and low‑stock product count.
  - **Excel export** with all transactions, daily and monthly sales.
  - **Light/Dark mode** toggle that changes the whole UI theme.