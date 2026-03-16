{{ config(materialized='table', schema='silver') }}

SELECT
    {{ surrogate_key(['rep_id']) }}                  AS rep_key,
    rep_id,
    rep_name,
    territory_id,
    region,
    manager_name,
    hire_date,
    annual_quota,
    monthly_quota,
    daily_quota,
    CURRENT_DATE - hire_date                         AS tenure_days,
    _loaded_at
FROM (
    SELECT
        *,
        ROUND(annual_quota / 12.0, 2)               AS monthly_quota,
        ROUND(annual_quota / 365.0, 2)              AS daily_quota
    FROM {{ ref('stg_reps') }}
) subq
