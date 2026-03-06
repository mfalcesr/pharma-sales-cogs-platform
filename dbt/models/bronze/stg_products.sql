{{ config(materialized='view', schema='bronze') }}

SELECT
    product_id::UUID                  AS product_id,
    TRIM(product_code)                AS product_code,
    TRIM(product_name)                AS product_name,
    TRIM(therapeutic_area)            AS therapeutic_area,
    TRIM(product_line)                AS product_line,
    TRIM(formulation)                 AS formulation,
    launch_date::DATE                 AS launch_date,
    unit_cost_standard::NUMERIC(14, 2) AS unit_cost_standard,
    CURRENT_TIMESTAMP                 AS _loaded_at
FROM {{ source('raw', 'products') }}
WHERE product_id IS NOT NULL
