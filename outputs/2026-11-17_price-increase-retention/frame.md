# Frame: March 2026 price increase and retention

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did monthly churn rise after the monthly price went from $10 to $12 on 2026-03-01, by more than the price rise can pay for, and in which groups Beam could price separately?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customers, and for which group.

## Audience
The head of growth.

## Population
Paid monthly subscribers: existing ones who first paid $12 at a renewal from March 2026, and new monthly starts who paid $12 from day one. Nothing is off limits if the data gives a good reason for it; the user expects new signups to be the easiest group to treat differently.
- Analyst suggestion: tenure band at the renewal, the four standard bands (long-tenure subscribers may react differently to a price change, and grandfathering them is a lever).
- Analyst suggestion: start cohort, new starts before vs after 2026-03-01 compared at the same tenure (this is the new-signups lever the user named).
- Analyst suggestion: region (US, EU, India, Rest) and signup device (iOS, Android, Web) (regional or app-store pricing is a realistic lever).
- Analyst suggestion: annual subscribers as a reference group only (their price did not change).
- Peer suggestion: a minimum group size and confidence intervals for every split, so a small group that looks worse by chance is not read as a finding.

## What would change the decision
Roll back for a group if its churn rose so much that the new price would be unprofitable longer term.
- Analyst suggestion: with a steady monthly churn rate, revenue per subscriber is price / churn, so $12 stays ahead of $10 unless churn rose by more than 20% relative to before (for example 5.0% to 6.0%). Show before and after rates in percentage points and the relative change against that 20% line.
- Analyst suggestion: the money at stake for each group over 12 months, for the whole group: the extra $2 a month from those who stay, against the revenue lost to extra churn.
- Peer suggestion: the monthly vs annual share of new paid starts, and new monthly starts per month, before vs after, since the price rise could move new customers to annual or put them off before churn shows it.

## Tables likely involved
- public.payments: prices charged, and monthly churn from missed renewals.
- public.subscriptions: plan, start date for tenure and start cohort, annual churn from end_date.
- public.users: region and signup device.

## Analysis window
Before: renewals due 2025-11-01 to 2026-02-28. After: renewals due 2026-03-01 to 2026-07-31. New paid starts compared over the same months.

## Additional context
- The user knows of no other changes around March 2026.
- Only the monthly price changed ($10 to $12 for charges from 2026-03-01); annual stayed at $100.

## Out of scope
- Trials, users with a trial record, and anything from 2026-08-01 on (trial launch; correction of 2026-11-07).
- Sep to Oct 2025 and earlier as a churn baseline (unexplained churn bump, and long-tenure churn that only appears from October 2025).
- Free users, who have no churn.
- Plan switches by existing subscribers, which the data cannot show (one subscription per user).

## Open questions
- Seasonality: no year-ago baseline is like for like, so a Nov-Feb vs Mar-Jul difference cannot be fully separated from season.
- Peer suggestion: no group escaped the price change, and annual renewals in the window are likely too few to act as a real control.
- February 2026 starters have their first renewal at $12, so that cohort straddles the change.
- Whether the 2025-09-17 block and the 2026-07-30 block (403 paid starts) distort the cohorts; show them separately or leave them out.
- 235 paid subscriptions from the 2025-09-17 block have no payments and cannot enter the renewal measure.
