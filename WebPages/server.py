"""
Flask web server for the Admin Dashboard.
Reads data from the shared vending.db and serves iOS-inspired React web pages.
All API endpoints mirror the desktop admin.py functionality for real-time parity.
"""

import hashlib
import sys
from dataclasses import asdict
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import database as db
from prediction_runtime import run_prediction_analysis
from admin.reports import list_sales_reports

PREDICTION_ANALYSIS_DIR = ROOT_DIR / "predictionAnalysis"
sys.path.insert(0, str(PREDICTION_ANALYSIS_DIR))

app = Flask(__name__)
app.secret_key = "hygiene-vending-admin-secret-key"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Page Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        stored_user, stored_hash = db.get_admin_credentials()
        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if username == stored_user and pwd_hash == stored_hash:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username", "Admin"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── API: Overview Stats ────────────────────────────────────────────

@app.route("/api/overview")
@login_required
def api_overview():
    return jsonify(db.get_admin_overview_stats())


# ── API: Charts ────────────────────────────────────────────────────

@app.route("/api/sales-trend")
@login_required
def api_sales_trend():
    days = request.args.get("days", 15, type=int)
    points = db.get_sales_trend_data(days)
    for p in points:
        if "date" in p:
            p["date"] = str(p["date"])
    return jsonify(points)


@app.route("/api/monthly-sales")
@login_required
def api_monthly_sales():
    months = request.args.get("months", 6, type=int)
    return jsonify(db.get_monthly_sales_data(months))


@app.route("/api/top-products")
@login_required
def api_top_products():
    limit = request.args.get("limit", None, type=int)
    return jsonify(db.get_top_selling_products(limit))


@app.route("/api/low-stock")
@login_required
def api_low_stock():
    return jsonify(db.get_low_stock_chart_data())


# ── API: Products ──────────────────────────────────────────────────

@app.route("/api/products")
@login_required
def api_products():
    return jsonify([dict(p) for p in db.get_all_products()])


@app.route("/api/products/<int:product_id>/restock", methods=["POST"])
@login_required
def api_restock_product(product_id):
    data = request.get_json(force=True)
    amount = data.get("amount", 0)
    new_price = data.get("new_price")
    db.restock_product(product_id, amount, new_price)
    return jsonify({"status": "ok"})


# ── API: RFID Users ───────────────────────────────────────────────

@app.route("/api/rfid-users")
@login_required
def api_rfid_users():
    return jsonify([dict(u) for u in db.get_all_rfid_users()])


@app.route("/api/rfid-users/<int:user_id>/role", methods=["PUT"])
@login_required
def api_update_rfid_role(user_id):
    data = request.get_json(force=True)
    role = data.get("role", "customer")
    db.update_rfid_user_role(user_id, role)
    return jsonify({"status": "ok"})


# ── API: Cash Pulse Settings ──────────────────────────────────────

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
        db.set_hardware_setting("coin_pulse_value", str(coin))
    if bill is not None:
        db.set_hardware_setting("bill_pulse_value", str(bill))
    return jsonify({"status": "ok"})


# ── API: Prediction Analysis ──────────────────────────────────────

@app.route("/api/prediction", methods=["POST"])
@login_required
def api_prediction():
    db_path = ROOT_DIR / "vending.db"
    results, summary = run_prediction_analysis(db_path=db_path)
    return jsonify({
        "results": [asdict(r) for r in results],
        "summary": asdict(summary),
    })


# ── API: Sales Reports ────────────────────────────────────────────

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


# ── API: Admin Credentials ────────────────────────────────────────

@app.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json(force=True)
    new_user = data.get("username", "").strip()
    new_pass = data.get("password", "").strip()
    if not new_user or not new_pass:
        return jsonify({"status": "error", "message": "Fields cannot be empty."}), 400
    if len(new_pass) < 4:
        return jsonify({"status": "error", "message": "Password must be at least 4 characters."}), 400
    db.update_admin_credentials(new_user, new_pass)
    session["username"] = new_user
    return jsonify({"status": "ok"})


# ── API: Full Prediction Analysis (predictionAnalysis pipeline) ────

@app.route("/api/analysis/run", methods=["POST"])
@login_required
def api_analysis_run():
    """Run the full ML prediction analysis pipeline and return all results."""
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
                on="product_id",
                how="left",
            ))
            forecasts_df, metrics_df = forecast_and_restock(daily_feat)
            forecasts_list = forecasts_df.to_dict(orient="records") if not forecasts_df.empty else []
            metrics_list = metrics_df.to_dict(orient="records") if not metrics_df.empty else []

        return jsonify({
            "status": "ok",
            "insights": {
                "top_products": top_products,
                "peak_hours": peak_hours,
                "weekday_totals": weekday_totals,
                "monthly_qty": monthly_qty,
            },
            "forecasts": forecasts_list,
            "metrics": metrics_list,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── API: Philippines Time ──────────────────────────────────────────

@app.route("/api/time/ph")
@login_required
def api_ph_time():
    from datetime import datetime, timezone, timedelta
    ph_tz = timezone(timedelta(hours=8))
    now = datetime.now(ph_tz)
    return jsonify({
        "datetime": now.isoformat(),
        "time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%A, %B %d, %Y"),
    })


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
