# Frame: March 2026 price increase and retention

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did monthly-plan churn rise after the March 2026 price increase ($10 to $12), for which groups the business can price separately did it rise most, and does the revenue lost to extra churn outweigh the revenue gained from the higher price?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customers, and for which ones.

## Audience
The head of growth.

## Population
Paid monthly subscribers: the only plan whose price changed (monthly $10 to $12 on charges from 2026-03-01; annual unchanged at $100). Free plans and trial users are left out.
The user named tenure and new vs existing subscribers as the likely levers the business can price separately.
- Tenure band (under 6, 6 to 12, 12 to 24, over 24 months): user lever; long-standing customers may react to a rise differently from recent ones.
- New vs existing: existing started before 2026-03-01 and met the rise at a renewal; new started at $12. User lever.
- For existing subscribers, the after period starts at each subscriber's first renewal charged at $12, not at 2026-03-01. Renewals not yet due by the analysis date are left out. (Peer suggestion, approved by the user.)
- Analyst suggestion: start cohort (start month), so each group is compared with others at the same stage.
- Analyst suggestion: region (country) and signup device as secondary splits, reported only as context unless the business says it can price them separately.
- Analyst suggestion: annual subscribers shown as context only, not as a control (too few renewals and too different a plan).

## What would change the decision
The user: too big a drop in retention or revenue.
- Analyst suggestion: a rise in monthly churn after March in a group the business can price separately, in percentage points against that group's own baseline before March.
- Analyst suggestion: per group, revenue gained from the $2 rise against revenue lost to extra churn over 12 months, in dollars for the whole group. A rollback is worth considering only where the loss outweighs the gain.
- The analysis plan should make "too big" measurable and show it to the user first.

## Tables likely involved
- public.payments: missed monthly renewals (monthly churn), prices charged and revenue.
- public.subscriptions: plan, start date, tenure band, annual churn from end_date.
- public.users: region and signup device, and to drop users with a trial record (with public.trials).
- public.trials: to identify and leave out users with a trial record.

## Analysis window
Before: renewals due November 2025 to February 2026. After: renewals due March to July 2026.

## Additional context
- The user does not know the rollout details. payments.yaml says every monthly charge from 2026-03-01 is $12, so existing subscribers paid the new price at their first renewal after that date.
- The user knows of no other changes in the period.

## Out of scope
- Everything from 2026-08-01 on, and users with a trial record: trials launched then (corrections.md, 2026-11-07).
- Baselines before November 2025: September to October 2025 has an unexplained churn bump, and long-tenure churn only appears from October 2025 (quirks.md). The same months a year earlier are not used as a season check (corrections.md, 2026-11-08; user confirmed on 2026-11-17).

## Open questions
- Plan switches are not directly visible (one subscription row per user). Analyse should check whether payments reveal them, for example a monthly subscription charged $100. If not, the brief says switches were not counted, so churn may overstate lost customers and the revenue math may overstate lost revenue. (Peer suggestion, approved by the user.)
- No clean season check exists: a year-earlier comparison is ruled out and annual renewals are too few and too different to be a control. The brief says seasonality is not separated from the price effect.
- The 2026-07-30 block of 403 paid starts falls inside the window; flag it or leave it out.
- Analyse confirms the analysis date and that July 2026 renewals are closed by it.
