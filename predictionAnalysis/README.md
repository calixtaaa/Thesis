## Prediction Analysis (ML)

This folder contains the code for **Prediction Analysis** based on your vending machine data (`vending.db`).

### Goals (from your prompt)
- Predict **product demand** and **future stock requirements**
- Find **most frequently purchased products**
- Identify **peak purchase times/days**
- Generate **low-stock alerts before depletion**
- Produce **restock recommendations** (avoid stockouts, minimize excess)

### What the scripts generate
Outputs are written to `predictionAnalysis/outputs/`:
- `dataset_transactions.csv` (raw joined dataset)
- `daily_sales.csv` (daily demand per product)
- `forecast_next_day.csv` (predicted sales tomorrow per product)
- `restock_recommendations.csv` (recommended restock quantity per product)
- `insights.txt` (top products + peak times)
- `charts/` (plots: daily/monthly trends, peaks, etc.)

### Tools used
- Python
- Pandas
- Scikit-learn
- Matplotlib
- SQLite (reads `vending.db` directly; works alongside your Excel export)

### Install dependencies

```bash
pip install -r predictionAnalysis/requirements.txt
```

### Run

```bash
python predictionAnalysis/run_all.py
```

### Notes
- The model uses **Random Forest + time-series lag features** (lags 1/7/14 days + rolling mean).
- Evaluation metrics: **MAE** and **RMSE** (time-based split).

