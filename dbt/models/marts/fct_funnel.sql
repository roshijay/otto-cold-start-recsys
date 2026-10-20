-- Funnel: sessions reaching each stage.
with sessions as (
    select * from {{ ref('int_sessions') }}
)

select
    count(*) as n_sessions,
    sum(case when n_clicks > 0 then 1 else 0 end) as n_with_click,
    sum(reached_cart) as n_with_cart,
    sum(converted) as n_with_order,
    sum(reached_cart) * 1.0 / nullif(sum(case when n_clicks > 0 then 1 else 0 end), 0) as click_to_cart_rate,
    sum(converted) * 1.0 / nullif(sum(reached_cart), 0) as cart_to_order_rate,
    sum(converted) * 1.0 / count(*) as session_conversion_rate
from sessions
