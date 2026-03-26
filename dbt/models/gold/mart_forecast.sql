{{ config(materialized='table', schema='gold') }}

SELECT
    DATE_TRUNC('month', fs.order_date)::DATE        AS revenue_month,
    dp.product_line,
    dp.therapeutic_area,
    SUM(fs.final_net_revenue)                       AS revenue,
    SUM(fs.net_units)                               AS units_sold,
    COUNT(DISTINCT fs.order_id)                     AS order_count,
    FALSE                                           AS is_forecast,
    NULL::NUMERIC(14,2)                             AS forecast_lower_bound,
    NULL::NUMERIC(14,2)                             AS forecast_upper_bound,
    CURRENT_TIMESTAMP                               AS _updated_at
FROM {{ ref('fact_sales') }} fs
LEFT JOIN {{ ref('dim_product') }} dp ON fs.product_key = dp.product_key
WHERE fs.order_date <= CURRENT_DATE
GROUP BY 1, 2, 3
