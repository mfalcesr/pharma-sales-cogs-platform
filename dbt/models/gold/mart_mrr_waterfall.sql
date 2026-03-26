{{ config(materialized='table', schema='gold') }}

WITH monthly_mrr AS (
    SELECT
        event_month,
        SUM(CASE WHEN is_new          THEN mrr_amount ELSE 0 END) AS new_mrr,
        SUM(CASE WHEN is_expansion    THEN mrr_amount ELSE 0 END) AS expansion_mrr,
        SUM(CASE WHEN is_contraction  THEN ABS(mrr_amount) ELSE 0 END) AS contraction_mrr,
        SUM(CASE WHEN is_churned      THEN ABS(mrr_amount) ELSE 0 END) AS churned_mrr,
        SUM(CASE WHEN is_reactivated  THEN mrr_amount ELSE 0 END) AS reactivation_mrr,
        COUNT(DISTINCT CASE WHEN is_new         THEN customer_id END) AS new_customers,
        COUNT(DISTINCT CASE WHEN is_churned     THEN customer_id END) AS churned_customers,
        COUNT(DISTINCT CASE WHEN is_reactivated THEN customer_id END) AS reactivated_customers,
        COUNT(DISTINCT customer_id)                AS total_active_customers
    FROM {{ ref('fact_mrr_monthly') }}
    GROUP BY 1
)

SELECT
    mm.event_month,
    dd.year,
    dd.quarter,
    dd.month_num,
    dd.month_name,
    dd.year_month,
    dd.fiscal_year,
    dd.fiscal_quarter,
    dd.is_current_month,
    mm.new_mrr,
    mm.expansion_mrr,
    mm.contraction_mrr,
    mm.churned_mrr,
    mm.reactivation_mrr,
    mm.new_mrr + mm.expansion_mrr + mm.reactivation_mrr
        - mm.contraction_mrr - mm.churned_mrr       AS net_new_mrr,
    SUM(mm.new_mrr + mm.expansion_mrr + mm.reactivation_mrr
        - mm.contraction_mrr - mm.churned_mrr) OVER (
        ORDER BY mm.event_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                               AS cumulative_mrr,
    mm.new_customers,
    mm.churned_customers,
    mm.reactivated_customers,
    mm.total_active_customers,
    LAG(mm.total_active_customers, 1) OVER (ORDER BY mm.event_month) AS prior_month_customers,
    CASE
        WHEN LAG(mm.total_active_customers, 1) OVER (ORDER BY mm.event_month) > 0
        THEN ROUND(
            mm.churned_customers::NUMERIC
            / LAG(mm.total_active_customers, 1) OVER (ORDER BY mm.event_month) * 100, 2)
        ELSE 0
    END                                             AS churn_rate_pct
FROM monthly_mrr mm
LEFT JOIN {{ ref('dim_date') }} dd ON mm.event_month = dd.date_day
ORDER BY mm.event_month
