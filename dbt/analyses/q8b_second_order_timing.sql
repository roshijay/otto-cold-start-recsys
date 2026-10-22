-- Q8b diagnostic: are "second orders" same-checkout multi-item purchases or true repurchases?
-- OTTO records each purchased item as a separate order event, so a multi-item basket
-- looks like several "orders" minutes apart. This splits second orders by timing to
-- separate same-checkout (<1h) from genuine later repurchase (>1d).
with orders as (
    select session_id, event_ts as order_ts,
           row_number() over (partition by session_id order by event_ts) as rn
    from {{ ref('stg_events') }}
    where event_type = 'orders'
),
firsts as (
    select session_id, min(order_ts) as first_ts from orders group by session_id
),
second as (
    select f.session_id, f.first_ts, o2.order_ts as second_ts
    from firsts f
    join orders o2 on o2.session_id = f.session_id and o2.rn = 2
)
select
    count(*) as second_orders,
    sum(case when date_diff('second', first_ts, second_ts) < 3600 then 1 else 0 end) as within_1h,
    sum(case when date_diff('second', first_ts, second_ts) >= 86400 then 1 else 0 end) as after_1d,
    round(100.0 * sum(case when date_diff('second', first_ts, second_ts) < 3600 then 1 else 0 end) / count(*), 1) as pct_within_1h,
    round(100.0 * sum(case when date_diff('second', first_ts, second_ts) >= 86400 then 1 else 0 end) / count(*), 1) as pct_after_1d
from second
