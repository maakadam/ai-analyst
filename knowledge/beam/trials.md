# trials

Grain (a guess from the data, confirm it): one row per trial_id. 2,073 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| trial_id | int64 | 0.00% | 2,073 |
| user_id | int64 | 0.00% | 2,073 |
| started_at | datetime64[ns] | 0.00% | 2,071 |
| ends_at | datetime64[ns] | 0.00% | 2,071 |
| outcome | object | 20.16% | 2 |
| outcome_at | datetime64[ns] | 20.16% | 1,655 |

## Date ranges

- `started_at`: 2026-08-01T00:29:17 to 2026-09-24T22:59:05
- `ends_at`: 2026-08-15T00:29:17 to 2026-10-08T22:59:05
- `outcome_at`: 2026-08-06T05:37:23 to 2026-09-24T23:55:08

## Low-cardinality values

- `outcome`: converted (828), canceled (827)

## Meaning


Grain in plain words (inferred): one row per trial, one trial per user.

- `trial_id`: key (inferred).
- `user_id`: the trialist; about 80% have a subscription row (free, monthly or annual) (inferred).
- `started_at`, `ends_at`: 14-day window; trials start from 2026-08-01 (quirk: trials mature late).
- `outcome`: converted or canceled; null for the 418 trials still open, none of which had ended by 2026-09-24 (quirk: trials mature late).
- `outcome_at`: when the outcome was recorded; null exactly when outcome is null.

Trials exist only after the March 2026 price change, so they cannot be compared before and after it.
