# Frame: March 2026 price increase and retention

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did monthly-plan retention get worse after the March 2026 price change ($10 to $12), by how much, for which plan and tenure groups, and is a partial rollback for any of those groups worth the revenue it gives up?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customers, and for which ones.

## Audience
Head of growth.

## Population
Paid subscribers (free plans excluded: they never end). The business can treat customers differently by plan and by tenure (user's answer); no other groups are targetable.
- Analyst suggestion: tenure measured at each subscriber's first $12 charge (existing subscribers only feel the increase at their next billing date; new and established customers may react differently).
- Analyst suggestion: start cohort, pre-increase vs post-increase starters (compares customers only with others at the same stage).
- Analyst suggestion: annual plan as the comparison group, read as difference-in-differences: each group against its own baseline, since annual customers can only leave at renewal and their raw churn does not behave like monthly churn.

## What would change the decision
The user gave no threshold; the analyst proposes one.
- Analyst suggestion: consider a rollback for a group only if (a) its churn rose clearly more than its own pre-increase baseline after allowing for the comparison group's change over the same months, at the same tenure, and (b) the revenue lost to that extra churn exceeds the extra $2 a month collected from those who stayed, over the 6 months after the change.
- Analyst suggestion: the money at stake for each whole group over that period, next to the rates. A rate says which way; money for the whole group says whether acting is worth it.
- Analyst suggestion: count reactions other than cancelling (monthly to annual, downgrade to free, fewer trials converting to monthly) in both the retention and the money. Not measurable in this data; see Out of scope.
The analysis plan should make this measurable and show it to the user first.

## Tables likely involved
- subscriptions: plan, start and end dates; churn, tenure, plan switches.
- payments: price actually charged, date of first $12 charge, revenue.
- users: signup date and customer attributes for tenure and cohort.
- trials: whether trial conversion to monthly changed after the increase (trials only start 2026-08-01, so likely limited).

## Analysis window
Before: 2025-09-01 to 2026-02-28. After: 2026-03-01 to 2026-09-24 (data end). Analyst suggestion: seasonality check on the same months a year earlier, if the data goes back that far.

## Additional context
- Only the monthly price changed ($10 to $12); annual did not.
- September 2025 signup spike (about 5x a normal month) sits in the baseline.
- Subscription end dates changed how they are recorded in October 2025; check stability before choosing a baseline.
- Recent months are open: future end dates are scheduled cancellations and still active.
- User expects no particular result (none given).

## Out of scope
- Groups other than plan and tenure: the business cannot target them.
- Free users as a retention group.
- Acquisition (new signups) except where it changes the revenue math.
- Plan switches (monthly to annual, paid to free): the data holds one subscription per user and shows no trace of switches, so they cannot be measured. The user chose to carry this as a caveat only (2026-11-07); a switcher recorded as a cancellation would count as churn.

## Open questions
- Exact date the new price took effect, and whether existing subscribers moved to $12 at their next billing date.
- Whether the baseline survives the October 2025 end-date recording change.
- How far back the data goes for the seasonality check.
