{{
    config(
        materialized='table',
        schema='staging'
    )
}}

-- MetricFlow time spine: one row per day from 2020-01-01 → 2030-12-31.
-- Required by MetricFlow to fill gaps in time-series metric queries.
-- Snowflake's generator() function creates the row sequence; dateadd shifts it into dates.
select
    dateadd('day', seq4(), '2020-01-01'::date) as date_day
from table(generator(rowcount => 4018))  -- 2020-01-01 to 2030-12-31 = 4018 days
where dateadd('day', seq4(), '2020-01-01'::date) <= '2030-12-31'::date
