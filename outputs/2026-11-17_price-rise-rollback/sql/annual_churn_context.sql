-- Context only (not a control): annual subscriptions active at each month start and those that ended
-- in the month, Nov 2025 to Jul 2026. Measures: paid_subscriptions_at_period_start, churned_subscriptions
-- (subscriptions.yaml), as in golden query monthly_paid_churn_rate. All end dates are before the
-- analysis date (2026-09-24). Trial users left out.
WITH months AS (
  SELECT generate_series(DATE '2025-11-01', DATE '2026-07-01', INTERVAL '1 month')::date AS month_start
)
SELECT to_char(m.month_start, 'YYYY-MM') AS month,
       COUNT(*) AS annual_at_month_start,
       COUNT(*) FILTER (WHERE s.end_date < m.month_start + INTERVAL '1 month') AS annual_churned
FROM months m
JOIN public.subscriptions s
  ON s.plan = 'annual'
 AND s.start_date < m.month_start
 AND (s.end_date IS NULL OR s.end_date >= m.month_start)
WHERE NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
GROUP BY m.month_start
ORDER BY m.month_start;
