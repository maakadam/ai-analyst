"""Act 6.5 mix check: country and device share of renewals per window. Aggregates only."""
import pandas as pd
D="data/"
subs=pd.read_csv(D+"subscriptions.csv",parse_dates=["start_date"]); users=pd.read_csv(D+"users.csv")
pay=pd.read_csv(D+"payments.csv",parse_dates=["payment_date"]); tr=pd.read_csv(D+"trials.csv")
s=subs[(subs.plan=="monthly")&~subs.user_id.isin(tr.user_id)&(subs.start_date.dt.normalize()!=pd.Timestamp("2025-09-17"))].merge(users,on="user_id")
p=pay.merge(s[["subscription_id","country","device_type"]],on="subscription_id")
p["due"]=p.payment_date+pd.Timedelta(days=30)
p["w"]=pd.cut(p.due,pd.to_datetime(["2025-03-01","2025-08-01","2025-09-01","2026-03-01","2026-08-01"]),labels=["year_earlier","gap","before","after"],right=False)
p=p[p.w.isin(["year_earlier","before","after"])]
for c in ["country","device_type"]:
    print((pd.crosstab(p.w,p[c],normalize="index")*100).round(1).to_string())
