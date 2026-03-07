## Personal Hygiene Vending Machine (Raspberry Pi Prototype)

**Version:** v.0.01

A Raspberry Pi–based **personal hygiene vending machine** with:

- 7" touchscreen GUI (Tkinter)
- Cash and RFID wallet payments
- Product search bar with icons & backspace
- Basic inventory & staff restock mode
- Admin dashboard (overview metrics, charts, reports)
- SQLite logging of sales
- Excel export for sales reporting (daily / monthly summaries)
- Light / Dark **theme toggle** on all main screens

> The app runs on Windows for development (GPIO mocked) and on Raspberry Pi with real hardware. Version and patch notes are centralized in `patchNotes.py`; the database layer lives in `database.py`.

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

- **Admin dashboard**
  - Login with username/password (hashed); change credentials in dashboard
  - Overview: total sales, orders, active customers, low‑stock count
  - Charts: sales trend (line), monthly sales (bar), top‑selling products, low‑stock products
  - Generate Excel report (saved to **Downloads / Hygiene Vending Reports**)
  - View and open existing sales reports

- **Database & reports**
  - SQLite DB `vending.db` (auto-created in project folder)
  - Tables: `products`, `rfid_users`, `transactions`, `admin_settings`
  - Excel export (`.xlsx`) with:
    - All transactions (product, amount, method, RFID UID)
    - Daily sales summary
    - Monthly sales summary

- **Hardware abstraction & UI**
  - Stepper motors per slot (GPIO pins configurable)
  - Coin hopper (for change)
  - GPIO mocked on Windows, real on Raspberry Pi
  - Light / Dark theme toggle; version (v.0.01) in window title and footer

---

## Project Structure

- **`main.py`** – Entry point; GUI, hardware abstraction, RFID/product flows, sidebar, theme. Imports from `database`, `patchNotes`, `admin`, `staff`.
- **`database.py`** – SQLite connection, schema, seeding, and all DB operations (products, transactions, RFID users, admin credentials, report queries, Excel export).
- **`patchNotes.py`** – App version (`VERSION`), patch notes content (Added / Improved / Bugs fixed / Future), and `get_patch_notes_text()` for the in-app Patch Notes dialog.
- **`admin/`**
  - `admin.py` – `AdminMixin`: admin login, dashboard UI, charts, sales reports screen, change credentials.
  - `reports.py` – Report paths (`get_reports_dir()` = Downloads/Hygiene Vending Reports), list/open reports.
- **`staff/`**
  - `staff.py` – `StaffMixin`: staff RFID login, restock screen, restock dialog.
- **`images/`** – Icons (hamburger, search, backspace, theme, admin, staff).

**Generated / runtime:**

- **`vending.db`** – SQLite database (products, transactions, RFID users, admin settings).
- **Downloads / Hygiene Vending Reports** – Generated Excel sales reports (`sales_report_YYYYMMDD_HHMMSS.xlsx`).
- **`debug_logs/`** – Debug log files (when debugging is enabled).

---

## Requirements

### Software (Windows dev OR Raspberry Pi)

- Python **3.10+** (3.11+ OK)
- System:
  - Tkinter (for GUI)
  - SQLite (bundled with Python)
  - **RPi.GPIO** only on Raspberry Pi
- Python packages:
  - `openpyxl` (Excel export)

Install dependencies:

```bash
pip install openpyxl
```

### Raspberry Pi setup

On Raspberry Pi OS / Debian-based:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk
sudo apt install -y python3-rpi.gpio
```

Tkinter is required for the touchscreen GUI. On Windows, GPIO is mocked so you can run and test the UI without hardware.

---

## How to Run

From the project directory:

```bash
python main.py
```

On Raspberry Pi with a 7" touchscreen, the app can run fullscreen; on Windows it uses a resizable window (e.g. 800×480).

---

## How It Works (Summary)

- **Startup:** `main.py` calls `init_db()` (in `database.py`), which creates/migrates `vending.db` and seeds:
  - 10 hygiene products (slots 1–10) with Philippine SRP prices.
  - Default staff RFID user (`STAFF001`).
  - Default admin credentials (username/password: `admin` / `admin`; change in admin dashboard).
- **Main screen:** Scrollable product grid, pill-shaped search bar (“Search for products”) with magnifying glass and backspace icons, navbar (hamburger, theme toggle), footer with **SyntaxError™** and version (v.0.01), live Philippine date/time, and buttons: Reload (RFID), Buy RFID Card, How to use?, Patch Notes.
- **Hamburger menu:** Opens a sidebar with Staff (restock) and Admin (dashboard). Admin requires login.
- **Flows:** Select product → quantity → payment (Cash or RFID) → dispense; Buy/Reload RFID; Staff restock; Admin dashboard (charts, generate Excel, view reports, change credentials).
- **Version:** Shown in the window title, footer on main screens, and Patch Notes dialog. Bump `VERSION` in `patchNotes.py` for new releases.
