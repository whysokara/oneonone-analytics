-- grain: one row per board, with its team size (reportees, excluding the manager)
-- reused by: dim_teams, dim_managers, mart_manager_health
-- edge: memberships -> boards (memberships.board_id = boards.board_id)

with boards as (
    select * from {{ ref('stg_boards') }}
),

memberships as (
    select * from {{ ref('stg_memberships') }}
),

-- members who are NOT the board's manager (business rule: manager isn't a team member)
team_members as (
    select
        memberships.board_id
        , memberships.user_id
    from memberships
    inner join boards
        on memberships.board_id = boards.board_id
    where memberships.user_id != boards.manager_id
),

final as (
    select
        boards.board_id
        , boards.manager_id
        -- boards with no reportees count as 0, not null (left join + count of non-nulls)
        , count(distinct team_members.user_id) as team_size
    from boards
    left join team_members
        on boards.board_id = team_members.board_id
    group by
        boards.board_id
        , boards.manager_id
)

select * from final
