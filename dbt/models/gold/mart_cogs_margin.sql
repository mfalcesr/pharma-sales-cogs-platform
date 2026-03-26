{{ config(materialized='table', schema='gold') }}

SELECT
    fc.cost_month,
    dd.year,
    dd.quarter,
    dd.month_num,
    dd.month_name,
    dd.year_month,
    dd.year_quarter,
    dd.fiscal_year,
    dd.fiscal_quarter,
    dd.is_current_month,
    dp.product_code,
    dp.product_name,
    dp.therapeutic_area,
    dp.product_line,
    dp.value_tier,
    fc.standard_cost,
    fc.actual_cost,
    fc.cost_variance,
    fc.cost_variance_pct,
    fc.units_sold,
    fc.net_revenue,
    fc.total_cogs,
    fc.gross_profit,
    fc.gross_margin_pct,
    -- 3-month rolling average margin
    AVG(fc.gross_margin_pct) OVER (
        PARTITION BY fc.product_id
        ORDER BY fc.cost_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    )                                               AS rolling_3m_margin_pct,
    -- Prior month margin for MoM comparison
    LAG(fc.gross_margin_pct, 1) OVER (
        PARTITION BY fc.product_id
        ORDER BY fc.cost_month
    )                                               AS prior_month_margin_pct,
    fc.gross_margin_pct - LAG(fc.gross_margin_pct, 1) OVER (
        PARTITION BY fc.product_id
        ORDER BY fc.cost_month
    )                                               AS margin_mom_delta
FROM {{ ref('fact_cogs') }} fc
LEFT JOIN {{ ref('dim_date') }}    dd ON fc.date_key    = dd.date_key
LEFT JOIN {{ ref('dim_product') }} dp ON fc.product_key = dp.product_key
