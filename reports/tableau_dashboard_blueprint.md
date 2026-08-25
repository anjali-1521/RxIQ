# RxIQ — Tableau Dashboard Blueprint

**Build status (2026-08-25):** All 4 dashboards are now assembled in
`rxiq_dashboard.twb` — Overview, Rep Performance, Product & Channel, Forecast.
See notes at the bottom of each section for what's built vs. simplified.

**Data source:** `data/processed/rxiq_tableau_flat.csv` (single denormalized
table — 251,418 rows, 24 columns — connect this directly in Tableau, no
joins needed since dimensions are already merged in)

This mirrors SupplyIQ's dashboard approach: one clean data source, a small
set of high-signal views, built around your headline finding rather than
a wall of generic charts.

---

## Dashboard 1: Executive Overview (top of the story)

| Viz | Fields | Purpose |
|---|---|---|
| KPI cards | SUM(sales), COUNT(transactions), AVG(sales) | Headline numbers |
| Bar: Sales by Country | country, SUM(sales) | Surfaces the 94/6 Germany-Poland split immediately |
| Line: Monthly Sales Trend | date (continuous), SUM(sales) | Shows seasonality/trend from EDA |
| Bar: Sales by Product Class | product_class, SUM(sales) | Shows the Analgesics-to-Antimalarial spread |

## Dashboard 2: Rep & Team Performance (the headline finding)

| Viz | Fields | Purpose |
|---|---|---|
| Bar: Sales Rep Leaderboard | sales_rep, SUM(sales), colored by sales_team | Visualizes Q2 from the SQL queries |
| **Scatter: Sales per City by Rep** | sales_rep (label), sales_per_city, cities_covered | **This is the money chart** — since every rep covers all 749 cities, plotting sales_per_city directly shows the efficiency gap (Jimmy Grey ~$1.33M vs Alan Ray ~$1.14M) without needing a map |
| Bar: Team Comparison | sales_team, SUM(sales), AVG(sales)/rep | Shows Delta leads, but per-rep efficiency (from the scatter) tells the real story |
| Highlight table | sales_rep x year, SUM(sales) | Rep performance over time — spot who's improving/declining |

## Dashboard 3: Product & Channel Mix

| Viz | Fields | Purpose |
|---|---|---|
| Treemap: Product Class x Product Name | product_class, product_name, SUM(sales) | Drill-down from class to individual product |
| Bar: Channel x Sub-channel | channel, SUM(sales), colored by sub_channel | Segment breakdown (Hospital/Pharmacy x Private/Retail/Institution/Government) |
| Bar: Top Products by Sales | product_name, SUM(sales), colored by country | Mirrors SQL Q6 (top products per country) |

**Built as:** Sheet 9 (treemap), Sheet 10 (channel bar), Sheet 11 (product bar).
Sheet 11 is a full sorted bar rather than a hard Top-3-per-country filter —
hand-writing Tableau's table-calc Top N filter XML directly was judged too
failure-prone to risk corrupting the workbook. To match SQL Q6 exactly,
right-click the Product Name pill → **Filter → Top tab → By field: Top 3 by
Sum(Sales)**, computed using Country — one click in Tableau's UI.

## Dashboard 4: Forecasting View (ties to Step 5)

| Viz | Fields | Purpose |
|---|---|---|
| Line: Actual vs Predicted | Load `rep_month_predictions.csv` as its own data source; date, actual_next_month_sales, predicted_rf | Shows model performance visually — good for explaining the "honest limitation" finding in an interview |

**Built as:** a new live-CSV data source (`rep_month_predictions.csv`, added
alongside the existing `rxiq_tableau_flat` source) feeding two sheets —
Sheet 13 (actual next-month sales, line) and Sheet 15 (avg absolute error by
rep, bar).

A third sheet (predicted RF, line) was hand-built the same way but
repeatedly failed Tableau Public's publish validation with "Dashboard
references sheet 'Sheet 14' which has no visual representation," even after
fixing an empty `<encodings>` tag and a zone-id collision that were both
genuine bugs. Since the error persisted after both fixes, it was pulled
rather than risk more blind XML edits. **To add it back:** in Tableau,
duplicate Sheet 13, swap `SUM(Actual Next Month Sales)` for
`SUM(Predicted (Random Forest))` on Rows, then drag it onto Sheet 13 as a
second axis (Analysis → right-click axis → Dual Axis, then sync axes) —
building it through Tableau's UI avoids whatever hand-XML issue caused the
publish failure.

## Overview & Rep Performance — completion note

Both dashboards existed only as individual worksheets (Sheets 1-8) plus one
broken, half-assembled `Dashboard 1` containing a single stray KPI zone. That
stub has been replaced with a fully zoned **Overview** dashboard (4 KPI
cards + Sales by Country + Monthly Trend + Product Class) and a new **Rep
Performance** dashboard (the Sales-per-City efficiency bar as the headline,
plus a new Team Comparison bar, Sheet 12).

---

## Build order (fastest path to a working dashboard)

1. Connect `rxiq_tableau_flat.csv` as the primary data source
2. Build Dashboard 2 first (rep efficiency scatter) — it's your strongest, most
   defensible insight and the one worth leading with
3. Build Dashboard 1 (overview) second — gives context/scale
4. Build Dashboard 3 (product/channel) if time allows — supporting detail
5. Combine into a single Tableau **Story** with 3-4 points: Overview → Rep
   Efficiency Finding → Recommendation. This is the closest Tableau equivalent
   to the "1-page memo" ZS-style deliverable (Step 7)

