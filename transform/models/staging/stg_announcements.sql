with source as (
    select * from {{ source('supabase', 'announcements') }}
),

renamed as (
    select
        "id"                      as announcement_id,
        "boardId"                 as board_id,
        "createdByUserId"         as created_by_user_id,
        "title"                   as title,
        "message"                 as message,
        "createdAt"::timestamp_tz as created_at,
        "updatedAt"::timestamp_tz as updated_at
    from source
)

select * from renamed
