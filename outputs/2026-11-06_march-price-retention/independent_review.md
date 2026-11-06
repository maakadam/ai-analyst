# Independent review: March 2026 price increase and retention

## Verdict
**Do not trust yet.** Churn clearly rose after March 2026, but the brief leads with a baseline taken from a period when cancellations were recorded differently, so the size of the rise, the "no group differs" finding and the revenue verdict all need redoing before the head of growth acts on them.

## Top issues
1. **The way subscriptions end changed in Sep/Oct 2025, before the price rise.** Through Aug 2025, every monthly ending falls exactly 30 days after the last payment (end of the paid period, date only). From Oct 2025, 80 to 100% of endings are mid-cycle (median 18 days after the last payment) and about 40% carry real clock times. Where: monthly_churn_series.csv, brief "rise holds under every baseline". Fix: treat Sep 2025 onward as a separate data regime, lead with the Sep 2025 to Feb 2026 baseline (+152%, 2.09% to 5.25%), drop or footnote the +557% same-season figure, and ask data engineering what changed.
2. **The 20% break-even does separate groups once the comparable baseline is used.** Against Sep 2025 to Feb 2026, 12 to 23 month subscribers rose only +52% (1.24% to 1.88%; rough 95% range +17% to +96%), close to break-even, while 0 to 2 months rose +5.6 points. Where: segment_tenure.csv and all segment_*.csv (built on the 12-month mixed baseline). Fix: rerun every segment against Sep 2025 to Feb 2026 and report points as well as percent.
3. **"Lifetime revenue" and "realised revenue" are not two answers; they are two horizons.** The 0.35 ratio is a steady state reached only after roughly two years; realised revenue at six months is bound to be higher. Where: brief "Lifetime revenue and realised revenue disagree", open question A2. Fix: show one projection with cumulative revenue at 6, 12 and 24 months (see spot checks) and let the head of growth pick the horizon.
4. **Churn after March is persistent, not a one-off first-$12 renewal shock**, and new subscribers who only ever saw $12 churn even faster (8 to 12% a month vs 4 to 6% for pre-March subscribers). Pre-March churners in Apr to Aug had made anywhere from 1 to 6 payments at $12. Where: not in the brief. Fix: say so; it argues for a lasting price effect (or another lasting cause), and a rollback cannot win back those already gone.
5. **Cause is not isolated.** The mid-cycle ending mechanism that drives almost all churn started in Oct 2025 with the signup spike; renewal-time (on-cycle) endings were 0.84% a month before Sep 2025 and near 0.1% after March. Statuses also flip from "expired" to "canceled" in Aug 2026. Where: brief limits section. Fix: state that the after-period jump lines up in time with the first $12 charge (Mar 2.62% to Apr 5.53%, same regime), which is the strongest causal evidence, but that the recording change is unexplained.
6. **Brief inconsistencies.** "Next step" asks to rerun tenure without the Sep 2025 cohort and to compare with annual, both already in the brief; open questions jump from A2 to A5 (internal review labels); chart title "annual churn did not" is contradicted by the brief's own text; tenure chart has no intervals; month labels overlap the source line. Fix: tidy before sending.
7. **Intervals are optimistic** (subscriber-months treated as independent, crude counts against a standardised rate), as the earlier review said. Fine for "churn rose", too weak to rank groups. Fix: bootstrap by subscriber if groups are compared.

## Numbers spot-checked
Recomputed from data/*.csv with my own scripts (aggregates only).
- Monthly churn series, monthly plan, Mar 2025 to Aug 2026 (at risk, churned, rate): all 18 months match monthly_churn_series.csv.
- Headline against Sep 2025 to Feb 2026, tenure-matched: 2.09% to 5.25%, +152%, 1,697 churned after. Matches.
- Revenue per month (Feb 2026 $49,970; Aug 2026 $66,636) and at-risk base (5,382; 5,402): match. Every monthly payment is $10 before March and $12 from March, every 30 days; no payments after end dates.
- Plan switches: 0 subscriptions with both monthly and annual payments, matches; annual new starts did not jump after March (57 to 82 a month until July), so no visible move to annual.
- New: share of endings exactly 30 days after the last payment: 100% each month to Aug 2025, 3 to 15% from Oct 2025.
- New: tenure-matched rise by group vs Sep 2025 to Feb 2026: EU +211%, India +169%, Rest +131%, US +128%; Android +180%, Web +147%, iOS +130%; tenure 0-2m +178%, 3-5m +111%, 6-11m +135%, 12-23m +52%, 24m+ +354%.
- New: projection from 5,486 subscribers in Mar 2026, 200 new starts a month: cumulative revenue at $12 and 5.25% churn vs $10 and 2.09% is $380k vs $342k at 6 months, $731k vs $711k at 12, $1.38m vs $1.52m at 24. The increase pays for now and loses after roughly 1.5 years if churn stays this high.

## What the brief gets right
- Says plainly that churn rose and that the data cannot yet say who to target, instead of forcing a ranking.
- Tenure matching by direct standardisation is sound and was what the user asked for.
- Shows several baselines, the annual comparison group, the Sep 2025 cohort sensitivity and the plan-switch check, with sources for every number.
- Flags that intervals are approximate and that early churn (same-month endings, 35) is not counted.

## Suggested next steps
1. Ask data engineering what changed in Sep/Oct 2025 (mid-cycle end dates with clock times) and in Aug 2026 (expired to canceled). Until answered, use only Sep 2025 onward.
2. Rerun headline and segments against Sep 2025 to Feb 2026; show points and percent, with subscriber-level bootstrap intervals.
3. Replace the lifetime ratio with the cumulative revenue projection at 6, 12 and 24 months, per segment.
4. Targeting rule for a partial rollback: rank segments (tenure band x country x device) by excess churned revenue = at-risk subscribers x extra churn points x price, and roll back only where the 24-month projection says $10 beats $12. On current numbers that points at the first year of tenure (0 to 11 months, +3.8 to +5.6 points) on Web and Android, and away from 12 to 23 months and US iOS (smallest rises).
5. Best of all, test it: offer $10 (or $11) to a random half of the targeted segments for two to three months. A randomised holdout answers "is it the price" directly, which this before/after data cannot.
