"""Act 6 follow-ups. Aggregates only."""
import pandas as pd
D = "data/"
subs = pd.read_csv(D+"subscriptions.csv", parse_dates=["start_date","end_date"])
pay = pd.read_csv(D+"payments.csv", parse_dates=["payment_date"])
trials = pd.read_csv(D+"trials.csv")
subs = subs[~subs.user_id.isin(set(trials.user_id))]
m = subs[(subs.plan=="monthly") & (subs.start_date.dt.normalize()!=pd.Timestamp("2025-09-17"))].copy()
m["cohort"] = pd.cut(m.start_date, pd.to_datetime(["2000-01-01","2023-01-01","2024-01-01","2025-01-01","2026-08-01"]), labels=["<2023","2023","2024","2025-26"])
e = m[m.end_date.notna()]
print("A monthly ends by half-year x start cohort")
print(pd.crosstab(e.end_date.dt.year.astype(str)+"H"+((e.end_date.dt.month>6)+1).astype(str), e.cohort).to_string())
print("A monthly ends by month 2025-01..2025-12 x cohort")
x = e[(e.end_date>="2025-01-01")&(e.end_date<"2026-01-01")]
print(pd.crosstab(x.end_date.dt.to_period("M"), x.cohort).to_string())
print("A starts by cohort:", m.cohort.value_counts().sort_index().to_dict())
# B: before-window payment churns whose end_date is on/after 2026-03-01
p = pay.merge(m[["subscription_id","start_date","end_date","cohort"]], on="subscription_id").sort_values(["subscription_id","payment_date"])
p["nxt"] = p.groupby("subscription_id").payment_date.shift(-1)
p["due"] = p.payment_date + pd.Timedelta(days=30)
ch = p[p.nxt.isna() & (p.due>="2025-09-01") & (p.due<="2026-02-28 23:59:59")]
print("B before-window churns:", len(ch), "; end_date on/after 2026-03-01:", int((ch.end_date>="2026-03-01").sum()), "; end_date null:", int(ch.end_date.isna().sum()))
ch2 = p[p.nxt.isna() & (p.due>="2026-03-01") & (p.due<="2026-07-31 23:59:59")]
print("B after-window churns:", len(ch2), "; end_date after 2026-07-31:", int((ch2.end_date>"2026-07-31 23:59:59").sum()), "; null:", int(ch2.end_date.isna().sum()))
# C: Sep-Oct 2025 churn bump (non-spike) by start month band
w = p[(p.due>="2025-08-01")&(p.due<"2025-12-01")].copy()
w["churned"] = w.nxt.isna()
w["start_band"] = w.start_date.dt.to_period("Q").astype(str).where(w.start_date>="2025-01-01","pre-2025")
print("C churn by due month x start quarter (rate %, n)")
g = w.groupby([w.due.dt.to_period("M"),"start_band"]).churned.agg(["mean","size"]); g["mean"]=(g["mean"]*100).round(2)
print(g.unstack(0).to_string())
# D: share of churned ends >31d after last payment, by end month
last = p.groupby("subscription_id").agg(last=("payment_date","max"), end=("end_date","first"))
last = last[last.end.notna() & (last.end>="2025-06-01") & (last.end<="2026-08-31")]
last["over31"] = (last.end-last["last"]).dt.days>31
print("D share ending >31d after last payment by end month (%):", (last.groupby(last.end.dt.to_period("M")).over31.mean()*100).round(1).to_dict())
