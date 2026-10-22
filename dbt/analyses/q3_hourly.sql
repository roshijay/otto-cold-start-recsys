-- Q3: Time patterns — when do people shop vs. buy?
select
    extract(hour from session_start) as hour_of_day,
    count(*) as sessions,
    avg(converted) as conversion_rate
from {{ ref('fct_session_summary') }}
group by 1
order by 1
