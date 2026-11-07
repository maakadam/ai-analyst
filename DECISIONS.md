# Design decisions

Why the skills work the way they do. The goal is a general analyst assistant for any business question on Beam's data. Each rule below was added because a trial run showed it was needed.

## Across the chain
- **Skills share only files.** Each step reads and writes the run folder and `knowledge/beam/`, nothing else, so any step can run on its own (`/validate` on an old run, `/deliver` on checked results).
- **The model reasons, the code computes.** Every number comes from `analysis.py` and a result CSV, never from arithmetic in the conversation, so anyone can rerun it.
- **Two dates.** Run folders use the real date; inside the analysis, "today" is the last day of data, so open months and unmatured trials are judged against the data, not the calendar.
- **General rules, not past answers.** Examples from trial runs were replaced with the rule they stood for, so the skills do not steer a new question toward an old answer.
- **Less text.** Each skill opens with one failure story and keeps only rules that earn their place.

## Frame
- **Approval before any data is touched.** A tidy answer to the wrong question is the most expensive failure, so the person asking approves the frame first. The draft is shown as plain text because option previews do not show on every device.
- **Population and Additional context.** Who the decision affects, any narrowing, and other changes in the period are agreed up front, not discovered halfway through.
- **Like with like.** Frame suggests the splits that make a fair comparison (such as tenure and start cohort) before anyone has to ask.
- **Levers before splits.** Frame asks which groups the business can actually treat differently, since a result about a group nobody can act on cannot inform the decision.
- **A peer check.** A fresh agent hears a short pitch and replies "makes sense" or with at most three questions: a cheap second opinion.
- **Money at stake.** When the decision has a money side, frame suggests sizing it for the whole affected group. It sits in frame rather than analyse, so analyse stays close to the course version.

## Analyse
- **Kept close to the course version**, plus one rule: every claim has a table. Validate and deliver only trust what is in a result CSV, so a check that lives in the conversation cannot reach the brief.
- **Tried and dropped: an "orient" step** (group sizes and base rates before the plan). It added length, and as its own skill it would apply the frame's filters separately and drift from the findings. Kept as an idea in `TODO.md`.

## Validate
- **A fresh reader.** It runs in its own context, so it judges the work without the reasoning that produced it.
- **Source data, not only code.** Clean code can sit on data whose meaning changes partway through the window, for example when a field starts being recorded differently. Only the data shows that, so `helpers.checks.stable_over_time` tests whether the fields a metric depends on are stable across compared periods.
- **Small fix vs Needs the user.** A question the data can answer is never handed to the user; only judgement calls are.
- **Recheck mode.** A fix that adds or changes a number the recommendation rests on goes back through validate, so the brief never leans on a number no reviewer saw.

## Deliver
- **Built from the frame and the analysis; the review only gates it and sets its limits.** A brief built around the review lists every caveat and ends on "it depends".
- **Two readers.** The body is for the decider in business words; codes, files and checks go in the appendix.
- **Commit to a recommendation**, say how sure, and name what would change it. When cause is unclear, name the cheapest way to find out, such as a holdout or a small test.
- **Size it in money** for the whole affected group, taken from a CSV, never worked out in the brief.

## Repo
- **`outputs/` is gitignored**, so runs stay local by default. One run is force-added as a worked example.
