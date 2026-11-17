-- Monthly-plan churn at renewal by due month and segment (tenure band at the renewal, region, signup device),
-- organic existing subscribers only: started before 2026-03-01, outside the 2025-09-17 block, no trial record.
-- Tenure band uses the subscriptions tenure_band bands with period_start = the renewal due date.
WITH r AS (
  SELECT s.start_date, u.country, u.device_type,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s USING (subscription_id)
  JOIN public.users u ON u.user_id = s.user_id
  WHERE s.plan = 'monthly'
    AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
), e AS (
  SELECT DATE_TRUNC('month', renewal_due_date)::date AS due_month,
         CASE WHEN renewal_due_date - start_date < INTERVAL '6 months'  THEN 'under 6 months'
              WHEN renewal_due_date - start_date < INTERVAL '12 months' THEN '6 to 12 months'
              WHEN renewal_due_date - start_date < INTERVAL '24 months' THEN '12 to 24 months'
              ELSE 'over 24 months' END AS tenure_band,
         country, device_type, next_payment_date
  FROM r
  WHERE renewal_due_date >= DATE '2025-11-01' AND renewal_due_date < DATE '2026-08-01'
    AND start_date < DATE '2026-03-01' AND start_date::date <> DATE '2025-09-17'
)
SELECT due_month, 'tenure_band' AS dimension, tenure_band AS segment, COUNT(*) AS renewals_due, COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals FROM e GROUP BY 1, 2, 3
UNION ALL
SELECT due_month, 'country', country, COUNT(*), COUNT(*) FILTER (WHERE next_payment_date IS NULL) FROM e GROUP BY 1, 2, 3
UNION ALL
SELECT due_month, 'device_type', device_type, COUNT(*), COUNT(*) FILTER (WHERE next_payment_date IS NULL) FROM e GROUP BY 1, 2, 3
ORDER BY 2, 3, 1;
