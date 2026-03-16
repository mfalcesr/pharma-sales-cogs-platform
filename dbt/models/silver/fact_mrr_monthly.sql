{{ config(materialized='table', schema='silver') }}

WITH events AS (
    SELECT
        event_id::UUID            AS event_id,
        customer_id::UUID         AS customer_id,
        product_id::UUID          AS product_id,
        event_month::DATE         AS event_month,
        event_type,
        mrr_amount::NUMERIC(14,2) AS mrr_amount
    FROM {{ source('raw', 'mrr_events') }}
)

SELECT
    {{ surrogate_key(['e.event_id']) }}              AS mrr_key,
    e.event_id,
    d.date_key,
    c.customer_key,
    p.product_key,
    e.customer_id,
    e.product_id,
    e.event_month,
    e.event_type,
    e.mrr_amount,
    e.event_type = 'new'          AS is_new,
    e.event_type = 'churn'        AS is_churned,
    e.event_type = 'reactivation' AS is_reactivated,
    e.event_type = 'expansion'    AS is_expansion,
    e.event_type = 'contraction'  AS is_contraction,
    CASE WHEN e.event_type IN ('new', 'reactivation', 'expansion') THEN e.mrr_amount
         ELSE 0 END               AS mrr_added,
    CASE WHEN e.event_type = 'churn' THEN ABS(e.mrr_amount)
         ELSE 0 END               AS mrr_lost
FROM events e
LEFT JOIN {{ ref('dim_date') }}     d ON e.event_month = d.date_day
LEFT JOIN {{ ref('dim_customer') }} c ON e.customer_id  = c.customer_id
LEFT JOIN {{ ref('dim_product') }}  p ON e.product_id   = p.product_id
