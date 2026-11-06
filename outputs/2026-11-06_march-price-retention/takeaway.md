# Run summary: March 2026 price increase and retention

Status: kept as a record. Not ready to send to the head of growth.

## Takeaway
Monthly-plan churn rose sharply after the price went from $10 to $12 on 2026-03-01, and it has stayed high since April 2026. The size of the rise in `brief.md` is overstated: an independent review found that the way cancellations are recorded changed in September/October 2025, so only September 2025 to February 2026 is a fair baseline. Against that baseline, churn went from 2.09% to 5.25% a month (+3.2 percentage points, +152%), still well above the 20% rise at which the increase stops paying for itself over a subscriber's lifetime. On that baseline, groups appear to differ by tenure, which may give the targeting the rollback decision needs. That result has not been rerun yet.

## How each step did
- Frame: good, but tenure came from the user, not the analyst.
- Analyse: ran clean, but chose baselines without checking that cancellations were recorded the same way across the window.
- Validate (`review.md`): "Think on it". Missed the recording change, because it reviews code and does not query the source data.
- Deliver (`brief.md`): too many numbers and internal references for a business reader, and a recommendation that hinged on an open question.
- Independent review (`independent_review.md`): "Do not trust yet". Found the recording change.

## Next
1. Improve the frame, validate and deliver skills (separate branch).
2. Rerun this analysis with September 2025 to February 2026 as the baseline, then validate and rewrite the brief.
