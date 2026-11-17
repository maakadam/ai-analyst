-- Monthly-plan renewals due and missed, Nov 2025 to Jul 2026, by due month, tenure band,
-- new vs existing (started before or from 2026-03-01) and the 2025-09-17 bulk block.
-- Measures: monthly_renewals_due, missed_monthly_renewals (payments.yaml); tenure_band
-- (subscriptions.yaml) with period_start = the due month. Users with a trial record are left out.
WITH r AS (
  SELECT p.subscription_id,
         s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
  WHERE s.plan = 'monthly'
    AND NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
), d AS (
  SELECT DATE_TRUNC('month', renewal_due_date)::date AS due_month,
         start_date, renewal_due_date, next_payment_date
  FROM r
  WHERE renewal_due_date >= DATE '2025-11-01'
    AND renewal_due_date <  DATE '2026-08-01'
)
SELECT to_char(due_month, 'YYYY-MM') AS due_month,
       CASE
         WHEN due_month - start_date < INTERVAL '6 months'  THEN 'under 6 months'
         WHEN due_month - start_date < INTERVAL '12 months' THEN '6 to 12 months'
         WHEN due_month - start_date < INTERVAL '24 months' THEN '12 to 24 months'
         ELSE 'over 24 months'
       END AS tenure_band,
       CASE WHEN start_date < DATE '2026-03-01' THEN 'existing' ELSE 'new' END AS start_group,
       (start_date::date = DATE '2025-09-17') AS block_2025_09_17,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM d
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;
