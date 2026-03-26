-- Returns rows where a non-churn/contraction event has negative MRR.
-- Test passes when this query returns 0 rows.
SELECT
    event_id,
    event_type,
    mrr_amount
FROM {{ ref('fact_mrr_monthly') }}
WHERE event_type NOT IN ('churn', 'contraction')
  AND mrr_amount <= 0
