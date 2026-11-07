# Frame: March 2026 price increase and retention (v2)

## Question
Raw: "Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers."
Framed: Did the March 2026 monthly price increase ($10 to $12) lower retention of monthly subscribers, compared only with subscribers at the same tenure, and for which customer groups?

## Decision it informs
Whether to roll back part of the March 2026 price increase for some customer groups.

## Audience
Head of growth.

## Population
Paying monthly-plan subscribers.
- Analyst suggestion: tenure (time since the subscriber started), so customers are only compared with others at the same stage (the user asked for like-for-like tenure in the first run).
- Analyst suggestion: start cohort, to separate the September 2025 signup spike and post-increase starters, who only ever saw $12.
- Analyst suggestion: country (US, EU, India, Rest) and device (Web, Android, iOS), the customer attributes in users.
- Annual-plan subscribers over the same months as a comparison group (peer suggestion, added by the user): their price did not change, so their churn shows what moved for reasons other than price.

## What would change the decision
Analyst suggestion: a group whose monthly churn rose clearly more than other groups' at the same tenure, beyond what annual-plan churn shows moved anyway, and where the revenue lost to that extra churn outweighs the extra $2 a month from those who stayed, over 6, 12 and 24 months. The analysis plan should make this measurable and show it to the user first.

## Tables likely involved
- subscriptions: plan, start and end dates; defines tenure, cohort and churn
- payments: price paid and realised revenue
- users: country and device for segmenting

## Analysis window
Baseline October 2025 to February 2026; after the increase March 2026 to August 2026 (September 2026 is open, data ends 2026-09-24). Cancellation dates were recorded differently up to and partly in September 2025, so earlier months are not a fair baseline (peer suggestion, added by the user).

## Additional context
- The user knows of no other changes in the period.
- Every monthly payment moved to $12 on 2026-03-01; no subscriber kept the old price.
- Quirks and corrections that apply: end dates recorded differently before October 2025; one subscription per user; free plans excluded; future start and end dates; September 2025 signup spike; compare on dates.
- The first run of this question is in outputs/2026-11-06_march-price-retention for comparison.

## Out of scope
- Annual plan pricing.
- Trial design and trial conversion: trials started on 2026-08-01, after the increase, so there is no before to compare with.

## Open questions
- Switches from monthly to annual or free are not visible (one subscription per user, and no subscription has both monthly and annual payments), so a switch may look like a cancellation or not at all (peer suggestion, added by the user).
- Only six closed months exist after the increase; 12- and 24-month revenue is a projection that assumes churn stays at its post-increase level, and is labelled as one (peer suggestion, added by the user).
- Why cancellation dates are recorded differently from October 2025.
