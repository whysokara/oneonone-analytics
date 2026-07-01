-- Reliability constraint: active managers can never exceed total managers.
-- Returns a row if the constraint is violated; a non-empty result fails the test.
with active as (
    select count(*) as cnt
    from {{ ref('mart_manager_health') }}
    where health_status != 'churning'
),
total as (
    select count(*) as cnt
    from {{ ref('dim_managers') }}
)
select
    active.cnt as active_count
    , total.cnt as total_count
from active
cross join total
where active.cnt > total.cnt
