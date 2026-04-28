"""
Offline per-user behavior model for Hygiene Hero.

Goal: personalize advice without internet by learning from local SQLite history.
We intentionally keep this lightweight (no sklearn dependency).
"""

from __future__ import annotations

import math
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class UserProfile:
    user_id: int
    top_products: list[str]
    top_hours: list[int]
    top_days: list[str]
    total_purchases: int


def _default_db_path() -> str:
    # Most of this project uses a local sqlite file named vending.db.
    # We resolve relative to repo root (two levels above chatbot/).
    base = Path(__file__).resolve().parents[1]
    return str(base / "vending.db")


def _safe_connect(db_path: str | None) -> sqlite3.Connection | None:
    path = db_path or _default_db_path()
    try:
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        return con
    except Exception:
        return None


def load_user_profile(user_id: int, *, db_path: str | None = None, lookback_days: int = 60) -> UserProfile | None:
    """
    Build a small behavior profile from local transactions.

    Expected schema (best effort):
      - transactions: (rfid_user_id, product_id, created_at/created_date, quantity, payment_method, ...)
      - products: (id, name, ...)
    Works even if some columns vary — we fall back gracefully.
    """
    if not user_id:
        return None

    con = _safe_connect(db_path)
    if con is None:
        return None

    since = datetime.now() - timedelta(days=int(lookback_days))
    since_iso = since.strftime("%Y-%m-%d %H:%M:%S")

    # Try common timestamp column names.
    ts_cols = ["created_at", "created_date", "timestamp", "created_on", "date_created"]
    ts_col = None
    try:
        cols = [r["name"] for r in con.execute("PRAGMA table_info(transactions)").fetchall()]
        for c in ts_cols:
            if c in cols:
                ts_col = c
                break
    except Exception:
        con.close()
        return None

    # If no timestamp column exists, still compute product prefs without time features.
    where_time = ""
    params: list[object] = [user_id]
    if ts_col:
        where_time = f" AND t.{ts_col} >= ?"
        params.append(since_iso)

    # Use quantity if present; else count rows.
    has_qty = False
    try:
        cols = [r["name"] for r in con.execute("PRAGMA table_info(transactions)").fetchall()]
        has_qty = "quantity" in cols
    except Exception:
        has_qty = False

    qty_expr = "COALESCE(t.quantity, 1)" if has_qty else "1"

    product_counts: Counter[str] = Counter()
    hours: Counter[int] = Counter()
    days: Counter[str] = Counter()
    total = 0

    try:
        rows = con.execute(
            f"""
            SELECT
              p.name AS product_name,
              t.{ts_col} AS ts,
              {qty_expr} AS qty
            FROM transactions t
            LEFT JOIN products p ON p.id = t.product_id
            WHERE t.rfid_user_id = ?
              AND t.product_id IS NOT NULL
              {where_time}
            """,
            params,
        ).fetchall()

        for r in rows:
            name = (r["product_name"] or "").strip()
            if not name:
                continue
            q = int(r["qty"] or 1)
            product_counts[name] += max(q, 1)
            total += max(q, 1)
            if ts_col and r["ts"]:
                try:
                    # Accept both "YYYY-MM-DD HH:MM:SS" and ISO-ish strings.
                    ts = str(r["ts"]).replace("T", " ").split(".")[0]
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    hours[dt.hour] += 1
                    days[dt.strftime("%a")] += 1  # Mon/Tue/...
                except Exception:
                    pass
    except Exception:
        con.close()
        return None
    finally:
        try:
            con.close()
        except Exception:
            pass

    if total <= 0:
        return None

    top_products = [p for p, _ in product_counts.most_common(3)]
    top_hours = [h for h, _ in hours.most_common(3)]
    top_days = [d for d, _ in days.most_common(3)]

    return UserProfile(
        user_id=int(user_id),
        top_products=top_products,
        top_hours=top_hours,
        top_days=top_days,
        total_purchases=int(total),
    )


def personalize_advice(base: str, profile: UserProfile | None) -> str:
    """
    Inject a short, user-specific suggestion. Must remain concise (machine UI).
    """
    if not profile:
        return base

    bits: list[str] = []
    if profile.top_products:
        bits.append(f"Based on your past buys: {', '.join(profile.top_products[:2])}.")
    if profile.top_hours:
        bits.append(f"You often buy around {profile.top_hours[0]:02d}:00.")
    if profile.top_days:
        bits.append(f"Peak day: {profile.top_days[0]}.")

    extra = " ".join(bits[:2]).strip()
    if not extra:
        return base

    return f"{base}\n\nPersonal tip: {extra}"

