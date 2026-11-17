-- Trials canceled before day 8, by group and the trial day of the cancel (1 = start day), with day-1 sessions.
WITH t AS (
  -- Matured trials (matured_trials measure): ends_at before analysis_date + 1 day (2026-09-25).
  SELECT tr.trial_id, tr.user_id, tr.started_at, tr.started_at::date AS d0, tr.outcome, tr.outcome_at,
         (tr.outcome = 'canceled' AND tr.outcome_at < tr.started_at::date + 7) AS early_cancel
  FROM public.trials tr
  WHERE tr.ends_at < DATE '2026-09-25'
), a AS (
  -- Sessions by trial_day (sessions.yaml): day 1 is the start date; days 1-14 only (ends_at day left out); capped at analysis_date + 1 day.
  SELECT t.trial_id,
         COUNT(s.session_id) FILTER (WHERE s.session_date = t.d0) AS day1_sessions,
         COUNT(s.session_id) FILTER (WHERE s.session_date < t.d0 + 7) AS week1_sessions,
         COUNT(s.session_id) FILTER (WHERE s.session_date BETWEEN t.d0 + 1 AND t.d0 + 3) AS day2_4_sessions,
         COUNT(DISTINCT s.session_date) FILTER (WHERE s.session_date BETWEEN t.d0 + 1 AND t.d0 + 6) AS active_days_2_7,
         COUNT(DISTINCT s.session_date) FILTER (WHERE s.session_date >= t.d0 + 7) AS active_days_8_14,
         COUNT(s.session_id) FILTER (WHERE s.session_date >= t.d0 + 7) AS sessions_8_14
  FROM t
  LEFT JOIN public.sessions s
    ON s.user_id = t.user_id
   AND s.session_date >= t.d0
   AND s.session_date < t.d0 + 14
   AND s.session_date < DATE '2026-09-25'
  GROUP BY t.trial_id
), c AS (
  SELECT t.*, a.day1_sessions, a.week1_sessions, a.day2_4_sessions, a.active_days_2_7, a.active_days_8_14, a.sessions_8_14,
         CASE WHEN a.day1_sessions >= 4 AND a.active_days_2_7 <= 2 THEN 'binge_quiet'
              WHEN a.day1_sessions >= 1 AND a.active_days_2_7 >= 5 THEN 'steady'
              ELSE 'neither' END AS trial_group
  FROM t JOIN a USING (trial_id)
)
SELECT trial_group, (outcome_at::date - d0) + 1 AS cancel_trial_day,
       COUNT(*) AS trials,
       SUM(day1_sessions) AS day1_sessions,
       SUM(active_days_2_7) AS active_days_2_7
FROM c
WHERE early_cancel
GROUP BY 1, 2
ORDER BY 1, 2;
