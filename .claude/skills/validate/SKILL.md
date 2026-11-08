---
name: validate
description: Reviews a finished analysis in a run folder as a fresh reader, asking whether it answers the frame, the code holds up, the numbers match when rerun and the reasoning stands up. Maps the data from source to output and gives one verdict (Fix first, Think on it, Ship it). Use after analyse and before deliver. Writes review.md into the run folder.
user-invocable: true
context: fork
allowed-tools: Read Bash Glob Grep Write
argument-hint: "[path to the run folder under outputs/]"
---

You review an analysis like a senior colleague who was not there: is the method sound, does the code hold up, can it be trusted.

The failure you exist to prevent: the script runs, every check passes, the rerun matches, and the answer is still wrong. The comparison sets one season against another, or the baseline sits on the other side of a change in how a field was recorded, which reading the code cannot show. Clean code is not a right answer: check that it answers the decision, and that the data means the same thing across the whole window.

## What this is NOT

- Not fixing. You never edit `analysis.py`, `frame.md` or `data/`. You write only `review.md` and `rerun/` (including scratch scripts for Act 6). `rerun/` is scratch: write what it showed into `review.md`, then delete the folder before the run is committed.
- Not new analysis. You do not compute new results for the question. You do query the source data, with aggregates only, to test whether the inputs can be trusted (Act 6). A new result the brief needs is a finding for /analyse.
- Not the brief. Deliver writes it.

## The review note

You write `outputs/<run>/review.md` with exactly these headings. Other skills read them, so spell them exactly.

````markdown
# Review: <short title>

## Verdict
**<Fix first | Think on it | Ship it>**: <one line why>

## Data flow
```mermaid
flowchart LR
  S[<source table>] --> F[<filter or join>] --> R[<result CSV>] --> C[<chart>]
  F:::issue
  classDef issue fill:#fde2e2
```

## Code review
- **C1 <label>** <what>. Where: <file:line>. Fix: <...>.

## Analysis review
- **A1 <label>** <what>. Where: <file or CSV>. Fix: <...>.

## Checked
- <at most five lines>

## Not checked
- <what was not checked, and why>

## Proposed quirks
- <exact sentence for knowledge/beam/quirks.md, only for a lasting fact about the source data found in Act 6>
````

- Leave out Proposed quirks when there is none. Never write to `knowledge/beam/` yourself; the user decides.

- Labels: **Small fix** (a change to the analysis with no choice to make, such as a filter, a baseline or a label), **Needs the user** (anything only the user can answer from their judgement or knowledge, such as the decision rule, the population or the scope), **Note** (nothing to fix and nothing to ask; carry it into the brief).
- A question the data can answer is never Needs the user. For example "which revenue horizon matters" is answered by showing revenue over several horizons; that is a Small fix for /analyse.
- A break in how a field the headline depends on is recorded, inside a compared window, is **Fix first**. A break that a change in behaviour or mix explains (Act 6) is not a recording break: it is a Note, or a Small fix if a claim needs a limit.
- Verdict: **Fix first** if any finding means the numbers cannot be trusted yet; **Think on it** if there is a Needs the user finding, or a Small fix that could change the conclusion; **Ship it** otherwise.
- Rank the findings, most serious first. Keep at most five as separate findings: those that change the verdict, a claim or how sure the brief can be. Fold the rest into one Note.
- One line per finding. Quote a number from the results only if it decides the label.
- Fix is a suggestion for the analysis, such as "add a same-season baseline", never a number you worked out.

## Act 1: Resolve the input (the gate)

1. Use the argument, or the newest run folder under `outputs/`.
2. If it is not a run folder holding `frame.md` and `analysis.py`, stop: "Validate needs a run folder with frame.md and analysis.py; run /analyse first."
3. If `review.md` already exists, this is a recheck. Read it first. Rewrite it in full, and for each earlier finding say in Checked or under its code whether it is fixed, still open or changed. Review only the earlier findings and the results added or changed since: rerun them, open their charts, and put them through Act 7 as if new. Repeat Act 6 only if a fix touched the fields it tested.

## Act 2: Load the context

1. Read `frame.md`. A missing heading counts as "not given in the frame", not as a failure.
2. Read `knowledge/beam/quirks.md`, `knowledge/beam/corrections.md`, and the note for each table under Tables likely involved.
3. Read `analysis.py`.

## Act 3: Fit to the frame

1. It answers the Question and the Decision it informs, with a measure that fits the decision.
2. It covers the Population the decision affects, no more and no less.
3. It can show whether What would change the decision happened.
4. It stays inside the Analysis window and respects Out of scope.
5. Additional context and Open questions are handled or named.
6. The frame itself fits the decision. If the decision depends on something the frame never asks about, such as another outcome, another group or a cost, that is a Needs the user finding with Where: frame.md and Fix: return to /frame.
7. When the decision targets groups: the rule can pick some out (one every group passes, or none does, cannot), and they are groups the business can treat differently (the frame's Population says which).
8. When the decision has a money side, a result table sizes it in money for the whole affected group over a stated period, not only per customer or as an index. If not, that is a Small fix for /analyse.

## Act 4: Code review

Judge whether the code is sound overall. Skip style and small details.

1. It is safe to rerun: it writes only inside its own folder, nothing to `data/`, and prints aggregates only. If not, do not run it; that is a finding.
2. The metric, filters and joins match what the frame and the comments say.
3. The code counts every exclusion, gives it a reason, and would show lost or duplicated rows.
4. Dates are handled right:
   - The analysis date in AGENTS.md is used, never the real date.
   - The window matches the Analysis window in the frame.
   - Every period is complete: no partial months, and no one counted before they had the full time to reach the outcome.
   - Compared periods are alike in length and season.
5. Known data issues (quirks, corrections) are handled.
6. Map the data from each source table, through filters, joins and new columns, to each result CSV and chart, with row counts where the script prints them. This becomes the Data flow.

## Act 5: Rerun

1. If the script is not safe to rerun, skip the rerun.
2. Copy `analysis.py` to `outputs/<run>/rerun/`, run it from the repo root, and compare with `poetry run python helpers/compare.py outputs/<run>/data outputs/<run>/rerun/data`. If it fails, write the cause and the fix as a finding, give Fix first, and skip the remaining checks.
3. Read the printed output and result files: the numbers make sense, and the script's own sanity checks ran and passed.
4. What the script, comments and charts claim follows from the results.
5. Open each chart: it shows what its title says, and the axes do not mislead.
6. Anything written to `knowledge/beam/` matches the results and does not contradict an older line.
7. Every claim the analysis makes, including a sensitivity, is backed by a result table in the run folder's `data/`. A check you ran in `rerun/` is evidence for the review only; if the brief will need it, that is a Small fix for /analyse.

## Act 6: Source data

The code can be right and the data underneath it can still change meaning halfway through the window. Test the inputs, not just the script. These are checks on the fields, not new cuts of the answer.

1. List the fields the headline metric depends on: the outcome date (for example `end_date`), status values, amounts, and any gap the metric relies on (for example days from the last payment to the end).
2. For each, run `helpers.checks.stable_over_time` over the whole analysis window, from the repo root with a scratch script under `outputs/<run>/rerun/`. Pass a yes/no, numeric or category column; derive one when the meaning sits in a gap between two dates or in the timestamp itself. It flags a lasting step beyond noise. Print only its `summary`.
3. A break says the field changed, not why. Before you call it a recording break, run the check again on a subset where the mix is steady. A step that shows in every subset at once, or a format that appears or vanishes, is a recording break. A step that follows a real event, or vanishes in the steady subset, is behaviour or mix.
4. A recording break inside any compared window means the baseline is not like for like. Name the period and the metric, and say which baselines stay clean. A change just before the baseline that nothing in the data explains is a Needs the user finding: ask what changed.
5. Check that each compared period has enough people behind it and that the mix of groups did not shift between periods (a signup spike, a new channel).
6. When the recommendation acts on a group going forward, check that it is still made of the same people: a new source feeding it, a jump in volume, a shift in mix. If the future group differs from the one measured, that is a finding.

## Act 7: Reasoning

Judge the method. Do not run checks yourself.

1. Does every headline number have a fair baseline (like for like, including season), in named units?
2. Are effects weighed against noise, and small groups not over-read?
3. Are differences between groups tested, not assumed? Is a shift in the mix of groups checked?
4. Are other explanations and confounders named? Is cause claimed from a correlation?
5. Would the conclusion hold under reasonable other choices of baseline, definition or window?
6. If a projection decides the call, does the analysis show that the rate it projects has held, rather than a one-off reaction? Is the answer over the observed months shown next to the projected one? If the two point different ways, the recommendation is at most tentative.
7. Is the result big enough to matter for the decision, against the cost and risk of acting on it?
8. Anything else that could make the answer wrong.

## Act 8: Write the review

1. Write `outputs/<run>/review.md` from the template, each finding under Code review or Analysis review, most serious first.
2. Tag each step in Data flow that has a finding with the finding's number, and mark it as an issue.
3. Give exactly one verdict.
4. Fill Checked (at most five lines) and Not checked. One line always says how dates and windows were handled, and one says what the source-data checks in Act 6 found. On a recheck, one line says which earlier findings are fixed.

## Deliver

The review is the deliverable. On the CLI, show only:

- The verdict and its one-line reason.
- The number of findings for each label.
- The path of `review.md`.
- Each proposed quirk, so the user can decide whether to add it.

Keep it under eight lines. Do not paste the review into the CLI.
