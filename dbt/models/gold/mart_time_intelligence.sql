{{ config(materialized='table', schema='gold') }}

WITH daily_revenue AS (
    SELECT
        fs.order_date,
        dp.product_line,
        dp.therapeutic_area,
        SUM(fs.final_net_revenue)                   AS daily_revenue,
        SUM(fs.units_sold)                          AS daily_units,
        COUNT(DISTINCT fs.order_id)                 AS daily_orders
    FROM {{ ref('fact_sales') }} fs
    LEFT JOIN {{ ref('dim_product') }} dp ON fs.product_key = dp.product_key
    WHERE fs.order_date <= CURRENT_DATE
    GROUP BY 1, 2, 3
)

SELECT
    dr.order_date,
    dd.year,
    dd.quarter,
    dd.month_num,
    dd.month_name,
    dd.year_month,
    dd.year_quarter,
    dd.fiscal_year,
    dd.fiscal_quarter,
    dd.is_current_month,
    dr.product_line,
    dr.therapeutic_area,
    dr.daily_revenue,
    dr.daily_units,
    dr.daily_orders,
    -- MTD
    SUM(dr.daily_revenue) OVER (
        PARTITION BY dd.year, dd.month_num, dr.product_line, dr.therapeutic_area
        ORDER BY dr.order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                               AS mtd_revenue,
    -- QTD
    SUM(dr.daily_revenue) OVER (
        PARTITION BY dd.year, dd.quarter, dr.product_line, dr.therapeutic_area
        ORDER BY dr.order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                               AS qtd_revenue,
    -- YTD
    SUM(dr.daily_revenue) OVER (
        PARTITION BY dd.year, dr.product_line, dr.therapeutic_area
        ORDER BY dr.order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                               AS ytd_revenue,
    -- Rolling 3-month revenue (90 days)
    SUM(dr.daily_revenue) OVER (
        PARTITION BY dr.product_line, dr.therapeutic_area
        ORDER BY dr.order_date
        ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    )                                               AS rolling_90d_revenue,
    -- Rolling 12-month revenue (365 days)
    SUM(dr.daily_revenue) OVER (
        PARTITION BY dr.product_line, dr.therapeutic_area
        ORDER BY dr.order_date
        ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    )                                               AS rolling_365d_revenue,
    -- Prior year same period (approximate via 364-day lag)
    LAG(dr.daily_revenue, 364) OVER (
        PARTITION BY dr.product_line, dr.therapeutic_area
        ORDER BY dr.order_date
    )                                               AS prior_year_daily_revenue,
    -- YoY growth
    CASE
        WHEN LAG(dr.daily_revenue, 364) OVER (
            PARTITION BY dr.product_line, dr.therapeutic_area ORDER BY dr.order_date
        ) > 0
        THEN ROUND(
            (dr.daily_revenue - LAG(dr.daily_revenue, 364) OVER (
                PARTITION BY dr.product_line, dr.therapeutic_area ORDER BY dr.order_date
            )) / LAG(dr.daily_revenue, 364) OVER (
                PARTITION BY dr.product_line, dr.therapeutic_area ORDER BY dr.order_date
            ) * 100, 2)
        ELSE NULL
    END                                             AS yoy_growth_pct
FROM daily_revenue dr
LEFT JOIN {{ ref('dim_date') }} dd ON dr.order_date = dd.date_day
