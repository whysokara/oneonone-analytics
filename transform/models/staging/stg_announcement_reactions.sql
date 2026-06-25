with source as (
    select * from {{ source('supabase', 'announcement_reactions') }}
),

renamed as (
    select
        "id"                      as reaction_id,
        "announcementId"          as announcement_id,
        "userId"                  as user_id,
        "reaction"                as reaction,
        "createdAt"::timestamp_tz as created_at,
        current_timestamp()       as _dbt_loaded_at
    from source
)

select * from renamed
