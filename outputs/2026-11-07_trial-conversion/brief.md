# Brief: Keep 14-day trials next quarter

## Question
Are the 14-day trials turning enough new signups into paying subscribers to keep them next quarter?

## Recommendation
**Keep 14-day trials next quarter, and hold back a random half of new signups without one as a comparison group.**
Trial users end up paying 14.1 percentage points more often than same-day signups without a trial, worth about $18,000 in extra revenue next quarter at today's signup rate.
Fairly confident: the gap holds every week, against pre-trial months, and if some unstarted plans never pay; but nothing records whether trials were handed out at random.
What would change this: if trial users were picked, not drawn at random, the gap could shrink; a random split settles it cheaply.

**Open for you**
- Trials for everyone would roughly double the gain, but leave no comparison group. Which do you prefer?
- Did anything else change around 1 August (a campaign, the signup flow)? Weekly signups jumped from about 153 to 522 then.

## Key Takeaways
- 53.3% of trial users end up on a paid plan, against 39.2% of same-day signups without a trial.
- Trial users beat the best pre-trial week in all 5 whole weeks; last August ran only 1.5 points above spring, so season does not explain it.
- Trials as they run now add roughly $4,000 to $23,000 in revenue next quarter.

## Findings
### Trials lift the share of signups who end up paying by about a third
![Share of signups on a paid plan: trial users, same-day non-trial signups, and Mar-Jul 2026 signups](charts/paid_share_by_group.png)
- Paid share (signups who end up on a monthly or annual plan) is 53.3% with a trial against 39.2% without, a 36% relative lift; against pre-trial months the gap is 13.9 points.
- Many non-trial plans start on 25 September, not yet charged. Past batches were charged in full; if these pay only at the worst past rate, the gap widens to 18.2 points.

### The gap is steady week to week, and the season does not explain it
![Weekly paid share: trial users against same-week non-trial signups and the best week before trials](charts/weekly_paid_share.png)
- Trial users ran 51.8% to 54.5% each week; non-trial signups never passed 45.1%. Only 5 whole weeks so far.

### Worth about $18,000 next quarter, with a wide range
**+487 extra paying subscribers next quarter, against none without trials**
- Low end ($4,000) assumes spring signup rates; high end ($23,000) today's rate and the upper gap. Trial running costs are not counted.

## Appendix
### How this was done
- Data: Beam users, subscriptions, trials and payments, up to 2026-09-24.
- Main test: new signups from 2026-08-01 to 2026-09-10, so that every trial had closed. That gives 1,553 trial users and 1,503 non-trial signups from the same days. The measure is the share who end up on a paid plan (monthly or annual), with a 95% interval on the gap (+10.6 to +17.6 points).
- Second baseline: signups from Mar-Jul 2026, at the same $12 monthly price, as one overall share and 21 whole weeks.
- Firmness of plans not yet started: share of paid plans on each earlier batch start day that were charged on day 0 to 5 (2026-07-30: 403 of 403; trial converts: 828 of 828). Two sensitivities: non-trial plans starting 2026-09-25 paid only at the worst past batch rate (83%, 2025-09-17), giving +18.2 points; and the Mar-Jul baseline counting charged plans only, giving +14.1 points (95% interval +11.1 to +17.1).
- Seasonality: Aug 2025 against Mar-Jul 2025.
- Mix and volume: country, device and plan mix by group, plus paying subscribers per week.
- Money: 13 weeks of signups times the gap, using the plan mix of trial converts, $12 monthly and $100 annual prices, and the share of monthly payers who pay a second time. Low, central and high cases, with each assumption listed in data/money_assumptions.csv.

### Sources
- Trials lift the share of signups who end up paying: data/paid_share_by_group.csv, data/lift.csv, analysis.py (Main comparison, lines 116-193)
- Firmness of plans not yet started: data/batch_start_firmness.csv, data/lift.csv (two Sensitivity rows), analysis.py (lines 153-192)
- The gap is steady week to week: data/weekly_trial_vs_non_trial.csv, data/weekly_baseline_mar_jul_2026.csv, data/weekly_summary.csv, data/seasonality_summary.csv, analysis.py (Weekly and Seasonality, lines 200-245)
- Worth about $18,000 next quarter: data/money_next_quarter.csv (trials for about half of signups, as now: Low, Central and High), data/money_assumptions.csv, data/revenue_90d_per_payer.csv, analysis.py (Money, lines 338-398)
- Recommendation and takeaways: the same files. The "trials for everyone" option is in data/money_next_quarter.csv (Trials for all signups rows).

### Checks
- Checked: a rerun from a copy matched all 17 result files exactly, including batch_start_firmness.csv and the new lift.csv rows. Joins do not fan out, parts add up to totals, and closed trials have no open outcome. Trial and non-trial groups are balanced on country and device (largest mix gap 1.9 points; data/mix.csv). Plan recording and the charged-at-start rate are level across months, apart from the known September 2025 spike. Both charts were checked against their titles.
- Not checked: whether trials were assigned at random, since only balance on recorded fields was checked. Whether plans starting 2026-09-25 will be paid, since there are no payments after 2026-09-24; the sensitivity bounds it instead. Why start dates are set in batches; it does not touch the plan field the headline uses. What caused the jump in signups on 2026-08-01 (153 to 522 a week; data/volume_per_week.csv): the central and high money cases use the Aug-Sep signup rate, and the low case uses the Mar-Jul rate. The cost of running trials, which no result table holds, so the money is revenue only. Retention as a warning sign: all 143 trial converts old enough paid a second time, but too few comparable non-trial starts exist (33) to compare.
- Not firm: the non-trial same-days against Mar-Jul consistency (-0.2 points in data/lift.csv) rests on non-trial plans not yet charged and is not quoted in the body.
- Out of scope: trial length (only 14-day trials exist) and retention past the first renewal.
- Review findings: no Small fix or Needs the user findings are open in the latest review (verdict Ship it). C1 (weekly series used partial weeks) and A2 (a "started only" column that could be quoted as a conversion rate) are fixed and confirmed by the rerun. A1 (batched start dates, so many non-trial plans not yet started or paid) was answered from the data and moved to a Note.
- Other review findings: 3 Notes, in review.md. A1: the 83% worst past rate comes from the September 2025 spike's unpaid plans, so it is a harsh floor. A3: the "trials for all" money rows assume the no-trial half responds like those who got one, which rests on the split being random. A4: retention cannot serve as a warning sign yet; segment lifts rest on 270 to 640 signups each and are not ranked; seasonality (+1.5 points) is small next to the lift.
