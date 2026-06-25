with source as (
    select * from {{ source('supabase', 'subscriptions') }}
),

renamed as (
    select
        "id"                               as subscription_id,
        "user_id"                          as user_id,
        "dodo_customer_id"                 as dodo_customer_id,
        "dodo_subscription_id"             as dodo_subscription_id,
        "plan"                             as plan,
        "billing_cycle"                    as billing_cycle,
        "status"                           as status,
        "current_period_end"::timestamp_tz as current_period_end,
        "is_complimentary"::boolean        as is_complimentary,
        "created_at"::timestamp_tz         as created_at,
        "updated_at"::timestamp_tz         as updated_at,
        current_timestamp()                as _dbt_loaded_at
    from source
)

select * from renamed
