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

- `subscription_id`: the subscription's key; joins to `payments.subscription_id` (inferred).
- `user_id`: the subscriber; joins to `users.user_id` without fan-out. Exactly one subscription per user, so plan switches (monthly to annual, paid to free) are not visible (inferred).
- `plan`: free, monthly or annual. Free rows never have an end date and never have payments (quirk "Free plans never end").
- `start_date`: when the subscription began. For paid plans started since Feb 2025 the first payment falls on the same day (all 7,040). Rows starting after 2026-09-24: 967 free, 425 monthly, 157 annual (quirk "Future start dates"). Bulk start days: 1,385 rows on 2025-09-17 (the September 2025 spike), 403 paid (302 monthly, 101 annual) on 2026-07-30, 582 paid on 2026-09-25 (inferred).
- `end_date`: when the subscription ended or will end; null exactly when status is active. 162 end after 2026-09-24, all canceled (quirk "Future end dates"). Until 2025-09, monthly end dates are midnight and fall exactly 30 days after the last payment (a paid-through date); from 2025-10 a growing share carry real times and fall 1 to 30 days after the last payment, and 14% to 29% of monthly ends in 2025-10 to 2026-02 fall more than 31 days after the last payment (inferred).
- `status`: active (no end date), canceled (end date set, may be in the future), expired (ended) (inferred).

Grain in plain words: one row per user's subscription; a user has exactly one (inferred).

Facts from profiling on 2026-11-07:
- Monthly end dates per month: about 20-35 (2024-07 to 2025-08), 55 in 2025-09, about 115-145 (2025-10 to 2026-03), about 250-340 (2026-04 to 2026-07). Read these against the active base: the 1,181 monthly starts on the 2025-09 spike inflate both.
- Monthly starts per month: about 140-220, except 1,181 in 2025-09, 67 in 2025-10 and 491 in 2026-07 (302 of them on 2026-07-30).
- 1,391 paid subscriptions have no payment row: 533 ended before payments start (2025-01-01), 582 start after 2026-09-24, 235 started in the 2025-09 spike (unexplained), the rest are small.
