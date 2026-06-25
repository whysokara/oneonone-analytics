-- grain: one row per manager, snapshot (recomputed each run; no history kept)
-- churn early-warning: exposes the raw activity components AND a derived verdict.

with managers as (
    select
        manager_id
        , last_entry_at
        , team_size
        , current_plan
    from {{ ref('dim_managers') }}
),

-- non-self team entries in the trailing 30 days (snapshot relative to today)
recent_entries as (
    select
        manager_id
        , count(*) as entries_30d
    from {{ ref('int_entries_enriched') }}
    where is_self_entry = false
      and entry_date >= dateadd(day, -30, current_date())
    group by manager_id
),

final as (
    select
        managers.manager_id
        , managers.last_entry_at
        , coalesce(recent_entries.entries_30d, 0) as entries_30d
        , managers.team_size
        , managers.current_plan
        , datediff(day, managers.last_entry_at, current_date()) as days_since_last_entry
        , case
            when managers.last_entry_at is null
                 or datediff(day, managers.last_entry_at, current_date()) > 30 then 'churning'
            when datediff(day, managers.last_entry_at, current_date()) > 14 then 'at_risk'
            else 'healthy'
          end as health_status
    from managers
    left join recent_entries
        on managers.manager_id = recent_entries.manager_id
)

select * from final
