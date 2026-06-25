-- grain: one row per subscription record (event) — the full history, not just current
-- adds per-row MRR contribution and a transition_type derived from the prior row per user.

with subscriptions as (
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
    from {{ ref('stg_subscriptions') }}
),

ranked as (
    select
        subscriptions.*
        -- ordered plan tiers so we can tell upgrades from downgrades
        , case plan
            when 'free' then 0
            when 'pro' then 1
            when 'pro_plus' then 2
            else -1
          end as plan_rank
    from subscriptions
),

with_prev as (
    select
        ranked.*
        , lag(plan_rank) over (partition by user_id order by created_at, updated_at) as prev_plan_rank
        , lag(status) over (partition by user_id order by created_at, updated_at) as prev_status
    from ranked
),

final as (
    select
        subscription_id
        , user_id
        , plan
        , billing_cycle
        , status
        , is_complimentary
        , current_period_end
        -- MRR rule: only active, non-complimentary, paid-plan rows contribute.
        -- NOTE: prices are PLACEHOLDERS (also duplicated in int_subscriptions_current) —
        --       a plan-pricing macro/seed is the right home once confirmed.
        , case
            when status = 'active' and is_complimentary = false then
                case plan
                    when 'pro' then 29.00
                    when 'pro_plus' then 99.00
                    else 0.00
                end
            else 0.00
          end::number(18, 2) as mrr_amount
        , case
            when prev_plan_rank is null then 'new'
            when status in ('canceled', 'expired') and prev_status not in ('canceled', 'expired') then 'churn'
            when plan_rank > prev_plan_rank then 'upgrade'
            when plan_rank < prev_plan_rank then 'downgrade'
            else 'unchanged'
          end as transition_type
    from with_prev
)

select * from final
