-- Returns rows that violate the margin bounds check.
-- Test passes when this query returns 0 rows.
SELECT
    product_id,
    cost_month,
    gross_margin_pct
FROM {{ ref('fact_cogs') }}
WHERE gross_margin_pct < -50
   OR gross_margin_pct > 100
