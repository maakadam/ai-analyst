import sys; from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
import pandas as pd
s = pd.read_csv(ROOT/"data/subscriptions.csv", parse_dates=["start_date"])
u = pd.read_csv(ROOT/"data/users.csv", parse_dates=["signup_date"])
p = pd.read_csv(ROOT/"data/payments.csv")
t = set(pd.read_csv(ROOT/"data/trials.csv").user_id)
m = s[(s.plan=="monthly") & s.subscription_id.isin(p.subscription_id)].merge(u, on="user_id")
m["mon"] = m.start_date.dt.to_period("M")
m = m[(m.mon>="2026-01")&(m.mon<="2026-09")]
m["src"] = m.user_id.isin(t).map({True:"trial",False:"non-trial"})
print(pd.crosstab(m.mon, m.src))
nt = m[m.src=="non-trial"]
print((pd.crosstab(nt.mon, nt.country, normalize="index")*100).round(0))
print((pd.crosstab(nt.mon, nt.device_type, normalize="index")*100).round(0))
nt["lag"] = (nt.start_date.dt.normalize()-nt.signup_date.dt.normalize()).dt.days
print(nt.groupby("mon").lag.median())
a = s[(s.plan=="annual")]; a["mon"]=a.start_date.dt.to_period("M")
print(a[(a.mon>="2026-01")&(a.mon<="2026-09")].groupby("mon").size())
