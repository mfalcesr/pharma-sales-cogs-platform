{{ config(materialized='view', schema='bronze') }}

SELECT
    cost_id::UUID                  AS cost_id,
    product_id::UUID               AS product_id,
    cost_month::DATE               AS cost_month,
    standard_cost::NUMERIC(14, 2)  AS standard_cost,
    actual_cost::NUMERIC(14, 2)    AS actual_cost,
    -- Derived variance columns computed at staging time
    actual_cost - standard_cost    AS cost_variance,
    ROUND(
        (actual_cost - standard_cost)
        / NULLIF(standard_cost, 0) * 100,
        4
    )                              AS cost_variance_pct,
    CURRENT_TIMESTAMP              AS _loaded_at
FROM {{ source('raw', 'costs') }}
WHERE cost_id IS NOT NULL
