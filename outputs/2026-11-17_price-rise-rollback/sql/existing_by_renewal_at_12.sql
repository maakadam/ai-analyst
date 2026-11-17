-- Existing monthly subscribers (started before 2026-03-01): renewals due March to July 2026 by
-- how many $12 renewals they had faced (1 = the first renewal charged at $12).
-- Measures: monthly_renewals_due, missed_monthly_renewals (payments.yaml). Trial users left out.
WITH r AS (
  SELECT p.subscription_id, s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
  WHERE s.plan = 'monthly' AND s.start_date < DATE '2026-03-01'
    AND NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
), n AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY subscription_id ORDER BY renewal_due_date) AS renewal_at_12
  FROM r WHERE renewal_due_date >= DATE '2026-03-01'
)
SELECT to_char(DATE_TRUNC('month', renewal_due_date), 'YYYY-MM') AS due_month,
       CASE WHEN renewal_at_12 >= 4 THEN '4+' ELSE renewal_at_12::text END AS renewal_at_12,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM n
WHERE renewal_due_date < DATE '2026-08-01'
GROUP BY 1, 2
ORDER BY 1, 2;
