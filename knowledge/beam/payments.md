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

- `payment_id`: the payment's key (inferred).
- `subscription_id`: the subscription paid for; every value matches `subscriptions`; no free subscription has a payment (inferred).
- `payment_date`: when the charge happened. Starts 2025-01-01, so nothing before 2025 can be read from it (inferred).
- `amount_usd`: monthly charges are $10 or $12, annual are $100. Every monthly charge up to 2026-02-28 is $10 and every one from 2026-03-01 is $12, with no $10 charge after that, so existing monthly subscribers moved to $12 at their first charge in March 2026. Annual stayed at $100 in 2025 and 2026 (inferred).
- `method`: card, paypal, apple_pay, google_pay (inferred).

Grain in plain words: one row per charge; monthly subscriptions usually have one charge per month, 1,603 subscription-months have two (inferred).

Facts from profiling on 2026-11-07:
- No monthly subscription has a payment after its end date, and every active monthly subscription has paid since 2026-08-20, so the last payment is a reliable marker of when a monthly subscriber stopped paying (inferred).
