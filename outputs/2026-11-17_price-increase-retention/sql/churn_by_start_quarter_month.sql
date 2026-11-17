-- Monthly-plan churn at renewal by start quarter and due month, organic existing subscribers only:
-- started before 2026-03-01, outside the 2025-09-17 block, no trial record (review A2: start cohort split).
WITH r AS (
  SELECT s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s USING (subscription_id)
  WHERE s.plan = 'monthly'
    AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
)
SELECT to_char(DATE_TRUNC('quarter', start_date), 'YYYY-"Q"Q') AS start_quarter,
       DATE_TRUNC('month', renewal_due_date)::date AS due_month,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM r
WHERE renewal_due_date >= DATE '2025-11-01' AND renewal_due_date < DATE '2026-08-01'
  AND start_date < DATE '2026-03-01' AND start_date::date <> DATE '2025-09-17'
GROUP BY 1, 2
ORDER BY 1, 2;
