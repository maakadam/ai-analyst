-- Monthly-plan renewals due and missed by due month and start cohort (half-year of start), Nov 2025 to
-- Jul 2026. The 2025-09-17 bulk block is its own cohort; starts from 2026-03-01 are "new" (started at $12).
-- Measures: monthly_renewals_due, missed_monthly_renewals (payments.yaml). Trial users left out.
WITH r AS (
  SELECT p.subscription_id, s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
  WHERE s.plan = 'monthly'
    AND NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
)
SELECT to_char(DATE_TRUNC('month', renewal_due_date), 'YYYY-MM') AS due_month,
       CASE WHEN start_date::date = DATE '2025-09-17' THEN '2025-09-17 block'
            WHEN start_date >= DATE '2026-03-01' THEN 'new (from 2026-03)'
            WHEN start_date >= DATE '2026-01-01' THEN '2026-01 to 02'
            ELSE to_char(start_date, 'YYYY') || (CASE WHEN EXTRACT(MONTH FROM start_date) <= 6 THEN '-H1' ELSE '-H2' END)
       END AS start_cohort,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM r
WHERE renewal_due_date >= DATE '2025-11-01' AND renewal_due_date < DATE '2026-08-01'
GROUP BY 1, 2
ORDER BY 1, 2;
