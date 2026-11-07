---
name: analyst
description: "Answer a business question about Beam's data end to end: frame, profile, analyse, validate, deliver."
user-invocable: true
argument-hint: "<the business question>"
---

Answer this question about Beam's data end to end: $ARGUMENTS

If the question above is empty, ask for the question and stop. Never invent one.

## The method

Every step below follows these rules.

1. **Frame the decision before touching data.** If the question does not say what decision it informs and who decides, ask; never reconstruct it.
2. **Never answer a table question from the schema alone.** Profile first; a table without a note in `knowledge/beam/` gets one before it is used.
3. **A naked number is not a finding.** Every number carries a comparison (prior period, segment or benchmark) or says none is available; percentage points and relative percent are named.
4. **Cite the table, the filter and the code.** Every number in a brief traces to `analysis.py` and a result table in the run folder.
5. **Parts sum to totals and joins do not fan out.** The checks in `helpers/checks.py` run in code, not in prose.
6. **Say what was not checked.** Open periods, unmatured trials and untested assumptions are part of the answer.
7. **Read the knowledge folder before writing code, and write back what you learn.** Read `knowledge/beam/` (table notes, `quirks.md`, `corrections.md`) first; when the user corrects you, append the correction to `corrections.md` as one dated line and continue.

## The steps

1. Run the `frame` skill with the question above: read `.claude/skills/frame/SKILL.md` and follow it. Note the run folder it created.
2. For each table named under "Tables likely involved" in the frame note that has no `knowledge/beam/<table>.md`, run the `profile` skill on it (`.claude/skills/profile/SKILL.md`).
3. Run the `analyse` skill on the run folder (`.claude/skills/analyse/SKILL.md`).
4. Run the `validate` skill on the run folder (`.claude/skills/validate/SKILL.md`). If its verdict is **Fix first**, fix `analysis.py` according to the findings, rerun it, and run `validate` again. At most two rounds. If it is still **Fix first**, stop and report the findings; do not write a brief. If its verdict is **Think on it**, apply any finding that is a small change to `analysis.py` (a filter, a baseline, a label) and rerun the script once, and carry every remaining finding into the brief's Appendix (Checks) as not verified.
   - If an applied fix adds a result or changes a number the recommendation is likely to rest on, run `validate` once more as a recheck before deliver. This round always runs, even after two rounds of Fix first. If the recheck gives Fix first, stop and report; do not write a brief.
   - Otherwise do not run `validate` again.
5. Run the `deliver` skill on the run folder (`.claude/skills/deliver/SKILL.md`).
6. Finish with the path of the run folder, the verdict from `review.md`, and the Key Takeaways from `brief.md` copied verbatim. If any number the Recommendation rests on is marked not verified in the brief, add one line naming it. Never call a run complete while that line applies. Nothing else on the CLI.
