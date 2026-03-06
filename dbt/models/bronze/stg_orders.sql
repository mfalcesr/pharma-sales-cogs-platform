{{ config(materialized='view', schema='bronze') }}

SELECT
    order_id::UUID                AS order_id,
    order_date::DATE              AS order_date,
    product_id::UUID              AS product_id,
    customer_id::UUID             AS customer_id,
    rep_id::UUID                  AS rep_id,
    territory_id::UUID            AS territory_id,
    quantity::INTEGER             AS quantity,
    list_price::NUMERIC(14, 2)    AS list_price,
    discount_pct::NUMERIC(8, 6)   AS discount_pct,
    net_price::NUMERIC(14, 2)     AS net_price,
    gross_amount::NUMERIC(14, 2)  AS gross_amount,
    net_amount::NUMERIC(14, 2)    AS net_amount,
    CURRENT_TIMESTAMP             AS _loaded_at
FROM {{ source('raw', 'orders') }}
WHERE order_id   IS NOT NULL
  AND order_date IS NOT NULL
