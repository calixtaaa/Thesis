"""
Machine ↔ Supabase realtime bridge (no hardware code changes).

This script reads local SQLite (`vending.db`) and upserts rows to Supabase using REST.
Run it alongside the machine app:

  python sync/machine_supabase_bridge.py

It uses credentials in `supabase.env`:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "vending.db"
ENV_PATH = BASE_DIR / "supabase.env"


def _load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _rest_json(method: str, url: str, headers: dict[str, str], body: dict | list | None = None):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}
    req = Request(url=url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))


def _supabase_headers(service_key: str) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def _fetch_products(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT slot_number, name, details, price, capacity, current_stock FROM products ORDER BY slot_number"
    )
    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "slot_number": int(r["slot_number"]),
                "name": r["name"],
                "details": r["details"],
                "price": float(r["price"]),
                "capacity": int(r["capacity"]),
                "current_stock": int(r["current_stock"]),
                "updated_at": "now()",
            }
        )
    return out


def _fetch_new_transactions(conn: sqlite3.Connection, last_id: int) -> tuple[int, list[dict]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          t.id,
          t.timestamp,
          t.product_id,
          p.name as product_name,
          p.slot_number as slot_number,
          t.quantity,
          t.total_amount,
          t.payment_method,
          t.rfid_user_id
        FROM transactions t
        LEFT JOIN products p ON p.id = t.product_id
        WHERE t.id > ?
        ORDER BY t.id ASC
        """,
        (int(last_id),),
    )
    rows = cur.fetchall()
    if not rows:
        return last_id, []
    max_id = max(int(r["id"]) for r in rows)
    payload = []
    for r in rows:
        payload.append(
            {
                # Keep original machine tx id in a separate field if you add one in Supabase;
                # for now we just insert new rows (id is identity on Supabase).
                "created_at": r["timestamp"],
                "product_id": int(r["product_id"]) if r["product_id"] is not None else None,
                "product_name": r["product_name"] or None,
                "slot_number": int(r["slot_number"]) if r["slot_number"] is not None else None,
                "quantity": int(r["quantity"]) if r["quantity"] is not None else None,
                "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                "payment_method": r["payment_method"] or None,
                "rfid_user_id": int(r["rfid_user_id"]) if r["rfid_user_id"] is not None else None,
            }
        )
    return max_id, payload


def main() -> int:
    env = _load_env(ENV_PATH)
    supabase_url = env.get("SUPABASE_URL", "").rstrip("/")
    service_key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not service_key:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in supabase.env")

    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    headers = _supabase_headers(service_key)
    products_endpoint = f"{supabase_url}/rest/v1/products?on_conflict=slot_number"
    tx_endpoint = f"{supabase_url}/rest/v1/transactions"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    last_tx_id = 0
    print("Machine↔Supabase bridge running. Press Ctrl+C to stop.")

    try:
        while True:
            # Upsert products every loop (cheap: only 10 rows)
            products = _fetch_products(conn)
            _rest_json("POST", products_endpoint, headers, products)

            # Insert new transactions since last seen
            last_tx_id, new_tx = _fetch_new_transactions(conn, last_tx_id)
            if new_tx:
                _rest_json("POST", tx_endpoint, headers, new_tx)

            time.sleep(1.0)
    except KeyboardInterrupt:
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

