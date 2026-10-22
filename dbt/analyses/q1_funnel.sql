-- Q1: Funnel — where does the drop-off happen?
select * from {{ ref('fct_funnel') }}
