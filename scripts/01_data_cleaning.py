"""
RxIQ — Data Cleaning & Preprocessing
Source: Pharmaceutical Company Wholesale-Retail Data (Foresight BI / Kaggle)
Input : data/raw/pharma-data.csv
Output: data/processed/pharma_clean.csv
        reports/data_quality_report.txt
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "pharma-data.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "pharma_clean.csv"
REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "data_quality_report.txt"

report_lines = []


def log(msg):
    print(msg)
    report_lines.append(str(msg))


def main():
    log("=" * 60)
    log("RxIQ DATA CLEANING REPORT")
    log("=" * 60)

    df = pd.read_csv(RAW_PATH)
    log(f"\nRaw shape: {df.shape}")

    # -----------------------------------------------------------
    # 1. Standardize column names (snake_case, no spaces)
    # -----------------------------------------------------------
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    log(f"\nStandardized columns: {list(df.columns)}")

    # -----------------------------------------------------------
    # 2. Strip whitespace from all string/object columns
    #    (Distributor names had trailing spaces, e.g. 'Gottlieb-Cruickshank  ')
    # -----------------------------------------------------------
    str_cols = df.select_dtypes(include="object").columns.tolist() + \
               [c for c in df.columns if df[c].dtype.name in ("string",)]
    str_cols = list(set(str_cols))
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    log(f"\nStripped whitespace on columns: {str_cols}")

    # -----------------------------------------------------------
    # 3. Drop exact duplicate rows
    # -----------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates()
    log(f"\nDropped duplicate rows: {before - len(df)} (before={before}, after={len(df)})")

    # -----------------------------------------------------------
    # 4. Handle zero-activity rows (Quantity=0 / Sales=0)
    #    These look like cancelled/returned orders. We separate
    #    them out rather than silently deleting, so they can be
    #    analyzed separately if needed.
    # -----------------------------------------------------------
    zero_activity = df[(df["quantity"] <= 0) | (df["sales"] <= 0)]
    log(f"\nZero-activity rows found: {len(zero_activity)} ({len(zero_activity)/len(df):.2%})")

    zero_path = REPORT_PATH.parent / "zero_activity_rows.csv"
    zero_activity.to_csv(zero_path, index=False)
    log(f"Saved zero-activity rows separately to: {zero_path.name}")

    df = df[(df["quantity"] > 0) & (df["sales"] > 0)].copy()
    log(f"Remaining rows after removing zero-activity: {len(df)}")

    # -----------------------------------------------------------
    # 5. Sanity check: Sales == Price * Quantity
    # -----------------------------------------------------------
    mismatch = (df["sales"] - df["price"] * df["quantity"]).abs() > 0.01
    log(f"\nRows where Sales != Price * Quantity: {mismatch.sum()}")

    # -----------------------------------------------------------
    # 6. Type fixes
    # -----------------------------------------------------------
    df["quantity"] = df["quantity"].astype(int)
    df["price"] = df["price"].astype(float)
    df["sales"] = df["sales"].astype(float)
    df["year"] = df["year"].astype(int)

    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)
    df["month_num"] = df["month"].cat.codes + 1

    # Build a proper date column (first of month) for time-series work
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month_num"], day=1)
    )

    # -----------------------------------------------------------
    # 7. Rename a few columns for clarity / SQL-friendliness
    # -----------------------------------------------------------
    df = df.rename(columns={
        "name_of_sales_rep": "sales_rep",
    })

    # -----------------------------------------------------------
    # 8. Final null check
    # -----------------------------------------------------------
    nulls = df.isnull().sum()
    log(f"\nFinal null check:\n{nulls[nulls > 0] if nulls.sum() else 'None'}")

    # -----------------------------------------------------------
    # 9. Summary stats for the report
    # -----------------------------------------------------------
    log(f"\nFinal shape: {df.shape}")
    log(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    log(f"Countries: {df['country'].unique().tolist()}")
    log(f"Sales teams: {df['sales_team'].unique().tolist()}")
    log(f"# Sales reps: {df['sales_rep'].nunique()}")
    log(f"# Distributors: {df['distributor'].nunique()}")
    log(f"# Cities: {df['city'].nunique()}")
    log(f"# Products: {df['product_name'].nunique()}")
    log(f"Total Sales (cleaned): {df['sales'].sum():,.0f}")

    # -----------------------------------------------------------
    # Save outputs
    # -----------------------------------------------------------
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    log(f"\nCleaned dataset saved to: {OUT_PATH}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines))
    log(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
