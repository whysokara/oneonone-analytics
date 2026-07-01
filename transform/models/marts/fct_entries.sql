-- grain: one row per entry
-- thin business-facing fact: a straight select from int_entries_enriched, where the
-- join + self-entry + first-entry logic already lives.

with enriched as (
    select * from {{ ref('int_entries_enriched') }}
)

select
    entry_id
    , board_id
    , employee_id
    , manager_id
    , category
    , status
    , visibility
    , is_self_entry
    , is_first_entry
    , entry_date
from enriched
