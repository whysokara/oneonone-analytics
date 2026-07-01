-- Reliability constraint: MRR amounts must never be negative.
-- Returns rows that violate this rule; a non-empty result fails the test.
select
    subscription_id
    , mrr_amount
from {{ ref('fct_subscriptions') }}
where mrr_amount < 0
