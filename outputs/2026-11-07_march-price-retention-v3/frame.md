# Frame: March 2026 price increase and retention

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did monthly-plan retention fall after the March 2026 price increase ($10 to $12 a month), compared like for like with before it, which customer groups moved most, and how much revenue is at stake for those groups?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customers.

## Audience
The head of growth.

## Population
Which customer groups Beam can actually charge differently (new against existing customers, country, platform, channel): not given. The analysis looks at all groups, and the brief should say which pricing lever any recommendation would need.
- Analyst suggestion: paying monthly subscribers active on or after the increase, with annual subscribers as a comparison group that did not get the monthly price change (separates the price effect from a general drift in retention).
- Analyst suggestion: split by tenure (months since the subscription started), so customers are compared only with others at the same stage; churn is usually highest in the first months whatever the price.
- Analyst suggestion: split by start cohort, in particular existing subscribers who started before March 2026 (who saw their price rise) against new subscribers who started after (who only ever saw $12); a rollback could target one and not the other.
- Analyst suggestion: split by plan (monthly, annual; free excluded from churn), since only the monthly price rose.
- Analyst suggestion: split by the customer attributes the users table holds once profiled (for example country, platform, acquisition channel), since a rollback by group needs a group that reacted differently.

## What would change the decision
Not given.
- Analyst suggestion: a rollback is worth considering for a group if its monthly churn rose clearly after the increase, beyond noise and beyond the change in a comparison group, at the same tenure, and the revenue it loses to extra churn is larger than the revenue the higher price brings in from that group. If churn did not rise, or rose evenly in every group, a targeted rollback is not supported.
- The analysis plan should make this measurable and show it to the user first.

## Tables likely involved
- subscriptions: plan, start and end dates, so churn by month, tenure and cohort (no note yet).
- payments: amounts paid, to confirm the price each subscriber paid and to size revenue at stake (no note yet).
- users: customer attributes (country, platform, channel) for the group splits (no note yet).
- trials: trials launched on 2026-08-01 may feed new monthly subscribers, which would change who the "new subscriber" group is (no note yet).

## Analysis window
Not given.
- Analyst suggestion: after-period March 2026 to August 2026 (the last full month before the data ends on 2026-09-24; September 2026 is partial). Baseline: the months before March 2026 in which subscription end dates are recorded the same way; per corrections.md the recording changed in October 2025, so the default baseline is October 2025 to February 2026, checked with stable_over_time before use. A same-season baseline a year earlier is used only if the end dates are recorded the same way then.

## Additional context
- The user knows of no other changes in the period (campaigns, launches, other price moves).
- No expected result given.
- Known from quirks.md, not from the user: trials launched on 2026-08-01; a September 2025 signup spike of about five times a normal month; subscription end dates changed how they are recorded in October 2025 (corrections.md).

## Out of scope
- Free plan users: they never end, so they have no churn (quirks.md).
- Trial conversion as an outcome in itself; trials enter only as a possible change in who new subscribers are.
- Setting a new price level; the analysis says whether and for whom retention fell, not the optimal price.

## Open questions
- Which customer groups Beam can price differently (new against existing, country, platform, channel): not known; the brief must name the lever any recommendation needs.
- Whether the annual plan price also changed in March 2026: quirks.md mentions only the monthly plan; the payments data will show it.
- Whether the October 2025 change in how end dates are recorded leaves enough clean baseline months, and of what season.
- Profile found two points no quirk explains (proposed as quirks, not appended because the user could not be asked): payments start on 2025-01-01, so there is no payment history before 2025; and `subscriptions.status` holds only "expired" for paid subscriptions ending up to July 2026 and only "canceled" from August 2026, so status cannot tell cancellations from lapses.
- The users table has no acquisition channel column, so channel cannot be split; country (US, EU, India, Rest) and device type (Web, Android, iOS) can.
