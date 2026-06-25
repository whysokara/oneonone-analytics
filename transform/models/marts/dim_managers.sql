-- grain: one row per manager
-- the reusable join/aggregation logic now lives in the intermediate layer; this mart
-- aggregates those int_ models to manager grain and joins them 1:1 (no fan-out).

with managers as (
    select
        user_id
        , email
        , created_at
    from {{ ref('stg_users') }}
    where role = 'manager'
),

-- per-manager team size: aggregate the per-board team sizes up to the manager
team_size as (
    select
        manager_id
        , sum(team_size) as team_size
    from {{ ref('int_board_team_size') }}
    group by manager_id
),

-- per-manager entry stats from enriched entries, excluding manager self-entries.
-- activation = at least one team member has at least one published entry.
entry_stats as (
    select
        manager_id
        , count(*) as entry_count
        , max(entry_date) as last_entry_at
        , coalesce(max(case when status = 'published' then 1 else 0 end) = 1, false) as is_activated
    from {{ ref('int_entries_enriched') }}
    where is_self_entry = false
    group by manager_id
),

current_subscription as (
    select
        user_id
        , current_plan
        , is_paying
    from {{ ref('int_subscriptions_current') }}
),

final as (
    select
        managers.user_id as manager_id
        , managers.email
        , managers.created_at::date as signup_date
        , coalesce(current_subscription.current_plan, 'free') as current_plan
        , coalesce(current_subscription.is_paying, false) as is_paying
        , coalesce(team_size.team_size, 0) as team_size
        , coalesce(entry_stats.is_activated, false) as is_activated
        , entry_stats.last_entry_at
        , coalesce(entry_stats.entry_count, 0) as entry_count
    from managers
    left join current_subscription
        on managers.user_id = current_subscription.user_id
    left join team_size
        on managers.user_id = team_size.manager_id
    left join entry_stats
        on managers.user_id = entry_stats.manager_id
)

select * from final
