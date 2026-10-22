-- Q6: post-order carting — do buyers save items for next time right after ordering?
with session_orders as (
    select
        session_id,
        min(case when event_type = 'orders' then event_ts end) as first_order_ts
    from {{ ref('stg_events') }}
    group by session_id
    having count(case when event_type = 'orders' then 1 end) > 0
),
post_first_order as (
    select
        so.session_id,
        count(case when e.event_type = 'carts' and e.event_ts > so.first_order_ts then 1 end) as carts_after_first_order,
        count(case when e.event_type = 'orders' and e.event_ts > so.first_order_ts then 1 end) as later_orders
    from session_orders so
    join {{ ref('stg_events') }} e on e.session_id = so.session_id
    group by so.session_id
)
select
    count(*) as converted_sessions,
    sum(case when carts_after_first_order > 0 then 1 else 0 end) as sessions_with_post_order_carts,
    round(100.0 * sum(case when carts_after_first_order > 0 then 1 else 0 end) / count(*), 1) as pct_with_post_order_carts,
    round(avg(carts_after_first_order), 1) as avg_post_order_carts,
    sum(case when later_orders > 0 then 1 else 0 end) as sessions_ordering_again_later
from post_first_order
