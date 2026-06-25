with source as (
    select * from {{ source('supabase', 'support_requests') }}
),

renamed as (
    select
        "id"                      as support_request_id,
        "userId"                  as user_id,
        "type"                    as request_type,
        "message"                 as message,
        "createdAt"::timestamp_tz as created_at
    from source
)

select * from renamed
