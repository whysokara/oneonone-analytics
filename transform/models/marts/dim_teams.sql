-- grain: one row per board (team)
-- reuses int_board_team_size (team size) and int_subscriptions_current (manager's plan).

with boards as (
    select
        board_id
        , manager_id
        , name
        , created_at
    from {{ ref('stg_boards') }}
),

team_size as (
    select
        board_id
        , team_size
    from {{ ref('int_board_team_size') }}
),

current_subscription as (
    select
        user_id
        , current_plan
    from {{ ref('int_subscriptions_current') }}
),

final as (
    select
        boards.board_id
        , boards.manager_id
        , boards.name as team_name
        , boards.created_at::date as created_date
        , coalesce(team_size.team_size, 0) as team_size
        , coalesce(current_subscription.current_plan, 'free') as manager_plan
    from boards
    left join team_size
        on boards.board_id = team_size.board_id
    left join current_subscription
        on boards.manager_id = current_subscription.user_id
)

select * from final
