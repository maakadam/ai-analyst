# Frame: March 2026 price increase and retention

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did the March 2026 monthly price increase ($10 to $12) lower retention among paying subscribers, and in which groups enough to justify rolling back part of the increase?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customer groups.

## Audience
Head of growth.

## Population
Paying monthly subscribers; annual subscribers only as a background check if their price did not change. Excluded: free plans, every user with a trial record, and subscriptions starting after the analysis window.
- Analyst suggestion: treatment is set per subscriber by their first $12 charge in payments (existing and new subscribers), not by calendar date alone; any monthly subscriber still paying $10 after March is a same-period comparison group (who was actually treated decides the comparison).
- Analyst suggestion: country (US, EU, India, Rest) (regional pricing is a usual lever and price sensitivity can differ by country).
- Analyst suggestion: device / store (Web, Android, iOS) (prices can be set per store).
- Analyst suggestion: tenure, time since start (grandfathering long-time subscribers is a lever; customers are compared only at the same tenure).
- Analyst suggestion: start cohort (like-for-like control, not a lever).
- Not treated differently: individual customers.

## What would change the decision
- Analyst suggestion: roll back for a group if its monthly churn after the increase, against the same tenure before it, rose enough to cancel the 20% price gain (expected subscriber lifetime down by more than about 17%); keep the increase where the rise is small or absent.
- Analyst suggestion: money at stake per group over 12 months: revenue at $12 with observed post-increase churn against $10 with pre-increase churn, for the whole affected group.
- Analyst suggestion: second outcome, the new paid start mix (monthly vs annual) and new monthly starts per month before vs after, to catch damage before churn.
- The analysis plan should make the threshold measurable and show it to the user first.

## Tables likely involved
- subscriptions: plan, start and end dates for churn and tenure.
- payments: who paid $10 or $12 and when, to set treatment and revenue.
- users: country and device for the groups.
- trials: only to identify trial users and confirm the trial launch date, so they can be excluded.

## Analysis window
- Before: 2025-09-01 to 2026-02-28.
- After: 2026-03-01 to 2026-07-31 (ends the day before trials launched on 2026-08-01; nothing from August or September 2026 is used).
- Analyst suggestion: seasonality check, 2025-03-01 to 2025-07-31 against 2026-03-01 to 2026-07-31, if end dates are recorded the same way in both years.
- Churn measured per subscriber-month of exposure; recent starts compared only at tenures reached by 2026-07-31.

## Additional context
- The user asked that the trial period not be included anywhere, since trials could change how people sign up and use the service.
- September 2025 signup spike (quirk) falls in the before window; flag it whenever it enters a comparison.

## Out of scope
- Everything from 2026-08-01 onward and all trial users (user's request; trial launch could change signup and usage).
- Trial conversion (no trials before the increase).
- Free plans (never end).
- Plan switches by existing subscribers, unless profiling shows they are visible.
- Annual subscribers as a primary control (renew once a year, too little churn to compare).

## Open questions
- Did existing monthly subscribers move to $12 in March, or only new ones?
- Did the annual price change?
- Is the subscription end date recorded the same way across the before, after and year-earlier periods?
- Are plan switches visible at all?
