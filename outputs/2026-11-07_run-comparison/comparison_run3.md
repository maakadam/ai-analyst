# Run comparison: run 3 against runs 1 and 2

Run 3: `outputs/2026-11-07_march-price-retention-v3/` on branch `analysis/march-2026-price-retention-v3` (commit 2b90cb9), made by a subagent in a clean checkout with the skills at `skills/frame-validate-deliver` ab48973. It could not see runs 1 and 2. The user's only new answer: which groups Beam can price separately is not known. Run 1 and 2 details are in `comparison.md`.

Rerun from a copy: all 16 result files match. (The copy's last print line fails when run from outside the repo; every file is written before it.)

## Verdict
**Run 3 is the most trustworthy of the three, and the most useful to the head of growth.** It sizes the decision in dollars, tests whether the churn rise is fading, flags that new subscribers are now mostly trial users, and gives a tentative recommendation that matches its evidence. One real flaw: it merges 12-23 and 24+ month subscribers, which hides that the longest-standing customers quadrupled their churn.

## Side by side

| | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| Baseline | Mar to Aug 2025 (old recording) | Nov 2025 to Feb 2026 | Oct 2025 to Feb 2026 |
| Monthly churn, raw | 0.80% to 5.25% (same tenure) | 2.1% to 5.0% | 2.1% to 5.0% (+2.9 pp) |
| Same tenure | +4.5 pp, +557% | +2.9 pp, +141% | +3.3 pp, +156% (weighted the other way) |
| Annual plan | +38% | flat | 0.50% to 0.46% |
| Money | lifetime ratio 0.35, left open | per 100 subscribers: +3% at 12 months | whole base: keeping $12 earns $31k more over 12 months, $104k less over 24; +$47k net so far |
| Has the rise faded? | not tested | not tested | no: 2.6x baseline in Apr-May, 2.4x in Jul-Aug |
| Who stands out | nobody (rule flags all) | new subscribers, joiners at $12 | same, plus "a year or more reacted least" (see below) |
| Recommendation | do not pick groups yet | test $10 for new subscribers | do not roll back now; if Beam can price new subscribers separately, any partial rollback starts there |
| How sure | not stated clearly | fairly confident | tentative |
| Review rounds | 1, Think on it | 2 + fixes not re-reviewed | Fix first, then Think on it |

My recomputation from `data/*.csv`, own code:
- Churn Oct 2025 to Feb 2026 against Mar to Aug 2026: 2.08% to 4.99%; at the baseline tenure mix 5.33% (+3.25 pp). Matches.
- 1,587 cancellations after, 650 expected at baseline rates, so 937 extra. Matches.
- 32,934 monthly payments at $12 from March to August, so the extra $2 brought in $65,868. Matches.
- My own tenure-aware projection from 5,352 subscribers on 1 Sep 2026 with 197 starts a month: a rollback gains -$40k over 6 months, -$33k over 12 and +$97k over 24. Run 3 reports -$41k, -$31k and +$104k. Same signs and close in size; the gaps come from timing conventions.

## What run 3 did better than run 2
- **Money for the whole decision.** It sizes keep against rollback for the whole base and for each group, over 6, 12 and 24 months, plus what has already been earned (+$47k). Run 2 gave indexes per 100 subscribers. The break-even line is especially useful: $12 still wins over 12 months unless churn rises 3.7 points, against 3.3 observed. The margin is thin, and the brief says so.
- **Persistence tested, not assumed.** Run 3 measured churn by month since the change among existing subscribers before projecting. Run 2 assumed it.
- **Who a new-subscriber price would reach.** It found that 79% of August's new monthly subscribers came from trials, and named this as a limit on the new-subscriber finding.
- **Recommendation matches the evidence.** The rollback for new subscribers only breaks even over 12 months ($0). So run 3 does not push a rollback now, says "tentative", and names the trigger: churn still more than double in early 2027. Run 2's "test $10 for new subscribers" rested on an unreviewed 93-per-100 figure.
- **Levers asked about up front.** The question of what Beam can price separately reached the head of growth as the first Open question, instead of surfacing in round 2 of the review.
- **Recording check read correctly.** The April 2026 shift in end-date timing was tested in steady cohorts and shown to be mix, not logging. Under the old rule it would have meant Fix first.

## What is still wrong
1. **Tenure 12+ hides the 24+ month reaction.** With run 3's own baseline, 12-23 months rose 1.46% to 1.88% (+0.4 pp), but 24+ months rose 0.95% to 3.82% (+2.9 pp, four times the old rate, on 9,372 subscriber-months). "Subscribers of a year or more reacted least" is wrong for the longest-standing group. That matters for "keep $12 for the existing base", and the merged 12+ rate will drift in the projection as 12-23 subscribers age into 24+.
2. **October 2025 is a transition month, not a clean one.** About 18% of October endings still fall exactly 30 days after the last payment, against 2 to 5% from November. Run 3's own full-window check flags breaks in both October and November 2025. Validate then checked only from October onward, where October has nothing before it to step from. Run 2 left October out. The effect on the headline is small (run 2's sensitivity moved it under 0.1 pp), but "wholly after the change" is not accurate.
3. **No call for a test.** Every run is before-and-after with an annual control of about 10 cancellations a month. Run 2's one strength in its recommendation, a randomised trial of $10, is gone. The cheapest way to settle "is it the price" before early 2027 is a holdout test.
4. **Small:** the monthly churn chart says annual "did not move", but annual climbs from 0.25% (Feb) to 0.77% (Aug), as run 1's review also noted. Group intervals still treat subscriber-months as independent (the brief says so).

## How the new skills behaved
- **Worked as intended:** money at stake (analyse, deliver), persistence before projecting (analyse, validate), future-group check (analyse, validate), lever question (frame), reading a break as recording or behaviour (validate, `stable_over_time`), "tentative" when the projection flips sign (deliver).
- **Recheck round:** correctly not triggered. The only fix after round 2 was a chart title, which changed no number.
- **Problems the run exposed:**
  - Validate's "rerun fails, so Fix first and skip the rest" spent a whole round on a path bug in the copy. The analyse skill never says to find the repo root from the working directory, and run 1 had the same bug.
  - Validate and deliver say `context: fork`, but the subagent had no way to fork, so the same agent reviewed its own work. Run 3's review is not a fresh reader's.
  - The validate source-data check (Act 6) does not say to start the check before the baseline; checking only inside the window cannot see a step at its edge.
  - Nothing asks for the tenure bands to separate the longest-standing customers.

## Skill changes to make next
1. **analyse:** find the repo root from the working directory (the convention in AGENTS.md), so a rerun copy works; keep tenure bands fine enough at the long end (12-23 and 24+) for pricing questions.
2. **validate Act 5:** a rerun failure caused by the copy's location is a Small fix; patch the copy's path and carry on, instead of a full Fix first round.
3. **validate Act 6:** run `stable_over_time` from at least three months before the baseline, so a step at the baseline's first month shows.
4. **validate Act 7:** when the evidence is before-and-after only, the review says whether a randomised holdout could settle it, and deliver offers it as the next step.
5. **analyst:** if validate cannot run in a fresh context, say so in the brief's Checks.
