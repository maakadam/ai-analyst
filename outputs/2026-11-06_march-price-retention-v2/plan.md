# Analysis plan (v2)

- Unit: subscriber-months. At risk in a month if active at its start; churned if the end date falls in that month. Closed months only.
- Baseline check in code: `stable_over_time` on monthly end dates (days after last payment, time of day) from March 2025; the baseline starts after the last break.
- Headline: monthly-plan churn March to August 2026 against October 2025 to February 2026, matched by tenure band (0-2, 3-5, 6-11, 12-23, 24+ months), in percentage points and relative %, with an approximate 95% range.
- Comparison group: annual-plan churn over the same months, tenure-matched; the price effect is the monthly change minus the annual change, in points.
- Groups: tenure band, start cohort, country, device. Each group's rise is tested against the rise of everyone else (ratio of rate ratios with a 95% range); only groups whose range excludes no difference are called different.
- Revenue: per 100 subscribers, cumulative revenue at $12 with after-churn against $10 with before-churn over 6, 12 and 24 months, and the month where $12 stops paying. 12 and 24 months are projections that hold churn at its after level.
- Quirks: free plans and future starts excluded; September 2026 open; September 2025 cohort as its own cohort; dates compared as dates.
- Checks: join fan-out, segments sum to totals, month boundaries, closed months only.
