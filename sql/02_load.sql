-- =====================================================================
-- RxIQ — Load table CSVs into MySQL
-- Run 01_schema.sql first. Update the file paths below to match
-- where you keep the RxIQ folder locally (MySQL needs absolute paths
-- and 'local_infile' enabled: SET GLOBAL local_infile = 1;)
-- =====================================================================

USE rxiq;

LOAD DATA LOCAL INFILE 'data/processed/tables/dim_distributor.csv'
INTO TABLE dim_distributor
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(distributor_id, distributor_name);

LOAD DATA LOCAL INFILE 'data/processed/tables/dim_customer.csv'
INTO TABLE dim_customer
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(customer_id, customer_name, city, country, latitude, longitude, channel, sub_channel);

LOAD DATA LOCAL INFILE 'data/processed/tables/dim_product.csv'
INTO TABLE dim_product
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, product_name, product_class);

LOAD DATA LOCAL INFILE 'data/processed/tables/dim_sales_rep.csv'
INTO TABLE dim_sales_rep
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(rep_id, sales_rep, manager, sales_team);

LOAD DATA LOCAL INFILE 'data/processed/tables/dim_date.csv'
INTO TABLE dim_date
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(date_id, full_date, month_name, month_num, quarter, year);

LOAD DATA LOCAL INFILE 'data/processed/tables/fact_sales.csv'
INTO TABLE fact_sales
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(sale_id, distributor_id, customer_id, product_id, rep_id, date_id, quantity, price, sales);

-- Quick sanity check after loading
SELECT 'dim_distributor' AS tbl, COUNT(*) AS row_count FROM dim_distributor
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_sales_rep', COUNT(*) FROM dim_sales_rep
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'fact_sales', COUNT(*) FROM fact_sales;
