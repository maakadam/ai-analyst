-- New monthly starts: churn at the same renewal number, starts Nov 2025 to Jan 2026 (renewals due before
-- 2026-03-01, so all at $10) against starts Mar to Jun 2026 (all at $12, renewals due before 2026-08-01).
-- renewal_number 1 is the renewal after the first charge. No trial record; the blocks fall outside both cohorts.
WITH r AS (
  SELECT p.subscription_id, s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date,
         ROW_NUMBER() OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS renewal_number
  FROM public.payments p
  JOIN public.subscriptions s USING (subscription_id)
  WHERE s.plan = 'monthly'
    AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
), c AS (
  SELECT CASE WHEN start_date >= DATE '2025-11-01' AND start_date < DATE '2026-02-01' AND renewal_due_date < DATE '2026-03-01' THEN 'starts_nov25_jan26_at_10'
              WHEN start_date >= DATE '2026-03-01' AND start_date < DATE '2026-07-01' AND renewal_due_date < DATE '2026-08-01' THEN 'starts_mar26_jun26_at_12' END AS cohort,
         renewal_number, next_payment_date
  FROM r
)
SELECT cohort, renewal_number,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals
FROM c
WHERE cohort IS NOT NULL AND renewal_number <= 4
GROUP BY 1, 2
ORDER BY 1, 2;
