{{ config(materialized='table', schema='silver') }}

SELECT
    {{ surrogate_key(['territory_id']) }}            AS territory_key,
    territory_id,
    territory_name,
    region,
    country,
    zone,
    CURRENT_TIMESTAMP                                AS _loaded_at
FROM {{ source('raw', 'territories') }}
