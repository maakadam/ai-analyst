# TODO

Ideas for later. Not built yet.

- [ ] **README**: update it to match how the project works now.
- [ ] **Profile writes sources and metrics**: profile should write its findings as sources and metrics, in my own structure, instead of only one note per table.
- [ ] **Index file**: add an index that points to the right metrics, sources and notes, so a skill can find what it needs quickly.
- [ ] **Frame suggests metrics**: frame proposes the metrics it thinks the question needs. They may or may not exist yet; profile checks which ones do.
- [ ] **Approve the frame before real work**: always take the frame back to the requester for approval before any analysis begins, i.e. after profile has checked what the data supports.
- [x] **Explore before answering**: analyse should start with basic exploration (number of customers, subscribers, plan mix and so on), then dig deeper into those numbers before it answers the question.
  - Add an "orient" step in analyse before the plan, with a fixed set of numbers about the population in the frame: size of each comparison group, base rate of the outcome (churn, conversion), time window, plan mix.
  - Save them to a result table (e.g. `data/baseline.csv`), so deliver can use them without computing anything.
  - Let them change the plan, e.g. a group too small to trust or a surprising base rate.
  - Keep it apart from profile: profile describes the whole table, orient describes only this question's population.
  - Risk: exploring turns into fishing. Hold it to the fixed set; anything interesting it spots goes to the appendix as an open question, not into the answer.
- [x] **Deliver opens with background**: the brief starts with that same background, e.g. "these are our comparison groups, they have X users and churn was Y", to anchor the story before the findings.
  - Place it after Key Takeaways, before Findings, so the recommendation still comes first.
  - Format: a heading like "The groups we compared", a 2 to 4 row table (group, users, outcome rate, window) and one sentence on why these groups.
  - Findings refer back to it, e.g. "annual subscribers (12,400 of them) churn half as often".
  - Also lets a reviewer check each finding's denominators at a glance.
  - Depends on item 6: the numbers must come from the baseline table.
  - The brief's headings are fixed because other skills read them; a new section means updating those skills too.
