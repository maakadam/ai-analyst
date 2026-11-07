# payments

Grain (a guess from the data, confirm it): one row per payment_id. 100,914 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| payment_id | int64 | 0.00% | 100,914 |
| subscription_id | int64 | 0.00% | 11,122 |
| payment_date | datetime64[ns] | 0.00% | 13,232 |
| amount_usd | float64 | 0.00% | 3 |
| method | object | 0.00% | 4 |

## Date ranges

- `payment_date`: 2025-01-01T00:00:00 to 2026-09-24T23:51:30

## Low-cardinality values

- `amount_usd`: 10.0 (59,064), 12.0 (37,384), 100.0 (4,466)
- `method`: card (50,237), paypal (20,272), apple_pay (15,298), google_pay (15,107)

## Meaning


Grain in plain words (inferred): one row per successful charge. Only successful charges appear; there is no status, failure or refund column, so a failed payment cannot be told apart from a voluntary cancellation.

- `payment_id`: key (inferred).
- `subscription_id`: every value is in `subscriptions` (checked 2026-11-07) (inferred).
- `payment_date`: charge date; monthly charges fall on the start-date anniversary, about one per month while active. Coverage starts 2025-01-01, so earlier history is missing for older subscriptions.
- `amount_usd`: $10 monthly up to 2026-02-28, $12 monthly from 2026-03-01 for every monthly subscriber, new and existing (no grandfathering; no $10 charge after 2026-02-28), $100 annual (quirk: monthly price change) (checked 2026-11-07).
- `method`: card, paypal, apple_pay, google_pay (inferred).

Annual charges spike in September 2025 (445) and September 2026 (567), in line with the September 2025 signup spike and its first renewal.
