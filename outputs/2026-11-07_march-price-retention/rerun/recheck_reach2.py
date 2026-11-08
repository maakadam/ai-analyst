import pandas as pd
W = pd.Timestamp("2026-07-31 23:59:59")
s = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date","end_date"])
p = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])
t = pd.read_csv("data/trials.csv")
s = s[~s.user_id.isin(set(t.user_id)) & (s.start_date <= W)]
m = p.merge(s[["subscription_id","plan","start_date"]], on="subscription_id")
m = m[(m.plan=="monthly") & (m.payment_date > W-pd.Timedelta(days=30)) & (m.payment_date <= W)]
d = m.start_date.dt.normalize()
m["grp"] = d.map(lambda x: "b0917" if x==pd.Timestamp("2025-09-17") else ("b0730" if x==pd.Timestamp("2026-07-30") else "org"))
days = (m.payment_date + pd.Timedelta(days=30) - m.start_date).dt.days
m["fy"] = days < 365
print(m.groupby(["grp","fy"]).size())
print("max payment_date", m.payment_date.max().date(), "max start", m.start_date.max().date())
print("money base (excl only 0917):", (m.grp!="b0917").sum())
ten = pd.cut((days/30).round(), [0,1,3,6,12,24,10000], labels=["1","2-3","4-6","7-12","13-24","25+"])
print(pd.crosstab(ten, m.grp))
print("days 365-374 (7-12 band but past_first_year):", ((days>=365)&(days<375)).sum())
print("org starts in Jul 2026:", ((m.grp=="org")&(m.start_date>=pd.Timestamp("2026-07-01"))).sum())
