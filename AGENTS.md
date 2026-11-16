# AI Analyst

A data analyst that runs inside Claude Code on Beam's data. Beam is a media app with free, monthly and annual plans and 14-day trials.

## How work routes
- A business question: `/analyst <question>` runs the whole chain.
- A script, notebook or run folder to check: `/validate`.
- Finished results to write up: `/deliver`.
- Each step is also its own skill (`/frame`, `/profile`, `/analyse`) and works alone; skills share nothing except the files in the run folder and `knowledge/beam/`.

## Where things live
```
knowledge/beam/          one YAML per table, index.yaml, quirks.md, corrections.md
helpers/                 checks, charts, compare, build_index, check_credentials
outputs/<date>_<slug>/   one folder per question:
                         frame.md, sql/, data/, analysis.py, charts/, review.md, brief.md
.claude/skills/          analyst, frame, profile, analyse, validate, deliver
```

## Conventions
- Run Python with `poetry run python ...` from the repo root.
- Never print raw rows into the conversation; aggregates only.
- In SQL, name every column; never `SELECT *`. When exploring, filter to a small slice first, such as the latest date or one month.
- Beam's data lives only in the database, reached through `course-db`; it is read-only, so never try to write to it.
- Name run folders with the real date from `date +%F` (YYYY-MM-DD).
- Treat the analysis date, looked up as `knowledge/beam/index.yaml` says, as "today" inside every analysis, never the real date.
- No em dashes in anything written for a reader.
- Before touching data, read `knowledge/beam/index.yaml`, then the YAML of each table in play in full, then `quirks.md` and `corrections.md`.
- A new fact about one table goes in its YAML: in the field's description if it changes how SQL is written, otherwise in `notes`. Only facts that span tables or are about reading results go in `quirks.md`. One home per fact.
- When the user corrects you, append one dated line to `corrections.md` and continue.
- Work on a branch and bring it into `main` through a PR; never push to `main` directly and never force-push.
- Before every push, run `poetry run python helpers/check_credentials.py`; push only on exit 0.
- Before changing anything in `.claude/skills/` or `helpers/`, read `DECISIONS.md` and `TODO.md`; when a change sets or drops a rule, add or update one line in `DECISIONS.md`.
