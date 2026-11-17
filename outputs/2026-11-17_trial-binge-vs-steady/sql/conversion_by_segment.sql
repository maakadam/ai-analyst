-- Conversion by group within region, signup device, new vs existing user and start week, early cancels left out.
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
, seg AS (
  SELECT c.trial_group, c.outcome, u.country, u.device_type,
         CASE WHEN u.signup_date::date < c.d0 THEN 'existing user' ELSE 'new signup' END AS user_type,
         to_char(DATE_TRUNC('week', c.started_at), 'YYYY-MM-DD') AS start_week
  FROM c JOIN public.users u ON u.user_id = c.user_id
  WHERE NOT c.early_cancel
)
SELECT CASE WHEN GROUPING(country) = 0 THEN 'region' WHEN GROUPING(device_type) = 0 THEN 'device'
            WHEN GROUPING(user_type) = 0 THEN 'user_type' ELSE 'start_week' END AS segment_type,
       COALESCE(country, device_type, user_type, start_week) AS segment,
       trial_group,
       COUNT(*) AS trials,
       COUNT(*) FILTER (WHERE outcome = 'converted') AS converted
FROM seg
GROUP BY GROUPING SETS ((country, trial_group), (device_type, trial_group), (user_type, trial_group), (start_week, trial_group))
ORDER BY 1, 2, 3;
