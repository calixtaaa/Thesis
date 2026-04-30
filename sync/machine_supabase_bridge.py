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
import os
import sqlite3
import sys
import time
import atexit
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "vending.db"
ENV_PATH = BASE_DIR / "supabase.env"
LOCK_PATH = BASE_DIR / "sync" / ".supabase_bridge.lock"


def env_configured() -> bool:
    """True when supabase.env exists and contains URL + service_role (used by main.py)."""
    env = _load_env(ENV_PATH)
    return bool((env.get("SUPABASE_URL") or "").strip() and (env.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip())
# Persist highest SQLite transaction id successfully pushed (avoids re-inserting all history on restart).
STATE_PATH = BASE_DIR / "sync" / ".supabase_last_tx_id"
PRODUCTS_PUSH_INTERVAL_S = 5.0


def _to_supabase_timestamptz(raw: str | None) -> str | None:
    """Convert SQLite timestamp (often 'YYYY-MM-DD HH:MM:SS' UTC) to ISO-8601 for Supabase."""
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # If it already looks like ISO with timezone, keep it.
    if "T" in s and (s.endswith("Z") or "+" in s or s.count("-") > 2):
        return s
    # Common SQLite CURRENT_TIMESTAMP format: 'YYYY-MM-DD HH:MM:SS' (UTC).
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    except Exception:
        return s


def _get_max_local_tx_id(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) AS mid FROM transactions")
    row = cur.fetchone()
    try:
        return int(row["mid"] or 0)
    except Exception:
        return 0


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
                # Deterministic id from the machine SQLite (used for safe upserts in Supabase).
                "source_tx_id": int(r["id"]),
                "created_at": _to_supabase_timestamptz(r["timestamp"]),
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
    # Make logs visible immediately even when stdout is redirected (Windows/PowerShell).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    env = _load_env(ENV_PATH)
    supabase_url = env.get("SUPABASE_URL", "").rstrip("/")
    service_key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    live_feed_mode = (env.get("SUPABASE_LIVE_FEED_MODE") or "trigger").strip().lower()
    # Modes:
    # - "trigger" (default): do NOT write public.live_feed here; rely on Supabase trigger from transactions
    # - "bridge": this script appends public.live_feed rows itself
    enable_bridge_live_feed = live_feed_mode in {"bridge", "direct"}
    if not supabase_url or not service_key:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in supabase.env")

    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    # Prevent multiple bridge instances from running (would cause duplicate inserts).
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8", errors="ignore"))
        os.close(fd)
    except FileExistsError:
        raise SystemExit(f"Bridge already running (lock exists): {LOCK_PATH}")

    def _cleanup_lock():
        try:
            if LOCK_PATH.exists():
                LOCK_PATH.unlink()
        except Exception:
            pass

    atexit.register(_cleanup_lock)

    headers = _supabase_headers(service_key)
    products_endpoint = f"{supabase_url}/rest/v1/products?on_conflict=slot_number"
    # Prefer safe upserts when the Supabase schema supports `source_tx_id` (unique).
    tx_endpoint_upsert = f"{supabase_url}/rest/v1/transactions?on_conflict=source_tx_id"
    tx_endpoint_plain = f"{supabase_url}/rest/v1/transactions"
    live_feed_endpoint = f"{supabase_url}/rest/v1/live_feed"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    last_tx_id_saved = _read_last_tx_id()
    # If the local DB was reset (ids start back at 1), the saved state can be ahead of MAX(id),
    # causing the website to never receive new rows. Auto-heal by resetting state.
    local_max_id = _get_max_local_tx_id(conn)
    if local_max_id and last_tx_id_saved > local_max_id:
        print(
            f"[Supabase bridge] Detected local tx id reset (state={last_tx_id_saved} > local_max={local_max_id}). "
            "Resetting sync cursor to 0.",
            flush=True,
        )
        last_tx_id_saved = 0
        _write_last_tx_id(last_tx_id_saved)

    # IMPORTANT: Do NOT replay history unless Supabase has a dedupe key (source_tx_id).
    # If the column isn't installed yet, replays would create duplicates.
    # Use the saved cursor normally; if you ever need a one-time repair, manually lower
    # sync/.supabase_last_tx_id (or install source_tx_id and then you can safely replay).
    last_tx_id = max(0, int(last_tx_id_saved))
    products_err_printed = False
    live_feed_available: bool | None = None if enable_bridge_live_feed else False
    tx_upsert_available: bool | None = None
    last_products_push = 0.0

    # Avoid non-ASCII symbols (Windows cp1252 terminals).
    print(
        f"Machine <-> Supabase bridge running (last SQLite tx id synced: {last_tx_id_saved}). Press Ctrl+C to stop.",
        flush=True,
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
                    # Attempt upsert-by-source_tx_id first.
                    if tx_upsert_available is not False:
                        try:
                            _rest_json("POST", tx_endpoint_upsert, headers, new_tx)
                            tx_upsert_available = True
                        except HTTPError as e:
                            body = ""
                            try:
                                body = e.read().decode("utf-8", errors="replace")
                            except Exception:
                                pass
                            # If the project hasn't run the migration yet, fall back to plain inserts.
                            if e.code in (400, 404) and ("source_tx_id" in body or "column" in body and "source_tx_id" in body):
                                if tx_upsert_available is None:
                                    _print_http_err("transactions upsert (source_tx_id missing; falling back)", e)
                                tx_upsert_available = False
                            else:
                                raise

                    if tx_upsert_available is False:
                        # Strip source_tx_id so old schemas accept the payload.
                        stripped = []
                        for t in new_tx:
                            d = dict(t)
                            d.pop("source_tx_id", None)
                            stripped.append(d)
                        _rest_json("POST", tx_endpoint_plain, headers, stripped)

                    # Optional: append a human-readable activity line so the website "live_feed"
                    # shows realtime events even if the SQL trigger wasn't installed.
                    if live_feed_available is not False:
                        feed_rows = []
                        for t in new_tx:
                            # Keep message short and readable on dashboard.
                            name = (t.get("product_name") or "").strip() if isinstance(t, dict) else ""
                            if not name:
                                name = f"Product #{t.get('product_id')}" if t.get("product_id") is not None else "Product"
                            slot = t.get("slot_number")
                            qty = t.get("quantity")
                            amt = t.get("total_amount")
                            slot_txt = f"slot {slot}" if slot is not None else "slot ?"
                            amt_txt = f"₱{amt}" if amt is not None else "₱0"
                            msg = f"Sale: {name} · {slot_txt} · {amt_txt}"
                            feed_rows.append(
                                {
                                    "event_type": "sale",
                                    "message": msg,
                                    "quantity": int(qty) if qty is not None else None,
                                    "total_amount": float(amt) if amt is not None else None,
                                    "payload": {
                                        "product_id": t.get("product_id"),
                                        "product_name": t.get("product_name"),
                                        "slot_number": t.get("slot_number"),
                                        "quantity": t.get("quantity"),
                                        "total_amount": t.get("total_amount"),
                                        "payment_method": t.get("payment_method"),
                                        "rfid_user_id": t.get("rfid_user_id"),
                                        "created_at": t.get("created_at"),
                                        "source_tx_id": t.get("source_tx_id"),
                                    },
                                }
                            )
                        if feed_rows:
                            try:
                                _rest_json("POST", live_feed_endpoint, headers, feed_rows)
                                live_feed_available = True
                            except HTTPError as e:
                                # 404 / missing table: disable further attempts (user can run SQL script later).
                                if getattr(e, "code", None) in (404, 400):
                                    if live_feed_available is None:
                                        _print_http_err("live_feed insert (optional)", e)
                                    live_feed_available = False
                                else:
                                    _print_http_err("live_feed insert (optional)", e)
                            except (URLError, OSError, ValueError) as e:
                                _print_http_err("live_feed insert (optional)", e)
                    last_tx_id = next_id
                    # Persist the cursor only after a successful push.
                    last_tx_id_saved = next_id
                    _write_last_tx_id(last_tx_id_saved)
                except (HTTPError, URLError, OSError, ValueError) as e:
                    _print_http_err("transactions insert", e)

            time.sleep(1.0)
    except KeyboardInterrupt:
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
