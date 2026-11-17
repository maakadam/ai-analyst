-- Converted trials by group and plan, with their first payment and, for monthly plans, whether the first renewal (renewal_due_date = payment_date + 30 days) fell due by the analysis date and was missed (missed_monthly_renewals).
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
, conv AS (
  SELECT c.trial_id, c.trial_group, s.subscription_id, s.plan
  FROM c JOIN public.subscriptions s ON s.user_id = c.user_id
  WHERE c.outcome = 'converted'
), p AS (
  SELECT conv.trial_id, pay.payment_date, pay.amount_usd,
         ROW_NUMBER() OVER (PARTITION BY pay.subscription_id ORDER BY pay.payment_date) AS n,
         LEAD(pay.payment_date) OVER (PARTITION BY pay.subscription_id ORDER BY pay.payment_date) AS next_payment_date
  FROM conv JOIN public.payments pay ON pay.subscription_id = conv.subscription_id
)
SELECT conv.trial_group, conv.plan,
       COUNT(*) AS converted_trials,
       COUNT(p.trial_id) AS with_first_payment,
       SUM(p.amount_usd) AS first_payment_usd,
       COUNT(*) FILTER (WHERE conv.plan = 'monthly' AND p.payment_date + INTERVAL '30 days' < DATE '2026-09-25') AS first_renewals_due,
       COUNT(*) FILTER (WHERE conv.plan = 'monthly' AND p.payment_date + INTERVAL '30 days' < DATE '2026-09-25' AND p.next_payment_date IS NULL) AS first_renewals_missed
FROM conv LEFT JOIN p ON p.trial_id = conv.trial_id AND p.n = 1
GROUP BY 1, 2
ORDER BY 1, 2;
