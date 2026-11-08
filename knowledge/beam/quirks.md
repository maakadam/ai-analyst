# Beam data quirks

Things we know about our own tables. Check this list before reading a number as a finding.

- **Monthly price change.** The monthly plan price rose from $10 to $12 in March 2026. Monthly payments before and after that point differ for that reason, not because of a data problem.
- **Trials mature late.** Trials launched on 2026-08-01 and last 14 days. A trial's outcome is only known once it matures, so recent trials show `outcome` empty. Those are still open and must not be counted as failures.
- **Free plans never end.** Rows with `subscriptions.plan = 'free'` have no `end_date`. Exclude them from any churn or retention calculation.
- **Future end dates.** `subscriptions.end_date` can be in the future for scheduled cancellations. A subscription with a future end date is still active today.
- **Future start dates.** A few subscriptions have a `start_date` after today: they are scheduled starts, mostly trials that will convert when they mature. Exclude rows that start after the analysis date from any count of what has happened.
- **September 2025 spike.** September 2025 shows a signup spike of roughly five times a normal month, with a matching jump in the active base and in monthly actives. The daily-to-monthly active ratio falls from about .25 to about .21 at that point. Treat it as a known anomaly and say so whenever it enters a comparison.
- **Timestamps everywhere.** Dates in the exports are timestamps. Many `users.signup_date` and subscription dates carry midnight times, others carry real times; compare on dates, not on timestamps, unless the time of day matters.
- **End-date recording change.** Until September 2025, monthly `subscriptions.end_date` values are midnight and fall exactly 30 days after the last payment (a paid-through date). From October 2025 many carry real times and fall 1 to 30 days after the last payment, and some fall more than 31 days after it. Measure monthly churn from the last payment, not from `end_date`.
- **Bulk start days.** 1,385 subscriptions start on 2025-09-17 (the September 2025 spike), 403 paid ones on 2026-07-30 and 582 paid ones on 2026-09-25. Treat each as a block, not as organic signups, and say so whenever one enters a comparison.
- **Price switch on one day.** Every monthly charge before 2026-03-01 is $10 and every one from 2026-03-01 is $12. Existing monthly subscribers moved to $12 at their first charge in March 2026. Annual stayed at $100.
- **One subscription per user.** `subscriptions` has exactly one row per user, so plan switches (monthly to annual, paid to free) cannot be seen in the data.
- **Payments start in 2025.** `payments` begins on 2025-01-01; nothing before 2025 can be read from it, though subscription dates go back to 2022.
- **Paid subscriptions without payments.** 235 paid subscriptions from the September 2025 spike have no payment rows. Unexplained; say so whenever they enter a count. A further 582 paid subscriptions have no payments because they start after 2026-09-24 (quirk "Future start dates"); that is expected.
- **Long-tenure churn appears in Oct 2025.** Monthly subscriptions that started before 2024 have no end dates and no missed payments from 2024 (2022 starts) or 2025 (2023 starts) until September 2025, then churn at about 1% a month from October 2025. Unexplained; a churn baseline before October 2025 is not like for like for subscribers past 12 months' tenure.
- **Sep-Oct 2025 churn bump.** Monthly subscribers who started January to September 2025, outside the 2025-09-17 block, miss 7% to 14% of renewals due in September and October 2025, against about 1% to 2% in the months either side. Unexplained; leave Sep-Oct 2025 out of churn baselines or show it separately.
