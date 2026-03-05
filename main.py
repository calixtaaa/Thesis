import os
import sys
import time
import uuid
import datetime
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog
from openpyxl import Workbook

# ======================
#  ENV & GPIO HANDLING
# ======================

ON_RPI = False
try:
    import RPi.GPIO as GPIO  # type: ignore
    ON_RPI = True
except ImportError:
    # Simple mock for development on Windows
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = 1
        LOW = 0
        PUD_UP = "PUD_UP"
        FALLING = "FALLING"

        def setmode(self, *_a, **_k): pass
        def setwarnings(self, *_a, **_k): pass
        def setup(self, *_a, **_k): pass
        def output(self, *_a, **_k): pass
        def cleanup(self): pass
        def add_event_detect(self, *_a, **_k): pass

    GPIO = MockGPIO()  # type: ignore

# ======================
#  CONFIG & CONSTANTS
# ======================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "vending.db"

# Simple theming (light / dark)
THEMES = {
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "button_bg": "#f0f0f0",
        "button_fg": "#000000",
    },
    "dark": {
        "bg": "#202124",
        "fg": "#e8eaed",
        "button_bg": "#3c4043",
        "button_fg": "#e8eaed",
    },
}

# Simple pin assignments (adjust on real Pi)
PRODUCT_STEPPER_PINS = {
    1: {"step": 17, "dir": 27},   # Slot 1
    2: {"step": 22, "dir": 23},   # Slot 2
}
COIN_HOPPER_PIN = 24
STEPS_PER_PRODUCT = 200  # adjust per mechanism
COINS_PER_SECOND = 5     # for hopper simulation
COIN_VALUE = 1.0         # 1 peso per coin (example)


# ======================
#  DATABASE LAYER
# ======================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        slot_number INTEGER NOT NULL UNIQUE,
        capacity INTEGER NOT NULL,
        current_stock INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        product_id INTEGER,
        quantity INTEGER,
        total_amount REAL,
        payment_method TEXT,
        rfid_user_id INTEGER,
        FOREIGN KEY(product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS rfid_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_uid TEXT NOT NULL UNIQUE,
        name TEXT,
        balance REAL NOT NULL DEFAULT 0,
        is_staff INTEGER NOT NULL DEFAULT 0
    );
    """)
    conn.commit()

    # Ensure new column exists if upgrading from older schema
    cur.execute("PRAGMA table_info(transactions)")
    cols = [row["name"] for row in cur.fetchall()]
    if "rfid_user_id" not in cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN rfid_user_id INTEGER")
        conn.commit()

    # Seed sample data if empty
    cur.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()["c"] == 0:
        sample_products = [
            ("Charmee Pad", 10.0, 1, 10, 5),
            ("Pantyliner", 8.0, 2, 10, 0),  # Out of stock to show greyed out
        ]
        cur.executemany("""
            INSERT INTO products (name, price, slot_number, capacity, current_stock)
            VALUES (?, ?, ?, ?, ?)
        """, sample_products)
        conn.commit()

    # Seed a default staff RFID user for testing
    cur.execute("SELECT COUNT(*) AS c FROM rfid_users")
    if cur.fetchone()["c"] == 0:
        cur.execute("""
            INSERT INTO rfid_users (rfid_uid, name, balance, is_staff)
            VALUES (?, ?, ?, ?)
        """, ("STAFF001", "Default Staff", 0.0, 1))
        conn.commit()
    conn.close()

def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY slot_number")
    rows = cur.fetchall()
    conn.close()
    return rows

def decrement_stock(product_id: int, quantity: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE products
        SET current_stock = current_stock - ?
        WHERE id = ? AND current_stock >= ?
    """, (quantity, product_id, quantity))
    if cur.rowcount == 0:
        conn.rollback()
        conn.close()
        raise ValueError("Insufficient stock")
    conn.commit()
    conn.close()

def record_transaction(product_id, quantity, total_amount, payment_method, rfid_user_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (product_id, quantity, total_amount, payment_method, rfid_user_id)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, quantity, total_amount, payment_method, rfid_user_id))
    conn.commit()
    conn.close()


def get_user_by_uid(rfid_uid: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rfid_users WHERE rfid_uid = ?", (rfid_uid,))
    row = cur.fetchone()
    conn.close()
    return row


def create_user(rfid_uid: str, name: str | None = None, is_staff: int = 0, initial_balance: float = 0.0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rfid_users (rfid_uid, name, balance, is_staff)
        VALUES (?, ?, ?, ?)
    """, (rfid_uid, name, initial_balance, is_staff))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def update_user_balance(user_id: int, new_balance: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE rfid_users SET balance = ? WHERE id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()


def adjust_user_balance(user_id: int, delta: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE rfid_users SET balance = balance + ? WHERE id = ?", (delta, user_id))
    conn.commit()
    conn.close()


def restock_product(product_id: int, amount: int, new_price: float | None = None):
    conn = get_connection()
    cur = conn.cursor()
    if new_price is not None:
        cur.execute("""
            UPDATE products
            SET current_stock = MIN(capacity, current_stock + ?),
                price = ?
            WHERE id = ?
        """, (amount, new_price, product_id))
    else:
        cur.execute("""
            UPDATE products
            SET current_stock = MIN(capacity, current_stock + ?)
            WHERE id = ?
        """, (amount, product_id))
    conn.commit()
    conn.close()


def export_sales_report():
    """Create an Excel file with all transactions, and daily/monthly summaries."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            t.timestamp,
            DATE(t.timestamp) AS sale_date,
            strftime('%Y-%m', t.timestamp) AS sale_month,
            p.name AS product_name,
            t.quantity,
            t.total_amount,
            t.payment_method,
            u.rfid_uid
        FROM transactions t
        LEFT JOIN products p ON t.product_id = p.id
        LEFT JOIN rfid_users u ON t.rfid_user_id = u.id
        ORDER BY t.timestamp
    """)
    rows = cur.fetchall()
    conn.close()

    # Prepare Excel workbook
    wb = Workbook()

    # Sheet 1: All Transactions
    ws_all = wb.active
    ws_all.title = "All Transactions"
    headers = [
        "Timestamp", "Date", "Month (YYYY-MM)", "Product",
        "Quantity", "Total Amount", "Payment Method", "RFID UID",
    ]
    ws_all.append(headers)

    daily_summary = {}
    monthly_summary = {}

    for r in rows:
        ts = r["timestamp"]
        date = r["sale_date"]
        month = r["sale_month"]
        product = r["product_name"] or ""
        qty = r["quantity"] if r["quantity"] is not None else 0
        total_amt = r["total_amount"] if r["total_amount"] is not None else 0.0
        method = r["payment_method"] or ""
        uid = r["rfid_uid"] or ""

        ws_all.append([ts, date, month, product, qty, total_amt, method, uid])

        # Build daily summary
        if date not in daily_summary:
            daily_summary[date] = {"quantity": 0, "amount": 0.0}
        daily_summary[date]["quantity"] += qty
        daily_summary[date]["amount"] += total_amt

        # Build monthly summary
        if month not in monthly_summary:
            monthly_summary[month] = {"quantity": 0, "amount": 0.0}
        monthly_summary[month]["quantity"] += qty
        monthly_summary[month]["amount"] += total_amt

    # Sheet 2: Daily Summary
    ws_daily = wb.create_sheet(title="Daily Summary")
    ws_daily.append(["Date", "Total Quantity", "Total Amount"])
    for date, agg in sorted(daily_summary.items()):
        ws_daily.append([date, agg["quantity"], agg["amount"]])

    # Sheet 3: Monthly Summary
    ws_monthly = wb.create_sheet(title="Monthly Summary")
    ws_monthly.append(["Month (YYYY-MM)", "Total Quantity", "Total Amount"])
    for month, agg in sorted(monthly_summary.items()):
        ws_monthly.append([month, agg["quantity"], agg["amount"]])

    # Save file
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = BASE_DIR / f"sales_report_{stamp}.xlsx"
    wb.save(filename)
    return filename


# ======================
#  HARDWARE ABSTRACTION
# ======================

def gpio_init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Stepper pins
    for cfg in PRODUCT_STEPPER_PINS.values():
        GPIO.setup(cfg["step"], GPIO.OUT)
        GPIO.setup(cfg["dir"], GPIO.OUT)

    # Hopper
    GPIO.setup(COIN_HOPPER_PIN, GPIO.OUT)

def dispense_from_slot(slot_number: int, quantity: int = 1):
    pins = PRODUCT_STEPPER_PINS.get(slot_number)
    if not pins:
        print(f"[HW] No stepper pins configured for slot {slot_number}")
        return

    print(f"[HW] Dispensing from slot {slot_number} x{quantity}")
    steps = STEPS_PER_PRODUCT * quantity
    delay = 0.001  # 1ms

    GPIO.output(pins["dir"], GPIO.HIGH)
    for _ in range(steps):
        GPIO.output(pins["step"], GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pins["step"], GPIO.LOW)
        time.sleep(delay)

def dispense_change(amount: float):
    coins_to_dispense = int(amount // COIN_VALUE)
    if coins_to_dispense <= 0:
        return
    print(f"[HW] Dispensing change: {coins_to_dispense} coins (₱{amount:.2f})")
    duration = coins_to_dispense / COINS_PER_SECOND
    GPIO.output(COIN_HOPPER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(COIN_HOPPER_PIN, GPIO.LOW)


# ======================
#  SIMPLE CASH SESSION
#  (Simulated for now)
# ======================

class CashSession:
    """
    For now: simulated cash input using "+" buttons on GUI.
    On real machine, replace with pulse‑based reader.
    """
    def __init__(self):
        self.total_amount = 0.0

    def reset(self):
        self.total_amount = 0.0

    def add(self, value: float):
        self.total_amount += value

    def get_amount(self) -> float:
        return self.total_amount

cash_session = CashSession()


# ======================
#  TKINTER GUI
# ======================

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hygiene Vending Machine")
        self.geometry("800x480")
        self.attributes("-fullscreen", False)  # set True on Pi if desired

        self.current_product = None
        self.current_quantity = 1

         # Theme state
        self.current_theme_name = "light"
        self.current_theme = THEMES[self.current_theme_name]
        self.configure(bg=self.current_theme["bg"])

        self.build_main_menu()

    # ---------- Screen helpers ----------

    def clear_screen(self):
        for w in self.winfo_children():
            w.destroy()

    def apply_theme_to_widget(self, widget):
        """Apply current theme colors to a widget and its children."""
        try:
            widget.configure(bg=self.current_theme["bg"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            if isinstance(child, (tk.Button, tk.Label, tk.Frame)):
                try:
                    if isinstance(child, tk.Button):
                        child.configure(
                            bg=self.current_theme["button_bg"],
                            fg=self.current_theme["button_fg"],
                            activebackground=self.current_theme["button_bg"],
                            activeforeground=self.current_theme["button_fg"],
                        )
                    elif isinstance(child, tk.Label) or isinstance(child, tk.Frame):
                        child.configure(
                            bg=self.current_theme["bg"],
                            fg=self.current_theme["fg"] if isinstance(child, tk.Label) else None,
                        )
                except tk.TclError:
                    pass

    def toggle_theme(self):
        """Switch between light and dark modes."""
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.current_theme = THEMES[self.current_theme_name]
        self.configure(bg=self.current_theme["bg"])
        # Rebuild current main screen so theme applies everywhere
        self.build_main_menu()

    # ---------- Main Menu ----------

    def build_main_menu(self):
        self.clear_screen()
        products = get_all_products()

        top = tk.Frame(self, bg=self.current_theme["bg"])
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tk.Label(
            top,
            text="Select Product",
            font=("Arial", 20),
            bg=self.current_theme["bg"],
            fg=self.current_theme["fg"],
        ).pack(pady=10)

        grid = tk.Frame(top, bg=self.current_theme["bg"])
        grid.pack()

        for idx, p in enumerate(products):
            name = p["name"]
            stock = p["current_stock"]
            capacity = p["capacity"]
            price = p["price"]

            btn_text = f"{name}\n{stock}/{capacity}\n₱{price:.2f}"
            state = tk.NORMAL if stock > 0 else tk.DISABLED

            btn = tk.Button(
                grid,
                text=btn_text,
                width=18,
                height=4,
                state=state,
                command=lambda prod=p: self.select_product(prod),
                bg=self.current_theme["button_bg"],
                fg=self.current_theme["button_fg"],
                activebackground=self.current_theme["button_bg"],
                activeforeground=self.current_theme["button_fg"],
            )
            r = idx // 3
            c = idx % 3
            btn.grid(row=r, column=c, padx=10, pady=10)

        bottom = tk.Frame(self, bg=self.current_theme["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        tk.Button(
            bottom,
            text="Restock (Staff)",
            command=self.enter_restock_mode,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            bottom,
            text="Reload (RFID)",
            command=self.reload_card_flow,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            bottom,
            text="Buy RFID Card",
            command=self.buy_card_flow,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            bottom,
            text="Export Sales (Excel)",
            command=self.export_sales_report_ui,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.RIGHT, padx=10)
        tk.Button(
            bottom,
            text=f"Theme: {self.current_theme_name.capitalize()}",
            command=self.toggle_theme,
            bg=self.current_theme["button_bg"],
            fg=self.current_theme["button_fg"],
        ).pack(side=tk.RIGHT, padx=10)

    def select_product(self, product_row):
        self.current_product = product_row
        self.current_quantity = 1
        self.show_quantity_screen()

    # ---------- Quantity Screen ----------

    def show_quantity_screen(self):
        self.clear_screen()
        p = self.current_product

        frame = tk.Frame(self)
        frame.pack(expand=True)

        tk.Label(frame, text=f"Selected: {p['name']}", font=("Arial", 18)).pack(pady=10)
        tk.Label(frame, text=f"Price: ₱{p['price']:.2f}", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, text=f"Available: {p['current_stock']}", font=("Arial", 12)).pack(pady=5)

        qty_var = tk.IntVar(value=self.current_quantity)

        def update_qty(delta):
            new = qty_var.get() + delta
            if 1 <= new <= p["current_stock"]:
                qty_var.set(new)

        qty_frame = tk.Frame(frame)
        qty_frame.pack(pady=20)

        tk.Button(qty_frame, text="-", width=5, command=lambda: update_qty(-1)).pack(side=tk.LEFT, padx=10)
        tk.Label(qty_frame, textvariable=qty_var, font=("Arial", 24)).pack(side=tk.LEFT, padx=10)
        tk.Button(qty_frame, text="+", width=5, command=lambda: update_qty(1)).pack(side=tk.LEFT, padx=10)

        def proceed():
            self.current_quantity = qty_var.get()
            self.show_payment_method_screen()

        tk.Button(frame, text="Proceed", font=("Arial", 14), command=proceed).pack(pady=10)
        tk.Button(frame, text="Back", font=("Arial", 12), command=self.build_main_menu).pack(pady=5)

    # ---------- Payment Method ----------

    def show_payment_method_screen(self):
        self.clear_screen()
        p = self.current_product
        q = self.current_quantity
        total = p["price"] * q

        frame = tk.Frame(self)
        frame.pack(expand=True)

        tk.Label(frame, text="Choose Payment Method", font=("Arial", 20)).pack(pady=10)
        tk.Label(frame, text=f"Product: {p['name']} x{q}", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, text=f"Total: ₱{total:.2f}", font=("Arial", 18)).pack(pady=10)

        tk.Button(
            frame,
            text="Pay with Cash",
            width=20,
            height=2,
            command=lambda: self.cash_payment_flow(total)
        ).pack(pady=10)

        tk.Button(
            frame,
            text="Pay with Cashless (RFID)",
            width=25,
            height=2,
            command=lambda: self.rfid_payment_flow(total)
        ).pack(pady=10)

        tk.Button(frame, text="Back", command=self.show_quantity_screen).pack(pady=10)

    # ---------- Cash Payment Flow ----------

    def cash_payment_flow(self, total_amount: float):
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self)
        frame.pack(expand=True)

        tk.Label(frame, text="Insert Cash (Simulation)", font=("Arial", 18)).pack(pady=10)
        tk.Label(frame, text=f"Total to Pay: ₱{total_amount:.2f}", font=("Arial", 14)).pack(pady=5)

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=total_amount)

        tk.Label(frame, text="Amount Inserted:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=amount_var, font=("Arial", 22)).pack()

        tk.Label(frame, text="Remaining:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=remaining_var, font=("Arial", 22)).pack()

        # Simulated cash buttons for development
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, total_amount - current))

        tk.Button(btn_frame, text="+₱1", width=8, command=lambda: add_money(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱5", width=8, command=lambda: add_money(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱10", width=8, command=lambda: add_money(10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱20", width=8, command=lambda: add_money(20)).pack(side=tk.LEFT, padx=5)

        def finish_if_enough():
            current = cash_session.get_amount()
            if current < total_amount:
                messagebox.showwarning("Not enough", "Please insert more cash.")
                return
            self.complete_purchase_cash(total_amount, current)

        tk.Button(frame, text="Confirm Payment", font=("Arial", 14),
                  command=finish_if_enough).pack(pady=15)

        tk.Button(frame, text="Cancel", command=self.build_main_menu).pack(pady=5)

    def complete_purchase_cash(self, total_amount: float, inserted: float):
        p = self.current_product
        q = self.current_quantity
        change = max(0.0, inserted - total_amount)

        self.show_wait_screen("Processing payment and dispensing...")

        try:
            decrement_stock(p["id"], q)
            dispense_from_slot(p["slot_number"], q)
            if change > 0:
                dispense_change(change)
            record_transaction(p["id"], q, total_amount, "cash")
            messagebox.showinfo(
                "Thank you",
                f"Please take your product.\nChange: ₱{change:.2f}"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.build_main_menu()

    # ---------- Utility Screens ----------

    def show_wait_screen(self, text: str):
        self.clear_screen()
        frame = tk.Frame(self)
        frame.pack(expand=True)
        tk.Label(frame, text=text, font=("Arial", 18)).pack(pady=20)

    # ---------- RFID Card Purchase ----------

    def buy_card_flow(self):
        """Customer buys a new RFID card for a fixed price (e.g. ₱50)."""
        CARD_PRICE = 50.0
        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self)
        frame.pack(expand=True)

        tk.Label(frame, text="Buy RFID Card", font=("Arial", 20)).pack(pady=10)
        tk.Label(frame, text=f"Please pay ₱{CARD_PRICE:.2f}", font=("Arial", 14)).pack(pady=5)

        amount_var = tk.DoubleVar(value=0.0)
        remaining_var = tk.DoubleVar(value=CARD_PRICE)

        tk.Label(frame, text="Amount Inserted:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=amount_var, font=("Arial", 22)).pack()

        tk.Label(frame, text="Remaining:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=remaining_var, font=("Arial", 22)).pack()

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            current = cash_session.get_amount()
            amount_var.set(current)
            remaining_var.set(max(0.0, CARD_PRICE - current))

        tk.Button(btn_frame, text="+₱1", width=8, command=lambda: add_money(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱5", width=8, command=lambda: add_money(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱10", width=8, command=lambda: add_money(10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱20", width=8, command=lambda: add_money(20)).pack(side=tk.LEFT, padx=5)

        def confirm_purchase():
            inserted = cash_session.get_amount()
            if inserted < CARD_PRICE:
                messagebox.showwarning("Not enough", "Please insert full card price.")
                return

            self.show_wait_screen("Issuing RFID card...")

            # Generate a simple random UID for demonstration
            uid = uuid.uuid4().hex[:8].upper()
            user_id = create_user(uid, name=None, is_staff=0, initial_balance=0.0)

            # Record transaction (no specific product)
            record_transaction(
                product_id=None,
                quantity=None,
                total_amount=CARD_PRICE,
                payment_method="card_purchase",
                rfid_user_id=user_id,
            )

            messagebox.showinfo(
                "Card Issued",
                f"New RFID card created.\nCard ID (simulate UID): {uid}"
            )
            self.build_main_menu()

        tk.Button(frame, text="Confirm Payment", font=("Arial", 14),
                  command=confirm_purchase).pack(pady=15)

        tk.Button(frame, text="Cancel", command=self.build_main_menu).pack(pady=5)

    # ---------- RFID Reload ----------

    def reload_card_flow(self):
        """Customer reloads an existing RFID card balance."""
        # Simulate RFID scan by asking for card ID
        uid = simpledialog.askstring(
            "RFID Reload",
            "Enter RFID Card ID (simulate tap):",
            parent=self,
        )
        if not uid:
            self.build_main_menu()
            return

        user = get_user_by_uid(uid)
        if not user:
            messagebox.showerror("Error", "Card not found. Please buy a new card first.")
            self.build_main_menu()
            return

        self.clear_screen()
        cash_session.reset()

        frame = tk.Frame(self)
        frame.pack(expand=True)

        tk.Label(frame, text="Reload RFID Card", font=("Arial", 20)).pack(pady=10)
        tk.Label(frame, text=f"Card ID: {uid}", font=("Arial", 12)).pack(pady=2)
        tk.Label(frame, text=f"Current Balance: ₱{user['balance']:.2f}", font=("Arial", 12)).pack(pady=5)

        amount_var = tk.DoubleVar(value=0.0)

        tk.Label(frame, text="Amount to Load:", font=("Arial", 14)).pack(pady=5)
        tk.Label(frame, textvariable=amount_var, font=("Arial", 22)).pack()

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=15)

        def add_money(val):
            cash_session.add(val)
            amount_var.set(cash_session.get_amount())

        tk.Button(btn_frame, text="+₱1", width=8, command=lambda: add_money(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱5", width=8, command=lambda: add_money(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱10", width=8, command=lambda: add_money(10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+₱20", width=8, command=lambda: add_money(20)).pack(side=tk.LEFT, padx=5)

        def confirm_reload():
            amount = cash_session.get_amount()
            if amount <= 0:
                messagebox.showwarning("No amount", "Please add some amount to reload.")
                return

            new_balance = user["balance"] + amount
            update_user_balance(user["id"], new_balance)

            record_transaction(
                product_id=None,
                quantity=None,
                total_amount=amount,
                payment_method="rfid_reload",
                rfid_user_id=user["id"],
            )

            messagebox.showinfo(
                "Reload Successful",
                f"New balance: ₱{new_balance:.2f}"
            )
            self.build_main_menu()

        tk.Button(frame, text="Confirm Reload", font=("Arial", 14),
                  command=confirm_reload).pack(pady=15)

        tk.Button(frame, text="Cancel", command=self.build_main_menu).pack(pady=5)

    # ---------- RFID Purchase Payment ----------

    def rfid_payment_flow(self, total_amount: float):
        """Purchase products using RFID card balance."""
        uid = simpledialog.askstring(
            "RFID Payment",
            "Enter RFID Card ID (simulate tap):",
            parent=self,
        )
        if not uid:
            self.build_main_menu()
            return

        user = get_user_by_uid(uid)
        if not user:
            messagebox.showerror("Error", "Card not found.")
            self.build_main_menu()
            return

        if user["balance"] < total_amount:
            messagebox.showerror("Error", "Insufficient card balance.")
            self.build_main_menu()
            return

        new_balance = user["balance"] - total_amount
        update_user_balance(user["id"], new_balance)

        p = self.current_product
        q = self.current_quantity

        self.show_wait_screen("Processing RFID payment and dispensing...")
        try:
            decrement_stock(p["id"], q)
            dispense_from_slot(p["slot_number"], q)
            record_transaction(
                product_id=p["id"],
                quantity=q,
                total_amount=total_amount,
                payment_method="rfid_purchase",
                rfid_user_id=user["id"],
            )
            messagebox.showinfo(
                "Thank you",
                f"Payment successful.\nRemaining balance: ₱{new_balance:.2f}\nPlease take your product."
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.build_main_menu()

    # ---------- Restock (Staff) ----------

    def enter_restock_mode(self):
        """Authenticate staff using RFID card ID."""
        uid = simpledialog.askstring(
            "Staff Login",
            "Enter Staff RFID Card ID (simulate tap):",
            parent=self,
        )
        if not uid:
            return

        user = get_user_by_uid(uid)
        if not user or not user["is_staff"]:
            messagebox.showerror("Access Denied", "Invalid staff card.")
            return

        self.show_restock_screen(user)

    def show_restock_screen(self, staff_user):
        self.clear_screen()

        tk.Label(self, text=f"Restock Mode - Staff: {staff_user['name'] or staff_user['rfid_uid']}",
                 font=("Arial", 16)).pack(pady=10)

        products = get_all_products()
        list_frame = tk.Frame(self)
        list_frame.pack(expand=True)

        for idx, p in enumerate(products):
            row = tk.Frame(list_frame)
            row.pack(fill=tk.X, padx=10, pady=5)

            info = f"Slot {p['slot_number']} - {p['name']} | {p['current_stock']}/{p['capacity']} | ₱{p['price']:.2f}"
            tk.Label(row, text=info, anchor="w").pack(side=tk.LEFT, expand=True)

            tk.Button(
                row,
                text="Restock",
                command=lambda prod=p: self.restock_product_dialog(prod)
            ).pack(side=tk.RIGHT, padx=5)

        tk.Button(self, text="Exit Restock Mode", command=self.build_main_menu).pack(pady=10)

    def restock_product_dialog(self, product_row):
        max_add = product_row["capacity"] - product_row["current_stock"]
        if max_add <= 0:
            messagebox.showinfo("Full", "This tray is already full.")
            return

        amount = simpledialog.askinteger(
            "Restock Amount",
            f"How many items to add? (max {max_add})",
            minvalue=1,
            maxvalue=max_add,
            parent=self,
        )
        if amount is None:
            return

        new_price = simpledialog.askfloat(
            "New Price",
            f"Enter new price per piece (current ₱{product_row['price']:.2f}), or cancel to keep:",
            parent=self,
        )

        try:
            restock_product(product_row["id"], amount, new_price)
            messagebox.showinfo(
                "Restocked",
                f"Added {amount} items to {product_row['name']}."
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

        # Refresh restock screen
        # Fetch a dummy staff user (not needed for display name here)
        dummy_staff = {"name": "", "rfid_uid": ""}
        self.show_restock_screen(dummy_staff)

    # ---------- Sales Report Export ----------

    def export_sales_report_ui(self):
        """Generate an Excel file with transaction, daily, and monthly sales."""
        try:
            path = export_sales_report()
            messagebox.showinfo(
                "Export Complete",
                f"Sales report saved as:\n{path}"
            )
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))


# ======================
#  MAIN ENTRYPOINT
# ======================

def main():
    init_db()
    gpio_init()

    app = MainApp()
    try:
        app.mainloop()
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()