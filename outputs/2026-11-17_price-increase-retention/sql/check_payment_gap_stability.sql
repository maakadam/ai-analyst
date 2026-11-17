-- Check (corrections 2026-11-06): is the renewal outcome recorded the same way in every month?
-- Share of paid monthly renewals whose next charge came exactly 30 days later, by due month. Feeds helpers.checks.stable_over_time.
WITH r AS (
  SELECT p.payment_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s USING (subscription_id)
  WHERE s.plan = 'monthly'
)
SELECT to_char(DATE_TRUNC('month', payment_date + INTERVAL '30 days'), 'YYYY-MM') AS period,
       COUNT(*) AS n,
       ROUND(AVG(CASE WHEN next_payment_date - payment_date = INTERVAL '30 days' THEN 1.0 ELSE 0.0 END), 4) AS level,
       MIN(EXTRACT(DAY FROM next_payment_date - payment_date))::int AS min_gap_days,
       MAX(EXTRACT(DAY FROM next_payment_date - payment_date))::int AS max_gap_days
FROM r
WHERE next_payment_date IS NOT NULL
  AND payment_date + INTERVAL '30 days' >= DATE '2025-11-01'
  AND payment_date + INTERVAL '30 days' <  DATE '2026-08-01'
GROUP BY 1
ORDER BY 1;
