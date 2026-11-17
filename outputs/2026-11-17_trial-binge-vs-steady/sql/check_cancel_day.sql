-- Check: the trial day on which canceled matured trials were canceled, and outcome counts, to see whether any cancel can fall before day 5.
SELECT outcome, (outcome_at::date - started_at::date) + 1 AS outcome_trial_day, COUNT(*) AS trials
FROM public.trials
WHERE ends_at < DATE '2026-09-25'
GROUP BY 1, 2
ORDER BY 1, 2;
