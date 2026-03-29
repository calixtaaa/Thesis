"""
Netlify Serverless Function — WSGI adapter for the Flask dashboard.
Converts AWS Lambda events into WSGI requests so Flask handles them
exactly the same way as local development.
"""

import base64
import io
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlencode

# ── Path Setup ─────────────────────────────────────────────────────
FUNC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FUNC_DIR))
sys.path.insert(0, str(FUNC_DIR / "WebPages"))
sys.path.insert(0, str(FUNC_DIR / "predictionAnalysis"))

# ── Database: copy bundled DB to writable /tmp ─────────────────────
_TMP_DB   = Path("/tmp/vending.db")
_SRC_DB   = FUNC_DIR / "vending.db"
_TMP_SALT = Path("/tmp/.secret_salt")
_SRC_SALT = FUNC_DIR / ".secret_salt"

if _SRC_DB.exists() and not _TMP_DB.exists():
    shutil.copy2(_SRC_DB, _TMP_DB)

if _SRC_SALT.exists() and not _TMP_SALT.exists():
    shutil.copy2(_SRC_SALT, _TMP_SALT)

# ── Import & initialise Flask app ──────────────────────────────────
import database as db                   # noqa: E402

if _TMP_DB.exists():
    db.DB_PATH = _TMP_DB

db.init_db()

from server import app as flask_app    # noqa: E402


# ══════════════════════════════════════════════════════════════════
#  Handler
# ══════════════════════════════════════════════════════════════════

def handler(event, context):
    """Netlify Functions entry-point (AWS Lambda compatible)."""
    environ = _event_to_wsgi(event)

    resp_meta = {}
    body_parts = []

    def start_response(status, headers, exc_info=None):
        resp_meta["status"] = status
        resp_meta["headers"] = headers

    result = flask_app.wsgi_app(environ, start_response)
    try:
        for chunk in result:
            body_parts.append(chunk)
    finally:
        if hasattr(result, "close"):
            result.close()

    status_code = int(resp_meta["status"].split(" ", 1)[0])
    headers_dict = {k: v for k, v in resp_meta.get("headers", [])}
    body = b"".join(body_parts)

    content_type = headers_dict.get("Content-Type", "")
    is_text = any(t in content_type for t in (
        "text/", "json", "javascript", "xml", "jsx", "html",
    ))

    return {
        "statusCode": status_code,
        "headers": headers_dict,
        "body": (
            body.decode("utf-8", errors="replace") if is_text
            else base64.b64encode(body).decode()
        ),
        "isBase64Encoded": not is_text,
    }


# ══════════════════════════════════════════════════════════════════
#  Event → WSGI environ conversion
# ══════════════════════════════════════════════════════════════════

def _event_to_wsgi(event):
    method  = event.get("httpMethod", "GET")
    path    = event.get("path", "/")
    qs      = event.get("queryStringParameters") or {}
    headers = event.get("headers") or {}
    raw_body = event.get("body") or ""
    is_b64   = event.get("isBase64Encoded", False)

    body_bytes = (
        base64.b64decode(raw_body) if is_b64 and raw_body
        else raw_body.encode("utf-8")
    )

    environ = {
        "REQUEST_METHOD":  method,
        "SCRIPT_NAME":     "",
        "PATH_INFO":       path,
        "QUERY_STRING":    urlencode(qs) if qs else "",
        "SERVER_NAME":     headers.get("host", "localhost"),
        "SERVER_PORT":     headers.get("x-forwarded-port", "443"),
        "SERVER_PROTOCOL": "HTTP/1.1",
        "CONTENT_LENGTH":  str(len(body_bytes)),
        "REMOTE_ADDR":     (
            headers.get("x-nf-client-connection-ip")
            or headers.get("x-forwarded-for", "127.0.0.1").split(",")[0].strip()
        ),
        "wsgi.version":      (1, 0),
        "wsgi.url_scheme":   headers.get("x-forwarded-proto", "https"),
        "wsgi.input":        io.BytesIO(body_bytes),
        "wsgi.errors":       sys.stderr,
        "wsgi.multithread":  False,
        "wsgi.multiprocess": False,
        "wsgi.run_once":     True,
    }

    for key, value in headers.items():
        wsgi_key = key.upper().replace("-", "_")
        if wsgi_key == "CONTENT_TYPE":
            environ["CONTENT_TYPE"] = value
        elif wsgi_key == "CONTENT_LENGTH":
            pass
        else:
            environ[f"HTTP_{wsgi_key}"] = value

    return environ
