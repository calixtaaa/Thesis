"""
Push rows to Supabase table `live_feed` for the Vue dashboard (Realtime).

Set on the machine (environment or process manager), never commit secrets:
  SUPABASE_URL=https://xxxx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=eyJ...   (Dashboard → Settings → API → service_role)

The web app uses the publishable/anon key; this module uses the service role so
inserts work without opening public INSERT policies on live_feed.
"""
from __future__ import annotations

import json
import os
import time
import base64
from typing import Any, Mapping
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_DID_WARN_MISSING = False


def _load_env_file_if_present() -> None:
    """
    Best-effort .env loader (no external deps).
    Supports lines like KEY=VALUE, ignores blanks/comments.

    We specifically look for a sibling `supabase.env` so the Raspberry Pi app can
    run under systemd/GUI without manually exporting env vars.
    """
    here = Path(__file__).resolve().parent
    for filename in ("supabase.env", ".env"):
        p = here / filename
        if not p.exists():
            continue
        try:
            for raw in p.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and v and not os.environ.get(k):
                    os.environ[k] = v
        except Exception:
            # Never break the machine flow due to env file parsing.
            pass


def _configured() -> bool:
    _load_env_file_if_present()
    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    global _DID_WARN_MISSING
    if not (url and key) and not _DID_WARN_MISSING:
        _DID_WARN_MISSING = True
        print(
            "[supabase_feed] SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing. "
            "Create `supabase.env` beside supabase_feed.py (see supabase.env.example) "
            "or set environment variables for the machine process."
        )
    return bool(url and key)


def _jwt_role(jwt: str) -> str | None:
    """Return the `role` claim from a Supabase JWT if parseable (no signature verify)."""
    try:
        parts = jwt.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        r = data.get("role")
        return str(r) if r is not None else None
    except Exception:
        return None


def insert_live_feed_row(row: Mapping[str, Any]) -> bool:
    """POST one row to public.live_feed. Returns True on HTTP 2xx."""
    if not _configured():
        return False

    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"].strip()
    role = _jwt_role(key)
    if role and role != "service_role":
        print(
            "[supabase_feed] Wrong key type: SUPABASE_SERVICE_ROLE_KEY must be the "
            f"`service_role` JWT from Supabase (decoded role is `{role}`). "
            "Using `anon` here causes RLS errors on INSERT."
        )
        return False
    endpoint = f"{base}/rest/v1/live_feed"

    body = json.dumps(dict(row), default=str).encode("utf-8")
    req = Request(endpoint, data=body, method="POST")
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "return=minimal")

    try:
        with urlopen(req, timeout=8) as resp:
            return 200 <= resp.status < 300
    except HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            detail = ""
        print(f"[supabase_feed] HTTP {e.code} {detail}")
    except URLError as e:
        print(f"[supabase_feed] {e}")
    return False
