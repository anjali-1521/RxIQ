-- =====================================================================
-- RxIQ — MySQL Schema
-- 6 normalized tables: 4 dimension, 1 bridge/rep, 1 fact
-- =====================================================================

DROP DATABASE IF EXISTS rxiq;
CREATE DATABASE rxiq;
USE rxiq;

-- ---------------------------------------------------------------------
-- 1. dim_distributor
-- ---------------------------------------------------------------------
CREATE TABLE dim_distributor (
    distributor_id   INT AUTO_INCREMENT PRIMARY KEY,
    distributor_name VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------
-- 2. dim_customer  (the buying entity: hospital / pharmacy / etc.)
-- ---------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    city          VARCHAR(100),
    country       VARCHAR(50),
    latitude      DECIMAL(9,6),
    longitude     DECIMAL(9,6),
    channel       VARCHAR(50),      -- Hospital / Pharmacy
    sub_channel   VARCHAR(50)       -- Private / Retail / Institution / Government
);

-- ---------------------------------------------------------------------
-- 3. dim_product
-- ---------------------------------------------------------------------
CREATE TABLE dim_product (
    product_id    INT AUTO_INCREMENT PRIMARY KEY,
    product_name  VARCHAR(150) NOT NULL UNIQUE,
    product_class VARCHAR(50)
);

-- ---------------------------------------------------------------------
-- 4. dim_sales_rep  (rep -> manager -> team hierarchy)
-- ---------------------------------------------------------------------
CREATE TABLE dim_sales_rep (
    rep_id      INT AUTO_INCREMENT PRIMARY KEY,
    sales_rep   VARCHAR(100) NOT NULL UNIQUE,
    manager     VARCHAR(100),
    sales_team  VARCHAR(50)
);

-- ---------------------------------------------------------------------
-- 5. dim_date
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    date_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_date  DATE NOT NULL UNIQUE,
    month_name VARCHAR(20),
    month_num  TINYINT,
    quarter    TINYINT,
    year       SMALLINT
);

-- ---------------------------------------------------------------------
-- 6. fact_sales
-- ---------------------------------------------------------------------
CREATE TABLE fact_sales (
    sale_id        INT AUTO_INCREMENT PRIMARY KEY,
    distributor_id INT,
    customer_id    INT,
    product_id     INT,
    rep_id         INT,
    date_id        INT,
    quantity       INT NOT NULL,
    price          DECIMAL(10,2) NOT NULL,
    sales          DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (distributor_id) REFERENCES dim_distributor(distributor_id),
    FOREIGN KEY (customer_id)    REFERENCES dim_customer(customer_id),
    FOREIGN KEY (product_id)     REFERENCES dim_product(product_id),
    FOREIGN KEY (rep_id)         REFERENCES dim_sales_rep(rep_id),
    FOREIGN KEY (date_id)        REFERENCES dim_date(date_id)
);

CREATE INDEX idx_fact_rep   ON fact_sales(rep_id);
CREATE INDEX idx_fact_date  ON fact_sales(date_id);
CREATE INDEX idx_fact_prod  ON fact_sales(product_id);
CREATE INDEX idx_fact_cust  ON fact_sales(customer_id);
