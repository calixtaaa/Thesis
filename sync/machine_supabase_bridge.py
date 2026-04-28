"""
Machine ↔ Supabase realtime bridge (no hardware code changes).

Sales are stored in local SQLite first. This process pushes new rows to Supabase so the
website Realtime subscription receives INSERT events.

Run manually:
  python sync/machine_supabase_bridge.py

Or start the vending app (main.py): it starts this script automatically when supabase.env exists.

Credentials (repo root):
  supabase.env:
    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=...   (Dashboard → Settings → API → service_role — bypasses RLS)
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "vending.db"
ENV_PATH = BASE_DIR / "supabase.env"


def env_configured() -> bool:
    """True when supabase.env exists and contains URL + service_role (used by main.py)."""
    env = _load_env(ENV_PATH)
    return bool((env.get("SUPABASE_URL") or "").strip() and (env.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip())
# Persist highest SQLite transaction id successfully pushed (avoids re-inserting all history on restart).
STATE_PATH = BASE_DIR / "sync" / ".supabase_last_tx_id"
PRODUCTS_PUSH_INTERVAL_S = 5.0


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


def _read_last_tx_id() -> int:
    try:
        if not STATE_PATH.exists():
            return 0
        raw = STATE_PATH.read_text(encoding="utf-8").strip()
        return max(0, int(raw))
    except (OSError, ValueError):
        return 0


def _write_last_tx_id(last_id: int) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(str(int(last_id)), encoding="utf-8")
    except OSError as e:
        print(f"[Supabase bridge] Could not save state file {STATE_PATH}: {e}")


def _print_http_err(context: str, exc: BaseException) -> None:
    if isinstance(exc, HTTPError):
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"[Supabase bridge] {context} failed: HTTP {exc.code} {exc.reason} {body}")
    else:
        print(f"[Supabase bridge] {context} failed: {exc}")


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
    ts = datetime.now(timezone.utc).isoformat()
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
                "updated_at": ts,
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

    last_tx_id = _read_last_tx_id()
    products_err_printed = False
    last_products_push = 0.0

    print(
        f"Machine↔Supabase bridge running (last SQLite tx id synced: {last_tx_id}). "
        "Press Ctrl+C to stop."
    )

    try:
        while True:
            # Throttle product upserts to reduce API traffic and avoid UI slowdowns.
            now = time.monotonic()
            if now - last_products_push >= PRODUCTS_PUSH_INTERVAL_S:
                try:
                    products = _fetch_products(conn)
                    _rest_json("POST", products_endpoint, headers, products)
                    products_err_printed = False
                    last_products_push = now
                except (HTTPError, URLError, OSError, ValueError) as e:
                    if not products_err_printed:
                        _print_http_err("products upsert", e)
                        products_err_printed = True

            next_id, new_tx = _fetch_new_transactions(conn, last_tx_id)
            if new_tx:
                try:
                    _rest_json("POST", tx_endpoint, headers, new_tx)
                    last_tx_id = next_id
                    _write_last_tx_id(last_tx_id)
                except (HTTPError, URLError, OSError, ValueError) as e:
                    _print_http_err("transactions insert", e)

            time.sleep(1.0)
    except KeyboardInterrupt:
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
