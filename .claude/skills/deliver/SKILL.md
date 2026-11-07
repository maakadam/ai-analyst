---
name: deliver
description: Writes the brief for a checked analysis in a run folder (a clear recommendation, key takeaways, findings with charts, and an appendix with sources and checks) for the audience named in the frame. Built from the frame and the analysis outputs; the review only gates it and sets its limits. Every number comes from a result CSV. Use after validate. Writes brief.md into the run folder.
user-invocable: true
context: fork
allowed-tools: Read Bash Glob Grep Write
argument-hint: "[path to the run folder under outputs/]"
---

You turn a checked analysis into a brief a business stakeholder can act on in two minutes, and an analyst can still question.

Three inputs, in this order of weight:

- **The frame** (`frame.md`) sets what the brief must answer: the decision, the audience, and what would change the decision.
- **The analysis outputs** (the result CSVs in `data/`, including `baseline.csv` with the groups compared, the charts in `charts/`, and `analysis.py` for what each table measures) supply the answer. The story of the brief comes from here.
- **The review** (`review.md`) gates the brief and sets its limits: how far each claim can go, and what is not verified. It never sets the story.

Two failures you exist to prevent:

- **The limit got lost.** A result only held within limits. The brief stated the result without the limit, and the reader acted on it.
- **The answer got lost.** The brief was built around the review: every finding code, every caveat, every file, ending on "it depends on which measure you use". The reader finished it and still did not know what to do.

## What this is NOT

- Not new analysis. You compute nothing. Every number is already in a CSV in `data/`.
- Not a new review. You take the findings in `review.md` as they are.
- Not fixing. You never edit `analysis.py`, `frame.md`, `review.md` or `data/`. You write only `brief.md`.

## The readers

One brief serves two readers, in two parts.

- **The decider** reads the body: Recommendation, Key Takeaways, The groups we compared, Findings. It is written for them alone, in business words. No finding codes (A1, C2), no file names, no section names of the script, no column names.
- **The reviewer or analyst** reads the Appendix: sources, method, checks, and every review finding by its code.

## The brief

You write `outputs/<run>/brief.md` with exactly these headings. Other skills read them, so spell them exactly.

```markdown
# Brief: <short title>

## Question
<the decision, in one sentence, in the audience's words>

## Recommendation
**<one sentence: what to do>**
<one or two sentences: why, with at most two numbers; when the decision has a money side, one of them is the money at stake for the whole group over a stated period>
<how sure, in plain words: confident / fairly confident / tentative, and the main reason>
<one line: what would change this recommendation, and how to find out if cause is unclear>

**Open for you**
- <at most two questions, only ones that need the decider's judgement>

## Key Takeaways
- <three lines, each one plain sentence with at most one or two numbers and their comparison>

## The groups we compared
<one sentence: who is compared and why these groups>

| Group | Users | <outcome> rate | Window |
|---|---|---|---|
| <group> | <n> | <rate> | <start to end> |

## Findings
### <finding as a claim in plain words>
![<what the chart shows>](charts/<name>.png)
- <what it means for the decision>
- <its limit, if one changes how far it goes>

## Appendix
### How this was done
- <data, population, window, measure and comparison, in plain words>

### Sources
- <each finding title>: data/<file>.csv, analysis.py (<section>)

### Checks
- Checked: <...>
- Not checked: <...>
- Out of scope: <...>
- Review findings: <code> <label>: <one line on how it was handled, or "not verified">
```

- Leave out Open for you and a chart when there is nothing to put there.
- The groups we compared has two to four rows, taken from `data/baseline.csv`, plus a total row when it helps. It anchors the story: Findings refer back to these groups and their sizes, for example "annual subscribers (12,400 of them) churn half as often".
- At most three Findings. Each leads with a chart, or one bold number against its comparison when no chart fits.

## Act 1: Read the run (the gate)

1. Use the argument, or the newest run folder under `outputs/`.
2. It needs `frame.md`, `analysis.py`, `data/` and `review.md`. If one is missing, stop and say which skill to run: /analyse or /validate.
3. If `data/baseline.csv` is missing, write the brief without The groups we compared, and add "Groups compared: no baseline table; rerun /analyse" under Not checked. Never work the group sizes out yourself.
4. If the verdict in `review.md` is Fix first, stop: "The numbers cannot be trusted yet; fix the findings in review.md first."

## Act 2: Decide what you are recommending

1. Read `frame.md`: the Question, the Decision it informs, the Audience and What would change the decision. This is what the brief must answer.
2. Read the analysis outputs: the result CSVs in `data/`, the charts in `charts/`, and `analysis.py` for what each table measures and which comparison it carries.
3. For each part of What would change the decision, mark it answered, partly answered or not answered from those outputs.
4. If nothing answers the decision, stop: "The results do not answer <decision>; run /analyse again."
5. Write the answer to the Question in one sentence, then the action it implies. This is the recommendation.
6. Only now read the findings in `review.md`, for two things: limits that change how far a claim goes (they go next to that claim, in plain words) and gaps that lower how sure you are. A finding that changes neither goes to the Appendix only.
7. **Pick a course.** Open questions do not make a recommendation conditional by default. Recommend what the evidence best supports today, say how sure you are, and put what would change it in one line. Only when the evidence points both ways with nothing to break the tie, say so and recommend the cheapest next step that would break it.
8. **Name how to find out.** When the evidence cannot separate cause from coincidence (before-and-after data, or a weak comparison group), the recommendation names the cheapest way to find out, such as a holdout, a staged rollout or a small experiment, instead of only waiting for more data.
9. **Size it.** When the decision has a money side, take the money at stake for the whole affected group from the CSVs and put it in the Recommendation. If no CSV holds it, say so under Not checked and lower how sure you are; never work it out.
10. **Weigh what is not verified.** If the number the recommendation rests on was added or changed after the last review, or the review marks it not verified, the recommendation is at most tentative and says in plain words which number is unchecked.
11. **Sort the open questions.** One that the data could answer (a horizon, a cut, a baseline) is a gap in the analysis: it goes in the Appendix as not verified and lowers how sure you are; it is never handed to the decider. Only a question that needs the decider's judgement or knowledge (a target, a risk appetite, another change they know of) goes under Open for you.

## Act 3: Write the brief

1. Write `outputs/<run>/brief.md` from the template. Overwrite an older one.
2. Round every number the same way: rates to one decimal place in percent, changes in percentage points to one decimal, relative change to whole percent, money to the nearest thousand.
3. Explain each term the first time it appears ("churn: the share of subscribers who cancel in a month").

## Act 4: Read it before saving

1. Find each number in the brief in a CSV in `data/`, and each claim it makes in a result table too. Fix or remove any you cannot find.
2. Read only the Recommendation and Key Takeaways, as the decider would. They say what to do, how sure, and the limit that matters, with nothing to look up.
3. Count: the body has no finding codes, file names or column names, at most two numbers in the Recommendation, at most two per takeaway.
4. If the decision has a money side, the Recommendation says how much is at stake in money, or says it is not known.
5. The recommendation follows from the findings, and no finding argues against it. A larger risk elsewhere in the results is named in the Recommendation or its "what would change this" line, not only as a limit further down.
6. Every Needs the user and Small fix finding in `review.md` appears once in the Appendix.

## Deliver

The brief is the deliverable. On the CLI, show only:

- The path of `brief.md`.
- The recommendation in one line.
- The number of questions under Open for you.

Keep it under five lines. Do not paste the brief into the CLI.

## Principles

- **Frame asks, analysis answers, review limits.** The brief is built from the frame and the analysis outputs. The review decides whether it ships and how far each claim goes, not what it says.
- **Answer first, and commit.** The decider asked what to do. Say it, say how sure, say what would change it. "It depends" is not a recommendation.
- **Business words in the body, references in the Appendix.** The decider never needs a file name or a finding code to follow the argument.
- **Size it.** A per-customer figure or index says which way; money for the whole group says whether it is worth doing.
- **Few numbers, each with its comparison.** A number that does not move the decision stays in the Appendix or out.
- **Limits travel with the claim.** A limit that changes how far a claim goes sits next to it, once, in plain words.
- **The analyst's gaps are not the decider's homework.** A question the data could answer is a gap to close, not a question to ask.
- **Anchor before you argue.** The reader sees who was compared, how many, and what is normal for them before any finding.
- **Show, then say.** Each finding leads with one chart or one number, then one or two short bullets. No paragraphs.
- **Every number has a home.** It comes from a CSV. If the comparison is not in the CSVs, drop the number; never work it out.
- **Plain words.** No em dashes.
