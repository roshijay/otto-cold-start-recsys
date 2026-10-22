-- Q5: click-to-order lag — how long from first click to first order?
with firsts as (
    select
        session_id,
        min(case when event_type = 'clicks' then event_ts end) as first_click,
        min(case when event_type = 'orders' then event_ts end) as first_order
    from {{ ref('stg_events') }}
    group by session_id
),
lags as (
    select date_diff('second', first_click, first_order) as lag_sec
    from firsts
    where first_order is not null and first_click is not null
)
select
    count(*) as converted_sessions,
    round(avg(lag_sec) / 60.0, 1) as avg_lag_min,
    round(quantile_cont(lag_sec, 0.25) / 60.0, 1) as p25_lag_min,
    round(quantile_cont(lag_sec, 0.50) / 60.0, 1) as median_lag_min,
    round(quantile_cont(lag_sec, 0.75) / 60.0, 1) as p75_lag_min,
    round(quantile_cont(lag_sec, 0.90) / 60.0, 1) as p90_lag_min,
    round(max(lag_sec) / 60.0, 1) as max_lag_min
from lags
