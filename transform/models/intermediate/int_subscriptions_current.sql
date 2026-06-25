-- grain: one row per user — their current subscription, plan, and MRR contribution
-- reused by: dim_managers, dim_teams, mart_manager_health
-- edge: subscriptions -> users (subscriptions.user_id = users.user_id)

with subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
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
        -- NOTE: plan prices are PLACEHOLDERS — confirm real monthly prices, and whether
        --       an annual billing_cycle should be normalised (/12) into a monthly figure.
        , case
            when status = 'active' and is_complimentary = false then
                case plan
                    when 'pro' then 29.00
                    when 'pro_plus' then 99.00
                    else 0.00
                end
            else 0.00
          end::number(18, 2) as mrr_amount
    from current_subscription
)

select * from final
