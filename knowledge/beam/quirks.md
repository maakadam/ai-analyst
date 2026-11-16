# Beam data quirks

Facts that span more than one table, or that are about how to read results. Check this list before reading a number as a finding.

**Where a new fact goes:**
- A fact about one table goes in `knowledge/beam/<table>.yaml`: in the field's description if it changes how SQL is written, otherwise in its `notes`.
- A fact goes here only if it involves two or more tables, or if it is about how to read results rather than how to query.
- One home per fact: never write it in both places. If a line here turns out to be about one table, move it to that table's YAML.

## Quirks

- **September 2025 spike.** September 2025 shows a signup spike of roughly five times a normal month, with a matching jump in the active base and in monthly actives. The daily-to-monthly active ratio falls from about .25 to about .21 at that point. Treat it as a known anomaly and say so whenever it enters a comparison.
- **Timestamps everywhere.** Dates in the tables are timestamps. Many `users.signup_date` and subscription dates carry midnight times, others carry real times; compare on dates, not on timestamps, unless the time of day matters.
- **Long-tenure churn appears in Oct 2025.** Monthly subscriptions that started before 2024 have no end dates and no missed payments from 2024 (2022 starts) or 2025 (2023 starts) until September 2025, then churn at about 1% a month from October 2025. Unexplained; a churn baseline before October 2025 is not like for like for subscribers past 12 months' tenure.
- **Sep-Oct 2025 churn bump.** Monthly subscribers who started January to September 2025, outside the 2025-09-17 block, miss 7% to 14% of renewals due in September and October 2025, against about 1% to 2% in the months either side. Unexplained; leave Sep-Oct 2025 out of churn baselines or show it separately.
