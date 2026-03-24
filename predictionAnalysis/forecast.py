from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


@dataclass
class ForecastMetrics:
    product_id: int
    product_name: str
    mae: float
    rmse: float
    train_days: int
    test_days: int


def make_daily_sales(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to daily demand per product.
    Returns columns: sale_date, product_id, product_name, slot_number, price, capacity, daily_qty
    """
    df = transactions.copy()
    df = df.dropna(subset=["sale_date", "product_id"])
    daily = (
        df.groupby(["sale_date", "product_id", "product_name", "slot_number", "price", "capacity"], as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "daily_qty"})
        .sort_values(["product_id", "sale_date"])
    )
    return daily


def add_time_series_features(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Create lag/rolling features per product:
    - lag_1, lag_7, lag_14
    - roll7_mean
    Also adds day-of-week and month.
    """
    df = daily.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values(["product_id", "sale_date"])

    # Use groupby shift/transform directly so product_id remains a normal column
    # across pandas versions (groupby.apply can alter grouping columns behavior).
    g = df.groupby("product_id", sort=False)
    df["lag_1"] = g["daily_qty"].shift(1)
    df["lag_7"] = g["daily_qty"].shift(7)
    df["lag_14"] = g["daily_qty"].shift(14)
    df["roll7_mean"] = g["daily_qty"].transform(
        lambda s: s.rolling(7, min_periods=1).mean().shift(1)
    )
    df["dow"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    return df


def _time_split(df: pd.DataFrame, test_ratio: float = 0.2):
    dates = np.array(sorted(df["sale_date"].dropna().unique()))
    if len(dates) < 10:
        # not enough data to forecast meaningfully
        return None, None
    cut = int(len(dates) * (1 - test_ratio))
    cut = max(1, min(cut, len(dates) - 1))
    train_dates = set(dates[:cut])
    test_dates = set(dates[cut:])
    train = df[df["sale_date"].isin(train_dates)].copy()
    test = df[df["sale_date"].isin(test_dates)].copy()
    return train, test


def fit_random_forest_forecaster(product_df: pd.DataFrame):
    """
    Fit RandomForestRegressor on lag features for a single product.
    Returns (model, metrics, next_day_prediction_qty or None)
    """
    features = ["lag_1", "lag_7", "lag_14", "roll7_mean", "dow", "month", "is_weekend", "price"]
    usable = product_df.dropna(subset=["daily_qty"]).copy()
    # For lags, drop rows where lags are missing (except rolling mean)
    usable = usable.dropna(subset=["lag_1", "lag_7", "lag_14"]).copy()

    train, test = _time_split(usable)
    if train is None or test is None or train.empty or test.empty:
        return None, None, None

    X_train = train[features]
    y_train = train["daily_qty"]
    X_test = test[features]
    y_test = test["daily_qty"]

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        min_samples_leaf=2,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(mean_squared_error(y_test, preds, squared=False))

    last_row = usable.sort_values("sale_date").iloc[-1]
    next_features = last_row[features].copy()
    # Next day: increment DOW and month if needed (simple approximation)
    next_features["dow"] = int((int(next_features["dow"]) + 1) % 7)
    next_features["is_weekend"] = int(next_features["dow"] >= 5)
    next_pred = float(model.predict(pd.DataFrame([next_features]))[0])
    next_pred = max(0.0, next_pred)
    return model, (mae, rmse, len(train), len(test)), next_pred


def forecast_and_restock(
    daily_features: pd.DataFrame,
    *,
    current_stock_by_product: dict[int, int] | None = None,
    safety_days: int = 2,
):
    """
    Forecast next-day demand per product and recommend restock.

    - Forecast: predicted sales tomorrow
    - Restock recommendation: target_stock = predicted_next_day * (1 + safety_days)
      recommended = max(0, target_stock - current_stock)
    """
    forecasts = []
    metrics_rows: list[ForecastMetrics] = []

    for pid, g in daily_features.groupby("product_id"):
        product_name = str(g["product_name"].iloc[0]) if "product_name" in g.columns else str(pid)
        model, m, next_pred = fit_random_forest_forecaster(g)
        if m is None or next_pred is None:
            continue
        mae, rmse, train_days, test_days = m
        metrics_rows.append(
            ForecastMetrics(
                product_id=int(pid),
                product_name=product_name,
                mae=float(mae),
                rmse=float(rmse),
                train_days=int(train_days),
                test_days=int(test_days),
            )
        )

        # Current stock: use provided mapping or last known row
        current_stock = None
        if current_stock_by_product and int(pid) in current_stock_by_product:
            current_stock = int(current_stock_by_product[int(pid)])
        else:
            if "current_stock" in g.columns:
                try:
                    current_stock = int(g.sort_values("sale_date")["current_stock"].dropna().iloc[-1])
                except Exception:
                    current_stock = 0
            else:
                current_stock = 0

        # Capacity (for clamping)
        try:
            capacity = int(g["capacity"].dropna().iloc[-1])
        except Exception:
            capacity = None

        target = int(np.ceil(next_pred * (1 + safety_days)))
        recommended = max(0, target - current_stock)
        if capacity is not None:
            recommended = min(recommended, max(0, capacity - current_stock))

        forecasts.append(
            {
                "product_id": int(pid),
                "product_name": product_name,
                "predicted_sales_tomorrow": float(round(next_pred, 3)),
                "current_stock": int(current_stock),
                "capacity": int(capacity) if capacity is not None else None,
                "recommended_restock_qty": int(recommended),
            }
        )

    forecast_columns = [
        "product_id",
        "product_name",
        "predicted_sales_tomorrow",
        "current_stock",
        "capacity",
        "recommended_restock_qty",
    ]
    if forecasts:
        forecasts_df = pd.DataFrame(forecasts).sort_values("predicted_sales_tomorrow", ascending=False)
    else:
        forecasts_df = pd.DataFrame(columns=forecast_columns)

    metric_columns = ["product_id", "product_name", "mae", "rmse", "train_days", "test_days"]
    if metrics_rows:
        metrics_df = pd.DataFrame([m.__dict__ for m in metrics_rows]).sort_values("rmse", ascending=True)
    else:
        metrics_df = pd.DataFrame(columns=metric_columns)
    return forecasts_df, metrics_df

