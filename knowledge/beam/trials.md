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

- Grain in plain words: one row per trial, one trial per user (inferred).
- `trial_id`: the trial's key (inferred).
- `user_id`: the user on trial; joins to users and subscriptions (inferred).
- `started_at`: when the trial began; all from 2026-08-01, when trials launched (trials mature late quirk) (inferred).
- `ends_at`: 14 days after started_at (trials mature late quirk) (inferred).
- `outcome`: converted or canceled; the 20.2% nulls are trials not resolved yet, which must not be counted as failures (trials mature late quirk) (inferred).
- `outcome_at`: when the outcome happened; null where outcome is null (inferred).

