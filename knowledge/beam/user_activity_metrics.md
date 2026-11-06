# user_activity_metrics

Grain (a guess from the data, confirm it): no id column found. 998 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| date | datetime64[ns] | 0.00% | 998 |
| dau | int64 | 0.00% | 842 |
| wau | int64 | 0.00% | 950 |
| mau | int64 | 0.00% | 985 |

## Date ranges

- `date`: 2024-01-01T00:00:00 to 2026-09-24T00:00:00

## Low-cardinality values

- None

## Meaning

One row per calendar day from 2024-01-01 to 2026-09-24 (inferred). Platform-wide totals only: there is no user id, so the table cannot segment customers or join to subscriptions (inferred).

- `date`: the day (inferred).
- `dau`: daily active users (inferred).
- `wau`: weekly active users, trailing seven days (inferred).
- `mau`: monthly active users, trailing month. The September 2025 jump and the DAU/MAU fall from about .25 to .21 are a known anomaly (quirk: September 2025 spike) (inferred).

