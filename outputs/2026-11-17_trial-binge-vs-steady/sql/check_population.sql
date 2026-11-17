-- Check: all vs matured trials (matured_trials, converted_trials), first and last start dates, one trial per user, the users join and the subscriptions join for converted trials do not fan out.
SELECT COUNT(*) AS all_trials,
       COUNT(*) FILTER (WHERE t.ends_at < DATE '2026-09-25') AS matured_trials,
       COUNT(*) FILTER (WHERE t.ends_at < DATE '2026-09-25' AND t.outcome = 'converted') AS converted_trials,
       COUNT(*) FILTER (WHERE t.ends_at >= DATE '2026-09-25' AND t.outcome IS NOT NULL) AS unmatured_with_outcome,
       MIN(t.started_at)::date AS first_start,
       (MAX(t.started_at) FILTER (WHERE t.ends_at < DATE '2026-09-25'))::date AS last_matured_start,
       COUNT(DISTINCT t.user_id) AS distinct_trial_users,
       (SELECT COUNT(*) FROM public.trials t2 JOIN public.users u ON u.user_id = t2.user_id WHERE t2.ends_at < DATE '2026-09-25') AS matured_rows_after_users_join,
       (SELECT COUNT(*) FROM public.trials t3 JOIN public.subscriptions s ON s.user_id = t3.user_id WHERE t3.ends_at < DATE '2026-09-25' AND t3.outcome = 'converted') AS converted_rows_after_subscriptions_join
FROM public.trials t
ORDER BY 1;
