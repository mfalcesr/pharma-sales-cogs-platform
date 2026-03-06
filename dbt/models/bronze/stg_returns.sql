{{ config(materialized='view', schema='bronze') }}

SELECT
    return_id::UUID                AS return_id,
    order_id::UUID                 AS order_id,
    return_date::DATE              AS return_date,
    quantity_returned::INTEGER     AS quantity_returned,
    TRIM(reason)                   AS return_reason,
    CURRENT_TIMESTAMP              AS _loaded_at
FROM {{ source('raw', 'returns') }}
WHERE return_id IS NOT NULL
