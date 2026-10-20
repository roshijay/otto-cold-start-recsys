-- One row per event, cleaned and typed. No business logic here.
with source as (
    select * from {{ source('raw', 'events') }}
),

deduped as (
    select distinct
        session_id,
        aid,
        event_ts,
        event_type,
        event_order
    from source
    where session_id is not null
      and aid is not null
      and event_ts is not null
)

select * from deduped
