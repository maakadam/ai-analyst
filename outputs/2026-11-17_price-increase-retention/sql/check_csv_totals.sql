-- Check: row count and totals of churn_by_due_month.csv, and the organic existing total that each
-- dimension in churn_by_segment_month.csv must add back to, computed straight from the source.
WITH r AS (
  SELECT p.subscription_id, s.start_date,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date
  FROM public.payments p
  JOIN public.subscriptions s USING (subscription_id)
  WHERE s.plan = 'monthly'
    AND s.user_id NOT IN (SELECT t.user_id FROM public.trials t)
), w AS (SELECT * FROM r WHERE renewal_due_date >= DATE '2025-11-01' AND renewal_due_date < DATE '2026-08-01')
SELECT COUNT(DISTINCT (DATE_TRUNC('month', renewal_due_date), start_date < DATE '2026-03-01', start_date::date = DATE '2025-09-17')) AS due_month_groups,
       COUNT(*) AS renewals_due_total,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_total,
       COUNT(*) FILTER (WHERE start_date < DATE '2026-03-01' AND start_date::date <> DATE '2025-09-17') AS organic_existing_renewals_due,
       COUNT(*) FILTER (WHERE start_date < DATE '2026-03-01' AND start_date::date <> DATE '2025-09-17' AND next_payment_date IS NULL) AS organic_existing_missed
FROM w
ORDER BY 1;
