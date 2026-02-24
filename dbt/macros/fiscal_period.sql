{% macro fiscal_year(date_col) %}
    CASE
        WHEN EXTRACT(MONTH FROM {{ date_col }}) >= 10
        THEN EXTRACT(YEAR FROM {{ date_col }}) + 1
        ELSE EXTRACT(YEAR FROM {{ date_col }})
    END::INTEGER
{% endmacro %}

{% macro fiscal_quarter(date_col) %}
    CASE
        WHEN EXTRACT(MONTH FROM {{ date_col }}) IN (10, 11, 12) THEN 1
        WHEN EXTRACT(MONTH FROM {{ date_col }}) IN (1, 2, 3)   THEN 2
        WHEN EXTRACT(MONTH FROM {{ date_col }}) IN (4, 5, 6)   THEN 3
        WHEN EXTRACT(MONTH FROM {{ date_col }}) IN (7, 8, 9)   THEN 4
    END::INTEGER
{% endmacro %}

{% macro fiscal_month(date_col) %}
    CASE
        WHEN EXTRACT(MONTH FROM {{ date_col }}) >= 10
        THEN EXTRACT(MONTH FROM {{ date_col }}) - 9
        ELSE EXTRACT(MONTH FROM {{ date_col }}) + 3
    END::INTEGER
{% endmacro %}
