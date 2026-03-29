"""
Database layer for the Hygiene Vending Machine.
Handles SQLite connection, schema, seeding, and all product/transaction/RFID/admin queries.
"""
import hashlib
import hmac as _hmac
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime as dt, timedelta

from openpyxl import Workbook

from admin.reports import get_reports_dir


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "vending.db"

# ── SHA-256 HMAC salt (shared with server.py) ──────────────────────
_SALT_FILE = BASE_DIR / ".secret_salt"
if _SALT_FILE.exists():
    _PASSWORD_SALT = _SALT_FILE.read_text(encoding="utf-8").strip()
else:
    _PASSWORD_SALT = secrets.token_hex(16)
    try:
        _SALT_FILE.write_text(_PASSWORD_SALT, encoding="utf-8")
    except Exception:
        pass


def _hash_password(password: str) -> str:
    """Create a salted SHA-256 HMAC hash."""
    return _hmac.new(
        _PASSWORD_SALT.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


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
        is_staff INTEGER NOT NULL DEFAULT 0,
        role TEXT NOT NULL DEFAULT 'customer'
    );
    """)
    conn.commit()

    # Ensure new column exists if upgrading from older schema
    cur.execute("PRAGMA table_info(transactions)")
    cols = [row["name"] for row in cur.fetchall()]
    if "rfid_user_id" not in cols:
        cur.execute("ALTER TABLE transactions ADD COLUMN rfid_user_id INTEGER")
        conn.commit()

    # Ensure RFID role column exists for door-based access control.
    cur.execute("PRAGMA table_info(rfid_users)")
    user_cols = [row["name"] for row in cur.fetchall()]
    if "role" not in user_cols:
        cur.execute("ALTER TABLE rfid_users ADD COLUMN role TEXT NOT NULL DEFAULT 'customer'")
        conn.commit()

    # Backfill legacy staff cards to a restock-access role.
    cur.execute("""
        UPDATE rfid_users
        SET role = 'restocker'
        WHERE is_staff = 1 AND (role IS NULL OR role = '' OR role = 'customer')
    """)
    conn.commit()

    # Seed sample data if empty
    cur.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()["c"] == 0:
        sample_products = [
            ("All Night Pads",          12.0, 1, 10, 5),
            ("Panty Liners",            8.0,  2, 10, 5),
            ("Regular W/ Wings Pads",   10.0, 3, 10, 5),
            ("Non-Wing Pads",           9.0,  4, 10, 5),
            ("Alcohol",                 25.0, 5, 10, 5),
            ("Mouthwash",               35.0, 6, 10, 5),
            ("Tissues",                 15.0, 7, 10, 5),
            ("Wet Wipes",               25.0, 8, 10, 5),
            ("Deodorant",               50.0, 9, 10, 5),
            ("Soap",                    30.0, 10, 10, 5),
        ]
        cur.executemany(
            """
            INSERT INTO products (name, price, slot_number, capacity, current_stock)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_products,
        )
        conn.commit()

    # Seed a default staff RFID user for testing
    cur.execute("SELECT COUNT(*) AS c FROM rfid_users")
    if cur.fetchone()["c"] == 0:
        cur.execute("""
            INSERT INTO rfid_users (rfid_uid, name, balance, is_staff, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("STAFF001", "Default Staff", 0.0, 1, "restocker"))
        conn.commit()

    # Admin credentials table (single row) with hashed password
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
    )
    cur.execute("SELECT COUNT(*) AS c FROM admin_settings")
    if cur.fetchone()["c"] == 0:
        default_user = "admin"
        default_pass = "admin"
        pwd_hash = _hash_password(default_pass)
        cur.execute(
            "INSERT INTO admin_settings (id, username, password_hash) VALUES (1, ?, ?)",
            (default_user, pwd_hash),
        )
        conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hardware_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        );
        """
    )
    cur.execute("SELECT COUNT(*) AS c FROM hardware_settings")
    if cur.fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO hardware_settings (setting_key, setting_value) VALUES (?, ?)",
            [
                ("coin_pulse_value", "1.0"),
                ("bill_pulse_value", "20.0"),
            ],
        )
        conn.commit()

    conn.close()


def get_admin_credentials():
    """Return (username, password_hash) for the single admin account."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash FROM admin_settings WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        return None, None
    return row["username"], row["password_hash"]


def update_admin_credentials(new_username: str, new_password: str):
    """Update the single admin username and password (stored as salted HMAC-SHA256)."""
    pwd_hash = _hash_password(new_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE admin_settings
        SET username = ?, password_hash = ?
        WHERE id = 1
        """,
        (new_username, pwd_hash),
    )
    conn.commit()
    conn.close()


def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY slot_number")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_product_by_id(product_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row


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


def create_user(
    rfid_uid: str,
    name: str | None = None,
    is_staff: int = 0,
    initial_balance: float = 0.0,
    role: str = "customer",
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rfid_users (rfid_uid, name, balance, is_staff, role)
        VALUES (?, ?, ?, ?, ?)
    """, (rfid_uid, name, initial_balance, is_staff, role))
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


def get_all_rfid_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, rfid_uid, name, balance, is_staff, role
        FROM rfid_users
        ORDER BY id
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_rfid_user_role(user_id: int, role: str):
    clean_role = (role or "customer").strip().lower()
    is_staff = 1 if clean_role in {"staff", "restocker", "admin"} else 0
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE rfid_users SET role = ?, is_staff = ? WHERE id = ?",
        (clean_role, is_staff, user_id),
    )
    conn.commit()
    conn.close()


def get_hardware_setting(key: str, default: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT setting_value FROM hardware_settings WHERE setting_key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return default
    return row["setting_value"]


def set_hardware_setting(key: str, value: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO hardware_settings (setting_key, setting_value)
        VALUES (?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
        """,
        (key, value),
    )
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

    wb = Workbook()
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

        if date not in daily_summary:
            daily_summary[date] = {"quantity": 0, "amount": 0.0}
        daily_summary[date]["quantity"] += qty
        daily_summary[date]["amount"] += total_amt

        if month not in monthly_summary:
            monthly_summary[month] = {"quantity": 0, "amount": 0.0}
        monthly_summary[month]["quantity"] += qty
        monthly_summary[month]["amount"] += total_amt

    ws_daily = wb.create_sheet(title="Daily Summary")
    ws_daily.append(["Date", "Total Quantity", "Total Amount"])
    for date, agg in sorted(daily_summary.items()):
        ws_daily.append([date, agg["quantity"], agg["amount"]])

    ws_monthly = wb.create_sheet(title="Monthly Summary")
    ws_monthly.append(["Month (YYYY-MM)", "Total Quantity", "Total Amount"])
    for month, agg in sorted(monthly_summary.items()):
        ws_monthly.append([month, agg["quantity"], agg["amount"]])

    stamp = dt.now().strftime("%Y%m%d_%H%M%S")
    filename = get_reports_dir() / f"sales_report_{stamp}.xlsx"
    wb.save(filename)
    return filename


def get_admin_overview_stats():
    """Compute high-level stats for the admin dashboard."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COUNT(*) AS orders
        FROM transactions
        WHERE total_amount IS NOT NULL
        """
    )
    row = cur.fetchone()
    total_sales = row["total_sales"]
    orders = row["orders"]

    cur.execute(
        """
        SELECT COUNT(DISTINCT rfid_user_id) AS active_customers
        FROM transactions
        WHERE rfid_user_id IS NOT NULL
        """
    )
    active_customers = cur.fetchone()["active_customers"]

    cur.execute("SELECT COUNT(*) AS low_count FROM products WHERE current_stock < 4")
    low_stock = cur.fetchone()["low_count"]

    conn.close()

    return {
        "total_sales": total_sales,
        "orders": orders,
        "active_customers": active_customers,
        "low_stock": low_stock,
    }


def get_sales_trend_data(days: int = 15):
    """Return daily sales totals for the last N days, including zero-sales days."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DATE(timestamp) AS sale_date, COALESCE(SUM(total_amount), 0) AS total_sales
        FROM transactions
        WHERE DATE(timestamp) >= DATE('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
        """,
        (f"-{days - 1} day",),
    )
    rows = cur.fetchall()
    conn.close()

    totals_by_date = {row["sale_date"]: float(row["total_sales"] or 0) for row in rows}
    today = dt.now().date()
    points = []
    for offset in range(days - 1, -1, -1):
        current_date = today - timedelta(days=offset)
        key = current_date.strftime("%Y-%m-%d")
        points.append(
            {
                "date": current_date,
                "label": current_date.strftime("%m/%d"),
                "value": totals_by_date.get(key, 0.0),
            }
        )
    return points


def get_monthly_sales_data(months: int = 6):
    """Return monthly sales totals for the last N months."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT strftime('%Y-%m', timestamp) AS sale_month, COALESCE(SUM(total_amount), 0) AS total_sales
        FROM transactions
        WHERE DATE(timestamp) >= DATE('now', 'start of month', ?)
        GROUP BY strftime('%Y-%m', timestamp)
        ORDER BY sale_month
        """,
        (f"-{months - 1} month",),
    )
    rows = cur.fetchall()
    conn.close()

    totals_by_month = {row["sale_month"]: float(row["total_sales"] or 0) for row in rows}
    today = dt.now().date()
    current_month = today.replace(day=1)
    points = []
    for offset in range(months - 1, -1, -1):
        year = current_month.year
        month = current_month.month - offset
        while month <= 0:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        key = f"{year:04d}-{month:02d}"
        label = f"{month:02d}/{str(year)[2:]}"
        points.append({"label": label, "value": totals_by_month.get(key, 0.0)})
    return points


def get_top_selling_products(limit: int | None = None):
    """Return product sales totals, including products with zero sales."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT
            p.name AS product_name,
            COALESCE(SUM(t.quantity), 0) AS total_quantity
        FROM products p
        LEFT JOIN transactions t ON t.product_id = p.id AND t.quantity IS NOT NULL
        GROUP BY p.id, p.name
        ORDER BY total_quantity DESC, p.name ASC
    """
    params: tuple = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (int(limit),)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [{"label": row["product_name"], "value": float(row["total_quantity"] or 0)} for row in rows]


def get_low_stock_chart_data(limit: int = 10):
    """Return low-stock product data for charting (current stock under 4)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name, current_stock, capacity
        FROM products
        WHERE current_stock < 4
        ORDER BY current_stock ASC, name ASC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "label": row["name"],
            "value": float(row["current_stock"]),
            "capacity": float(row["capacity"]),
        }
        for row in rows
    ]
