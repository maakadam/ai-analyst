# AI Analyst

An AI data analyst that runs inside Claude Code and answers business questions about Beam's data. Beam is a media app where users browse, listen to and read content on free, monthly and annual plans. The data lives in a read-only Postgres database that Claude Code reaches through an MCP server. You ask a question in plain words; the analyst frames it, checks what it knows about the tables, answers it with SQL and pandas, checks its own work and hands back a written brief.

## How It Works

1. **Frame:** pins the question, the decision it informs, the audience and what would change the decision, then gets your approval before any data is touched
2. **Profile:** checks a table's YAML against the database and proposes changes, or finds and describes a table the frame needs that isn't covered yet
3. **Analyse:** runs aggregate SQL against the database, saves each query with its result, and writes a pandas script on those results, where every number carries a comparison
4. **Validate:** reviews the work as a fresh reader (fit to the frame, code, a rerun of every query, source data, reasoning) and gives one verdict: Fix first, Think on it or Ship it
5. **Deliver:** writes a brief for the decider, with the recommendation first and the sources and checks in an appendix

## Setup

### Prerequisites

- Python 3.10 or 3.11
- [Poetry](https://python-poetry.org/docs/#installation)
- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview)
- [MCP Toolbox for Databases](https://github.com/googleapis/genai-toolbox) (`toolbox` on your PATH; tested with 1.17.0)
- The database credentials from the course (host, port, database, user, password)

### Installation

1. **Install Poetry** (if not already installed):
   
   **Windows (PowerShell)**:
   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
   ```
   
   **macOS/Linux**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   
   After installation, restart your terminal. If `poetry` command is not found:
   - **Windows**: Add `%APPDATA%\Python\Scripts` to your system PATH
   - **macOS/Linux**: Add `export PATH="$HOME/.local/bin:$PATH"` to your `~/.bashrc` or `~/.zshrc`

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set the database credentials** as environment variables: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER` and `POSTGRES_PASSWORD` (on Windows, as user or system variables). Type the password yourself; never paste it into a chat or a file in the repo.

4. **Register the database server** in a `.mcp.json` at the repo root. It is gitignored, and it holds only references to the variables, never the values:
   ```json
   {
     "mcpServers": {
       "course-db": {
         "type": "stdio",
         "command": "toolbox",
         "args": ["--prebuilt", "postgres", "--stdio"],
         "env": {
           "POSTGRES_HOST": "${POSTGRES_HOST}",
           "POSTGRES_PORT": "${POSTGRES_PORT}",
           "POSTGRES_DATABASE": "${POSTGRES_DATABASE}",
           "POSTGRES_USER": "${POSTGRES_USER}",
           "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"
         }
       }
     }
   }
   ```
   The server must be named `course-db`: the skills call its tools by that name.

5. **Start Claude Code** from the repo root, in a terminal where the variables are set:
   ```bash
   claude
   ```
   In VS Code, open the editor from that terminal (`code .`) or restart it fully after setting the variables, then approve `course-db` when asked. `claude mcp list` should show `course-db` as connected.

## How the agent is put together

There is no framework and no Python program controlling the model. The agent is a Claude Code project:

- **An entry-point skill:** `.claude/skills/analyst/SKILL.md` lists the five steps in order, and `/analyst <question>` runs them.
- **Routing lines:** a few lines in `AGENTS.md` say which skill handles which kind of request. A business question runs the full chain, a file to check goes to Validate, and finished results go to Deliver.
- **One skill per step:** each step is its own skill under `.claude/skills/`.
- **A knowledge folder:** `knowledge/beam/` holds one YAML per table (fields, measures, joins and example queries, checked against the database), a generated `index.yaml` that lists them and the tables left out, a file of known quirks, and a corrections file the agent reads before every run and adds to when you correct it.
- **Helpers:** small Python modules in `helpers/`: checks, charts, comparing reruns, building the index, and the credentials check run before every push. The arithmetic runs in SQL and code, never in the model's head.
- **One output folder per question:** the frame, every SQL query with its result, the pandas script, the charts, the review and the brief, so anyone can rerun it. `/analyst` works on its own branch per question and commits after every step; at the end it asks whether to open a PR.

## Status

All six skills are in place and work against the database, so `/analyst` runs end to end. The course repo shipped Profile, Analyse and the helpers; Frame, Validate and Deliver were written here, and in Week 2 every skill moved from CSV exports to the database. `knowledge/beam/` holds a YAML for every table the analyst may use. `TODO.md` lists ideas for later.

## The course questions

Each run folder holds the whole answer: start with `brief.md`, then `review.md`, `analysis.py`, `sql/`, `data/` and `charts/`.

**The price question**, answered against the database in `outputs/2026-11-17_price-increase-retention/`. Monthly churn rose from 1.3% before March 2026 to 4.2% from April to July; the brief recommends keeping $12 and testing a rollback on new monthly signups.

```
/analyst Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers.
```

**The trial question**, in `outputs/2026-11-17_trial-binge-vs-steady/`. Trial users who binge on day one and then go quiet convert at 5.1%, against 86.0% for steady users; the brief recommends onboarding emails that bring users back on several days, launched as a test.

```
/analyst Do trial users who binge on day one and then go quiet convert worse than steady users? The head of growth is deciding whether the onboarding emails should push trial users to spread their first week out.
```

The Week 1 answer to the price question is kept in `outputs/2026-11-07_march-price-retention/` as a record. It was computed from the CSV exports, now on the `archive/week1-csv-data` branch, so its script no longer reruns on `main`; it put churn after the increase at 5.1%. An earlier run, made before the trial period was excluded, is on the `archive/march-price-retention-v1` branch.

## Design decisions

Why the skills work the way they do is in `DECISIONS.md`.

## How changes reach main

`main` is protected: no direct pushes and no force pushes. Every change comes in through a pull request, one per piece of work (a step in building the analyst, or one analysis).

- Rebase the branch onto `main` before opening the PR.
- Merge with a merge commit, not squash, so each PR shows as one unit on `main` and the commits inside keep their messages.
- Before every push, run `poetry run python helpers/check_credentials.py` from the terminal where the database variables are set; push only on exit 0.
- Analysis PRs come from `/analyst`'s publish step and are for review: merge the runs worth keeping and close the rest with a short comment. A rerun of the same question replaces the older run folder.

## Project Structure

```
ai-analyst/
├── knowledge/beam/       # One YAML per table, index.yaml, quirks and corrections
├── helpers/              # Shared Python helpers for analysis scripts
├── outputs/              # One folder per question
├── .claude/              # Skills for Claude Code
└── pyproject.toml        # Dependencies
```

## Data

Beam's Postgres database, read-only, reached through `course-db`. Each table has a YAML in `knowledge/beam/`:

- `public.users`: 31,165 rows, one per user
- `public.subscriptions`: 30,747 rows, one per subscription
- `public.payments`: 144,065 rows, payments from 2022-01-12
- `public.trials`: 2,073 rows, one per 14-day trial (trials launched 2026-08-01)
- `public.sessions`: about 4.3 million rows, one per app session; query it only with aggregates
- `marts.user_activity_metrics`: one row per day of daily, weekly and monthly active users
- `ml.trial_snapshot` and `ml.churn_snapshot`: model training snapshots of trial conversion and churn

`marts.user_revenue_summary` is excluded: it is an unverified snapshot whose payments disagree with `public.payments`. The analysis date is looked up per run from the data, not the calendar.

---
