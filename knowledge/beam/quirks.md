# Beam data quirks

Things we know about our own tables. Check this list before reading a number as a finding.

- **Monthly price change.** The monthly plan price rose from $10 to $12 in March 2026. Monthly payments before and after that point differ for that reason, not because of a data problem.
- **Trials mature late.** Trials launched on 2026-08-01 and last 14 days. A trial's outcome is only known once it matures, so recent trials show `outcome` empty. Those are still open and must not be counted as failures.
- **Free plans never end.** Rows with `subscriptions.plan = 'free'` have no `end_date`. Exclude them from any churn or retention calculation.
- **Future end dates.** `subscriptions.end_date` can be in the future for scheduled cancellations. A subscription with a future end date is still active today.
- **Future start dates.** A few subscriptions have a `start_date` after today: they are scheduled starts, mostly trials that will convert when they mature. Exclude rows that start after the analysis date from any count of what has happened.
- **September 2025 spike.** September 2025 shows a signup spike of roughly five times a normal month, with a matching jump in the active base and in monthly actives. The daily-to-monthly active ratio falls from about .25 to about .21 at that point. Treat it as a known anomaly and say so whenever it enters a comparison.
- **Timestamps everywhere.** Dates in the exports are timestamps. Many `users.signup_date` and subscription dates carry midnight times, others carry real times; compare on dates, not on timestamps, unless the time of day matters.
- **Price switch on one day.** Every monthly charge before 2026-03-01 is $10 and every one from 2026-03-01 is $12. Existing monthly subscribers moved to $12 at their first charge in March 2026, not on a later renewal.
- **One subscription per user.** `subscriptions` has exactly one row per user, so plan switches (monthly to annual, paid to free) cannot be seen in the data.
- **Payments start in 2025.** `payments` begins on 2025-01-01; nothing before 2025 can be read from it, though subscription dates go back to 2022.
- **Paid subscriptions without payments.** 235 paid subscriptions from the September 2025 spike (all since ended) have no payment rows. Unexplained; say so whenever they enter a count. A further 582 paid subscriptions (425 monthly, 157 annual) have no payments because they start after 2026-09-24 (quirk "Future start dates"); that is expected, and they drop out once rows starting after the analysis date are excluded.
