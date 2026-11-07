# subscriptions

Grain (a guess from the data, confirm it): one row per subscription_id. 30,747 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| subscription_id | int64 | 0.00% | 30,747 |
| user_id | int64 | 0.00% | 30,747 |
| plan | object | 0.00% | 3 |
| start_date | datetime64[ns] | 0.00% | 9,584 |
| end_date | datetime64[ns] | 87.90% | 1,789 |
| status | object | 0.00% | 3 |

## Date ranges

- `start_date`: 2022-01-11T00:00:00 to 2026-10-04T17:15:33
- `end_date`: 2022-03-07T00:00:00 to 2026-11-11T18:47:46

## Low-cardinality values

- `plan`: free (18,234), monthly (9,376), annual (3,137)
- `status`: active (27,028), expired (2,929), canceled (790)

## Meaning


Grain in plain words (inferred): one row per subscription, and each user has exactly one subscription (user_id is also unique), so a plan change is not visible as a new row.

- `subscription_id`: key; joins to `payments.subscription_id` (inferred).
- `user_id`: the subscriber; every value is in `users` (checked 2026-11-07) (inferred).
- `plan`: free, monthly ($10, $12 from 2026-03-01) or annual ($100) (inferred from payments).
- `start_date`: when the subscription began; the first payment falls on this date for every paid subscription started since 2025 (checked 2026-11-07). 1,549 rows start after 2026-09-24 (quirk: future start dates).
- `end_date`: when the subscription ended or is scheduled to end; null for every `active` row and every free row (quirk: free plans never end). 162 rows end after 2026-09-24, all `canceled` (quirk: future end dates). Recording changed around October 2025: before it, end_date sits exactly 30 days after the last payment; after it the gap is shorter and drifts (median 14 to 25 days in 2026), and the share with midnight times falls from 100% to about 60% (`stable_over_time` break in 2025-10) (inferred). Do not measure tenure from end_date across that change; use payments.
- `status`: active (no end date), expired (ended), canceled (ended or scheduled to end; only end dates from 2026-08 onward carry it) (inferred).

Monthly starts by month are about 140 to 220 a month, except September 2025 (1,181; quirk: September 2025 spike), October 2025 (67), July 2026 (491, none from trials, unexplained) and August to September 2026 (trial conversions).
