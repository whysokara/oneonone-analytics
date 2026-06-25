with source as (
    select * from {{ source('supabase', 'usage_events') }}
),

renamed as (
    select
        "id"                       as usage_event_id,
        "user_id"                  as user_id,
        "feature"                  as feature,
        "created_at"::timestamp_tz as created_at,
        current_timestamp()        as _dbt_loaded_at
    from source
)

select * from renamed
