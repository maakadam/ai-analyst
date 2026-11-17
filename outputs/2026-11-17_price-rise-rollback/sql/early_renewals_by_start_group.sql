-- First three renewals of monthly subscriptions (renewal_number = the payment the renewal follows),
-- by due month and new vs existing, Nov 2025 to Jul 2026: like-for-like tenure for new subscribers.
-- The 2025-09-17 bulk block and trial users are left out.
WITH r AS (
  SELECT p.subscription_id, s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date,
         ROW_NUMBER() OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS renewal_number
  FROM public.payments p
  JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
  WHERE s.plan = 'monthly'
    AND s.start_date::date <> DATE '2025-09-17'
    AND NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
)
SELECT to_char(DATE_TRUNC('month', renewal_due_date), 'YYYY-MM') AS due_month,
       CASE WHEN start_date < DATE '2026-03-01' THEN 'existing' ELSE 'new' END AS start_group,
       CASE WHEN renewal_number >= 4 THEN '4+' ELSE renewal_number::text END AS renewal_number,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM r
WHERE renewal_due_date >= DATE '2025-11-01' AND renewal_due_date < DATE '2026-08-01'
  AND renewal_number <= 3
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
