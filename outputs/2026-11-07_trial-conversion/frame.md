# Frame: Trial conversion and the keep decision

## Question
Raw: "Are the new 14-day trials converting well enough to keep them? The head of growth decides whether to keep trials next quarter."
Framed: Since trials launched on 2026-08-01, do they turn more new signups into paying subscribers than before trials existed, and is that worth keeping next quarter?

## Decision it informs
Whether to keep 14-day trials next quarter.

## Audience
Head of growth.

## Population
New signups. The user asked the analyst to suggest the splits; none are confirmed as levers.
- Analyst suggestion: tenure, signups compared on their final plan, and trial users only once their trial has ended, so open trials are not read as failures.
- Analyst suggestion: weekly signup cohorts, so one unusual week does not drive the answer.
- Analyst suggestion: plan at conversion (monthly or annual), because annual is worth more per subscriber.
- Analyst suggestion: country and device, only as a lever if trials could be offered to some groups and not others (not confirmed); otherwise used to check whether the signup mix moved.

## What would change the decision
- Analyst suggestion: main test is the share of signups who end up on a paid plan, trial users (ended trials only) against non-trial signups from the same weeks, with the Mar-Jul 2026 weekly range as a second baseline. Keep if trial users sit clearly above both; drop or rethink if they sit inside the range or below it. (Changed 2026-11-07 with the user's approval: pre-trial payers take a median of about 45 days to pay, so a 30-day measure would favour trials, which convert on day 14, on timing alone. About half of signups since 2026-08-01 got no trial, which gives a same-week comparison group.)
- Analyst suggestion: mix and volume. Also count paying subscribers per week, not only per signup, in case trials changed how many people sign up or who they are; split by plan, country and device to see whether the mix moved.
- Analyst suggestion: seasonality. Compare Aug 2025 with Mar-Jul 2025 (before the Sep 2025 spike); if August is usually higher, read the trial lift net of that.
- Analyst suggestion: retention is a warning sign only, not a deciding test: first renewal of trial converts against direct paid starts at the same tenure, for the few converts old enough.
- Analyst suggestion: money. Extra paying subscribers and revenue next quarter for all new signups, given as a low and high case with each assumption stated (signup volume, conversion lift from the weekly spread, plan mix, $12 monthly and $100 annual).
- The analysis plan should make this measurable and show it to the user first.

## Tables likely involved
- trials: trial starts, ends and outcomes.
- subscriptions: paid starts for the baseline and for trial converts; plan; ends for first-renewal checks.
- payments: revenue and first renewals.
- users: signup date (cohorts), country, device.

## Analysis window
- Trial era (main test): signups 2026-08-01 to 2026-09-24; trial users count once their trial has an outcome, and non-trial signups are taken from the same weeks (changed 2026-11-07 with the user's approval).
- Baseline: signups 2026-03-01 to 2026-07-31 (same $12 monthly price), on the same measure.
- Seasonality check: signups 2025-03-01 to 2025-08-31.

## Additional context
- The monthly price rose from $10 to $12 in March 2026, so the 2026 baseline starts there; the 2025 seasonality check runs at $10.
- Peer review asked about data maturity, mix and seasonality, and giving the revenue as a range; the user asked for all three to be built in.

## Out of scope
- Trial length (7 versus 14 days): only 14-day trials exist.
- Retention past the first renewal: the data is too short.

## Open questions
- About half of new signups since 2026-08-01 got a trial; whether that split was random is not recorded.
- Trials start on the signup date (checked in aggregate 2026-11-07).
- Weekly signups rose about 3.5 times in August 2026, non-trial signups included; the cause is not known.
- Whether about 8 weeks of trial era is enough to tell a lift apart from weekly noise; if not, the answer says so and names the date by which it would be.
- 418 trials (20%) are still open; the main test cohort should have none, to be checked in code.
