from __future__ import annotations

import datetime as _dt
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PredictionRow:
    product_id: int
    product_name: str
    slot_number: int
    price: float
    capacity: int
    current_stock: int
    predicted_sales_tomorrow: float
    recommended_restock_qty: int

    @property
    def restock_needed(self) -> bool:
        return self.recommended_restock_qty > 0


@dataclass
class PredictionSummary:
    generated_at_iso: str
    based_on_last_date: str | None
    peak_hour: int | None
    peak_weekday: int | None  # 0=Sun (SQLite %w)
    top_products: list[tuple[str, int]]  # (name, qty)


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _ymd(s: str | None) -> _dt.date | None:
    if not s:
        return None
    try:
        return _dt.date.fromisoformat(str(s))
    except Exception:
        return None


def _next_day(d: _dt.date) -> _dt.date:
    return d + _dt.timedelta(days=1)


def run_prediction_analysis(
    *,
    db_path: Path,
    window_days: int = 7,
    safety_days: int = 2,
) -> tuple[list[PredictionRow], PredictionSummary]:
    """
    Lightweight prediction that runs on the app runtime (no pandas/numpy/sklearn).

    Forecast logic (per product):
    - baseline = mean(daily_qty over last `window_days` days that exist in history)
    - weekday_factor = mean(qty for next weekday) / overall_mean (clamped)
    - predicted = baseline * weekday_factor
    - restock target = ceil(predicted * (1 + safety_days))
    - recommended = clamp(target - current_stock, 0..capacity-current_stock)
    """
    conn = _connect(db_path)
    try:
        # Products (current state)
        products = conn.execute(
            "SELECT id, name, slot_number, price, capacity, current_stock FROM products ORDER BY slot_number"
        ).fetchall()

        # Daily sales per product
        daily_rows = conn.execute(
            """
            SELECT
                DATE(timestamp) AS sale_date,
                CAST(strftime('%w', timestamp) AS INTEGER) AS sale_weekday,
                product_id,
                SUM(quantity) AS daily_qty
            FROM transactions
            WHERE product_id IS NOT NULL
            GROUP BY DATE(timestamp), product_id
            ORDER BY DATE(timestamp)
            """
        ).fetchall()

        # Peak hour + weekday (overall)
        peak_hour_row = conn.execute(
            """
            SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS h, SUM(quantity) AS q
            FROM transactions
            GROUP BY h
            ORDER BY q DESC
            LIMIT 1
            """
        ).fetchone()
        peak_weekday_row = conn.execute(
            """
            SELECT CAST(strftime('%w', timestamp) AS INTEGER) AS w, SUM(quantity) AS q
            FROM transactions
            GROUP BY w
            ORDER BY q DESC
            LIMIT 1
            """
        ).fetchone()

        # Top products overall
        top_rows = conn.execute(
            """
            SELECT p.name AS product_name, SUM(t.quantity) AS qty
            FROM transactions t
            JOIN products p ON p.id = t.product_id
            WHERE t.product_id IS NOT NULL
            GROUP BY p.id
            ORDER BY qty DESC
            LIMIT 5
            """
        ).fetchall()

    finally:
        conn.close()

    # Organize daily history by product_id
    by_pid: dict[int, list[dict[str, Any]]] = {}
    last_date: _dt.date | None = None
    for r in daily_rows:
        d = _ymd(r["sale_date"])
        if d is None:
            continue
        last_date = d if last_date is None else max(last_date, d)
        pid = int(r["product_id"])
        by_pid.setdefault(pid, []).append(
            {"date": d, "weekday": int(r["sale_weekday"]), "qty": int(r["daily_qty"] or 0)}
        )

    based_on_last_date = last_date.isoformat() if last_date else None
    next_date = _next_day(last_date) if last_date else _dt.date.today() + _dt.timedelta(days=1)
    next_weekday_sqlite = int(next_date.strftime("%w"))  # 0=Sun..6=Sat (matches SQLite)

    results: list[PredictionRow] = []
    for p in products:
        pid = int(p["id"])
        hist = by_pid.get(pid, [])
        hist = sorted(hist, key=lambda x: x["date"])

        # baseline: last N available days (not necessarily consecutive)
        tail = hist[-window_days:] if hist else []
        baseline = (sum(x["qty"] for x in tail) / len(tail)) if tail else 0.0

        # weekday factor
        overall_mean = (sum(x["qty"] for x in hist) / len(hist)) if hist else 0.0
        wd_vals = [x["qty"] for x in hist if x["weekday"] == next_weekday_sqlite]
        wd_mean = (sum(wd_vals) / len(wd_vals)) if wd_vals else overall_mean
        if overall_mean > 0:
            factor = wd_mean / overall_mean
        else:
            factor = 1.0
        # clamp factor to avoid extreme swings on small data
        factor = max(0.5, min(1.8, float(factor)))

        predicted = max(0.0, baseline * factor)

        capacity = int(p["capacity"] or 0)
        current_stock = int(p["current_stock"] or 0)
        target = int(math.ceil(predicted * (1 + safety_days)))
        recommended = max(0, target - current_stock)
        if capacity > 0:
            recommended = min(recommended, max(0, capacity - current_stock))

        results.append(
            PredictionRow(
                product_id=pid,
                product_name=str(p["name"] or ""),
                slot_number=int(p["slot_number"] or 0),
                price=float(p["price"] or 0.0),
                capacity=capacity,
                current_stock=current_stock,
                predicted_sales_tomorrow=float(round(predicted, 2)),
                recommended_restock_qty=int(recommended),
            )
        )

    # Sort by predicted demand desc
    results.sort(key=lambda x: x.predicted_sales_tomorrow, reverse=True)

    summary = PredictionSummary(
        generated_at_iso=_dt.datetime.now().isoformat(timespec="seconds"),
        based_on_last_date=based_on_last_date,
        peak_hour=int(peak_hour_row["h"]) if peak_hour_row else None,
        peak_weekday=int(peak_weekday_row["w"]) if peak_weekday_row else None,
        top_products=[(str(r["product_name"]), int(r["qty"] or 0)) for r in top_rows],
    )
    return results, summary

