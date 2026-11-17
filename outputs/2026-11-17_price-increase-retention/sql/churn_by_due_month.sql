-- Monthly-plan churn at renewal by due month, existing (started before 2026-03-01) vs new starts,
-- with the 2025-09-17 block apart. Users with a trial record are dropped. Built on golden query monthly_renewal_churn_rate.
WITH r AS (
  SELECT p.subscription_id, s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s USING (subscription_id)
  WHERE s.plan = 'monthly'
    AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
)
SELECT DATE_TRUNC('month', renewal_due_date)::date AS due_month,
       CASE WHEN start_date < DATE '2026-03-01' THEN 'existing' ELSE 'new' END AS customer_type,
       CASE WHEN start_date::date = DATE '2025-09-17' THEN 'block_2025_09_17' ELSE 'organic' END AS block_flag,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM r
WHERE renewal_due_date >= DATE '2025-11-01'
  AND renewal_due_date <  DATE '2026-08-01'
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
