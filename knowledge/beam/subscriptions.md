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
- `user_id`: the subscriber; joins to `users.user_id`. Exactly one subscription per user, so a plan switch (monthly to annual, paid to free) is not visible as a second row (inferred).
- `plan`: free, monthly or annual (inferred). Free rows never end (quirk "Free plans never end").
- `start_date`: when the subscription began; first payment falls on this day for paid plans started since Feb 2025 (inferred). 102 free rows and 582 paid rows start after 2026-09-24 (the free ones all trial users) (quirk "Future start dates").
- `end_date`: when the subscription ended or will end; null means still running (inferred). 150 rows end after 2026-09-24, all status `canceled` (quirk "Future end dates"). Midnight-only times until Sep 2025, then a mix of real times (quirk on the October 2025 recording change in corrections.md).
- `status`: active (no end date), canceled (end date set, 150 of 790 still in the future), expired (ended) (inferred).

Grain in plain words: one row per user's subscription; a user has exactly one (inferred).

Facts from profiling on 2026-11-07:
- Monthly end dates per month jump from about 20-35 (2025-01 to 2025-09) to about 115-145 (2025-10 to 2026-03), the same month end-date times start changing; then to about 250-355 (2026-04 to 2026-09). Read the October 2025 jump with the recording change in mind.
- 1,391 paid subscriptions have no payment row: 533 ended before payments start (2025-01-01); 582 paid subscriptions (425 monthly, 157 annual) start after 2026-09-24, so have no payment yet (scheduled starts, expected; corrected 2026-11-07); 235 started in the 2025-09 spike, all ended after 30-360 days with no payment (unexplained); the rest are small.

