-- grain: one row per user — their current subscription, plan, and MRR contribution
-- reused by: dim_managers, dim_teams, mart_manager_health
-- edge: subscriptions -> users (subscriptions.user_id = users.user_id)

with subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

plan_pricing as (
    select * from {{ ref('plan_pricing') }}
),

-- collapse to one row per user: prefer an active sub, then the latest period end,
-- then the most recently updated row (fallback when no active sub exists)
current_subscription as (
    select
        subscription_id
        , user_id
        , plan
        , billing_cycle
        , status
        , is_complimentary
        , current_period_end
        , created_at
        , updated_at
    from subscriptions
    qualify row_number() over (
        partition by user_id
        order by
            iff(status = 'active', 1, 0) desc
            , current_period_end desc nulls last
            , updated_at desc nulls last
    ) = 1
),

priced as (
    select
        current_subscription.*
        , plan_pricing.monthly_price
        , plan_pricing.annual_price
    from current_subscription
    left join plan_pricing
        on current_subscription.plan = plan_pricing.plan
),

final as (
    select
        user_id
        , subscription_id
        , plan as current_plan
        , billing_cycle
        , status
        , is_complimentary
        , current_period_end
        , (status = 'active') as is_active
        -- paying = active, non-complimentary, AND on a paid plan (free = $0 MRR per business rule)
        , (status = 'active' and is_complimentary = false and plan in ('pro', 'pro_plus')) as is_paying
        -- MRR rule (CLAUDE.md): only active AND non-complimentary subs contribute.
        -- Prices come from the plan_pricing seed (OneOnOne landing page). Annual subs are
        -- normalised to a monthly figure (annual_price / 12); annual /= monthly * 12 because
        -- paid plans include 2 free months when billed yearly.
        , case
            when status = 'active' and is_complimentary = false then
                case
                    when billing_cycle = 'annual' then annual_price / 12.0
                    else monthly_price
                end
            else 0.00
          end::number(18, 2) as mrr_amount
    from priced
)

select * from final
