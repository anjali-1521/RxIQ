"""
RxIQ — Forecasting Model (Step 5)
Predicts next-month sales per rep using lag/rolling features + Random Forest.
Mirrors SupplyIQ's Random Forest approach, adapted for a regression/forecasting task.

Input : data/processed/pharma_clean.csv
Output: reports/forecasting_report.txt
        data/processed/rep_month_predictions.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "data" / "processed" / "pharma_clean.csv"
OUT_PRED = BASE / "data" / "processed" / "rep_month_predictions.csv"
REPORT_PATH = BASE / "reports" / "forecasting_report.txt"

report_lines = []


def log(msg):
    print(msg)
    report_lines.append(str(msg))


def build_features(monthly: pd.DataFrame) -> pd.DataFrame:
    monthly = monthly.sort_values(["sales_rep", "date"]).copy()

    # Target: next month's sales for this rep
    monthly["target_next_month_sales"] = monthly.groupby("sales_rep")["sales"].shift(-1)

    # Lag features (this month, 1/2/3 months ago)
    for lag in [1, 2, 3]:
        monthly[f"lag_{lag}"] = monthly.groupby("sales_rep")["sales"].shift(lag)

    # Rolling mean (3-month trailing average, excluding current month via shift)
    monthly["rolling_mean_3"] = (
        monthly.groupby("sales_rep")["sales"]
        .shift(1)
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
    )

    # Calendar features
    monthly["month_num"] = monthly["date"].dt.month
    monthly["quarter"] = monthly["date"].dt.quarter
    monthly["year"] = monthly["date"].dt.year

    # Team one-hot
    monthly = pd.get_dummies(monthly, columns=["sales_team"], prefix="team")

    return monthly


def main():
    df = pd.read_csv(IN_PATH, parse_dates=["date"])

    log("=" * 60)
    log("RxIQ FORECASTING MODEL REPORT")
    log("=" * 60)

    monthly = df.groupby(["sales_rep", "sales_team", "date"])["sales"].sum().reset_index()
    log(f"\nAggregated to rep-month level: {monthly.shape[0]} rows "
        f"({monthly['sales_rep'].nunique()} reps x {monthly['date'].nunique()} months)")

    feat = build_features(monthly)

    # Drop rows without enough lag history (first 3 months per rep) or no target (last month per rep)
    feature_cols = ["lag_1", "lag_2", "lag_3", "rolling_mean_3", "month_num", "quarter", "year"] + \
                   [c for c in feat.columns if c.startswith("team_")]

    model_df = feat.dropna(subset=feature_cols + ["target_next_month_sales"]).copy()
    log(f"\nRows usable for modeling after dropping warm-up/edge rows: {len(model_df)}")
    log(f"(13 reps x 48 months = 624 total; lose first 3 + last 1 month per rep = 13*4 = 52 rows)")

    X = model_df[feature_cols]
    y = model_df["target_next_month_sales"]

    # Time-based split: train on 2017-2019, test on 2020
    train_mask = model_df["date"] < "2020-01-01"
    test_mask = model_df["date"] >= "2020-01-01"

    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]

    log(f"\nTrain rows: {len(X_train)} (2017-2019)")
    log(f"Test rows:  {len(X_test)} (2020)")

    # --- Baseline: naive forecast (predict next month = this month's lag_1) ---
    naive_pred = X_test["lag_1"]
    naive_mae = mean_absolute_error(y_test, naive_pred)
    naive_rmse = np.sqrt(mean_squared_error(y_test, naive_pred))
    naive_r2 = r2_score(y_test, naive_pred)
    log(f"\n--- Baseline (naive: predict = last month's sales) ---")
    log(f"MAE:  {naive_mae:,.0f}")
    log(f"RMSE: {naive_rmse:,.0f}")
    log(f"R2:   {naive_r2:.4f}")

    # --- Linear Regression ---
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    lr_mae = mean_absolute_error(y_test, lr_pred)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
    lr_r2 = r2_score(y_test, lr_pred)
    log(f"\n--- Linear Regression ---")
    log(f"MAE:  {lr_mae:,.0f}")
    log(f"RMSE: {lr_rmse:,.0f}")
    log(f"R2:   {lr_r2:.4f}")

    # --- Random Forest Regressor ---
    rf = RandomForestRegressor(
        n_estimators=300, max_depth=6, min_samples_leaf=3,
        random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    rf_r2 = r2_score(y_test, rf_pred)
    log(f"\n--- Random Forest Regressor ---")
    log(f"MAE:  {rf_mae:,.0f}")
    log(f"RMSE: {rf_rmse:,.0f}")
    log(f"R2:   {rf_r2:.4f}")

    # Feature importance
    importances = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    log(f"\n--- Random Forest Feature Importance ---")
    log(importances.to_string())

    # Model comparison summary
    log(f"\n--- Model Comparison (test set = 2020) ---")
    comparison = pd.DataFrame({
        "Model": ["Naive (last month)", "Linear Regression", "Random Forest"],
        "MAE": [naive_mae, lr_mae, rf_mae],
        "RMSE": [naive_rmse, lr_rmse, rf_rmse],
        "R2": [naive_r2, lr_r2, rf_r2],
    })
    log(comparison.to_string(index=False))

    best_model = comparison.loc[comparison["RMSE"].idxmin(), "Model"]
    log(f"\nBest model by RMSE: {best_model}")

    # Save predictions for inspection / dashboard use
    result = model_df.loc[test_mask, ["sales_rep", "date"]].copy()
    result["actual_next_month_sales"] = y_test.values
    result["predicted_rf"] = rf_pred
    result["predicted_lr"] = lr_pred
    result["predicted_naive"] = naive_pred.values
    result["abs_error_rf"] = (result["actual_next_month_sales"] - result["predicted_rf"]).abs()
    result.to_csv(OUT_PRED, index=False)
    log(f"\nPredictions saved to: {OUT_PRED}")

    REPORT_PATH.write_text("\n".join(report_lines))
    log(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
