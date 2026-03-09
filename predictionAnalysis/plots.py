from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def plot_monthly_quantity(monthly_df: pd.DataFrame, out_path: Path):
    _ensure_dir(out_path.parent)
    plt.figure(figsize=(9, 4))
    plt.plot(monthly_df["sale_month"], monthly_df["quantity"], marker="o")
    plt.title("Monthly Sales Quantity")
    plt.xlabel("Month")
    plt.ylabel("Quantity sold")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_peak_hours(peak_hours_df: pd.DataFrame, out_path: Path):
    _ensure_dir(out_path.parent)
    plt.figure(figsize=(8, 4))
    x = peak_hours_df["sale_hour"].astype(int)
    y = peak_hours_df["quantity"].astype(int)
    plt.bar([f"{h:02d}:00" for h in x], y)
    plt.title("Peak Purchase Hours (Top)")
    plt.xlabel("Hour")
    plt.ylabel("Quantity sold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

