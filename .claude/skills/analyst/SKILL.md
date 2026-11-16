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
2. **Never answer a table question from the schema alone.** A table without a YAML in `knowledge/beam/` is profiled before it is used.
3. **A naked number is not a finding.** Every number carries a comparison (prior period, segment or benchmark) or says none is available; percentage points and relative percent are named.
4. **Cite the query, the table and the code.** Every number in a brief traces to a saved `sql/` query, a result table and, where pandas changed it, `analysis.py`.
5. **Parts sum to totals and joins do not fan out.** Checks run as saved SQL and code, not in prose.
6. **Say what was not checked.** Open periods, unmatured trials and untested assumptions are part of the answer.
7. **Read the knowledge folder before writing code, and write back what you learn.** Read `knowledge/beam/` (`index.yaml`, the table YAMLs, `quirks.md`, `corrections.md`) first; when the user corrects you, append the correction to `corrections.md` as one dated line and continue.

## The steps

Each step ends with a commit of what it wrote, with a message naming the step: `git add -f outputs/<run> ':(exclude,glob)**/__pycache__/**'` (outputs/ is gitignored). Never commit while `outputs/<run>/rerun/` exists. A change under `knowledge/beam/` gets its own commit, so it can be picked onto another branch if the run is closed.

0. Start on `main`, up to date with `origin/main` after a `git fetch`, with no modified tracked files (untracked files are fine). If not, say so and stop.
1. Run the `frame` skill with the question above: read `.claude/skills/frame/SKILL.md` and follow it. Note the run folder it created. Create the branch `analysis/<run folder>`, adding `-2`, `-3` if that name exists locally or on `origin`, then commit.
2. For each Gap line under "Tables likely involved" in the frame note, run the `profile` skill with that data need (`.claude/skills/profile/SKILL.md`). If no table holds it, tell the user the frame can't be fully answered and ask whether to go on. Commit only if a YAML changed.
3. Run the `analyse` skill on the run folder (`.claude/skills/analyse/SKILL.md`). Commit.
4. Run the `validate` skill on the run folder (`.claude/skills/validate/SKILL.md`), then act on its verdict:
   - **Fix first:** fix `sql/` and `analysis.py` from the findings, rerun the changed queries and resave their CSVs, rerun the script, and validate again. If the second round is still Fix first, stop and report the findings; write no brief.
   - **Think on it:** apply the Small fix findings (a filter, a baseline, a label) in `sql/` or `analysis.py`, rerun the changed queries and the script once, and carry the rest into the brief: Needs the user findings to Open for you or the Appendix (deliver sorts them), unapplied Small fix findings to the Appendix as not verified, and Notes to the Appendix as they are. If a fix adds a result or changes a number the recommendation rests on, validate once more; if that gives Fix first, stop and write no brief.
   - **Ship it:** go to deliver.
   Commit after each validate round and each round of fixes.
5. Run the `deliver` skill on the run folder (`.claude/skills/deliver/SKILL.md`).
   If `review.md` has Proposed quirks, ask about each with AskUserQuestion and append to `knowledge/beam/quirks.md` only on a yes. Commit.
6. Publish. Ask with AskUserQuestion whether to push the run and open a PR; on no, leave the branch local. On yes:
   - `git fetch`. If the branch is not on `origin` yet, rebase it onto `origin/main`.
   - If `origin/main` holds a run folder with this run's slug (the name after the date) under another name, remove it with `git rm -r` on this branch and commit, so merging replaces it.
   - Run `poetry run python helpers/check_credentials.py`. On anything but exit 0, stop and show its output.
   - Push the branch and open a PR to `main` with `gh pr create`: the framed question as the title, the brief's Recommendation and Key Takeaways copied verbatim in the body, a "Knowledge changes" list of any commits under `knowledge/beam/`, and a link to `brief.md` at the pushed commit.
7. Finish with the path of the run folder, the verdict from `review.md`, the Key Takeaways from `brief.md` copied verbatim, and the PR link if published. If the brief marks a number the Recommendation rests on as not verified, add one line naming it; the run is not complete until it is verified. Nothing else on the CLI.
