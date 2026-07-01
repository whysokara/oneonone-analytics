with source as (
    select * from {{ source('supabase', 'users') }}
),

renamed as (
    select
        "id"                      as user_id,
        "authUserId"              as auth_user_id,
        "fullName"                as full_name,
        "email"                   as email,
        "role"                    as role,
        "orgName"                 as org_name,
        "jobTitle"                as job_title,
        "linkedinUrl"             as linkedin_profile_url,
        "birthday"::date          as birthday,
        "createdAt"::timestamp_tz as created_at,
        "updatedAt"::timestamp_tz as updated_at,
        current_timestamp()       as _dbt_loaded_at
    from source
)

select * from renamed
