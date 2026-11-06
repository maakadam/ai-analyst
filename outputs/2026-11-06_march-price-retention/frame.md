# Frame: March 2026 price increase and retention

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did the March 2026 monthly price increase ($10 to $12) lower retention of monthly subscribers, compared like for like by how long they had been subscribed, and for which customer groups?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customer groups.

## Audience
Head of growth.

## Population
Paying monthly-plan subscribers. The user's key dimension is how long they have been subscribed (tenure): comparisons are only made between subscribers with similar tenure. Analyst suggestion: also split by whatever user attributes exist in users (for example country, platform, channel) and by engagement (to find groups a partial rollback could target). Annual and free plans are not directly affected by the increase.

## What would change the decision
Not given. Analyst suggestion: a tenure group (or other segment) whose monthly churn rose clearly more after the increase than before at the same tenure, and more than other groups, where the revenue lost to that extra churn outweighs the extra $2 a month from those who stayed. The analysis plan should make this measurable and show it to the user first.

## Tables likely involved
- subscriptions: plan, start and end dates; defines tenure and churn (no note yet)
- payments: amounts paid; dates when each subscriber first paid $12 and revenue per subscriber (no note yet)
- users: customer attributes for segmenting (no note yet)
- user_activity_metrics: engagement as a possible segment (no note yet)

## Analysis window
Analyst suggestion: September 2025 to 2026-09-24 (the data end), about six months either side of the March 2026 increase.

## Additional context
- The user knows of no other changes in the period (campaigns, launches, other price moves, grandfathering).
- Quirks that apply: monthly price rose $10 to $12 in March 2026; September 2025 signup spike (cohort sizes and mix shift); free plans excluded from churn; future end dates mean still active; future start dates excluded; trials launched 2026-08-01 and recent trials are unmatured; compare on dates, not timestamps.
- Peer questions raised at framing, not yet acted on: whether annual subscribers are a fair comparison group; when each existing subscriber first paid $12, and whether post-March new starts are self-selected; weighing extra churn against extra revenue.

## Out of scope
- Annual plan pricing (the increase was on the monthly plan).
- Trial design and trial-to-paid pricing (trials only began 2026-08-01, mostly after the increase).

## Open questions
- Exact date of the increase in March 2026, and whether existing subscribers moved to $12 at their next renewal.
- Which customer attributes the users table holds.
- Whether monthly subscribers who switched to annual or free count as churned.
