# TODO

Ideas for later. Not built yet.

- [x] **README**: update it to match how the project works now (done 2026-11-08).
- [ ] **Profile writes sources and metrics**: profile should write its findings as sources and metrics, in my own structure, instead of only one note per table.
- [ ] **Index file**: add an index that points to the right metrics, sources and notes, so a skill can find what it needs quickly.
- [ ] **Frame suggests metrics**: frame proposes the metrics it thinks the question needs. They may or may not exist yet; profile checks which ones do.
- [ ] **Second approval after profile**: frame already gets approval before any data is touched; add a second check with the requester once profile has shown what the data supports, before any analysis begins.
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
  - Depends on item 6: the numbers must come from the baseline table.
  - The brief's headings are fixed because other skills read them; a new section means updating those skills too.
- [ ] **Brief is evidence, in the skill**: add the rule from DECISIONS.md to the deliver skill: a finished brief is not edited by hand; a change goes through a new run.
- [ ] **No crossing claims inside the range**: deliver should not say a threshold is passed when the range spans it. The price brief says churn is "past the point where $12 stops paying off" while the 12-month result runs from a $17,000 loss to a $4,000 gain.
- [ ] **Enforce the body length**: deliver aims for about 400 words in the body, but the price brief's body is about 476. Make the count a hard check, or set the limit to what a brief needs.
- [ ] **Branch clean-up**: delete the four branches already merged into main (`analysis/march-2026-price-retention-final`, `claude/project-todos-brainstorm-b4t71n`, `skills/frame-validate-deliver`, `test/price-question-fresh`) and decide on the six unmerged ones (`analysis/march-2026-price-retention`, `-v2`, `-v3`, `analysis/run-comparison`, `ccr-3d637bae-2ss3kt`, `test/trials-question`).
