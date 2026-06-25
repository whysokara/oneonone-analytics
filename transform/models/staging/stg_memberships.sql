with source as (
    select * from {{ source('supabase', 'memberships') }}
),

renamed as (
    select
        "id"                     as membership_id,
        "boardId"                as board_id,
        "userId"                 as user_id,
        "joinedAt"::timestamp_tz as joined_at,
        current_timestamp()      as _dbt_loaded_at
    from source
)

select * from renamed
