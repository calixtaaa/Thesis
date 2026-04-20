## Personal Hygiene Vending Machine (Raspberry Pi Prototype)

**Version:** v1.0.0

A Raspberry Pi–based **personal hygiene vending machine** with an integrated AI chatbot, redesigned UI/UX, and a Vue 3 + Vite website with Tailwind CSS:

- 7" touchscreen GUI (Tkinter) with improved UI/UX design
- **AI Chatbot** for customer support and product recommendations
- Cash and RFID wallet payments
- Advanced product search with icons & smart suggestions
- Inventory management & staff restock mode
- Admin dashboard (overview metrics, charts, reports, analytics)
- SQLite logging of sales transactions
- Excel export for sales reporting (daily / monthly / weekly summaries)
- Light / Dark **theme toggle** on all main screens
- Real-time stock monitoring and alerts

> The app runs on Windows for development (GPIO mocked) and on Raspberry Pi with real hardware. Version and patch notes are centralized in `patchNotes.py`; the database layer lives in `database.py`. The website is now built with Vue 3 + Vite and styled with Tailwind CSS.

---

## Features

### Machine Interface (Tkinter)

- **Product vending**
  - Product list with available stock and price
  - Greyed-out / disabled buttons if product is out of stock
  - Quantity selection per product
  - Cash payment (simulated buttons; later replace with coin/bill acceptors)
  - RFID cashless payment (balance deducted from card)
  - Smart product recommendations based on purchase history

- **AI Chatbot**
  - Real-time customer support within the vending machine
  - Product recommendations and availability queries
  - Payment assistance and troubleshooting
  - FAQ and quick help responses
  - Natural language processing for better UX

- **RFID wallet**
  - Buy new RFID card (fixed price, e.g. ₱50)
  - Reload existing RFID card using cash
  - Link transactions to RFID UID
  - Quick balance check

- **Staff restock mode**
  - Staff login using RFID card ID (simulated)
  - Shows all product trays, capacities, and current stock
  - Restock a tray (with optional price change)
  - Updates inventory in SQLite
  - Restock notifications and reminders

- **Admin dashboard**
  - Login with username/password (hashed); change credentials in dashboard
  - Overview: total sales, orders, active customers, low-stock count
  - Charts: sales trend (line), monthly sales (bar), top-selling products, low-stock products
  - Generate Excel report (saved to **Downloads / Hygiene Vending Reports**)
  - View and open existing sales reports
  - Advanced analytics and insights
  - Prediction-based restock recommendations

- **Database & reports**
  - SQLite DB `vending.db` (auto-created in project folder)
  - Tables: `products`, `rfid_users`, `transactions`, `admin_settings`, `chatbot_logs`
  - Excel export (`.xlsx`) with:
    - All transactions (product, amount, method, RFID UID)
    - Daily/weekly/monthly sales summaries
    - Customer insights

- **Hardware abstraction & UI**
  - Stepper motors per slot (GPIO pins configurable)
  - Coin hopper (for change)
  - Single shared MFRC522 RFID reader for payment, reload, restock-door auth, and troubleshoot-door auth taps
  - GPIO mocked on Windows, real on Raspberry Pi
  - Redesigned Light / Dark theme with smooth transitions
  - Version (v1.0.0) in window title and footer
  - Improved responsive touchscreen layout

### Website (Vue 3 + Vite + Tailwind CSS)

- **Modern responsive design** with Tailwind CSS
- **Real-time dashboard** synced with vending machine data
- **Sales analytics & reports** accessible from web
- **RFID card management** portal
- **Admin panel** for remote monitoring
- **Customer portal** for transaction history and card balance
- **Chatbot integration** on website for support
- **Fast development** with Vite hot module replacement (HMR)

---

## Project Structure

### Machine Backend (Python)

- **`main.py`** – Entry point; GUI, hardware abstraction, RFID/product flows, sidebar, theme, chatbot integration. Imports from `database`, `patchNotes`, `admin`, `staff`, `chatbot`.
- **`database.py`** – SQLite connection, schema, seeding, and all DB operations (products, transactions, RFID users, admin credentials, report queries, Excel export, chatbot logs).
- **`patchNotes.py`** – App version (`VERSION`), patch notes content (Added / Improved / Bugs fixed / Future), and `get_patch_notes_text()` for the in-app Patch Notes dialog.
- **`chatbot/`**
  - `chatbot.py` – AI chatbot logic, natural language processing, product recommendations, FAQs.
  - `responses.py` – Predefined responses and templates.
- **`admin/`**
  - `admin.py` – `AdminMixin`: admin login, dashboard UI, charts, sales reports screen, change credentials.
  - `reports.py` – Report paths (`get_reports_dir()` = Downloads/Hygiene Vending Reports), list/open reports.
- **`staff/`**
  - `staff.py` – `StaffMixin`: staff RFID login, restock screen, restock dialog.
- **`images/`** – Icons (hamburger, search, backspace, theme, admin, staff, chatbot).

### Website Frontend (Vue 3 + Vite)

- **`src/`** – Vue 3 source files
  - `main.js` – Entry point
  - `App.vue` – Root component
  - `components/` – Reusable Vue components
  - `views/` – Page components (Dashboard, Analytics, Reports, etc.)
  - `stores/` – Pinia state management
  - `utils/` – Helper functions and API calls
- **`public/`** – Static assets
- **`vite.config.js`** – Vite configuration
- **`tailwind.config.js`** – Tailwind CSS configuration
- **`index.html`** – HTML entry point

**Generated / runtime:**

- **`vending.db`** – SQLite database (products, transactions, RFID users, admin settings, chatbot logs).
- **Downloads / Hygiene Vending Reports** – Generated Excel sales reports (`sales_report_YYYYMMDD_HHMMSS.xlsx`).
- **`debug_logs/`** – Debug log files (when debugging is enabled).
- **`bug_reports/`** – Bug report submissions (NDJSON format).

---

## Requirements

### Software (Windows dev OR Raspberry Pi)

#### Machine (Python)

- Python **3.10+** (3.11+ OK)
- System:
  - Tkinter (for GUI)
  - SQLite (bundled with Python)
  - **RPi.GPIO** only on Raspberry Pi
- Python packages:
  - `openpyxl` (Excel export)
  - `python-dotenv` (environment variables)
  - `requests` (API calls)
  - `mfrc522` (MFRC522 RFID reader access)

Install dependencies:

```bash
pip install -r requirements.txt
```

#### Website (Node.js)

- Node.js **16+** (18+ recommended)
- npm or yarn

Install dependencies:

```bash
cd WebSite
npm install
```

### Raspberry Pi setup

On Raspberry Pi OS / Debian-based:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk
sudo apt install -y python3-rpi.gpio
sudo apt install -y nodejs npm
```

Tkinter is required for the touchscreen GUI. On Windows, GPIO is mocked so you can run and test the UI without hardware.

---

## How to Run

### Machine

From the project directory:

```bash
python main.py
```

### RFID Hardware Smoke Test (Raspberry Pi)

Before running the full app, verify the single shared MFRC522 reader:

```bash
python rfid_single_reader_test.py
```

This test script polls the shared reader on CE0 and prints detected UIDs.

For a touchscreen-friendly UI tester:

```bash
python rfid_single_reader_test.py --ui
```

On Raspberry Pi with a 7" touchscreen, the app can run fullscreen; on Windows it uses a resizable window (e.g. 800×480).

### Website (Development)

```bash
cd WebSite
npm run dev
```

The website will be available at `http://localhost:5173`

### Website (Production Build)

```bash
cd WebSite
npm run build
npm run preview
```

---

## How It Works (Summary)

- **Startup:** `main.py` calls `init_db()` (in `database.py`), which creates/migrates `vending.db` and seeds:
  - 10 hygiene products (slots 1–10) with Philippine SRP prices
  - Default staff RFID user (`STAFF001`)
  - Default admin credentials (username/password: `admin` / `admin`; change in admin dashboard)
  - Chatbot knowledge base and FAQ entries
- **Main screen:** Scrollable product grid with improved card design, advanced search bar with AI suggestions, navbar (hamburger, theme toggle, chatbot button), footer with real-time status, and integrated chatbot widget
- **AI Chatbot:** Accessible via button on main screen; provides instant customer support, product recommendations, payment help, and FAQ responses
- **Hamburger menu:** Opens a sidebar with Staff (restock) and Admin (dashboard). Admin requires login.
- **Flows:** Select product → quantity → payment (Cash or RFID) → dispense; Buy/Reload RFID; Staff restock; Admin dashboard (charts, generate Excel, view reports, change credentials, analytics)
- **Website:** Vue 3 + Vite dashboard synced with machine data; displays real-time sales, analytics, customer management, and remote administration
- **Version:** Shown in the window title, footer on main screens, and Patch Notes dialog. Bump `VERSION` in `patchNotes.py` for new releases.

---

## Changelog (v1.0.0)

### Major Updates
- **AI Chatbot Integration:** Added intelligent chatbot for customer support, product recommendations, and FAQs
- **UI/UX Redesign:** Complete redesign of the machine interface with improved card layouts, smoother animations, and better touch responsiveness
- **Website Overhaul:** Migrated from React to Vue 3 + Vite + Tailwind CSS for better performance and developer experience
- **Bug Fixes:** Fixed critical issues with payment processing, RFID detection, and theme persistence

### New Features
- Chatbot natural language processing for better customer interactions
- Real-time stock monitoring with predictive alerts
- Enhanced admin analytics dashboard with advanced insights
- Improved search functionality with AI-powered product suggestions
- Website real-time sync with machine sales data
- Customer portal for viewing transaction history and card balance

### Improvements
- Better UI responsiveness on 7" touchscreen
- Faster load times with optimized database queries
- Smoother theme switching without visual flicker
- Improved error handling and user feedback
- Better accessibility features

### Technical Changes
- Chatbot logs added to SQLite schema
- Vue 3 Composition API for better code organization
- Tailwind CSS for consistent styling across website
- Improved API communication between machine and website
- Enhanced security for admin credentials (password hashing improvements)