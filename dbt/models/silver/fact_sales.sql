{{ config(materialized='table', schema='silver') }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
reps AS (
    SELECT rep_id, annual_quota, daily_quota
    FROM {{ ref('dim_rep') }}
),
returns_agg AS (
    SELECT
        order_id,
        SUM(quantity_returned) AS total_returned_qty
    FROM {{ ref('stg_returns') }}
    GROUP BY order_id
)

SELECT
    {{ surrogate_key(['o.order_id']) }}              AS sales_key,
    o.order_id,
    d.date_key,
    p.product_key,
    c.customer_key,
    r.rep_key,
    t.territory_key,
    o.order_date,
    o.quantity                                       AS units_sold,
    COALESCE(ret.total_returned_qty, 0)              AS units_returned,
    o.quantity - COALESCE(ret.total_returned_qty, 0) AS net_units,
    o.list_price,
    o.discount_pct,
    o.net_price,
    o.gross_amount,
    o.net_amount                                     AS net_revenue,
    o.gross_amount - o.net_amount                    AS discount_amount,
    COALESCE(ret.total_returned_qty, 0) * o.net_price AS returned_revenue,
    o.net_amount - COALESCE(ret.total_returned_qty, 0) * o.net_price AS final_net_revenue,
    CASE
        WHEN rp.daily_quota > 0
        THEN ROUND(o.net_amount / rp.daily_quota * 100, 2)
        ELSE 0
    END                                              AS daily_quota_attainment_pct
FROM orders o
LEFT JOIN {{ ref('dim_date') }}      d   ON o.order_date   = d.date_day
LEFT JOIN {{ ref('dim_product') }}   p   ON o.product_id   = p.product_id
LEFT JOIN {{ ref('dim_customer') }}  c   ON o.customer_id  = c.customer_id
LEFT JOIN {{ ref('dim_rep') }}       r   ON o.rep_id       = r.rep_id
LEFT JOIN {{ ref('dim_territory') }} t   ON o.territory_id = t.territory_id
LEFT JOIN reps                       rp  ON o.rep_id       = rp.rep_id
LEFT JOIN returns_agg                ret ON o.order_id     = ret.order_id
