{{ config(materialized='table', schema='gold') }}

SELECT
    fs.order_id,
    fs.order_date,
    dd.year,
    dd.quarter,
    dd.month_num,
    dd.month_name,
    dd.year_month,
    dd.year_quarter,
    dd.fiscal_year,
    dd.fiscal_quarter,
    dd.is_current_month,
    dd.is_actual,
    dp.product_code,
    dp.product_name,
    dp.therapeutic_area,
    dp.product_line,
    dp.formulation,
    dp.value_tier,
    dc.account_name,
    dc.segment                          AS customer_segment,
    dc.tier                             AS customer_tier,
    dc.region                           AS customer_region,
    dc.is_active                        AS customer_is_active,
    dr.rep_name,
    dr.manager_name,
    dr.annual_quota,
    dr.monthly_quota,
    dt.territory_name,
    dt.region                           AS territory_region,
    dt.zone,
    fs.units_sold,
    fs.units_returned,
    fs.net_units,
    fs.gross_amount,
    fs.net_revenue,
    fs.discount_amount,
    fs.final_net_revenue,
    fs.discount_pct,
    fs.daily_quota_attainment_pct,
    FALSE                               AS is_forecast
FROM {{ ref('fact_sales') }} fs
LEFT JOIN {{ ref('dim_date') }}      dd ON fs.date_key       = dd.date_key
LEFT JOIN {{ ref('dim_product') }}   dp ON fs.product_key    = dp.product_key
LEFT JOIN {{ ref('dim_customer') }}  dc ON fs.customer_key   = dc.customer_key
LEFT JOIN {{ ref('dim_rep') }}       dr ON fs.rep_key        = dr.rep_key
LEFT JOIN {{ ref('dim_territory') }} dt ON fs.territory_key  = dt.territory_key
