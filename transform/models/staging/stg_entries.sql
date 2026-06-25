with source as (
    select * from {{ source('supabase', 'entries') }}
),

renamed as (
    select
        "id"                      as entry_id,
        "boardId"                 as board_id,
        "employeeId"              as employee_id,
        "createdByUserId"         as created_by_user_id,
        "visibility"              as visibility,
        "category"                as category,
        "title"                   as title,
        "description"             as description,
        "entryDate"::date         as entry_date,
        "status"                  as status,
        "certificationUrl"        as certification_url,
        "goalTag"                 as goal_tag,
        "managerNote"             as manager_note,
        "createdAt"::timestamp_tz as created_at,
        "updatedAt"::timestamp_tz as updated_at,
        current_timestamp()       as _dbt_loaded_at
    from source
)

select * from renamed
