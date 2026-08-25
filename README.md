# RxIQ — Pharma Sales Force Effectiveness & Territory Analytics

Portfolio project analyzing rep/territory performance for a pharma wholesale-retail
business, built for ZS Associates-style commercial analytics applications.

## Folder structure

```
RxIQ/
├── data/
│   ├── raw/                  # original, untouched source file
│   │   └── pharma-data.csv
│   └── processed/            # cleaned output, ready for SQL load / EDA
│       ├── pharma_clean.csv
│       ├── rxiq_tableau_flat.csv    # denormalized, Tableau-ready
│       ├── rep_month_predictions.csv
│       └── tables/           # 6 normalized tables (star schema CSVs)
├── notebooks/
│   └── 01_preprocessing_and_eda.ipynb   # cleaning + EDA in one notebook
├── scripts/
│   ├── 01_data_cleaning.py   # cleaning & preprocessing script (run this first)
│   ├── 02_build_tables.py    # builds the 6 normalized tables
│   └── 03_forecasting_model.py   # Step 5: rep-month sales forecasting
├── sql/
│   ├── 01_schema.sql         # MySQL DDL
│   ├── 02_load.sql           # LOAD DATA INFILE script
│   └── 03_business_queries.sql   # 10 tested business queries
├── reports/
│   ├── data_quality_report.txt   # log of every cleaning step + summary stats
│   ├── zero_activity_rows.csv    # rows removed (Quantity=0 / Sales=0), kept for reference
│   ├── forecasting_report.txt    # Step 5 model comparison results
│   ├── tableau_dashboard_blueprint.md   # Step 6 dashboard build plan
│   └── tableau_build_guide.md    # Step 6: click-by-click Tableau build steps
└── README.md
```

## Published Tableau dashboards

Built directly in Tableau Desktop's UI (not hand-edited XML — see
`reports/tableau_build_guide.md` for why) and published to Tableau Public:

- [Overview](https://public.tableau.com/app/profile/anjali.s5047/viz/Overview_17876704499320/Dashboard1) — KPIs, sales by country, product class, monthly trend
- [Rep Performance](https://public.tableau.com/app/profile/anjali.s5047/viz/RepPerformance_17876758276410/Dashboard2) — the headline rep-efficiency finding + team comparison
- [Forecast](https://public.tableau.com/app/profile/anjali.s5047/viz/Forecast_17876769000990/Dashboard1) — actual vs. predicted sales + forecast error by rep

A 4th dashboard (Product & Channel — treemap, channel/sub-channel mix, top
products by country) was scoped out to keep the deliverable focused on the
three findings that matter most: the efficiency gap, the country
concentration, and the forecasting honesty note. The full build steps for
it are still in `reports/tableau_build_guide.md` if it's added later.

## Pipeline status

- [x] Step 1 — Data cleaning & preprocessing
- [x] Step 2 — MySQL table design + load
- [x] Step 3 — SQL business queries
- [x] Step 4 — Python EDA
- [x] Step 5 — Forecasting / ML model
- [x] Step 6 — Tableau dashboard (Overview, Rep Performance, Forecast — published to Tableau Public; Product & Channel intentionally scoped out)
- [ ] Step 7 — 1-page recommendation memo

## Step 1 summary

- Source: 254,082 rows, 18 columns (Foresight BI pharma wholesale-retail dataset)
- Standardized column names to snake_case
- Stripped whitespace from all text fields (distributor names had trailing spaces)
- Removed 4 exact duplicate rows
- Separated out 2,660 zero-activity rows (Quantity=0 or Sales=0 — likely
  cancelled/returned orders) into `reports/zero_activity_rows.csv` rather than
  silently discarding them
- Verified Sales = Price × Quantity for all remaining rows (0 mismatches)
- Added a proper `date` column (from year + month) for time-series work
- **Final: 251,418 rows, 20 columns**, covering Jan 2017–Dec 2020,
  Poland & Germany, 13 sales reps, 4 sales teams, 29 distributors,
  749 cities, 240 products

## Step 2 summary

- Designed a 6-table normalized (star) schema: `dim_distributor`,
  `dim_customer`, `dim_product`, `dim_sales_rep`, `dim_date`, `fact_sales`
- `sql/01_schema.sql` — MySQL DDL (run this first on your local MySQL)
- `scripts/02_build_tables.py` — builds each dimension + fact table as CSV
  from the cleaned data (`data/processed/tables/`)
- `sql/02_load.sql` — `LOAD DATA LOCAL INFILE` script to load the CSVs
  into MySQL (update file paths to your local setup; requires
  `SET GLOBAL local_infile = 1;`)
- Validated: fact table row count (251,418) matches cleaned source exactly
  — no join fan-out or duplicate-key issues
- Table sizes: 29 distributors, 751 customers, 240 products, 13 sales reps,
  48 months (dim_date), 251,418 fact rows

## Notebook — Preprocessing & EDA

- `notebooks/01_preprocessing_and_eda.ipynb` — self-contained notebook covering
  data cleaning (same steps as `scripts/01_data_cleaning.py`) plus exploratory
  analysis: sales by country/channel, rep performance, team comparison,
  product class breakdown, monthly trend, geographic coverage
- **Important finding from EDA:** every sales rep transacts across all 749
  cities — there's no exclusive rep-territory assignment in this dataset.
  This overturns the original "coverage gap" hypothesis; the revised,
  data-backed headline finding is a **rep efficiency gap** (top rep ~16%
  higher sales-per-city than bottom rep, same footprint) plus a strong
  **Germany/Poland market concentration** (~94%/6% split). See the notebook's
  Key Findings section for full numbers.

## Step 3 summary

- `sql/03_business_queries.sql` — 10 queries, all tested against the schema
  (validated in SQLite locally; syntax targets MySQL 8.0+ for window functions)
- Covers: country overview, rep leaderboard (RANK), team comparison, rep
  efficiency per city (the headline-finding query), month-over-month growth
  (LAG), top 3 products per country (CTE + ROW_NUMBER), product class %
  breakdown, channel/sub-channel segmentation, running total by rep,
  year-over-year growth by team (LAG)
- Confirms in SQL: Germany ~$11.26B vs Poland ~$0.68B; Jimmy Grey top rep at
  ~$1.33M sales/city vs Alan Ray lowest at ~$1.14M/city; Delta top team at
  ~$3.68B

## Step 5 summary

- `scripts/03_forecasting_model.py` — predicts **next month's sales per rep**
  using lag features (1/2/3-month lag, 3-month rolling mean), calendar
  features (month, quarter, year), and team dummies
- Data: 624 rep-months (13 reps x 48 months) -> 572 usable after lag/target
  warm-up -> time-based split: train 2017-2019 (429 rows), test 2020 (143 rows)
- Compared 3 approaches: naive (predict = last month), Linear Regression,
  Random Forest (300 trees, max_depth=6)
- **Results (test set = 2020):**
  | Model | MAE | RMSE | R² |
  |---|---|---|---|
  | Naive (last month) | 6.70M | 10.17M | -0.75 |
  | Linear Regression | 6.33M | 8.50M | -0.22 |
  | Random Forest | 6.42M | 8.47M | -0.21 |
- **Honest finding:** both models beat the naive baseline by ~17% on RMSE,
  but R² stays negative — month-to-month rep-level sales are highly volatile
  in this dataset, so precise point forecasts aren't reliable at this
  granularity. Framed correctly in the write-up: the model gives a
  *directional* signal (better than assuming flat sales) but isn't precise
  enough for exact quota-setting — an honest, defensible limitation rather
  than an inflated result.
- Top predictive features: `month_num` (seasonality), followed by the lag
  features — team identity contributed very little, reinforcing the Step 4
  finding that performance differences are individual, not structural
- Predictions saved to `data/processed/rep_month_predictions.csv` for
  dashboard use
