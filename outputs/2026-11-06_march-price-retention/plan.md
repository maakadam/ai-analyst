# Analysis plan (approved 2026-11-06)

- Unit: monthly-plan subscriber-months. At risk in a month if active at its start (started before, not ended before); churned if end_date falls in that month. Closed months only: Mar 2025 to Aug 2026 (Sep 2026 is open, data ends 2026-09-24).
- Headline: monthly churn after the increase (Mar-Aug 2026) vs before (Mar 2025-Feb 2026), matched by tenure band (0-2, 3-5, 6-11, 12-23, 24+ months), as percentage points and relative %. Sensitivity baseline: same months a year earlier (Mar-Aug 2025).
- Segments: tenure band, country, device. The before rate of each segment is reweighted to its after-period tenure mix, so comparisons are like for like by tenure.
- Rollback test per segment: lifetime revenue ratio = (12 / churn after) / (10 / churn before). Below 1 means the increase lowered lifetime revenue for that segment (relative churn rise above 20%).
- Comparison group: annual-plan churn over the same months (price unchanged).
- Quirks: free plans excluded; future starts excluded; Sep 2026 open and excluded; Sep 2025 signup cohort flagged and a rerun without it; dates compared as dates.
- Checks: join fan-out subscriptions to users; segments sum to totals; month boundaries; closed months only.
- Not covered: plan switches (one row per user), trial conversion, engagement (activity table has no user id).
