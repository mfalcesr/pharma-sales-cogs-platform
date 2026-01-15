-- Create pipeline schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Raw tables (loaded from CSVs)
CREATE TABLE IF NOT EXISTS raw.territories (
    territory_id    UUID PRIMARY KEY,
    territory_name  VARCHAR(100) NOT NULL,
    region          VARCHAR(50)  NOT NULL,
    country         VARCHAR(50)  NOT NULL DEFAULT 'US',
    zone            VARCHAR(50)  NOT NULL,
    _loaded_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.products (
    product_id          UUID PRIMARY KEY,
    product_code        VARCHAR(20)     NOT NULL UNIQUE,
    product_name        VARCHAR(200)    NOT NULL,
    therapeutic_area    VARCHAR(100)    NOT NULL,
    product_line        VARCHAR(100)    NOT NULL,
    formulation         VARCHAR(50)     NOT NULL,
    launch_date         DATE            NOT NULL,
    unit_cost_standard  NUMERIC(14,2)   NOT NULL,
    _loaded_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id         UUID PRIMARY KEY,
    account_name        VARCHAR(200)    NOT NULL,
    segment             VARCHAR(50)     NOT NULL,
    tier                CHAR(1)         NOT NULL,
    region              VARCHAR(50)     NOT NULL,
    territory_id        UUID            REFERENCES raw.territories(territory_id),
    contract_start_date DATE            NOT NULL,
    contract_end_date   DATE,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    _loaded_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.reps (
    rep_id          UUID PRIMARY KEY,
    rep_name        VARCHAR(200)    NOT NULL,
    territory_id    UUID            REFERENCES raw.territories(territory_id),
    region          VARCHAR(50)     NOT NULL,
    manager_name    VARCHAR(200)    NOT NULL,
    hire_date       DATE            NOT NULL,
    annual_quota    NUMERIC(14,2)   NOT NULL,
    _loaded_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id        UUID PRIMARY KEY,
    order_date      DATE            NOT NULL,
    product_id      UUID            REFERENCES raw.products(product_id),
    customer_id     UUID            REFERENCES raw.customers(customer_id),
    rep_id          UUID            REFERENCES raw.reps(rep_id),
    territory_id    UUID            REFERENCES raw.territories(territory_id),
    quantity        INTEGER         NOT NULL,
    list_price      NUMERIC(14,2)   NOT NULL,
    discount_pct    NUMERIC(8,6)    NOT NULL,
    net_price       NUMERIC(14,2)   NOT NULL,
    gross_amount    NUMERIC(14,2)   NOT NULL,
    net_amount      NUMERIC(14,2)   NOT NULL,
    _loaded_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.costs (
    cost_id         UUID PRIMARY KEY,
    product_id      UUID            REFERENCES raw.products(product_id),
    cost_month      DATE            NOT NULL,
    standard_cost   NUMERIC(14,2)   NOT NULL,
    actual_cost     NUMERIC(14,2)   NOT NULL,
    _loaded_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.returns (
    return_id           UUID PRIMARY KEY,
    order_id            UUID            REFERENCES raw.orders(order_id),
    return_date         DATE            NOT NULL,
    quantity_returned   INTEGER         NOT NULL,
    reason              VARCHAR(200)    NOT NULL,
    _loaded_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.mrr_events (
    event_id        UUID PRIMARY KEY,
    customer_id     UUID            REFERENCES raw.customers(customer_id),
    product_id      UUID            REFERENCES raw.products(product_id),
    event_month     DATE            NOT NULL,
    event_type      VARCHAR(20)     NOT NULL,
    mrr_amount      NUMERIC(14,2)   NOT NULL,
    _loaded_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_orders_date         ON raw.orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_product       ON raw.orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer      ON raw.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_rep           ON raw.orders(rep_id);
CREATE INDEX IF NOT EXISTS idx_costs_product_month  ON raw.costs(product_id, cost_month);
CREATE INDEX IF NOT EXISTS idx_mrr_customer_month   ON raw.mrr_events(customer_id, event_month);
