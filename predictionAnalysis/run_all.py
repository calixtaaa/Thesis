from __future__ import annotations

from pathlib import Path

import pandas as pd

from extract_dataset import extract_transactions_dataset, OUTPUTS_DIR
from forecast import make_daily_sales, add_time_series_features, forecast_and_restock
from insights import compute_insights, save_insights_txt
from plots import plot_monthly_quantity, plot_peak_hours


BASE_DIR = Path(__file__).resolve().parents[1]


def main():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    charts_dir = OUTPUTS_DIR / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    tx = extract_transactions_dataset()
    tx_out = OUTPUTS_DIR / "dataset_transactions.csv"
    tx.to_csv(tx_out, index=False)

    # Insights
    ins = compute_insights(tx)
    save_insights_txt(ins, OUTPUTS_DIR / "insights.txt")
    plot_monthly_quantity(ins["monthly_qty"], charts_dir / "monthly_quantity.png")
    plot_peak_hours(ins["peak_hours"], charts_dir / "peak_hours.png")

    # Forecasting
    daily = make_daily_sales(tx)
    daily_out = OUTPUTS_DIR / "daily_sales.csv"
    daily.to_csv(daily_out, index=False)

    daily_feat = add_time_series_features(daily.merge(
        tx[["product_id", "current_stock"]].dropna().drop_duplicates(subset=["product_id"], keep="last"),
        on="product_id",
        how="left",
    ))
    forecasts_df, metrics_df = forecast_and_restock(daily_feat)

    forecasts_path = OUTPUTS_DIR / "forecast_next_day.csv"
    restock_path = OUTPUTS_DIR / "restock_recommendations.csv"
    metrics_path = OUTPUTS_DIR / "model_metrics.csv"

    forecasts_df.to_csv(forecasts_path, index=False)
    # Restock recommendation is included in forecasts_df; also save separately for convenience
    forecasts_df[["product_id", "product_name", "current_stock", "capacity", "predicted_sales_tomorrow", "recommended_restock_qty"]].to_csv(
        restock_path, index=False
    )
    metrics_df.to_csv(metrics_path, index=False)

    print("Saved outputs:")
    for p in [tx_out, daily_out, forecasts_path, restock_path, metrics_path, OUTPUTS_DIR / "insights.txt"]:
        print(f"- {p}")
    print(f"- {charts_dir / 'monthly_quantity.png'}")
    print(f"- {charts_dir / 'peak_hours.png'}")


if __name__ == "__main__":
    main()

