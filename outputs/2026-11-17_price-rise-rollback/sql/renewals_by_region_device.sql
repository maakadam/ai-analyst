-- Context: monthly-plan renewals due and missed, before (Nov 2025 to Feb 2026) and after
-- (Mar to Jul 2026), by region (country) and, separately, by signup device.
-- Measures: monthly_renewals_due, missed_monthly_renewals (payments.yaml). Trial users left out.
WITH r AS (
  SELECT s.user_id,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
  WHERE s.plan = 'monthly'
    AND NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
)
SELECT CASE WHEN r.renewal_due_date < DATE '2026-03-01' THEN 'before' ELSE 'after' END AS period,
       COALESCE(u.country, 'all') AS country,
       COALESCE(u.device_type, 'all') AS device_type,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE r.next_payment_date IS NULL) AS missed_renewals
FROM r
JOIN public.users u ON u.user_id = r.user_id
WHERE r.renewal_due_date >= DATE '2025-11-01' AND r.renewal_due_date < DATE '2026-08-01'
GROUP BY GROUPING SETS ((1, u.country), (1, u.device_type))
ORDER BY 1, 2, 3;
