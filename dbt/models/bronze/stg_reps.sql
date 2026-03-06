{{ config(materialized='view', schema='bronze') }}

SELECT
    rep_id::UUID                   AS rep_id,
    TRIM(rep_name)                 AS rep_name,
    territory_id::UUID             AS territory_id,
    TRIM(region)                   AS region,
    TRIM(manager_name)             AS manager_name,
    hire_date::DATE                AS hire_date,
    annual_quota::NUMERIC(14, 2)   AS annual_quota,
    CURRENT_TIMESTAMP              AS _loaded_at
FROM {{ source('raw', 'reps') }}
WHERE rep_id IS NOT NULL
