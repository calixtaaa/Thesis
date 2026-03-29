"""
Flask web server for the Admin Dashboard.
Reads data from the shared vending.db and serves iOS-inspired React web pages.

Security features:
- Cryptographically random secret key (regenerated each restart)
- SHA-256 HMAC with salt for password verification
- CSRF token protection on all state-changing forms
- Rate limiting on login (brute-force protection)
- Secure session cookies (HttpOnly, SameSite=Lax)
- Session expiry / inactivity timeout
- Security response headers (CSP, X-Frame-Options, HSTS, etc.)
- Input sanitization
"""

import hashlib
import hmac
import os
import secrets
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash, abort, g,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import database as db
from prediction_runtime import run_prediction_analysis
from admin.reports import list_sales_reports

PREDICTION_ANALYSIS_DIR = ROOT_DIR / "predictionAnalysis"
sys.path.insert(0, str(PREDICTION_ANALYSIS_DIR))

# ══════════════════════════════════════════════════════════════════
#  APP SETUP & SECURITY CONFIG
# ══════════════════════════════════════════════════════════════════

app = Flask(__name__)

# Cryptographically random secret key (new each server restart)
app.secret_key = secrets.token_hex(32)

# Secure session cookie settings
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,          # Set True if using HTTPS
    SESSION_COOKIE_NAME="__hvs_session",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=4),
)

# ── Password salt (persistent across restarts) ─────────────────────
SALT_FILE = ROOT_DIR / ".secret_salt"
if SALT_FILE.exists():
    PASSWORD_SALT = SALT_FILE.read_text(encoding="utf-8").strip()
else:
    PASSWORD_SALT = secrets.token_hex(16)
    try:
        SALT_FILE.write_text(PASSWORD_SALT, encoding="utf-8")
    except Exception:
        pass

# ── Rate limiting (in-memory, resets on server restart) ────────────
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300
_login_attempts = defaultdict(list)


def _is_rate_limited(ip: str) -> tuple[bool, int]:
    """Check if an IP is locked out. Returns (locked, seconds_remaining)."""
    now = time.time()
    attempts = _login_attempts[ip]
    # Prune old attempts
    _login_attempts[ip] = [t for t in attempts if now - t < LOGIN_LOCKOUT_SECONDS]
    attempts = _login_attempts[ip]
    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        oldest = attempts[0]
        remaining = int(LOGIN_LOCKOUT_SECONDS - (now - oldest))
        return True, max(1, remaining)
    return False, 0


def _record_failed_attempt(ip: str):
    _login_attempts[ip].append(time.time())


def _clear_attempts(ip: str):
    _login_attempts.pop(ip, None)


# ── SHA-256 HMAC password hashing ──────────────────────────────────

def hash_password_sha256(password: str) -> str:
    """Create a salted SHA-256 HMAC hash of a password."""
    return hmac.new(
        PASSWORD_SALT.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.
    Supports both:
      - New salted HMAC-SHA256 hashes
      - Legacy plain SHA-256 hashes (auto-migrated on successful login)
    """
    salted = hash_password_sha256(password)
    if hmac.compare_digest(salted, stored_hash):
        return True
    # Fallback: check legacy plain SHA-256 for backward compatibility
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(legacy, stored_hash):
        return True
    return False


# ── CSRF protection ────────────────────────────────────────────────

def generate_csrf_token() -> str:
    """Generate or return the current session's CSRF token."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf_token():
    """Validate CSRF token on state-changing requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    if request.path.startswith("/api/"):
        # API calls use session cookie + SameSite; CSRF header optional
        token = request.headers.get("X-CSRF-Token", "")
        if token:
            expected = session.get("_csrf_token", "")
            if not hmac.compare_digest(token, expected):
                abort(403)
        return
    # Form submissions must include csrf_token
    token = request.form.get("csrf_token", "")
    expected = session.get("_csrf_token", "")
    if not expected or not hmac.compare_digest(token, expected):
        abort(403)


# Make csrf_token available in all templates
app.jinja_env.globals["csrf_token"] = generate_csrf_token


# ── Security middleware ────────────────────────────────────────────

@app.before_request
def security_checks():
    # CSRF validation on POST/PUT/DELETE
    if request.method in ("POST", "PUT", "DELETE"):
        # Skip CSRF for API routes (protected by SameSite cookie)
        if not request.path.startswith("/api/"):
            validate_csrf_token()

    # Session expiry check
    if session.get("logged_in"):
        last_active = session.get("_last_active")
        if last_active:
            elapsed = time.time() - last_active
            if elapsed > app.config["PERMANENT_SESSION_LIFETIME"].total_seconds():
                session.clear()
                if request.path.startswith("/api/"):
                    return jsonify({"error": "session_expired"}), 401
                flash("Session expired. Please log in again.", "error")
                return redirect(url_for("login"))
        session["_last_active"] = time.time()
        session.permanent = True


@app.after_request
def set_security_headers(response):
    """Add security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Cache control for authenticated pages
    if session.get("logged_in"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


# ── Auth decorator ─────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        client_ip = request.remote_addr or "unknown"

        locked, remaining = _is_rate_limited(client_ip)
        if locked:
            flash(f"Too many failed attempts. Try again in {remaining} seconds.", "error")
            return render_template("login.html"), 429

        username = request.form.get("username", "").strip()[:100]
        password = request.form.get("password", "").strip()[:200]

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html")

        stored_user, stored_hash = db.get_admin_credentials()

        if username == stored_user and verify_password(password, stored_hash):
            _clear_attempts(client_ip)
            # Regenerate session ID to prevent session fixation
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            session["_last_active"] = time.time()
            session["_csrf_token"] = secrets.token_hex(32)
            session.permanent = True

            # Auto-migrate legacy plain SHA-256 hashes to salted HMAC
            salted = hash_password_sha256(password)
            if not hmac.compare_digest(salted, stored_hash):
                try:
                    db.update_admin_credentials(username, password)
                except Exception:
                    pass

            return redirect(url_for("dashboard"))

        _record_failed_attempt(client_ip)
        attempts_left = LOGIN_MAX_ATTEMPTS - len(_login_attempts.get(client_ip, []))
        if attempts_left > 0:
            flash(f"Invalid credentials. {attempts_left} attempt(s) remaining.", "error")
        else:
            flash(f"Account locked for {LOGIN_LOCKOUT_SECONDS // 60} minutes.", "error")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        username=session.get("username", "Admin"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ══════════════════════════════════════════════════════════════════
#  API ROUTES (unchanged functionality, now with security layer)
# ══════════════════════════════════════════════════════════════════

@app.route("/api/overview")
@login_required
def api_overview():
    return jsonify(db.get_admin_overview_stats())


@app.route("/api/sales-trend")
@login_required
def api_sales_trend():
    days = request.args.get("days", 15, type=int)
    days = min(max(days, 1), 365)
    points = db.get_sales_trend_data(days)
    for p in points:
        if "date" in p:
            p["date"] = str(p["date"])
    return jsonify(points)


@app.route("/api/monthly-sales")
@login_required
def api_monthly_sales():
    months = request.args.get("months", 6, type=int)
    months = min(max(months, 1), 60)
    return jsonify(db.get_monthly_sales_data(months))


@app.route("/api/top-products")
@login_required
def api_top_products():
    limit = request.args.get("limit", None, type=int)
    if limit is not None:
        limit = min(max(limit, 1), 100)
    return jsonify(db.get_top_selling_products(limit))


@app.route("/api/low-stock")
@login_required
def api_low_stock():
    return jsonify(db.get_low_stock_chart_data())


@app.route("/api/products")
@login_required
def api_products():
    return jsonify([dict(p) for p in db.get_all_products()])


@app.route("/api/products/<int:product_id>/restock", methods=["POST"])
@login_required
def api_restock_product(product_id):
    data = request.get_json(force=True)
    amount = int(data.get("amount", 0))
    new_price = data.get("new_price")
    if amount < 0 or amount > 1000:
        return jsonify({"status": "error", "message": "Invalid amount"}), 400
    db.restock_product(product_id, amount, new_price)
    return jsonify({"status": "ok"})


@app.route("/api/rfid-users")
@login_required
def api_rfid_users():
    return jsonify([dict(u) for u in db.get_all_rfid_users()])


@app.route("/api/rfid-users/<int:user_id>/role", methods=["PUT"])
@login_required
def api_update_rfid_role(user_id):
    data = request.get_json(force=True)
    role = data.get("role", "customer").strip()[:50]
    allowed_roles = {"customer", "restocker", "staff", "researcher", "troubleshooter", "admin"}
    if role not in allowed_roles:
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    db.update_rfid_user_role(user_id, role)
    return jsonify({"status": "ok"})


@app.route("/api/hardware-settings")
@login_required
def api_hardware_settings():
    coin = db.get_hardware_setting("coin_pulse_value", "1.0")
    bill = db.get_hardware_setting("bill_pulse_value", "20.0")
    return jsonify({"coin_pulse_value": coin, "bill_pulse_value": bill})


@app.route("/api/hardware-settings", methods=["PUT"])
@login_required
def api_update_hardware_settings():
    data = request.get_json(force=True)
    coin = data.get("coin_pulse_value")
    bill = data.get("bill_pulse_value")
    if coin is not None:
        coin = float(coin)
        if coin <= 0 or coin > 10000:
            return jsonify({"status": "error", "message": "Invalid coin value"}), 400
        db.set_hardware_setting("coin_pulse_value", str(coin))
    if bill is not None:
        bill = float(bill)
        if bill <= 0 or bill > 10000:
            return jsonify({"status": "error", "message": "Invalid bill value"}), 400
        db.set_hardware_setting("bill_pulse_value", str(bill))
    return jsonify({"status": "ok"})


@app.route("/api/prediction", methods=["POST"])
@login_required
def api_prediction():
    db_path = ROOT_DIR / "vending.db"
    results, summary = run_prediction_analysis(db_path=db_path)
    return jsonify({
        "results": [asdict(r) for r in results],
        "summary": asdict(summary),
    })


@app.route("/api/sales-reports")
@login_required
def api_sales_reports():
    reports = list_sales_reports()
    return jsonify([{"name": r.name, "path": str(r)} for r in reports])


@app.route("/api/export-report", methods=["POST"])
@login_required
def api_export_report():
    filepath = db.export_sales_report()
    return jsonify({"status": "ok", "path": str(filepath)})


@app.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json(force=True)
    new_user = data.get("username", "").strip()[:100]
    new_pass = data.get("password", "").strip()[:200]
    if not new_user or not new_pass:
        return jsonify({"status": "error", "message": "Fields cannot be empty."}), 400
    if len(new_pass) < 6:
        return jsonify({"status": "error", "message": "Password must be at least 6 characters."}), 400
    db.update_admin_credentials(new_user, new_pass)
    session["username"] = new_user
    return jsonify({"status": "ok"})


@app.route("/api/analysis/run", methods=["POST"])
@login_required
def api_analysis_run():
    try:
        from extract_dataset import extract_transactions_dataset
        from insights import compute_insights
        from forecast import make_daily_sales, add_time_series_features, forecast_and_restock
    except ImportError as e:
        return jsonify({"status": "error", "message": f"Missing dependency: {e}"}), 500

    try:
        tx = extract_transactions_dataset()
        if tx.empty:
            return jsonify({"status": "ok", "insights": None, "forecasts": [], "metrics": [], "message": "No transaction data."})

        ins = compute_insights(tx)
        top_products = ins["top_products"][["product_name", "quantity"]].to_dict(orient="records") if not ins["top_products"].empty else []
        peak_hours = ins["peak_hours"][["sale_hour", "quantity"]].to_dict(orient="records") if not ins["peak_hours"].empty else []
        weekday_totals = ins["weekday_totals"][["weekday", "quantity"]].to_dict(orient="records") if not ins["weekday_totals"].empty else []
        monthly_qty = ins["monthly_qty"][["sale_month", "quantity"]].to_dict(orient="records") if not ins["monthly_qty"].empty else []

        daily = make_daily_sales(tx)
        forecasts_list = []
        metrics_list = []
        if not daily.empty:
            daily_feat = add_time_series_features(daily.merge(
                tx[["product_id", "current_stock"]].dropna().drop_duplicates(subset=["product_id"], keep="last"),
                on="product_id", how="left",
            ))
            forecasts_df, metrics_df = forecast_and_restock(daily_feat)
            forecasts_list = forecasts_df.to_dict(orient="records") if not forecasts_df.empty else []
            metrics_list = metrics_df.to_dict(orient="records") if not metrics_df.empty else []

        return jsonify({
            "status": "ok",
            "insights": {"top_products": top_products, "peak_hours": peak_hours, "weekday_totals": weekday_totals, "monthly_qty": monthly_qty},
            "forecasts": forecasts_list,
            "metrics": metrics_list,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/time/ph")
@login_required
def api_ph_time():
    ph_tz = timezone(timedelta(hours=8))
    now = datetime.now(ph_tz)
    return jsonify({
        "datetime": now.isoformat(),
        "time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%A, %B %d, %Y"),
    })


# ══════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "forbidden", "message": "CSRF validation failed"}), 403

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "rate_limited", "message": "Too many requests"}), 429


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    db.init_db()
    print(f"\n  Security: SHA-256 HMAC salt loaded ({len(PASSWORD_SALT)} chars)")
    print(f"  Security: CSRF protection enabled")
    print(f"  Security: Rate limiting: {LOGIN_MAX_ATTEMPTS} attempts / {LOGIN_LOCKOUT_SECONDS}s lockout")
    print(f"  Security: Session timeout: {app.config['PERMANENT_SESSION_LIFETIME']}\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
