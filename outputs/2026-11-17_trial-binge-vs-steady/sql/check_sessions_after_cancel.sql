-- Check: do canceled matured trials have sessions after the cancel day (inside trial days 1-14)? If not, quiet after a cancel is caused by the cancel.
SELECT t.outcome,
       COUNT(DISTINCT t.trial_id) AS trials,
       COUNT(s.session_id) FILTER (WHERE s.session_date > t.outcome_at::date) AS sessions_after_outcome_day,
       COUNT(DISTINCT t.trial_id) FILTER (WHERE s.session_date > t.outcome_at::date) AS trials_with_sessions_after_outcome_day
FROM public.trials t
LEFT JOIN public.sessions s
  ON s.user_id = t.user_id
 AND s.session_date >= t.started_at::date
 AND s.session_date < t.started_at::date + 14
 AND s.session_date < DATE '2026-09-25'
WHERE t.ends_at < DATE '2026-09-25'
GROUP BY 1
ORDER BY 1;
