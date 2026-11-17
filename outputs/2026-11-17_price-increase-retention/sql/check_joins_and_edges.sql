-- Check: joins do not fan out, the trial exclusion removes nobody in the window, and the window edges.
SELECT (SELECT COUNT(*) FROM public.payments p JOIN public.subscriptions s USING (subscription_id) WHERE s.plan = 'monthly') AS monthly_payment_rows_after_subscriptions_join,
       (SELECT COUNT(*) FROM public.payments p JOIN public.subscriptions s USING (subscription_id) JOIN public.users u ON u.user_id = s.user_id WHERE s.plan = 'monthly') AS monthly_payment_rows_after_users_join,
       (SELECT COUNT(*) FROM public.payments p WHERE p.subscription_id IN (SELECT subscription_id FROM public.subscriptions WHERE plan = 'monthly')) AS monthly_payment_rows,
       (SELECT COUNT(DISTINCT s.user_id) FROM public.subscriptions s JOIN public.trials t ON t.user_id = s.user_id WHERE s.plan = 'monthly' AND s.start_date < DATE '2026-08-01') AS monthly_subs_with_trial_starting_before_aug,
       (SELECT MIN(p.payment_date + INTERVAL '30 days')::date FROM public.payments p WHERE p.payment_date + INTERVAL '30 days' >= DATE '2025-11-01') AS first_due_in_window,
       (SELECT MAX(p.payment_date + INTERVAL '30 days')::date FROM public.payments p WHERE p.payment_date + INTERVAL '30 days' < DATE '2026-08-01') AS last_due_in_window
ORDER BY 1;
