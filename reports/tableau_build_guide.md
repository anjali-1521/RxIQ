# RxIQ — Build the Tableau Dashboard Yourself (Step-by-Step)

Why from scratch: every "no visual representation" publish error traced back
to hand-written XML I patched into `rxiq_dashboard.twb`. Building through
Tableau's own UI generates that XML correctly the first time, so this guide
has you rebuild the 4 dashboards natively. Total time: ~60-90 min.

**Recommended starting point:** open the current `rxiq_dashboard.twb`.
Sheets 1-4 and 5-8 (KPI cards) were built by you in the UI originally, not
by hand-edited XML — they're safe to keep and reuse as-is. Everything from
"Sheet 9" onward, and all 4 dashboard tabs, were hand-authored by me and hit
publish errors — right-click and **Delete** those worksheet tabs and
dashboard tabs before starting, so you're rebuilding on a clean base.

If you'd rather start completely fresh: File → New, then Data → New Data
Source → Text File → pick `data/processed/rxiq_tableau_flat.csv`.

---

## Setup — data sources

You need two, connected separately (not joined):

1. **`rxiq_tableau_flat.csv`** — the main table (251,418 rows). Already
   connected if you're continuing the existing file.
2. **`rep_month_predictions.csv`** — for the Forecast dashboard only. Data
   → New Data Source → Text File → `data/processed/rep_month_predictions.csv`.
   Columns: `sales_rep`, `date`, `actual_next_month_sales`, `predicted_rf`,
   `predicted_lr`, `predicted_naive`, `abs_error_rf`.

**The one gotcha to remember everywhere:** `sales_per_city` and
`efficiency_rank` in the flat file are pre-calculated and **repeated on
every row** for a given rep. Any pill using `sales_per_city` must be
aggregated as **AVG**, never the default SUM — SUM multiplies the repeated
value by row count and inflates it by orders of magnitude.

---

## Dashboard 1: Overview

**Worksheets needed** (reuse Sheets 1-8 if you kept them; otherwise build):

| Sheet | Build |
|---|---|
| KPI: Total Sales | Drag `Sales` to Text (Marks card) → mark type **Text**. Right-click the pill → default aggregation is SUM, keep it. |
| KPI: Transactions | Drag `Sales` to Text, right-click the pill on the Marks card → Measure → **Count** (not Sum). |
| KPI: Reps | Drag `Sales Rep` to Text, right-click → Measure → **Count Distinct**. |
| KPI: Products Sold | Drag `Product Name` to Text, right-click → Measure → **Count Distinct**. |
| Sales by Country | `Country` → Rows, `Sales` → Columns. Mark type Bar or Automatic. Add a quick table calc for % of Total: right-click `SUM(Sales)` on Columns (or on Label) → Add Table Calculation → **Percent of Total**. |
| Monthly Sales Trend | `Date` → Columns (click the field, choose **continuous** MONTH, the green pill, not blue/discrete), `Sales` → Rows. Mark type **Line**. |
| Product Class breakdown | `Product Class` → Rows, `Sales` → Columns. Mark type Bar. Color by `SUM(Sales)` for a gradient, or leave plain. |

**Assemble the dashboard:**
1. New Dashboard (bottom tab bar → the dashboard icon, or Dashboard menu → New Dashboard).
2. Set size: Dashboard pane on the left → Size → **Fixed**, 1200 × 800 (or leave Automatic if you prefer responsive).
3. Drag the 4 KPI sheets into a **horizontal container** across the top (Tableau auto-suggests a grid layout when you drop near existing objects — accept it, or manually drag a "Horizontal" container from the Objects list first, then drop each KPI sheet inside it).
4. Below that, drag Sales by Country (left half) and Monthly Trend (right half) side by side.
5. Below that, drag Product Class breakdown full-width.
6. Rename the dashboard tab to **Overview** (double-click the tab name).

---

## Dashboard 2: Rep Performance (your headline chart)

**Worksheets:**

| Sheet | Build |
|---|---|
| Rep Efficiency (the money chart) | `Sales Rep` → Rows, `Sales Per City` → Columns. **Right-click the Sales Per City pill → Measure → change from SUM to AVG.** Color by `Sales Rep` to make the top/bottom performer visually distinct — or better, color by the measure itself with a diverging palette to highlight the gap. Sort descending by the measure (click the sort icon on the axis, or right-click the Sales Rep pill → Sort → Descending → by Sales Per City AVG). |
| Team Comparison | `Sales Team` → Rows, `Sales` → Columns. Mark type Bar, color by `Sales Team`. |

**Assemble:** New Dashboard, drop the Rep Efficiency chart large across the top (~65% height), Team Comparison below it (~35% height). Rename tab to **Rep Performance**.

Optional extra credit (from the original blueprint, not yet built): a
highlight table of `Sales Rep` × `Year` with `SUM(Sales)` in cells and
color, to show trend over time per rep.

---

## Dashboard 3: Product & Channel

**Worksheets:**

| Sheet | Build |
|---|---|
| Product Treemap | Leave Rows and Columns **empty**. Drag `Product Class` to Color, `Sales` to Size, `Product Name` to Label (or Detail). Tableau auto-switches the mark type to **Treemap** once size + hierarchy are set (mark type shows "Automatic"). |
| Channel × Sub-channel | `Channel` → Rows, `Sales` → Columns. Mark type Bar. Drag `Sub Channel` to Color. |
| Top Products by Country | `Product Name` → Rows, `Sales` → Columns. Mark type Bar. Drag `Country` to Color. Sort descending by Sales. **To match the SQL "top 3 per country" finding exactly:** right-click the `Product Name` pill → Filter → **Top** tab → "By field" → Top **3** by `Sum(Sales)` → under Table Calculation, set "Compute Using" to **Country**. |

**Assemble:** New Dashboard. Treemap left (~60% width), Channel bar right (~40% width), both in the top ~55%. Top Products table full-width below. Rename tab to **Product & Channel**.

---

## Dashboard 4: Forecast

Switch to the `rep_month_predictions` data source for these.

**Worksheets:**

| Sheet | Build |
|---|---|
| Actual vs Predicted | `Date` → Columns (continuous, green pill). Drag `Actual Next Month Sales` to Rows. Then **also drag `Predicted (Random Forest)` on top of the same Rows axis** (drop it right on the existing axis, not next to it) — Tableau will offer to create a **dual axis**. Accept it, then right-click the second axis → **Synchronize Axis** so both lines share the same scale. Mark type Line for both (set individually via the two mark cards Tableau creates). |
| Forecast Error by Rep | `Sales Rep` → Rows, `Absolute Error (RF)` → Columns. **Change the aggregation to AVG** (right-click the pill → Measure → Average). Mark type Bar, color by Sales Rep, sort descending.|

**Assemble:** New Dashboard. Actual vs Predicted full-width top (~65% height), Error by Rep full-width below (~35%). Rename tab to **Forecast**.

This single combined line chart (dual-axis) is exactly the thing I couldn't
safely hand-code in raw XML — doing it here via drag-and-drop is the correct
and much more reliable way to get it.

---

## Publishing

File → **Save to Tableau Public As...** Sign in (or create a free account),
name it, save. If it prompts to convert a live connection to an extract,
say yes — Tableau Public doesn't support live file connections, only
extracts, which is very likely why the hand-built `rep_month_predictions`
source kept failing validation earlier.

Once published you'll get a `public.tableau.com/...` URL — send it to me
and I'll open it in my browser tool to check the four dashboards actually
render as expected.
