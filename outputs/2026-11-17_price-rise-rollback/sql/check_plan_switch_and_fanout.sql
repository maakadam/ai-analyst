-- Check: plan switches visible in payments (a monthly subscription charged $100, or an annual one
-- charged $10 or $12), and that joining payments to subscriptions neither drops nor repeats rows
-- (payment_rows_after_join summed over plans should equal payment_rows_total).
SELECT s.plan,
       COUNT(DISTINCT s.subscription_id) AS subscriptions_with_payments,
       COUNT(DISTINCT s.subscription_id) FILTER (WHERE p.amount_usd = 100) AS subs_with_100_charge,
       COUNT(DISTINCT s.subscription_id) FILTER (WHERE p.amount_usd IN (10, 12)) AS subs_with_10_or_12_charge,
       COUNT(*) AS payment_rows_after_join,
       (SELECT COUNT(*) FROM public.payments) AS payment_rows_total
FROM public.payments p
JOIN public.subscriptions s ON s.subscription_id = p.subscription_id
GROUP BY s.plan
ORDER BY s.plan;
