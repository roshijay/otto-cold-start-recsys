-- Q3b diagnostic: what calendar window does the sample actually cover?
select
    cast(session_start as date) as d,
    count(*) as sessions,
    min(session_start) as first_session,
    max(session_start) as last_session
from {{ ref('fct_session_summary') }}
group by 1
order by 1
