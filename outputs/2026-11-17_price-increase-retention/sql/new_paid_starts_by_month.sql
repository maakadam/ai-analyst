-- New paid starts per month and plan, to see whether new customers moved from monthly to annual or fell off.
-- Blocks (2025-09-17, 2026-07-30) and users with a trial record left out.
SELECT DATE_TRUNC('month', s.start_date)::date AS start_month,
       s.plan,
       COUNT(*) AS new_paid_starts
FROM public.subscriptions s
WHERE s.plan IN ('monthly', 'annual')
  AND s.start_date >= DATE '2025-11-01'
  AND s.start_date <  DATE '2026-08-01'
  AND s.start_date::date NOT IN (DATE '2025-09-17', DATE '2026-07-30')
  AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
GROUP BY 1, 2
ORDER BY 1, 2;
