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

- `trial_id`: the trial's key (inferred).
- `user_id`: the trial user; one trial per user (inferred).
- `started_at` / `ends_at`: always 14 days apart; every trial starts on or after 2026-08-01 (quirk "Trials mature late").
- `outcome`: converted (828) or canceled (827); empty for 418 open trials, all ending after 2026-09-24 and none with a subscription yet (quirk "Trials mature late").
- `outcome_at`: when the outcome happened. Converted trials became monthly (590) or annual (238), canceled ones free (827); the earliest such subscription starts 2026-08-15 (inferred).

Grain in plain words: one row per user's trial (inferred). No trials exist before the March 2026 price change, so trials cannot show a before/after.
