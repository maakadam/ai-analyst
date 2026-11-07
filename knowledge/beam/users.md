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


Grain in plain words (inferred): one row per user, including users who never subscribed.

- `user_id`: key; joins to `subscriptions.user_id` one to one (inferred).
- `signup_date`: account creation; monthly subscribers typically start about 45 days after signup, but the September 2025 cohort started on the signup day (quirk: September 2025 spike) (inferred).
- `country`: US, EU, India, Rest; a plausible lever for regional pricing (inferred).
- `device_type`: Web, Android, iOS; a plausible lever because app-store pricing can differ by platform (inferred).
