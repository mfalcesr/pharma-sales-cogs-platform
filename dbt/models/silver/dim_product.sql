{{ config(materialized='table', schema='silver') }}

SELECT
    {{ surrogate_key(['product_id']) }}             AS product_key,
    product_id,
    product_code,
    product_name,
    therapeutic_area,
    product_line,
    formulation,
    launch_date,
    unit_cost_standard,
    EXTRACT(YEAR FROM launch_date)::INTEGER          AS launch_year,
    CASE
        WHEN product_line IN ('Biologics', 'Specialty') THEN 'High Value'
        WHEN product_line = 'Primary Care'              THEN 'Standard'
        ELSE 'Generic'
    END                                              AS value_tier,
    _loaded_at
FROM {{ ref('stg_products') }}
