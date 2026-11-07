# Workflow fix: keep unverified numbers out of the brief

Status: proposed, not applied.

## What happened
In the March 2026 price increase run, a fix after the first review added the money estimate for new subscribers (about $46k). The second review flagged it: constant churn assumed for a year, the wrong group of signups, and a mismatched time span. The workflow still allowed the brief to put it in the Recommendation, marked "tentative" and "not verified". The user removed it: a number that has not passed review should not be used.

## Root cause
Three rules together let it through:
1. `.claude/skills/deliver/SKILL.md:98` (Act 2, step 10) allows a recommendation to rest on an unverified number as long as it is called tentative.
2. `.claude/skills/analyst/SKILL.md:31` (Think on it) caps fixes at one round. Findings from the second review go to the Appendix as not verified, even when they are about a number the recommendation uses.
3. `.claude/skills/analyst/SKILL.md:34` treats an unverified headline number as something to flag at the end, not something that stops the brief.

## Suggested edits
1. **deliver, Act 2 step 10.** Replace with: "Use only verified numbers. A number the review flags, did not see, or marks not verified is left out of the body entirely. Where it was needed (for example the money at stake), say it is not known and why, and lower how sure you are."
2. **deliver, Act 4 (read it before saving).** Add a check: "Every number in the body traces to a result the latest review saw and did not flag. Remove any that does not."
3. **analyst, step 4, Think on it.** Add: "If the second review flags a number the recommendation would rest on, either fix it and validate again (one more round), or tell deliver to leave it out. Never carry it into the body as not verified."
4. **analyst, step 6.** Change the last sentence to: "If a number the recommendation needed was left out as unverified, add one line naming it and what would verify it."
5. **validate, Act 8.** Add a short list under Verdict, "Numbers not cleared for the brief", so deliver has an explicit list to exclude instead of inferring it from findings.

A correction line was added to `knowledge/beam/corrections.md` on 2026-11-07 so the rule applies before the skills are edited.
