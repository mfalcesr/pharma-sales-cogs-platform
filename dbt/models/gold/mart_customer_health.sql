{{ config(materialized='table', schema='gold') }}

WITH monthly_orders AS (
    SELECT
        dc.customer_id,
        DATE_TRUNC('month', fs.order_date)::DATE    AS activity_month,
        COUNT(DISTINCT fs.order_id)                  AS order_count,
        SUM(fs.final_net_revenue)                    AS monthly_revenue,
        SUM(fs.net_units)                            AS monthly_units,
        MAX(fs.order_date)                           AS last_order_date
    FROM {{ ref('fact_sales') }} fs
    LEFT JOIN {{ ref('dim_customer') }} dc ON fs.customer_key = dc.customer_key
    GROUP BY 1, 2
),
mrr AS (
    SELECT
        customer_id,
        event_month,
        SUM(mrr_added)                               AS mrr_added,
        SUM(mrr_lost)                                AS mrr_lost,
        BOOL_OR(is_churned)                          AS is_churned,
        BOOL_OR(is_new)                              AS is_new,
        BOOL_OR(is_reactivated)                      AS is_reactivated,
        BOOL_OR(is_expansion)                        AS is_expansion
    FROM {{ ref('fact_mrr_monthly') }}
    GROUP BY 1, 2
),
customer_ltv AS (
    SELECT
        dc.customer_id,
        SUM(fs.final_net_revenue)                    AS lifetime_value
    FROM {{ ref('fact_sales') }} fs
    LEFT JOIN {{ ref('dim_customer') }} dc ON fs.customer_key = dc.customer_key
    GROUP BY 1
)

SELECT
    dc.customer_id,
    dc.account_name,
    dc.segment,
    dc.tier,
    dc.tier_rank,
    dc.region,
    dc.contract_start_date,
    dc.contract_end_date,
    dc.is_active,
    dc.tenure_days,
    COALESCE(mo.activity_month, mrr.event_month)    AS report_month,
    COALESCE(mo.order_count, 0)                     AS order_count,
    COALESCE(mo.monthly_revenue, 0)                 AS monthly_revenue,
    COALESCE(mo.monthly_units, 0)                   AS monthly_units,
    mo.last_order_date,
    CURRENT_DATE - mo.last_order_date               AS days_since_last_order,
    COALESCE(mrr.mrr_added, 0)                      AS mrr_added,
    COALESCE(mrr.mrr_lost, 0)                       AS mrr_lost,
    COALESCE(mrr.is_churned, FALSE)                 AS is_churned,
    COALESCE(mrr.is_new, FALSE)                     AS is_new_customer,
    COALESCE(mrr.is_reactivated, FALSE)             AS is_reactivated,
    COALESCE(mrr.is_expansion, FALSE)               AS is_expansion,
    COALESCE(ltv.lifetime_value, 0)                 AS lifetime_value
FROM {{ ref('dim_customer') }} dc
LEFT JOIN monthly_orders mo   ON dc.customer_id = mo.customer_id
LEFT JOIN mrr                 ON dc.customer_id = mrr.customer_id
                             AND COALESCE(mo.activity_month, '1900-01-01'::DATE) = mrr.event_month
LEFT JOIN customer_ltv ltv    ON dc.customer_id = ltv.customer_id
