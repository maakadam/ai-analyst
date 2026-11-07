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

- Grain in plain words: one row per payment; a subscription has many payments, so joining payments onto subscriptions fans out unless payments are first aggregated per subscription (inferred).
- `payment_id`: the payment's key (inferred).
- `subscription_id`: the subscription the payment is for; 11,122 distinct, about the number of paid (monthly plus annual) subscriptions (inferred).
- `payment_date`: when the payment was taken. The table starts on 2025-01-01, so payment history before 2025 is not in this export (inferred; not explained by a quirk).
- `amount_usd`: only three values: 10 and 12 (monthly before and after the March 2026 price change, per the monthly price change quirk) and 100 (annual). The annual amount is the same throughout, so the annual price did not change (inferred).
- `method`: card, paypal, apple_pay or google_pay (inferred).

