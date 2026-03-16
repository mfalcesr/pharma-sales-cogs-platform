{{ config(materialized='table', schema='silver') }}

WITH costs AS (
    SELECT * FROM {{ ref('stg_costs') }}
),
-- Monthly revenue aggregated to product level for margin calculation
monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE   AS revenue_month,
        product_id,
        SUM(net_amount)                          AS net_revenue,
        SUM(quantity)                            AS units_sold
    FROM {{ ref('stg_orders') }}
    GROUP BY 1, 2
)

SELECT
    {{ surrogate_key(['c.cost_id']) }}               AS cogs_key,
    c.cost_id,
    d.date_key,
    p.product_key,
    c.product_id,
    c.cost_month,
    c.standard_cost,
    c.actual_cost,
    c.cost_variance,
    c.cost_variance_pct,
    COALESCE(mr.units_sold, 0)                       AS units_sold,
    COALESCE(mr.net_revenue, 0)                      AS net_revenue,
    c.actual_cost * COALESCE(mr.units_sold, 0)       AS total_cogs,
    COALESCE(mr.net_revenue, 0)
        - c.actual_cost * COALESCE(mr.units_sold, 0) AS gross_profit,
    CASE
        WHEN COALESCE(mr.net_revenue, 0) > 0
        THEN ROUND(
            (COALESCE(mr.net_revenue, 0)
             - c.actual_cost * COALESCE(mr.units_sold, 0))
            / mr.net_revenue * 100, 2)
        ELSE 0
    END                                              AS gross_margin_pct
FROM costs c
LEFT JOIN {{ ref('dim_date') }}    d  ON c.cost_month = d.date_day
LEFT JOIN {{ ref('dim_product') }} p  ON c.product_id = p.product_id
LEFT JOIN monthly_revenue          mr ON c.cost_month = mr.revenue_month
                                     AND c.product_id = mr.product_id
