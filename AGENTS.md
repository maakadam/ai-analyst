# AI Analyst

A data analyst that runs inside Claude Code on Beam's data. Beam is a media app with free, monthly and annual plans and 14-day trials.

## How work routes
- A business question: `/analyst <question>` runs the whole chain.
- A script, notebook or run folder to check: `/validate`.
- Finished results to write up: `/deliver`.
- Each step is also its own skill (`/frame`, `/profile`, `/analyse`) and works alone; skills share nothing except the files in the run folder and `knowledge/beam/`.

## Where things live
```
data/                    Beam CSV exports; never modified
knowledge/beam/          one YAML per table, index.yaml, quirks.md, corrections.md
helpers/                 profile, checks, charts, build_index; the arithmetic runs here
outputs/<date>_<slug>/   one folder per question:
                         frame.md, analysis.py, data/, charts/, review.md, brief.md
.claude/skills/          analyst, frame, profile, analyse, validate, deliver
```

## Conventions
- Run Python with `poetry run python ...` from the repo root.
- Never print raw rows into the conversation; aggregates only.
- Never modify anything in `data/`.
- Name run folders with the real date from `date +%F` (YYYY-MM-DD).
- The data ends on 2026-09-24. Treat that as "today" inside every analysis, never the real date.
- No em dashes in anything written for a reader.
- Before touching data, read `knowledge/beam/index.yaml`, then the YAML of each table in play in full, then `quirks.md` and `corrections.md`.
- A new fact about one table goes in its YAML: in the field's description if it changes how SQL is written, otherwise in `notes`. Only facts that span tables or are about reading results go in `quirks.md`. One home per fact.
- When the user corrects you, append one dated line to `corrections.md` and continue.
- Work on a branch, one PR per step.
- Rebase the branch onto `main` before opening the PR; merge it with a merge commit, not squash.
- Never push to `main` directly and never force-push.
- Before every push, check that no database credentials are in the diff, the commit messages or `.env`/`.mcp.json`.
- Before changing anything in `.claude/skills/` or `helpers/`, read `DECISIONS.md` and `TODO.md`; when a change sets or drops a rule, add or update one line in `DECISIONS.md`.
