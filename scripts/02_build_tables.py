"""
RxIQ — Build normalized dimension & fact tables from pharma_clean.csv
Outputs CSVs ready for MySQL LOAD DATA INFILE (see sql/02_load.sql)
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "data" / "processed" / "pharma_clean.csv"
OUT_DIR = BASE / "data" / "processed" / "tables"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    df = pd.read_csv(IN_PATH, parse_dates=["date"])

    # ---------------------------------------------------------
    # dim_distributor
    # ---------------------------------------------------------
    dim_distributor = (
        df[["distributor"]]
        .drop_duplicates()
        .rename(columns={"distributor": "distributor_name"})
        .reset_index(drop=True)
    )
    dim_distributor["distributor_id"] = dim_distributor.index + 1

    # ---------------------------------------------------------
    # dim_customer
    # ---------------------------------------------------------
    dim_customer = (
        df[["customer_name", "city", "country", "latitude", "longitude",
            "channel", "sub_channel"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_customer["customer_id"] = dim_customer.index + 1

    # ---------------------------------------------------------
    # dim_product
    # ---------------------------------------------------------
    dim_product = (
        df[["product_name", "product_class"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_product["product_id"] = dim_product.index + 1

    # ---------------------------------------------------------
    # dim_sales_rep
    # ---------------------------------------------------------
    dim_sales_rep = (
        df[["sales_rep", "manager", "sales_team"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_sales_rep["rep_id"] = dim_sales_rep.index + 1

    # ---------------------------------------------------------
    # dim_date
    # ---------------------------------------------------------
    dim_date = (
        df[["date", "month", "month_num", "year"]]
        .drop_duplicates()
        .reset_index(drop=True)
        .rename(columns={"date": "full_date", "month": "month_name"})
    )
    dim_date["quarter"] = ((dim_date["month_num"] - 1) // 3) + 1
    dim_date["date_id"] = dim_date.index + 1
    dim_date = dim_date[["date_id", "full_date", "month_name", "month_num", "quarter", "year"]]

    # ---------------------------------------------------------
    # fact_sales  (join back to get surrogate keys)
    # ---------------------------------------------------------
    fact = df.merge(dim_distributor, left_on="distributor", right_on="distributor_name") \
             .merge(dim_customer, on=["customer_name", "city", "country", "latitude",
                                       "longitude", "channel", "sub_channel"]) \
             .merge(dim_product, on=["product_name", "product_class"]) \
             .merge(dim_sales_rep, on=["sales_rep", "manager", "sales_team"]) \
             .merge(dim_date[["date_id", "full_date"]], left_on="date", right_on="full_date")

    fact_sales = fact[["distributor_id", "customer_id", "product_id", "rep_id",
                        "date_id", "quantity", "price", "sales"]].reset_index(drop=True)
    fact_sales["sale_id"] = fact_sales.index + 1
    fact_sales = fact_sales[["sale_id", "distributor_id", "customer_id", "product_id",
                              "rep_id", "date_id", "quantity", "price", "sales"]]

    # ---------------------------------------------------------
    # Save all tables
    # ---------------------------------------------------------
    dim_distributor[["distributor_id", "distributor_name"]].to_csv(
        OUT_DIR / "dim_distributor.csv", index=False)
    dim_customer[["customer_id", "customer_name", "city", "country", "latitude",
                  "longitude", "channel", "sub_channel"]].to_csv(
        OUT_DIR / "dim_customer.csv", index=False)
    dim_product[["product_id", "product_name", "product_class"]].to_csv(
        OUT_DIR / "dim_product.csv", index=False)
    dim_sales_rep[["rep_id", "sales_rep", "manager", "sales_team"]].to_csv(
        OUT_DIR / "dim_sales_rep.csv", index=False)
    dim_date.to_csv(OUT_DIR / "dim_date.csv", index=False)
    fact_sales.to_csv(OUT_DIR / "fact_sales.csv", index=False)

    print("Table row counts:")
    print(f"  dim_distributor : {len(dim_distributor)}")
    print(f"  dim_customer    : {len(dim_customer)}")
    print(f"  dim_product     : {len(dim_product)}")
    print(f"  dim_sales_rep   : {len(dim_sales_rep)}")
    print(f"  dim_date        : {len(dim_date)}")
    print(f"  fact_sales      : {len(fact_sales)}")
    print(f"\nSource cleaned rows: {len(df)}  ->  fact_sales rows: {len(fact_sales)}")
    if len(fact_sales) != len(df):
        print("  WARNING: row count mismatch — check join keys for duplicates/nulls")

    print(f"\nAll table CSVs saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
