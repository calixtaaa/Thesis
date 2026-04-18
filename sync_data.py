"""
Pi / kiosk offline queue → Supabase `live_feed` (same target as database.py on the machine).

Environment (see supabase.env.example):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY

Optional:
  OFFLINE_DB_PATH — SQLite file for queued payloads (default: offline_queue.sqlite3)
  NETLIFY_SYSTEM_LOG_URL / NETLIFY_SYSTEM_TOKEN — middleman for sensitive ops only
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, Dict, Iterable, List, Optional

import requests

from supabase_feed import insert_live_feed_row

SQLITE_PATH = os.environ.get("OFFLINE_DB_PATH", "offline_queue.sqlite3")
NETLIFY_SYSTEM_LOG_URL = os.environ.get("NETLIFY_SYSTEM_LOG_URL", "https://api.netlify.com/api/v1/sites/thesis-2b65f/functions/system-log")
NETLIFY_SYSTEM_TOKEN = os.environ.get("NETLIFY_SYSTEM_TOKEN", "1234567890")


def is_online(timeout_s: float = 2.5) -> bool:
    try:
        requests.get("https://www.google.com", timeout=timeout_s)
        return True
    except Exception:
        return False


def init_sqlite() -> None:
    con = sqlite3.connect(SQLITE_PATH)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts INTEGER NOT NULL,
              payload TEXT NOT NULL
            )
            """
        )
        con.commit()
    finally:
        con.close()


def enqueue_offline(payload: Dict[str, Any]) -> None:
    con = sqlite3.connect(SQLITE_PATH)
    try:
        con.execute(
            "INSERT INTO queue (ts, payload) VALUES (?, ?)",
            (int(time.time() * 1000), json.dumps(payload, separators=(",", ":"))),
        )
        con.commit()
    finally:
        con.close()


def fetch_offline_batch(limit: int = 100) -> List[Dict[str, Any]]:
    con = sqlite3.connect(SQLITE_PATH)
    try:
        cur = con.execute("SELECT id, payload FROM queue ORDER BY id ASC LIMIT ?", (limit,))
        rows = cur.fetchall()
        out = []
        for _id, payload_json in rows:
            try:
                out.append({"id": _id, "payload": json.loads(payload_json)})
            except Exception:
                out.append({"id": _id, "payload": {"raw": payload_json}})
        return out
    finally:
        con.close()


def delete_offline_ids(ids: Iterable[int]) -> None:
    ids = list(ids)
    if not ids:
        return
    con = sqlite3.connect(SQLITE_PATH)
    try:
        con.executemany("DELETE FROM queue WHERE id = ?", [(i,) for i in ids])
        con.commit()
    finally:
        con.close()


def push_live_feed(activity: Dict[str, Any]) -> None:
    """Insert one row into Supabase public.live_feed (requires service role env)."""
    activity.setdefault("ts", int(time.time() * 1000))
    ok = insert_live_feed_row(activity)
    if not ok:
        raise RuntimeError("Supabase live_feed insert failed (check SUPABASE_* env and RLS).")


def ping_netlify_system_log(action: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not NETLIFY_SYSTEM_LOG_URL:
        raise RuntimeError("Missing NETLIFY_SYSTEM_LOG_URL env var.")
    if not NETLIFY_SYSTEM_TOKEN:
        raise RuntimeError("Missing NETLIFY_SYSTEM_TOKEN env var.")
    r = requests.post(
        NETLIFY_SYSTEM_LOG_URL,
        json={"action": action, "data": data or {}},
        headers={"x-system-token": NETLIFY_SYSTEM_TOKEN},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def sync_offline_to_supabase(max_rows: int = 200) -> int:
    synced = 0
    while synced < max_rows:
        batch = fetch_offline_batch(limit=min(100, max_rows - synced))
        if not batch:
            break
        ids: List[int] = []
        for row in batch:
            push_live_feed(row["payload"])
            ids.append(row["id"])
        delete_offline_ids(ids)
        synced += len(ids)
    return synced


def handle_transaction(payload: Dict[str, Any]) -> None:
    """
    If offline: queue payload locally.
    If online: flush queue to Supabase live_feed, then push this payload.
    """
    init_sqlite()
    if not is_online():
        enqueue_offline(payload)
        return

    try:
        sync_offline_to_supabase()
    except Exception:
        enqueue_offline(payload)
        return

    try:
        push_live_feed(payload)
    except Exception:
        enqueue_offline(payload)


if __name__ == "__main__":
    sample = {
        "title": "Vend",
        "item": "Hand Sanitizer — Slot A1",
        "amount": 25.00,
        "slot": "A1",
    }
    handle_transaction(sample)
