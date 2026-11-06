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

Each row is one user's subscription (inferred). `user_id` is distinct on every row, so the table holds one subscription per user: a plan change (for example monthly to annual) is not visible as a new row (inferred).

- `subscription_id`: key of the subscription; joins to `payments.subscription_id` (inferred).
- `user_id`: the subscriber; joins to `users.user_id` (inferred).
- `plan`: free, monthly or annual. Free rows never end (quirk: Free plans never end) and are excluded from churn (inferred).
- `start_date`: when the subscription began. Some are after 2026-09-24 (quirk: Future start dates) and must be excluded from counts of what happened (inferred).
- `end_date`: when the subscription ended or is scheduled to end; empty while active. The 87.90% null rate is mostly free plans plus active paid plans (quirk: Free plans never end). Values after 2026-09-24 are scheduled cancellations still active today (quirk: Future end dates) (inferred).
- `status`: active, expired or canceled. Read churn from `end_date` against the analysis date, not from `status`, since scheduled cancellations may read either way (inferred).

