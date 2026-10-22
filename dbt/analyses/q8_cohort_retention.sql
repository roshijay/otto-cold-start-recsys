-- Q8: repeat purchase by first-order cohort -- the leaky bucket.
-- Fear: "we acquire buyers but they never come back." Q6 showed 51.9% of buyers order
-- again at some point; this adds WHEN: cohort buyers by week of first order and track
-- second-order rate + median days to it.
-- Caveat (right-censoring): later cohorts have less follow-up time before the data ends
-- (~2022-08-28), so their repeat rates are mechanically understated. Read the SHAPE
-- across cohorts, not just the levels.
with orders as (
    select
        session_id,
        event_ts as order_ts,
        row_number() over (partition by session_id order by event_ts) as rn
    from {{ ref('stg_events') }}
    where event_type = 'orders'
),
firsts as (
    select session_id, min(order_ts) as first_ts
    from orders
    group by session_id
)
select
    date_trunc('week', first_ts) as cohort_week,
    count(*) as buyers,
    sum(case when o2.order_ts is not null then 1 else 0 end) as with_second_order,
    round(100.0 * sum(case when o2.order_ts is not null then 1 else 0 end) / count(*), 1)
        as repeat_rate_pct,
    round(quantile_cont(case when o2.order_ts is not null
                              then date_diff('second', firsts.first_ts, o2.order_ts) / 86400.0 end, 0.5), 1)
        as median_days_to_second_order
from firsts
left join orders o2
    on o2.session_id = firsts.session_id and o2.rn = 2
group by 1
order by 1
