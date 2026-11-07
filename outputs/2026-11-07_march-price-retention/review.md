# Review: March 2026 price increase and monthly retention (third recheck)

## Verdict
**Ship it**: every earlier Small fix is in and the rerun matches; no rollback clearly pays over the frame's six months under any baseline, window or calibration, and the twelve-month passes are flagged tentative and still hold on non-trial customers alone, so what remains are limits for the brief.

## Data flow
```mermaid
flowchart LR
  S[subscriptions.csv<br/>30,747 rows] --> P[paid, started by 2026-09-24<br/>11,931: 8,951 monthly, 2,980 annual]
  PY[payments.csv<br/>100,914 rows] --> J[join on subscription_id<br/>100,914 kept, no fan-out]
  T[trials.csv] --> SRC[source: trial convert or non-trial]
  P --> CP[monthly churn panel by plan x tenure x start cohort<br/>Oct 2024 to Aug 2026, 136,057 at-risk months]
  CP --> W[before Oct 2025-Feb 2026 vs after Mar-Jul 2026<br/>and Apr-Jul sensitivity]
  W --> D[did_monthly_vs_annual_by_tenure.csv<br/>A5]
  D --> CH2[did_by_tenure.png]
  CP --> BY[churn_monthly_by_plan.csv] --> CH1[churn_by_plan.png]
  CP --> CO[churn_after_by_tenure_and_start_cohort.csv]
  CP --> HD[churn_by_month_joined_at_10.csv<br/>A3]
  J --> PR[payment_stop_rate_by_period.csv<br/>A5]
  CP --> SE[seasonality_year_earlier_did.csv<br/>A6]
  P --> PP[paying subs only] --> H[band hazards: before, before without Sep 2025, after, joined at $12]
  P --> MB[monthly base 1 Mar 2026: 5,358<br/>24 Sep 2026: 5,560, 0-2 band 573 trial + 609 non-trial]
  SRC --> MB
  SRC --> NS[new starters Aug 2026: 68 non-trial, 255 trial converts<br/>A2]
  H --> M[money_rollback_by_tenure.csv<br/>6 and 12 months, 1,000 bootstrap draws, keep side calibrated]
  MB --> M
  NS --> M
  J --> MC[money_model_vs_paid_by_tenure.csv<br/>6-11 months 5.5% off, logged]
  MC --> M
  M --> R[decision_rule_by_tenure.csv<br/>A1 A3]
  D --> R
  R --> CH3[rollback_gain_6m.png<br/>C1]
  R --> CH4[rollback_gain_12m.png]
  NS:::issue
  R:::issue
  CH3:::issue
  D:::issue
  PR:::issue
  SE:::issue
  HD:::issue
  classDef issue fill:#fde2e2
```

## Code review
- **C1 Note** The six-month chart title says every rollback option "loses revenue", which holds for the uncalibrated gains it plots, but with the keep side calibrated the 0-2 month cut is about break-even and both intro rows sit just above zero, all with intervals spanning zero. Where: analysis.py:500, rollback_gain_6m.png. Fix: in the brief say "none clearly pays over six months" rather than "every option loses".

## Analysis review
- **A1 Note** (earlier A1, mostly fixed) The trial-convert rows are labelled "rate unmeasured" but still carry `rollback_recommended` True at twelve months and give the largest projected gain, while early evidence suggests trial converts churn less than non-trial $12 starters, which would shrink a rollback's gain. The non-trial rows pass at twelve months on their own, so the call does not rest on them. Where: decision_rule_by_tenure.csv, money_rollback_by_tenure.csv. Fix: in the brief, base any twelve-month case on the non-trial rows and show trial-convert rows as unmeasured, not as support.
- **A2 Note** The intro price is sized on August 2026 alone (68 non-trial starters), one month in a volatile run: about 200 a month Mar-Jun, 491 in July, 68 in August, 126 in the first 24 days of September. Volume scales the size of the intro rows, not their sign. Where: analysis.py:310, money_rollback_by_tenure.csv. Fix: give the intro money as a range over recent monthly volumes in the brief.
- **A3 Note** (earlier A3, unchanged in substance) No row passes the frame's six-month rule under any variant (main, Apr-Jul, without September 2025 starters, keep side calibrated); every pass is twelve-month only and flagged tentative; churn among $10 joiners eased in July, so the projected rate may not hold. Where: decision_rule_by_tenure.csv, churn_by_month_joined_at_10.csv. Fix: lead the brief with the six-month answer and present the newest-customer and intro options as a tentative twelve-month projection worth a test, not a rollout.
- **A4 Note** (earlier A4, unchanged) The frame does not name the form of a tenure rollback; both forms (price cut for the current base, intro price for new starters) are sized side by side. Where: frame.md, money_rollback_by_tenure.csv. Fix: lay out both options in the brief.
- **A5 Note** (earlier A5, unchanged) For 12-23 months the two churn measures point different ways (end-date churn up slightly, stopping payment down), and part (a) of the rule passes for every band, so only the money separates groups. Where: payment_stop_rate_by_period.csv, did_monthly_vs_annual_by_tenure.csv. Fix: give the brief the range from both measures and do not call the 12-23 rise clear.
- **A6 Note** (earlier A6, unchanged) Season is not ruled out: before and after are different seasons and the same-months check sits before the October 2025 end-date step. Where: seasonality_year_earlier_did.csv. Fix: say so in the brief's limits.
- **A7 Note** (earlier A7, unchanged) Plan switches cannot be seen and count as churn. Where: frame.md. Fix: keep it in the brief's limits.

## Checked
- Earlier findings: C1 fixed (calibration now on the keep side only, 1 March keep side uses months actually paid, rule column added; no sign flips the call); C2 fixed (twelve-month title says projected and tentative); A1 mostly fixed (0-2 band and intro split by source, intro sized on recent volume, trial rows labelled; remainder carried as A1 and A2); A2 fixed (money variant without September 2025 starters, no row changes); A3-A7 carried as notes.
- Rerun: copy with the root path moved up one level, exit clean, all 17 result files match; writes only inside its folder, prints aggregates only; join does not fan out; tenure and money bands sum to their totals; 6-11 month model check fails by 5.5% and is logged and calibrated.
- Dates and windows: analysis date 2026-09-24 throughout; before Oct 2025-Feb 2026, after Mar-Jul 2026 with Apr-Jul as a sensitivity; August and partial September out of every compared window; future end dates treated as active; intro volume taken from August, the last complete month.
- Source data (Act 6): earlier checks stand (end-time and last-payment-gap steps are mix and behaviour after the price change, not recording; `canceled` share stable). New this round: trial converts first appear in August 2026, so the source split is clean; every monthly start has a payment, so the 582 unpaid September 2026 starts in the knowledge note are not monthly and do not enter the base; non-trial starts are volatile month to month (A2).
- Charts opened: both rollback charts match decision_rule_by_tenure.csv and their titles (C1 on wording); churn_by_plan and did_by_tenure unchanged and match their tables.

## Not checked
- Twelve-month projection beyond the data: not testable; the after rate has about four months behind it and eased in July.
- Trial converts' churn beyond their first month: they only start from August 2026.
- The cost of running a targeted price (billing work, fairness complaints): not in the data.
- Why non-trial monthly starts jumped in July 2026 and fell in August: unexplained in the data.
- Uncertainty in the calibration factor itself: the calibrated interval is the bootstrap interval shifted, not redrawn; small next to the gaps that decide the call.
- Nothing was written to `knowledge/beam/` by this run, so there was nothing to reconcile.
