# TODO

Ideas for later. Not built yet.

## Skills
- [ ] **Analyse saves its plan, with the user's approval**: write the plan to the run folder (e.g. `plan.md`) and record that the user approved it before any outcome was looked at. In the trial run the group definitions were approved in chat, so validate could not see it and flagged it as Needs the user. This also covers a second check with the requester once the data has shown what it supports (for example, that a group is too small to show the gap the frame asks for).
- [ ] **Small fixes under Ship it**: the analyst skill says nothing about Small fix findings left under a Ship it verdict. In the trial run, two were left open and the brief's $201,000 rests on one of them, so the run ended "not complete". Apply a Small fix whenever it touches a number the recommendation uses, then validate once more.
- [ ] **Save query results without hand-copying**: every result CSV is typed in from the `execute_sql` output. Totals matched in the trial run, but a helper that writes the returned rows straight to `data/<name>.csv` would remove the risk of a copying slip.
- [ ] **Explore before answering** (tried once as an orient step and dropped for length; see DECISIONS.md): analyse should start with basic exploration (number of customers, subscribers, plan mix and so on), then dig deeper into those numbers before it answers the question.
  - Add an "orient" step in analyse before the plan, with a fixed set of numbers about the population in the frame: size of each comparison group, base rate of the outcome (churn, conversion), time window, plan mix.
  - Save them to a result table (e.g. `data/baseline.csv`), so deliver can use them without computing anything.
  - Let them change the plan, e.g. a group too small to trust or a surprising base rate.
  - Keep it apart from profile: profile describes the whole table, orient describes only this question's population.
  - Risk: exploring turns into fishing. Hold it to the fixed set; anything interesting it spots goes to the appendix as an open question, not into the answer.
- [ ] **Deliver opens with background**: the brief starts with that same background, e.g. "these are our comparison groups, they have X users and churn was Y", to anchor the story before the findings.
  - Place it after Key Takeaways, before Findings, so the recommendation still comes first.
  - Format: a heading like "The groups we compared", a 2 to 4 row table (group, users, outcome rate, window) and one sentence on why these groups.
  - Findings refer back to it, e.g. "annual subscribers (12,400 of them) churn half as often".
  - Also lets a reviewer check each finding's denominators at a glance.
  - Depends on Explore before answering: the numbers must come from the baseline table.
  - The brief's headings are fixed because other skills read them; a new section means updating those skills too.
- [ ] **Brief is evidence, in the skill**: add the rule from DECISIONS.md to the deliver skill: a finished brief is not edited by hand; a change goes through a new run.
- [ ] **No crossing claims inside the range**: deliver should not say a threshold is passed when the range spans it. The Week 1 price brief says churn is "past the point where $12 stops paying off" while the 12-month result runs from a $17,000 loss to a $4,000 gain.
- [ ] **Enforce the body length**: deliver aims for about 400 words in the body; the Week 1 price brief's body was about 476 and the trial brief's about 408. Make the count a hard check, or set the limit to what a brief needs.

## Knowledge
- [ ] **Explain the two price answers**: the Week 1 run (CSV exports) puts monthly churn after the increase at 5.1%, the database run at 4.2% (April to July 2026). Nothing explains the difference yet; the database has payments back to 2022, the CSVs from 2025.
- [ ] **Two review findings left from the semantic layer**: `weekly_trial_conversion_rate` (trials.yaml) counts partial first and last weeks; the `monthly_paid_churn_rate` description (subscriptions.yaml) lacks its date range.
- [ ] **Stale docstring**: `helpers/build_index.py` still says the hand-written part holds "tables not covered yet"; that list is gone, and the header now holds the dialect, conventions and `excluded`.

## Repo
- [ ] **Branch clean-up**: as of 2026-11-17, 24 remote branches are merged into `main`. Delete all but `archive/week1-csv-data` and `archive/march-price-retention-v1`, which hold the Week 1 data and an earlier run. Decide on the 7 unmerged ones: `analysis/2026-11-17_price-rise-rollback`, `analysis/march-2026-price-retention`, `-v2`, `-v3`, `analysis/run-comparison`, `ccr-3d637bae-2ss3kt`, `test/trials-question`. Delete the 16 merged local branches too.
