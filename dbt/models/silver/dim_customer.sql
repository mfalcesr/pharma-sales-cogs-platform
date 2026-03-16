{{ config(materialized='table', schema='silver') }}

SELECT
    {{ surrogate_key(['customer_id']) }}             AS customer_key,
    customer_id,
    account_name,
    segment,
    tier,
    region,
    territory_id,
    contract_start_date,
    contract_end_date,
    is_active,
    COALESCE(
        contract_end_date - contract_start_date,
        CURRENT_DATE - contract_start_date
    )                                                AS tenure_days,
    CASE tier
        WHEN 'A' THEN 3
        WHEN 'B' THEN 2
        ELSE 1
    END                                              AS tier_rank,
    _loaded_at
FROM {{ ref('stg_customers') }}
