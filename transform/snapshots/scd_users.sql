{% snapshot scd_users %}

{{
    config(
        target_schema='snapshots',
        unique_key='user_id',
        strategy='timestamp',
        updated_at='updated_at'
    )
}}

-- Exclude _dbt_loaded_at — it's current_timestamp() and changes every run,
-- which would create a false new version on every snapshot even when the user
-- record itself hasn't changed.
select
    user_id
    , auth_user_id
    , full_name
    , email
    , role
    , org_name
    , job_title
    , linkedin_profile_url
    , birthday
    , created_at
    , updated_at
from {{ ref('stg_users') }}

{% endsnapshot %}
