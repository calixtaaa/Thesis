from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "vending.db"
OUTPUTS_DIR = BASE_DIR / "predictionAnalysis" / "outputs"


def extract_transactions_dataset(db_path: Path = DB_PATH) -> pd.DataFrame:
    """
    Extract a joined dataset from SQLite:
    transactions + products + (optional) rfid_users.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        df = pd.read_sql_query(
            """
            SELECT
                t.timestamp,
                DATE(t.timestamp, '+8 hours') AS sale_date,
                strftime('%Y-%m', t.timestamp, '+8 hours') AS sale_month,
                CAST(strftime('%H', t.timestamp, '+8 hours') AS INTEGER) AS sale_hour,
                CAST(strftime('%w', t.timestamp, '+8 hours') AS INTEGER) AS sale_weekday,
                t.product_id,
                p.name AS product_name,
                p.slot_number,
                p.price,
                p.capacity,
                p.current_stock,
                t.quantity,
                t.total_amount,
                t.payment_method,
                u.rfid_uid
            FROM transactions t
            LEFT JOIN products p ON p.id = t.product_id
            LEFT JOIN rfid_users u ON u.id = t.rfid_user_id
            ORDER BY t.timestamp
            """,
            conn,
        )
    finally:
        conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["sale_month"] = df["sale_month"].astype(str)
    return df


def main():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    df = extract_transactions_dataset()
    out = OUTPUTS_DIR / "dataset_transactions.csv"
    df.to_csv(out, index=False)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()

