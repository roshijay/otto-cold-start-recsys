-- One row per session: counts by event type, duration, conversion flag.
with events as (
    select * from {{ ref('stg_events') }}
),

sessionized as (
    select
        session_id,
        count(*) as n_events,
        sum(case when event_type = 'clicks' then 1 else 0 end) as n_clicks,
        sum(case when event_type = 'carts' then 1 else 0 end) as n_carts,
        sum(case when event_type = 'orders' then 1 else 0 end) as n_orders,
        count(distinct aid) as n_distinct_items,
        min(event_ts) as session_start,
        max(event_ts) as session_end
    from events
    group by session_id
)

select
    *,
    -- duration in seconds; single-event sessions get 0
    date_diff('second', session_start, session_end) as duration_sec,
    case when n_orders > 0 then 1 else 0 end as converted,
    case when n_carts > 0 then 1 else 0 end as reached_cart
from sessionized
