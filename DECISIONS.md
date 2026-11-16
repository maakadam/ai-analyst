# Design decisions

Why the skills work the way they do. The goal is a general analyst assistant for any business question on Beam's data. Each rule below was added because a trial run showed it was needed.

## Across the chain
- **Skills share only files.** Each step reads and writes the run folder and `knowledge/beam/`, nothing else, so any step can run on its own (`/validate` on an old run, `/deliver` on checked results).
- **The model reasons, the code computes.** Every number comes from a saved query, a result CSV and, where pandas changed it, `analysis.py`, never from arithmetic in the conversation, so anyone can rerun it.
- **Two dates.** Run folders use the real date; inside the analysis, "today" is the analysis date, looked up per run as the earliest last day of the event date columns in play, so open months and unmatured trials are judged against the data, not the calendar. Only columns marked as event dates count: scheduled dates and `sessions` (which runs two days long) would set it too late, and snapshot dates too early.
- **General rules, not past answers.** Examples from trial runs were replaced with the rule they stood for, so the skills do not steer a new question toward an old answer.
- **Less text.** Each skill opens with one failure story and keeps only rules that earn their place.

## Frame
- **Approval before any data is touched.** A tidy answer to the wrong question is the most expensive failure, so the person asking approves the frame first. The draft is shown as plain text because option previews do not show on every device.
- **Population and Additional context.** Who the decision affects, any narrowing, and other changes in the period are agreed up front, not discovered halfway through.
- **Like with like.** Frame suggests the splits that make a fair comparison (such as tenure and start cohort) before anyone has to ask.
- **Levers before splits.** Frame asks which groups the business can actually treat differently, since a result about a group nobody can act on cannot inform the decision.
- **A peer check.** A fresh agent hears a short pitch and replies "makes sense" or with at most three questions: a cheap second opinion.
- **Money at stake.** When the decision has a money side, frame suggests sizing it for the whole affected group. It sits in frame rather than analyse, so analyse stays close to the course version.

## Profile
- **Checks the YAML, doesn't write notes.** Profile tests the YAML and the database comments against aggregate SQL and proposes changes only where the data disagrees or SQL would be written differently, so each table keeps one source of truth. A table it can't trust is proposed for `excluded` instead.

## Analyse
- **Kept close to the course version**, plus one rule: every claim has a table. Validate and deliver only trust what is in a result CSV, so a check that lives in the conversation cannot reach the brief.
- **SQL computes, Claude saves the rows, pandas does the rest.** A test showed a typical aggregate costs under 1,000 tokens through the MCP, so neither a query subagent nor a query helper earns its extra layer. Claude runs each `sql/<name>.sql` through `course-db` and saves its rows unchanged as `data/<name>.csv`; `analysis.py` only reads the CSVs, so Python needs no database access and validate can rerun each query and compare.
- **Checks as SQL.** Checks that need raw rows (join fan-out, edge periods, matured windows) are small aggregate queries saved as `data/check_<name>.csv`; `helpers.checks` keeps only what runs on result tables.
- **Tried and dropped: an "orient" step** (group sizes and base rates before the plan). It added length, and as its own skill it would apply the frame's filters separately and drift from the findings. Kept as an idea in `TODO.md`.

## Validate
- **A fresh reader.** It runs in its own context, so it judges the work without the reasoning that produced it.
- **Source data, not only code.** Clean code can sit on data whose meaning changes partway through the window, for example when a field starts being recorded differently. Only the data shows that, so `helpers.checks.stable_over_time` tests whether the fields a metric depends on are stable across compared periods.
- **Small fix vs Needs the user.** A question the data can answer is never handed to the user; only judgement calls are.
- **Recheck mode.** A fix that adds or changes a number the recommendation rests on goes back through validate, so the brief never leans on a number no reviewer saw. A recheck looks only at what changed, so reviews converge instead of starting over.
- **Ranked and capped.** At most five findings that change the verdict, a claim or how sure the brief can be; the rest fold into one Note. A senior reviewer ranks, not lists.
- **Checks that apply.** Targeting, money and projection checks run only when the decision targets groups, has a money side or rests on a projection, so a plain "what happened" question is not judged as a pricing decision.
- **Learning across questions.** Validate proposes lasting source-data facts as quirk lines; the user decides whether they go into `quirks.md`, as with profile.
- **The rerun starts from the saved SQL.** Validate reruns each `sql/*.sql` through `course-db`, then a copy of `analysis.py` on those rows, and compares every CSV, so a query, a hand-copied row or the pandas step that no longer matches shows up. It reads AGENTS.md itself, since it runs in its own context.
- **Compare what the rows say, not how they are written.** `helpers/compare.py` sorts rows and reads ISO dates one way before comparing, and saved queries always have an `ORDER BY`, so row order or a date format is never a false Fix first.
- **Stability from aggregates.** `stable_over_time` takes one row per period (count, level, spread) from an aggregate query, so the source-data check never needs raw rows.
- **`rerun/` is scratch.** The rerun copy duplicates the run's outputs and can be regenerated from the saved queries and `analysis.py`, so validate writes what it showed into `review.md` and deletes the folder before the run is committed.

## Deliver
- **Built from the frame and the analysis; the review only gates it and sets its limits.** A brief built around the review lists every caveat and ends on "it depends".
- **Two readers.** The body is for the decider in business words; codes, files and checks go in the appendix.
- **Commit to a recommendation**, say how sure, and name what would change it. When cause is unclear, name the cheapest way to find out, such as a holdout or a small test.
- **Size it in money** for the whole affected group, taken from a CSV, never worked out in the brief.
- **Short body.** The body stays under about 400 words; the appendix lists only the review findings that changed the brief, and counts the rest.
- **A brief is evidence from its run.** Once a run is finished its brief is not edited by hand; a change goes through a new run, so the brief always matches the frame, script and review it came from.

## Repo
- **One source of truth per table.** Each table is described only in its `knowledge/beam/<table>.yaml`; the `.md` table notes were folded in and removed.
- **`index.yaml` is generated.** `helpers/build_index.py` builds it from the table files and `_index_header.yaml`, so it never drifts; edit those, never the index.
- **Quirks vs table YAML.** A fact about one table lives in that table's YAML; `quirks.md` holds only facts that span tables or are about reading results. The rule sits in AGENTS.md, so every session sees it and no fact gets two homes.
- **`main` is protected.** Every change reaches `main` through a PR from a branch rebased onto it and merged with a merge commit, so each step shows as one unit and its commits keep their evidence. A GitHub ruleset and `deny` rules in `.claude/settings.json` block direct and force pushes.
- **Name columns, explore small.** SQL names every column and never uses `SELECT *`, and exploration starts from a small slice such as the latest date, so every query reads only what it needs and `sessions` is never scanned blind.
- **The index rebuilds itself.** A hook in `.claude/settings.json` reruns the builder after any edit to a `.yaml` file in `knowledge/beam/`, so no one has to remember.
- **`outputs/` is gitignored**, so runs stay local by default. One run is force-added as a worked example; an earlier run of the same question is kept on the `archive/march-price-retention-v1` branch rather than on main, so main holds one answer per question.
