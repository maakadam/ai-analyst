# Run summary: March 2026 price increase and retention (v2)

Status: complete. Second run of the same question, made with the revised frame, validate and deliver skills (branch `skills/frame-validate-deliver`, merged into this branch). The first run is in `outputs/2026-11-06_march-price-retention` on `analysis/march-2026-price-retention`.

## Takeaway
The price rise more than doubled monthly-plan churn: 2.1% to 5.0% a month at the same tenure, against November 2025 to February 2026, while annual-plan churn stayed flat. New subscribers are the only group where $12 earns less than $10 within a year (about $93 per $100). The brief recommends testing $10 for new subscribers and keeping $12 for everyone else. No country or device stands out once revenue is counted.

## How each step did
- Frame: suggested tenure and start cohort without being asked, and showed the draft as plain text before asking for approval. The peer check added three points, which the user accepted: a baseline from October or November 2025, annual plan as a comparison group, and naming plan switches and projection limits.
- Analyse: checked in code that end dates are recorded the same way inside the baseline, and added an annual-plan comparison, tests of whether groups differ from the rest, and revenue over 6, 12 and 24 months. Chart titles first had to be rewritten to match the results.
- Validate, round 1: Fix first. It found a bug: tenure bands where a group had no subscribers before the increase were counted as zero churn, which made the September 2025 cohort look hardest hit. It also found October 2025 still held old-style end dates. Both were fixed, along with paying subscribers only, a payment-based churn measure, and subscriber-level bootstrap ranges.
- Validate, round 2: Think on it. Five small fixes were applied and rerun once (no third review): August and September 2025 left out of payment baselines, revenue projected by following subscribers as they age, ranges on revenue, a counted exclusion, and a clearer cohort chart title. One question went to the user: which groups Beam can price separately.
- Deliver: one recommendation, three plain takeaways, and references in an appendix.

## Gaps
- 12- and 24-month revenue figures are projections from six closed months after the increase.
- Switches from monthly to annual are not visible in the data.
- The helper `stable_over_time` needs a yes/no field when a value has no dominant level (it picked an arbitrary gap of 60 days until the field was changed to "ends exactly 30 days after the last payment").
