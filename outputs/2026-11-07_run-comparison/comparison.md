# Run comparison: March 2026 price increase and retention

Run 1: `outputs/2026-11-06_march-price-retention/` (original skills). Run 2: `outputs/2026-11-06_march-price-retention-v2/` (revised skills). Data end 2026-09-24 treated as today. Both scripts were rerun from the repo root with `poetry run python`: run 1 reproduces 16 of 16 result files, run 2 reproduces 11 of 11.

## Verdict
**Run 2 is more trustworthy.** It tests its baseline against the source data, compares groups with each other instead of with a bar every group clears, and gives a recommendation the head of growth can act on. But the number that recommendation rests on was added after the last review and never reviewed.

## Side by side

| | Run 1 | Run 2 |
| --- | --- | --- |
| Baseline (lead) | Mar to Aug 2025, which uses the old way of recording end dates | Nov 2025 to Feb 2026, checked in code; Oct 2025 as sensitivity |
| Monthly churn, tenure-matched | 0.80% to 5.25% a month (+557%); range of baselines +152% to +557% | 2.07% to 4.99% (+2.9 points, +141%, range +120% to +165%) |
| Annual plan (control) | 0.37% to 0.51% (+38%) | 0.46% to 0.46% (0%, range -35% to +59%) |
| Price effect net of annual | not computed | +2.9 points (2.6 to 3.3) |
| For whom | every group above the 20% "break-even", so none can be picked | new subscribers (0 to 2 months) and joiners at $12 rose more than the rest; country and device no clear difference on revenue |
| Revenue | lifetime ratio 0.35 vs realised revenue up a third, left to the decider | per 100 subscribers: +12% at 6 months, +3% at 12, -11% at 24 (12 and 24 projected); new subscribers 93 per 100 at 12 months |
| Recommendation | do not pick groups; four open questions | test $10 for new subscribers, keep $12 for everyone else |
| Review verdict | Think on it (missed the recording break) | Fix first, then Think on it after fixes |
| Independent review | Do not trust yet | none |

Independent recomputation from `data/*.csv` with my own script (own month loop and tenure bands):
- Monthly churn Nov 2025 to Feb 2026 vs Mar to Aug 2026, tenure-matched: 2.07% to 4.99%, +2.91 points, +140%. Matches run 2.
- Annual churn: 0.46% both periods, on 36 and 63 cancellations (about 10 a month). Matches run 2.
- Monthly-plan revenue: $49,970 in Feb 2026, $66,636 in Aug 2026; monthly payments 4,997 vs 5,553. Matches both runs.
- New-subscriber 12-month revenue, following run 2's band rates: $95.5 at $12 vs $102.6 at $10, index 93. Matches run 2.

## What run 2 fixed
- **Baseline.** Run 1 led with a baseline from before October 2025, when every monthly ending was logged exactly 30 days after the last payment; from October endings are mid-cycle and carry clock times. Run 2 asserts in code that end dates are recorded steadily from November 2025 and drops October. Its +141% replaces run 1's +557%.
- **A decision rule that can separate groups.** Each group's rise is tested against everyone else's with subscriber-level bootstrap ranges, so run 2 can say who stands out (new subscribers, joiners at $12) and who does not (country, device). Run 1's 20% rule flagged all 12 country and device pairs.
- **Revenue over horizons, not a steady-state ratio.** Run 1 handed "which revenue measure?" to the decider. Run 2 shows 6, 12 and 24 months and follows subscribers as they age through tenure bands.
- **Season.** A payment-based churn measure, independent of end dates, rose from 0.8% (Mar to Jul 2025) to 5.0%, so the Nov to Feb vs Mar to Aug season gap does not explain the rise.
- **Readable brief.** One recommendation, three takeaways, at most three findings, codes and files in the appendix. A head of growth can act on it in two minutes.
- **Validate caught a real bug.** Round 1 found tenure bands with no before-period subscribers counted as zero churn, which had made the Sep 2025 cohort look hardest hit.

## What is still wrong
1. **The recommendation's number was never reviewed.** The follow-through revenue projection (the 93) and the revenue ranges were added after validate round 2 and rerun once. The brief marks them "not re-reviewed", but the run summary calls the run "complete".
2. **The prize is not sized.** $7 less per new subscriber over 12 months is about $1,500 to $3,500 per monthly cohort (200 to 490 starts a month), against about $790,000 a year of monthly-plan revenue. The head of growth needs that number to judge whether a separate price and its backlash risk are worth it.
3. **The bigger risk is the existing base, not new subscribers.** Overall, $12 stops out-earning $10 after month 15 and is 11% behind at 24 months if churn stays where it is. My cohort check shows churn among pre-September 2025 subscribers stayed roughly double (1.7 to 2.2% before; 3.3 to 4.3% in Apr to Aug), easing only slightly. The brief keeps this as a limit and an open question; it should carry a recheck date in the recommendation.
4. **Who a new-subscriber price would reach has changed.** Trials launched 2026-08-01; 255 of 323 monthly starts in Aug 2026 came from trial users, a group with no before period and not in the analysis. The July 2026 jump (491 starts, no trials) is unexplained, and the claim "the early-cancellation rise holds without July" comes from a validate scratch script, not a result file.
5. **"The price clearly drove" is too strong.** Timing supports it (payment lapses jump in March, cancellations in April, in every cohort at once). But payment-based churn had already doubled before the price change (0.8% in spring 2025 to 1.5% in Nov to Feb), alongside an unexplained change in how subscriptions end. The annual control rests on about ten cancellations a month and is a different, self-selected population, so the narrow 2.6 to 3.3 point range overstates certainty.
6. **Shared by both runs:** plan switches are invisible (one row per user); subscriptions that start and end in the same month are never at risk (4 before vs 21 after in run 2), so early churn is understated in the after period; group ranges are not adjusted for 16 tests (EU and Android "rose more" are borderline); run 2's monthly chart source line overlaps the month labels.

Where I disagree with the takeaways and the independent review:
- Run 1's takeaway and the independent review call Sep 2025 to Feb 2026 a fair baseline. Run 2's check shows September (87% fixed 30-day endings) and October (time-of-day break) are still mixed. November onward is right.
- Run 1's takeaway still uses the 20% steady-state break-even. The independent review was right that it is a horizon, not a threshold.
- The independent review's targeting idea (first-year Web and Android) does not survive run 2's group tests: device and country show no clear revenue difference.
- Both treat the October 2025 change as recording only. Payment lapses, which do not depend on how end dates are logged, doubled at the same time, so something about cancellation itself may have changed. Ask data engineering before calling the winter baseline "normal".
- Run 2's takeaway credits the skills with the better baseline. Much of it came from `knowledge/beam/corrections.md` (added in the same lessons commit) and from the user accepting peer suggestions that drew on run 1's independent review. This is not a clean test of the skills.

## Skill changes that worked, and skill changes to make next
**Worked**
- **validate Act 6 (source data) and `stable_over_time`.** This is the change that made the difference: the baseline is now tested and asserted in code, and validate found the October leftovers and the Aug to Sep 2025 payment-stop burst.
- **validate: "a rule every group passes cannot inform a targeted decision" and "a question the data can answer is never Needs the user".** These turned run 1's dead end into group-vs-rest tests and revenue horizons.
- **deliver: frame asks, analysis answers, review limits; pick a course.** Produced a committed, readable recommendation instead of "it depends".
- **frame: always propose tenure and start cohort.** The cohort split is what exposed joiners at $12.

**Did not help, or not enough**
- frame's plain-text preview and "never take silence as approval" are fine but did not change the analysis.
- `stable_over_time` compares each month with the first month's mode at a loose default tolerance of 25%; it needed a hand-built yes/no field and a 10% tolerance to catch the break.
- The analyst chain still allows fixes after the last review that change the number the recommendation rests on.

**Make next**
1. **analyst / validate:** if a fix changes a number the recommendation rests on, run a short targeted validate on that number before deliver; never mark the run complete otherwise.
2. **deliver:** size the decision in money (total revenue at stake per month or year), not only per 100 subscribers.
3. **analyse (unchanged so far):** for any population the recommendation acts on, check it is the same population going forward (trials, new channels, signup bumps), and write every claim the brief makes into a result file.
4. **validate Act 7:** when a projection decides the call, ask whether the post-change rate is persistent or a shock, and show the observed-horizon answer next to it.
5. **`stable_over_time`:** detect a step against the recent level, not the first month, report the largest shift, and default to a tighter tolerance.
6. **frame:** ask what the business can actually price separately before analysis, so the decision rule targets levers that exist.
