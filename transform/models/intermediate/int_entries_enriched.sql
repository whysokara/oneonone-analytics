-- grain: one row per entry, enriched with the entry's manager + business-rule flags
-- reused by: fct_entries, dim_managers, mart_manager_health
-- edge: entries -> boards (entries.board_id = boards.board_id)

with entries as (
    select * from {{ ref('stg_entries') }}
),

boards as (
    select * from {{ ref('stg_boards') }}
),

joined as (
    select
        entries.entry_id
        , entries.board_id
        , entries.employee_id
        , entries.created_by_user_id
        , boards.manager_id
        , entries.category
        , entries.status
        , entries.visibility
        , entries.entry_date
        , entries.created_at
        -- business rule: a "self-entry" is the manager logging their own work
        -- (employee == the board's manager). null board -> not a self-entry.
        , coalesce(entries.employee_id = boards.manager_id, false) as is_self_entry
    from entries
    left join boards
        on entries.board_id = boards.board_id
),

-- rank only published entries per employee so a draft can never be "first"
published_ranked as (
    select
        entry_id
        , row_number() over (
            partition by employee_id
            order by entry_date, created_at
        ) as published_rank
    from joined
    where status = 'published'
),

final as (
    select
        joined.entry_id
        , joined.board_id
        , joined.employee_id
        , joined.created_by_user_id
        , joined.manager_id
        , joined.category
        , joined.status
        , joined.visibility
        , joined.entry_date
        , joined.created_at
        , joined.is_self_entry
        -- true only for an employee's earliest published entry; false everywhere else
        , coalesce(published_ranked.published_rank = 1, false) as is_first_entry
    from joined
    left join published_ranked
        on joined.entry_id = published_ranked.entry_id
)

select * from final
