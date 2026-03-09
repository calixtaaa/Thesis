from __future__ import annotations

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = BASE_DIR / "predictionAnalysis" / "outputs"


def compute_insights(transactions: pd.DataFrame) -> dict:
    df = transactions.copy()
    df = df.dropna(subset=["timestamp"])

    # Most purchased products
    top_products = (
        df.groupby(["product_id", "product_name"], as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
        .head(10)
    )

    # Peak hours and weekdays
    by_hour = (
        df.groupby("sale_hour", as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
        .head(10)
    )
    by_weekday = (
        df.groupby("sale_weekday", as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
    )
    # 0=Sunday in SQLite strftime('%w'), map to labels
    weekday_map = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
    by_weekday["weekday"] = by_weekday["sale_weekday"].map(weekday_map)

    # Monthly trend
    monthly = (
        df.groupby("sale_month", as_index=False)["quantity"]
        .sum()
        .sort_values("sale_month")
    )

    return {
        "top_products": top_products,
        "peak_hours": by_hour,
        "weekday_totals": by_weekday,
        "monthly_qty": monthly,
    }


def save_insights_txt(ins: dict, out_path: Path):
    lines = []
    lines.append("Prediction Analysis Insights")
    lines.append("")
    lines.append("Most frequently purchased products (Top 10):")
    for _, r in ins["top_products"].iterrows():
        lines.append(f"- {r['product_name']}: {int(r['quantity'])}")
    lines.append("")
    lines.append("Peak purchase hours (Top 10):")
    for _, r in ins["peak_hours"].iterrows():
        lines.append(f"- {int(r['sale_hour']):02d}:00 → {int(r['quantity'])} items")
    lines.append("")
    lines.append("Purchases by weekday:")
    for _, r in ins["weekday_totals"].iterrows():
        lines.append(f"- {r['weekday']}: {int(r['quantity'])} items")
    lines.append("")
    lines.append("Monthly sales quantity trend:")
    for _, r in ins["monthly_qty"].iterrows():
        lines.append(f"- {r['sale_month']}: {int(r['quantity'])} items")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    from .extract_dataset import extract_transactions_dataset

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    tx = extract_transactions_dataset()
    ins = compute_insights(tx)
    out = OUTPUTS_DIR / "insights.txt"
    save_insights_txt(ins, out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()

