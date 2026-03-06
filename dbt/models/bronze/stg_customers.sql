{{ config(materialized='view', schema='bronze') }}

SELECT
    customer_id::UUID                              AS customer_id,
    TRIM(account_name)                             AS account_name,
    TRIM(segment)                                  AS segment,
    TRIM(tier)                                     AS tier,
    TRIM(region)                                   AS region,
    territory_id::UUID                             AS territory_id,
    contract_start_date::DATE                      AS contract_start_date,
    NULLIF(TRIM(contract_end_date::TEXT), '')::DATE AS contract_end_date,
    CASE
        WHEN TRIM(LOWER(is_active::TEXT)) IN ('true', '1', 'yes')
        THEN TRUE
        ELSE FALSE
    END                                            AS is_active,
    CURRENT_TIMESTAMP                              AS _loaded_at
FROM {{ source('raw', 'customers') }}
WHERE customer_id IS NOT NULL
