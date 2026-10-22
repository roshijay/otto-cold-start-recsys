-- Q7: cart abandonment -- the revenue left on the table.
-- Fear: "carts keep getting abandoned." Q1 showed 94,561 sessions reach cart but only
-- 50,871 order. This asks: how much demand is carted-but-never-ordered, how deep do
-- abandoners go, and how long do they hesitate first?
-- Caveat: "abandoned" = no order observed within our window; sessions are long-lived,
-- so some may convert after 2022-08-28 (unobserved).
with per_session as (
    select
        session_id,
        count(*) filter (where event_type = 'carts') as n_carts,
        count(*) filter (where event_type = 'orders') as n_orders,
        count(distinct case when event_type = 'carts' then aid end) as distinct_carted,
        min(case when event_type = 'carts' then event_ts end) as first_cart_ts,
        max(event_ts) as last_ts
    from {{ ref('stg_events') }}
    group by session_id
)
select
    count(*) as carted_sessions,
    sum(case when n_orders = 0 then 1 else 0 end) as abandoned_sessions,
    round(100.0 * sum(case when n_orders = 0 then 1 else 0 end) / count(*), 1)
        as abandon_rate_pct,
    round(avg(case when n_orders = 0 then n_carts end), 1) as avg_carts_when_abandoned,
    round(avg(case when n_orders = 0 then distinct_carted end), 1)
        as avg_distinct_items_abandoned,
    round(avg(case when n_orders > 0 then n_carts end), 1) as avg_carts_when_converted,
    round(avg(case when n_orders = 0
                   then date_diff('second', first_cart_ts, last_ts) / 3600.0 end), 1)
        as avg_hours_first_cart_to_session_end_abandoned
from per_session
where n_carts > 0
