-- Returns orders with dates in the future, which should not exist for actuals.
-- Test passes when this query returns 0 rows.
SELECT
    order_id,
    order_date
FROM {{ ref('stg_orders') }}
WHERE order_date > CURRENT_DATE
