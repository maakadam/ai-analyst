-- Check: do canceled matured trials have sessions after the cancel day (inside trial days 1-14)? If not, quiet after a cancel is caused by the cancel. Canceled trials only: a converted trial's outcome day is day 15, outside the window.
SELECT COUNT(DISTINCT t.trial_id) AS canceled_trials,
       COUNT(s.session_id) FILTER (WHERE s.session_date > t.outcome_at::date) AS sessions_after_cancel_day,
       COUNT(DISTINCT t.trial_id) FILTER (WHERE s.session_date > t.outcome_at::date) AS trials_with_sessions_after_cancel_day
FROM public.trials t
LEFT JOIN public.sessions s
  ON s.user_id = t.user_id
 AND s.session_date >= t.started_at::date
 AND s.session_date < t.started_at::date + 14
 AND s.session_date < DATE '2026-09-25'
WHERE t.ends_at < DATE '2026-09-25'
  AND t.outcome = 'canceled'
ORDER BY 1;
