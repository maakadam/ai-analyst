---
name: analyse
description: Answers a framed business question about Beam's data with aggregate SQL through course-db, saved with its results, and one pandas script that can be rerun, where every headline number carries its comparison. Use after a question has been framed, when it is time to compute the answer. Reads the frame note in the run folder under outputs/ and writes the SQL, result tables, script and charts next to it.
user-invocable: true
allowed-tools: Read Bash Write Edit Glob AskUserQuestion mcp__course-db__list_tables mcp__course-db__execute_sql
argument-hint: "[path to the run folder under outputs/]"
---

You answer the framed question with queries and code that can be rerun.

The failure you exist to prevent: a confident number with no baseline, or a number that came out of a chain of arithmetic written in prose that nobody can check. "Trial conversion is 50%" tells a reader nothing until it says 50% against what. And a number computed in the conversation cannot be rerun, reviewed or corrected. The answer might even be right. Nobody can tell.

So the model reasons, SQL and code compute. You decide what to compute and what to compare it with. Saved queries and a script in the run folder do every count, rate, check and chart.

## What this is NOT

- Not the brief. You report numbers on the CLI; the Deliver step writes the brief.
- Not the review. You run the checks your plan needs; the Validate step reviews the work.
- Not a window into raw rows. Every `course-db` result lands in the conversation, so aggregate in SQL.

## The rules

These hold in every act.

- **A number alone is not a finding.** Every headline number carries a comparison: a prior period, a segment, or a benchmark.
- **If no comparison exists, say "no comparison available".** Never invent a baseline to fill the gap.
- **Segment before you average** when the frame or a quirk suggests groups behave differently. An average over groups that move in opposite directions hides both.
- **Percentage points and relative percent are different numbers.** A rate going from 40% to 44% is up 4 percentage points and up 10% relative. Name which one you mean, every time.
- **Never trust a period that has not closed.** A month still in progress, or a trial still inside its 14 days, is not a result yet.
- **Every claim has a table.** A number or a sensitivity the brief may use is saved to the run folder's `data/`. A check that lives only in the conversation cannot reach the brief.

## Act 1: Find the question (the gate)

1. Find the run folder. Use the argument if given. Otherwise use the newest folder under `outputs/` that holds a `frame.md`.
2. Read `frame.md` for the question, the decision it informs, the audience, and what would change the decision.
3. If there is no frame note, ask with AskUserQuestion for the question and the decision it informs. Then write `outputs/<YYYY-MM-DD>_<slug>/frame.md` yourself before anything else, with the same fields the Frame step writes: question, decision, audience, what would change the decision, and the tables likely involved. Get the date with `date +%F`; never guess it.
4. Never proceed on a guessed question. You may confirm a question you infer; you may not assume one.

## Act 2: Load the context

1. Read `knowledge/beam/index.yaml`, the YAML of each table involved in full, `quirks.md` and `corrections.md`.
2. If a table involved has no YAML, run the profile skill on it first: read `.claude/skills/profile/SKILL.md` and follow it, then come back here.
3. Say in one line which measures and golden queries apply, which quirks, and which corrections.
4. Look up the analysis date as the index conventions say, with one query saved as `sql/analysis_date.sql` and `data/analysis_date.csv`.

## Act 3: Plan

Write three to six bullets describing the computation. The plan must say:

- The analysis date and the column it came from.
- What each headline number is and the comparison it will carry, or that none exists.
- Which YAML measures and golden queries it uses, by name. Definitions come from the YAML; never restate them.
- How each applicable quirk is handled.
- Which segments you will split by and why.
- Which checks will run.

Show the plan before running any query for it.

## Act 4: Query, save, then script

1. One aggregate `execute_sql` per result table, starting from a golden query when one fits. Over about 200 rows means aggregate further or filter.
2. Save each statement to `outputs/<run>/sql/<name>.sql` and its rows to `outputs/<run>/data/<name>.csv`, exactly as returned, header first, with the same name. Then check the CSV's row count and one column total against a `COUNT` and `SUM` over the same query.
3. Each check is a small aggregate query saved the same way as `check_<name>`: rows before and after a join, the first and last dates at the edges, matured against all.
4. Write `outputs/<run>/analysis.py`: it reads the CSVs with pandas, derives what SQL did not, saves any new table to `data/`, and prints each check. Use `helpers.checks.parts_sum_to_total` when segments should add back to a total.
5. Make charts only through `helpers.charts`: `bar` or `line`, then `save` into `outputs/<run>/charts/<name>.png`. Every title states the takeaway the chart proves, not a label.
6. Run it from the repo root with `poetry run python outputs/<run>/analysis.py`, and fix it until it runs clean. If a check fails, decide whether it changes the answer and fix the query or report it. If the data cannot answer the question, say so plainly and stop.

## Act 5: Report

On the CLI, report:

- Each headline number with its comparison, stated as percentage points or relative percent, saying which.
- What was segmented and why.
- Which checks ran and what each said.
- What was not checked.
- The path of the run folder.

Keep it under twenty lines. No brief here; the Deliver step writes the brief.

## Principles

- **The question is the gate.** No frame note, no analysis. Ask; never guess.
- **SQL and code compute.** Every number comes from a saved query or `analysis.py`. None comes from prose arithmetic.
- **Rows as returned.** A saved CSV holds exactly what its `.sql` returned, so anyone can rerun the query and compare.
- **Always compare.** A number without its comparison is not a finding. When there is no comparison, say so.
- **The YAML defines.** Measures, joins and caveats come from the table YAML; the plan names them, never redefines them.
- **Closed periods only.** An open month or an unmatured trial is not a result.
- **Name the unit of change.** Percentage points or relative percent, never left for the reader to guess.
- **Say what you did not check.** A gap you name is safer than one a reader finds later.
