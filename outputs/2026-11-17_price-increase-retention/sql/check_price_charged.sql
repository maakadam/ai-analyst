-- Check: the price actually charged per month and plan, to confirm who was treated and when.
SELECT DATE_TRUNC('month', p.payment_date)::date AS payment_month,
       s.plan,
       p.amount_usd,
       COUNT(*) AS charges
FROM public.payments p
JOIN public.subscriptions s USING (subscription_id)
WHERE p.payment_date >= DATE '2025-10-01'
  AND p.payment_date <  DATE '2026-08-01'
  AND s.plan IN ('monthly', 'annual')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
