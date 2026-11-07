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

- Grain in plain words: one row per subscription, and each user appears once (user_id is distinct on every row), so one subscription per user (inferred).
- `subscription_id`: the subscription's key; payments join on it (inferred).
- `user_id`: the subscriber; joins to users (inferred).
- `plan`: free, monthly ($10, then $12 from March 2026, per the monthly price change quirk) or annual (inferred).
- `start_date`: when the subscription began. Some are after 2026-09-24: scheduled starts, per the future start dates quirk; exclude them from counts of what has happened (inferred).
- `end_date`: when the subscription ended or is scheduled to end. The 87.9% nulls are free plans (free plans never end quirk) plus paid subscriptions still running. Dates after 2026-09-24 are scheduled cancellations that are still active today (future end dates quirk). Per corrections.md, end dates changed how they are recorded in October 2025; check with stable_over_time before comparing across it (inferred).
- `status`: active, expired or canceled. The difference between expired and canceled is not documented here; it may be lapse at renewal against an explicit cancellation (inferred).
- Mixed timestamps: some dates carry midnight, others a real time (timestamps everywhere quirk).

