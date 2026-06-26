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

plan_pricing as (
    select * from {{ ref('plan_pricing') }}
),

ranked as (
    select
        subscriptions.*
        , plan_pricing.monthly_price
        , plan_pricing.annual_price
        -- ordered plan tiers so we can tell upgrades from downgrades
        , case subscriptions.plan
            when 'free' then 0
            when 'pro' then 1
            when 'pro_plus' then 2
            else -1
          end as plan_rank
    from subscriptions
    left join plan_pricing on subscriptions.plan = plan_pricing.plan
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
        -- Prices from plan_pricing seed. Annual subs normalized to monthly (annual_price / 12).
        , case
            when status = 'active' and is_complimentary = false then
                case
                    when billing_cycle = 'annual' then annual_price / 12.0
                    else monthly_price
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
