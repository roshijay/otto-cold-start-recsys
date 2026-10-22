-- Q4: Item concentration — head vs. long tail?
select
    aid,
    n_clicks, n_carts, n_orders,
    order_rate_per_click
from {{ ref('fct_item_stats') }}
where n_clicks >= 50
order by n_orders desc
limit 20
