with source as (
    select * from {{ source('supabase', 'boards') }}
),

renamed as (
    select
        "id"                                as board_id,
        "managerId"                         as manager_id,
        "name"                              as name,
        "description"                       as description,
        "inviteCode"                        as invite_code,
        "inviteCodeExpiresAt"::timestamp_tz as invite_code_expires_at,
        "createdAt"::timestamp_tz           as created_at,
        "updatedAt"::timestamp_tz           as updated_at,
        current_timestamp()                 as _dbt_loaded_at
    from source
)

select * from renamed
