SELECT LEAST((SELECT MAX(payment_date)::date FROM public.payments),
             (SELECT MAX(signup_date)::date FROM public.users),
             (SELECT MAX(started_at)::date FROM public.trials)) AS analysis_date,
       (SELECT MAX(payment_date)::date FROM public.payments) AS max_payment_date,
       (SELECT MAX(signup_date)::date FROM public.users) AS max_signup_date,
       (SELECT MAX(started_at)::date FROM public.trials) AS max_trial_start;
