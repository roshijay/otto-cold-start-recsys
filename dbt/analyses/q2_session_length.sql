-- Q2: Session length — how do people browse, and does length relate to conversion?
select
    n_events,
    count(*) as sessions,
    avg(converted) as conversion_rate
from {{ ref('fct_session_summary') }}
group by n_events
order by n_events
