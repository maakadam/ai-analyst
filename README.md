# AI Analyst

An AI data analyst that runs inside Claude Code and answers business questions about Beam's data. Beam is a media app where users browse, listen to and read content on free, monthly and annual plans. You ask a question in plain words; the analyst frames it, profiles the data, analyses it with pandas, checks its own work and hands back a written brief.

## How It Works

1. **Frame:** pins the question, the decision it informs, the audience and what would change the decision, then gets your approval before any data is touched
2. **Profile:** describes each table from the data and writes it down
3. **Analyse:** writes pandas code that can be rerun, where every number carries a comparison
4. **Validate:** reviews the work as a fresh reader (fit to the frame, code, rerun, source data, reasoning) and gives one verdict: Fix first, Think on it or Ship it
5. **Deliver:** writes a brief for the decider, with the recommendation first and the sources and checks in an appendix

## Setup

### Prerequisites

- Python 3.10 or 3.11
- [Poetry](https://python-poetry.org/docs/#installation)
- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview)

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

3. **Start Claude Code**:
   ```bash
   claude
   ```
   Run `claude` from the repo root so it picks up the project's skills and instructions.

## How the agent is put together

There is no framework and no Python program controlling the model. The agent is a Claude Code project:

- **An entry-point skill:** `.claude/skills/analyst/SKILL.md` lists the five steps in order, and `/analyst <question>` runs them.
- **Routing lines:** a few lines in `AGENTS.md` say which skill handles which kind of request. A business question runs the full chain, a file to check goes to Validate, and finished results go to Deliver.
- **One skill per step:** each step is its own skill under `.claude/skills/`.
- **A knowledge folder:** `knowledge/beam/` holds one note per table (Profile writes these), a file of known quirks, and a corrections file the agent reads before every run and adds to when you correct it.
- **Helpers:** small Python modules in `helpers/`. Claude writes the analysis script, and the arithmetic runs in code, never in the model's head.
- **One output folder per question:** the brief, the charts and the script that produced the numbers, so anyone can rerun it.

## Status

All six skills are in place, so `/analyst` runs end to end. The course repo shipped Profile, Analyse and the helpers; Frame, Validate and Deliver were written here. `knowledge/beam/` holds a note for each of the four main tables (users, subscriptions, payments, trials), the known quirks and the corrections file; the analyst reads it before touching any data. `TODO.md` lists ideas for later.

## The price question

The answer to the course question is in `outputs/2026-11-07_march-price-retention/`: start with `brief.md`, then `review.md`, `analysis.py`, `data/` and `charts/`. Monthly churn rose from 1.3% to 5.1% after the increase, mostly in the first year of a subscription.

An earlier run of the same question, made before the trial period was excluded, is kept on the `archive/march-price-retention-v1` branch for comparison.

Try it with the course question:

```
/analyst Did the March 2026 price increase hurt retention, and for whom? The head of growth is deciding whether to roll back part of the increase for some customers.
```

## Design decisions

Why the skills work the way they do is in `DECISIONS.md`.

## Project Structure

```
ai-analyst/
├── data/                 # Beam's exported tables (CSV)
├── knowledge/beam/       # Table notes, known data quirks and corrections
├── helpers/              # Shared Python helpers for analysis scripts
├── outputs/              # One folder per question
├── .claude/              # Skills for Claude Code
└── pyproject.toml        # Dependencies
```

## Data

- `users.csv`: 31,165 rows, one per user
- `subscriptions.csv`: 30,747 rows, one per subscription
- `payments.csv`: 100,914 rows, payments from 2025-01-01
- `trials.csv`: 2,073 rows, one per trial
- `user_activity_metrics.csv`: 998 daily rows of active user counts (dau, wau, mau)

Session-level data is not included.

---
