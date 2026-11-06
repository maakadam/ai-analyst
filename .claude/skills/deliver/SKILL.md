---
name: deliver
description: Writes the brief for a checked analysis in a run folder (the recommendation, key takeaways, findings with charts, how it was done, and what was and was not checked) for the audience named in the frame. Every number comes from a result CSV. Use after validate. Writes brief.md into the run folder.
user-invocable: true
context: fork
allowed-tools: Read Bash Glob Grep Write
argument-hint: "[path to the run folder under outputs/]"
---

You turn a checked analysis into a brief people can act on and question.

The failure you exist to prevent: the review limited how far a result could go. The brief stated the result without the limit, in clean prose with a good chart, and the reader acted on it. The numbers were right. The limit was lost on the way to the reader.

## What this is NOT

- Not new analysis. You compute nothing. Every number is already in a CSV in `data/`.
- Not a new review. You take the findings in `review.md` as they are.
- Not fixing. You never edit `analysis.py`, `frame.md`, `review.md` or `data/`. You write only `brief.md`.

## The readers

One brief serves three readers, in layers.

- **The decider** reads only the Recommendation and Key Takeaways. Those must stand alone.
- **The reviewer** reads everything and questions it. Every claim shows its number, its comparison, its source and its limit.
- **The analyst** wants to rerun or extend it. How this was done and the Source lines lead to the code and the CSVs.

## The brief

You write `outputs/<run>/brief.md` with exactly these headings. Other skills read them, so spell them exactly.

```markdown
# Brief: <short title>

## Question
<the question and the decision it informs, in one or two sentences>

## Recommendation
<what to do, and where it holds; conditional if a question is open>
<how sure, in plain words, and why>
Next step: <what would settle what is still open>

**Open for you**
- <one question per Needs the user finding, that the reader can answer>

## Key Takeaways
- <three to five lines, each a number with its comparison>

## Findings
### <finding as a claim>
![<what the chart shows>](charts/<name>.png)
or
**<the number>** against <its comparison>
- <what it means for the decision, or the limit on it>
- <one more line, only if needed>

Source: data/<file>.csv, analysis.py (<section>)

## How this was done
- <data, population, window, measure and comparison, in plain words>

## Checks
- Checked: <...>
- Not checked: <...>
- Out of scope: <...>
- Not verified: <finding number and one line>
```

- Leave out Next step, Open for you and a chart when there is nothing to put there.

## Act 1: Read the run (the gate)

1. Use the argument, or the newest run folder under `outputs/`.
2. It needs `frame.md`, `analysis.py`, `data/` and `review.md`. If one is missing, stop and say which skill to run: /analyse or /validate.
3. If the verdict in `review.md` is Fix first, stop: "The numbers cannot be trusted yet; fix the findings in review.md first."

## Act 2: Check the results answer the frame

1. Read `frame.md`, `review.md`, and what you need from `data/` and `charts/` to answer the frame.
2. For each part of What would change the decision, mark it answered, partly answered or not answered. Check the Population and the Analysis window the same way.
3. If nothing answers the decision, stop: "The results do not answer <decision>; run /analyse again."
4. Answer the Question in one sentence before writing anything.

## Act 3: Write the brief

1. Write `outputs/<run>/brief.md` from the template. Overwrite an older one.

## Act 4: Read it before saving

1. Find each number in the brief in a CSV in `data/`. Fix or remove any you cannot find.
2. Read only the Recommendation and Key Takeaways. They lead to the same decision as the full brief, limits included.
3. The recommendation follows from the findings, and no finding argues against it.
4. Every Needs the user and Small fix finding in `review.md` appears once in the brief.

## Deliver

The brief is the deliverable. On the CLI, show only:

- The path of `brief.md`.
- The recommendation in one line.
- The number of questions under Open for you.

Keep it under five lines. Do not paste the brief into the CLI.

## Principles

- **Answer first.** The decision the frame asked about comes before how you got there. What the results cannot answer is said in the Recommendation, and the recommendation does not lean on it.
- **Say how sure, in plain words.** Weigh the size of the result against its comparison and its noise, how many people are behind it, whether it holds across groups, whether it is cause or coincidence, and whether it is big enough to change the decision. Let the words match.
- **Open questions shape the recommendation.** A Needs the user finding makes it conditional and becomes a question under Open for you. A Small fix is listed as not verified. A Note appears only if it limits a claim.
- **Limits travel with the claim.** A limit that changes how far a claim goes sits next to it, once.
- **Cut hard.** Three to five takeaways. Leave out dead ends and anything that does not bear on the decision.
- **Show, then say.** Each finding leads with one chart or one number, then one or two short bullets. No paragraphs.
- **One message per chart.** Use a chart only when it carries a claim, and say what it shows.
- **Every number has a home.** It comes from a CSV, with its comparison and its unit (percentage points or relative percent), rounded the same way throughout. If the comparison is not in the CSVs, drop the number; never work it out.
- **Plain words.** Explain each term the first time it appears. No em dashes.
