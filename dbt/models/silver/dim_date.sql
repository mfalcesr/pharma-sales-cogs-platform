{{ config(materialized='table', schema='silver') }}

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2022-01-01' as date)",
        end_date="cast('2028-01-01' as date)"
    ) }}
)

SELECT
    TO_CHAR(date_day, 'YYYYMMDD')::INTEGER                                              AS date_key,
    date_day,
    EXTRACT(YEAR FROM date_day)::INTEGER                                                AS year,
    EXTRACT(QUARTER FROM date_day)::INTEGER                                             AS quarter,
    EXTRACT(MONTH FROM date_day)::INTEGER                                               AS month_num,
    TO_CHAR(date_day, 'Month')                                                          AS month_name,
    TO_CHAR(date_day, 'Mon')                                                            AS month_abbr,
    EXTRACT(WEEK FROM date_day)::INTEGER                                                AS week_of_year,
    EXTRACT(ISODOW FROM date_day)::INTEGER                                              AS day_of_week,  -- 1=Mon, 7=Sun
    EXTRACT(DAY FROM date_day)::INTEGER                                                 AS day_of_month,
    EXTRACT(DOY FROM date_day)::INTEGER                                                 AS day_of_year,
    TO_CHAR(date_day, 'YYYY-"Q"Q')                                                      AS year_quarter,
    TO_CHAR(date_day, 'YYYY-MM')                                                        AS year_month,
    DATE_TRUNC('week', date_day)::DATE                                                  AS week_start_date,
    DATE_TRUNC('month', date_day)::DATE                                                 AS first_day_of_month,
    (DATE_TRUNC('month', date_day) + INTERVAL '1 month - 1 day')::DATE                 AS last_day_of_month,
    EXTRACT(DAY FROM (DATE_TRUNC('month', date_day) + INTERVAL '1 month - 1 day'))::INTEGER AS days_in_month,
    -- Fiscal year (Oct 1 start)
    {{ fiscal_year('date_day') }}                                                       AS fiscal_year,
    {{ fiscal_quarter('date_day') }}                                                    AS fiscal_quarter,
    {{ fiscal_month('date_day') }}                                                      AS fiscal_month,
    'FY' || {{ fiscal_year('date_day') }}::TEXT || '-Q' || {{ fiscal_quarter('date_day') }}::TEXT AS fiscal_year_quarter,
    -- Relative flags
    date_day = CURRENT_DATE                                                             AS is_today,
    date_day = DATE_TRUNC('month', CURRENT_DATE)                                        AS is_first_of_current_month,
    DATE_TRUNC('month', date_day) = DATE_TRUNC('month', CURRENT_DATE)                  AS is_current_month,
    DATE_TRUNC('quarter', date_day) = DATE_TRUNC('quarter', CURRENT_DATE)              AS is_current_quarter,
    EXTRACT(YEAR FROM date_day) = EXTRACT(YEAR FROM CURRENT_DATE)                      AS is_current_year,
    date_day <= CURRENT_DATE                                                            AS is_actual,  -- FALSE for future dates
    EXTRACT(ISODOW FROM date_day) BETWEEN 1 AND 5                                      AS is_weekday
FROM date_spine
