# users

Grain (a guess from the data, confirm it): one row per user_id. 31,165 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| user_id | int64 | 0.00% | 31,165 |
| signup_date | datetime64[ns] | 0.00% | 12,512 |
| country | object | 0.00% | 4 |
| device_type | object | 0.00% | 3 |

## Date ranges

- `signup_date`: 2022-01-01T00:00:00 to 2026-09-24T22:59:05

## Low-cardinality values

- `country`: US (12,472), Rest (6,270), India (6,238), EU (6,185)
- `device_type`: Web (10,466), Android (10,363), iOS (10,336)

## Meaning

- `user_id`: the user's key; every subscription's user is here, and the join to subscriptions does not fan out (inferred).
- `signup_date`: account creation; a subscription starts 0 to 90 days after it (median 33) (inferred). All midnight times to 2024, about half in 2025, none in 2026 (quirk "Timestamps everywhere").
- `country`: US, EU, India, Rest; no nulls (inferred).
- `device_type`: Web, Android, iOS; no nulls (inferred).

Grain in plain words: one row per user account; 418 users (open trials) have no subscription yet (inferred).
