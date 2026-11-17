# Frame: Day-one binge vs steady trial conversion

## Question
Raw: "Do trial users who binge on day one and then go quiet convert worse than steady users? The head of growth is deciding whether the onboarding emails should push trial users to spread their first week out."
Framed: Among Beam trial users, do those who are heavily active on trial day 1 and then quiet for the rest of their first week convert to paid at a lower rate than those who use the app steadily across their first week?

## Decision it informs
Whether the onboarding emails should push trial users to spread their first-week use across several days.

## Audience
The head of growth.

## Population
All 14-day trials started since the 2026-08-01 launch. Growth can split the emails however it wants, so any group difference is a usable lever.
- Analyst suggestion: split by trial start week (users compared with others who started at the same time; the user asked to compare similar time periods).
- Analyst suggestion: split by region (country) and signup device (email targeting could follow either, and either could carry a different pattern).
- Analyst suggestion: split new signups (signed up for the trial) from existing free users who started a trial (existing users may already know the app and use it differently).
- Analyst suggestion: show trials canceled during days 1 to 7 separately (an early cancel can cause the quiet pattern rather than follow from it).
- Peer suggestion: compare binge and steady users at the same total week-one activity (sessions or minutes), so the result is about the spread of use, not heavy vs light users.

## What would change the decision
A conversion gap of at least a few percentage points (pp), with steady users ahead and a 95% interval that excludes zero, supports the emails. No gap, or binge users ahead, argues against them.
- Analyst suggestion: the money at stake, the yearly paid revenue added if binge-then-quiet users converted at the steady rate, next to the rate gap (a rate says which way; money for the whole group says whether acting is worth it).
- Peer suggestion: activity on trial days 8 to 13 and, where time allows, the first paid renewal, by group (trials convert automatically unless canceled, so a quiet user may convert by forgetting to cancel and leave soon after).

The groups are not defined yet. The analysis plan should make this measurable and show it to the user first. Starting point (analyst suggestion): week one is trial days 1 to 7; "binge then quiet" means most of week-one sessions fall on day 1 and none on days 2 to 4; "steady" means sessions on at least four of the seven days. Tune the thresholds from the data.

## Tables likely involved
- public.trials: trial starts, ends, outcome and conversion.
- public.sessions: sessions and minutes per trial day for weeks one and two.
- public.users: region, signup device and signup date (new vs existing user).

## Analysis window
Trials started 2026-08-01 to about 2026-09-10 that had ended by the analysis date (about 2026-09-24), so every outcome is final.

## Additional context
- The user asks that comparisons be made between similar time periods.
- The user has no prior definition of binge or steady use and expects the analyst to propose one from the data.
- 2026-11-17, before any outcome was looked at: the user approved the analysis plan's definitions, binge then quiet as 4+ day-1 sessions and active on at most 2 of days 2 to 7, steady as active on day 1 and on 5+ of days 2 to 7 (stricter than the 4-of-7 starting point above, which runs as a variant). Told that about 85 binge-then-quiet trials can only show a large gap (roughly 16 pp), the user chose to keep the definitions rather than loosen them.
- The 2026-11-07 correction to exclude the trial period was made for a churn question and does not apply here; this question is about trials only.

## Out of scope
- Whether an email can change how people use the app. The data is observational with no email test, so a gap shows association, not what the emails would cause (peer suggestion). An email A/B test would answer that.
- Long-run retention after conversion. Trials launched too recently to measure it.

## Open questions
- Analysis date and the last trial start that has matured: Analyse confirms them against `index.yaml`.
- How many trials fall in each group and in neither (peer suggestion). The main estimate pools all start weeks with week as a control; week-by-week rates are a consistency check only.
- Few converted trials have reached a first renewal yet, so the inertia check may be thin (peer suggestion).
- Early cancels: whether quiet follows from canceling rather than leading to it.
- Bingeing may reflect who the user is; the comparison cannot rule that out.
