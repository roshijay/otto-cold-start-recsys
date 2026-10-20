-- One row per item: event counts and conversion rates.
with events as (
    select * from {{ ref('stg_events') }}
),

item_events as (
    select
        aid,
        sum(case when event_type = 'clicks' then 1 else 0 end) as n_clicks,
        sum(case when event_type = 'carts' then 1 else 0 end) as n_carts,
        sum(case when event_type = 'orders' then 1 else 0 end) as n_orders,
        count(distinct session_id) as n_sessions
    from events
    group by aid
)

select
    *,
    -- order rate per click: P(order | click). Null-safe for items with zero clicks.
    case when n_clicks > 0 then n_orders * 1.0 / n_clicks end as order_rate_per_click,
    case when n_carts > 0 then n_orders * 1.0 / n_carts end as order_rate_per_cart
from item_events
