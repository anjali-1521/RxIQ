-- =====================================================================
-- RxIQ — SQL Business Queries
-- All queries tested against the schema (sql/01_schema.sql).
-- Window functions require MySQL 8.0+.
-- =====================================================================

USE rxiq;

-- ---------------------------------------------------------------------
-- Q1. Country overview — transactions, total sales, avg deal size
-- ---------------------------------------------------------------------
SELECT c.country,
       COUNT(*) AS num_transactions,
       ROUND(SUM(f.sales),0) AS total_sales,
       ROUND(AVG(f.sales),0) AS avg_deal_size
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.country
ORDER BY total_sales DESC;

-- ---------------------------------------------------------------------
-- Q2. Sales rep leaderboard — overall rank + rank within team
-- ---------------------------------------------------------------------
SELECT r.sales_rep, r.sales_team,
       ROUND(SUM(f.sales),0) AS total_sales,
       RANK() OVER (ORDER BY SUM(f.sales) DESC) AS overall_rank,
       RANK() OVER (PARTITION BY r.sales_team ORDER BY SUM(f.sales) DESC) AS team_rank
FROM fact_sales f
JOIN dim_sales_rep r ON f.rep_id = r.rep_id
GROUP BY r.sales_rep, r.sales_team
ORDER BY total_sales DESC;

-- ---------------------------------------------------------------------
-- Q3. Team performance comparison
-- ---------------------------------------------------------------------
SELECT r.sales_team,
       COUNT(DISTINCT r.sales_rep) AS num_reps,
       ROUND(SUM(f.sales),0) AS total_sales,
       ROUND(SUM(f.sales) / COUNT(DISTINCT r.sales_rep),0) AS avg_sales_per_rep
FROM fact_sales f
JOIN dim_sales_rep r ON f.rep_id = r.rep_id
GROUP BY r.sales_team
ORDER BY total_sales DESC;

-- ---------------------------------------------------------------------
-- Q4. Rep efficiency — sales per city covered (headline finding query:
--     every rep covers all 749 cities, so this isolates true
--     performance differences rather than territory-size differences)
-- ---------------------------------------------------------------------
SELECT r.sales_rep,
       COUNT(DISTINCT c.city) AS cities_covered,
       ROUND(SUM(f.sales),0) AS total_sales,
       ROUND(SUM(f.sales) / COUNT(DISTINCT c.city),0) AS sales_per_city
FROM fact_sales f
JOIN dim_sales_rep r ON f.rep_id = r.rep_id
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY r.sales_rep
ORDER BY sales_per_city DESC;

-- ---------------------------------------------------------------------
-- Q5. Month-over-month sales growth (LAG window function)
-- ---------------------------------------------------------------------
WITH monthly AS (
    SELECT d.year, d.month_num, SUM(f.sales) AS total_sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.year, d.month_num
)
SELECT year, month_num, total_sales,
       LAG(total_sales) OVER (ORDER BY year, month_num) AS prev_month_sales,
       ROUND(
         (total_sales - LAG(total_sales) OVER (ORDER BY year, month_num)) * 100.0
         / LAG(total_sales) OVER (ORDER BY year, month_num), 2
       ) AS mom_growth_pct
FROM monthly
ORDER BY year, month_num;

-- ---------------------------------------------------------------------
-- Q6. Top 3 products by revenue, per country (CTE + ROW_NUMBER)
-- ---------------------------------------------------------------------
WITH product_country_sales AS (
    SELECT c.country, p.product_name, SUM(f.sales) AS total_sales,
           ROW_NUMBER() OVER (PARTITION BY c.country ORDER BY SUM(f.sales) DESC) AS rn
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY c.country, p.product_name
)
SELECT country, product_name, ROUND(total_sales,0) AS total_sales
FROM product_country_sales
WHERE rn <= 3
ORDER BY country, total_sales DESC;

-- ---------------------------------------------------------------------
-- Q7. Product class breakdown with % of total sales
-- ---------------------------------------------------------------------
SELECT p.product_class,
       ROUND(SUM(f.sales),0) AS total_sales,
       ROUND(SUM(f.sales) * 100.0 / (SELECT SUM(sales) FROM fact_sales), 2) AS pct_of_total
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_class
ORDER BY total_sales DESC;

-- ---------------------------------------------------------------------
-- Q8. Channel / sub-channel segmentation
-- ---------------------------------------------------------------------
SELECT c.channel, c.sub_channel,
       COUNT(*) AS num_transactions,
       ROUND(SUM(f.sales),0) AS total_sales
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.channel, c.sub_channel
ORDER BY total_sales DESC;

-- ---------------------------------------------------------------------
-- Q9. Running total of sales over time for a given rep
--     (swap the rep name to inspect any individual)
-- ---------------------------------------------------------------------
WITH rep_monthly AS (
    SELECT r.sales_rep, d.year, d.month_num, SUM(f.sales) AS monthly_sales
    FROM fact_sales f
    JOIN dim_sales_rep r ON f.rep_id = r.rep_id
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE r.sales_rep = 'Jimmy Grey'
    GROUP BY r.sales_rep, d.year, d.month_num
)
SELECT sales_rep, year, month_num, monthly_sales,
       SUM(monthly_sales) OVER (PARTITION BY sales_rep ORDER BY year, month_num) AS running_total
FROM rep_monthly
ORDER BY year, month_num;

-- ---------------------------------------------------------------------
-- Q10. Year-over-year growth by sales team (LAG window function)
-- ---------------------------------------------------------------------
WITH yearly AS (
    SELECT r.sales_team, d.year, SUM(f.sales) AS total_sales
    FROM fact_sales f
    JOIN dim_sales_rep r ON f.rep_id = r.rep_id
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY r.sales_team, d.year
)
SELECT sales_team, year, total_sales,
       LAG(total_sales) OVER (PARTITION BY sales_team ORDER BY year) AS prev_year_sales,
       ROUND(
         (total_sales - LAG(total_sales) OVER (PARTITION BY sales_team ORDER BY year)) * 100.0
         / LAG(total_sales) OVER (PARTITION BY sales_team ORDER BY year), 2
       ) AS yoy_growth_pct
FROM yearly
ORDER BY sales_team, year;
