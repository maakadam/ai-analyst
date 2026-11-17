-- Annual plans (price unchanged at $100), reference only: active at month start, ended in the month
-- (churned_subscriptions from end_date), and anniversaries in the month. No trial record, 2025-09-17 block left out.
WITH months AS (
  SELECT generate_series(DATE '2025-11-01', DATE '2026-07-01', INTERVAL '1 month')::date AS month_start
)
SELECT m.month_start,
       COUNT(*) AS annual_at_month_start,
       COUNT(*) FILTER (WHERE s.end_date < m.month_start + INTERVAL '1 month') AS annual_churned,
       COUNT(*) FILTER (WHERE EXTRACT(MONTH FROM s.start_date) = EXTRACT(MONTH FROM m.month_start) AND s.start_date < m.month_start - INTERVAL '11 months') AS annual_anniversaries_in_month,
       COUNT(*) FILTER (WHERE s.end_date < m.month_start + INTERVAL '1 month' AND EXTRACT(MONTH FROM s.start_date) = EXTRACT(MONTH FROM m.month_start)) AS annual_churned_at_anniversary
FROM months m
JOIN public.subscriptions s
  ON s.plan = 'annual'
 AND s.start_date < m.month_start
 AND (s.end_date IS NULL OR s.end_date >= m.month_start)
 AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
 AND s.start_date::date <> DATE '2025-09-17'
GROUP BY m.month_start
ORDER BY m.month_start;
