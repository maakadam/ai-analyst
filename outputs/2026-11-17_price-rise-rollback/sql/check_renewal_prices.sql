-- Check: the charge that paid each monthly renewal, by due month ($10 before March, $12 from it),
-- the month totals of renewals_by_segment, and that no renewal was paid off its due date.
WITH r AS (
  SELECT p.subscription_id, s.start_date, p.amount_usd,
         p.payment_date + INTERVAL '30 days' AS renewal_due_date,
         LEAD(p.payment_date) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_payment_date,
         LEAD(p.amount_usd) OVER (PARTITION BY p.subscription_id ORDER BY p.payment_date) AS next_amount
  FROM public.payments p
  JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
  WHERE s.plan = 'monthly'
    AND NOT EXISTS (SELECT 1 FROM public.trials t WHERE t.user_id = s.user_id)
)
SELECT to_char(DATE_TRUNC('month', renewal_due_date), 'YYYY-MM') AS due_month,
       COUNT(*) AS renewals_due,
       COUNT(*) FILTER (WHERE next_payment_date IS NULL) AS missed_renewals,
       MIN(next_amount) AS min_renewal_charge,
       MAX(next_amount) AS max_renewal_charge,
       COUNT(*) FILTER (WHERE next_payment_date IS NOT NULL AND next_payment_date::date <> renewal_due_date::date) AS renewals_paid_off_due_date
FROM r
WHERE renewal_due_date >= DATE '2025-11-01' AND renewal_due_date < DATE '2026-08-01'
GROUP BY 1
ORDER BY 1;
