import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from helpers import checks
TODAY_END = pd.Timestamp("2026-09-24 23:59:59")
u = pd.read_csv(ROOT/"data/users.csv", parse_dates=["signup_date"])
s = pd.read_csv(ROOT/"data/subscriptions.csv", parse_dates=["start_date","end_date"])
t = pd.read_csv(ROOT/"data/trials.csv", parse_dates=["started_at","ends_at","outcome_at"])
p = pd.read_csv(ROOT/"data/payments.csv", parse_dates=["payment_date"])
d = u.merge(s, on="user_id").merge(t, on="user_id", how="left")
d["has_trial"]=d.trial_id.notna(); d["paid"]=d.plan.isin(["monthly","annual"])
d["sd"]=d.start_date.dt.normalize()
top = d.groupby("sd").size().sort_values(ascending=False).head(6)
print("busiest start days:\n", top.to_string())
first = p.merge(s[["subscription_id","start_date"]], on="subscription_id")
first["day"]=(first.payment_date.dt.normalize()-first.start_date.dt.normalize()).dt.days
day0 = set(first[first.day.between(0,5)].subscription_id)
for day in ["2025-09-17","2026-07-30","2026-09-25"]:
    g = d[d.sd==day]
    print(day, "rows", len(g), "trial", int(g.has_trial.sum()), "paid share", round(g.paid.mean(),3),
          "signup range", g.signup_date.min().date(), g.signup_date.max().date(),
          "paid with day0 charge", round(g[g.paid].subscription_id.isin(day0).mean(),3) if day!="2026-09-25" else "n/a")
# Jul-30 pin: of Mar-Jul 2026 monthly starts used as retention baseline
mon = d[(d.plan=="monthly")&(d.sd>="2026-03-01")&(d.sd<="2026-07-31")]
print("Mar-Jul monthly starts:", len(mon), "on 2026-07-30:", int((mon.sd=="2026-07-30").sum()))
# matured trial conversion by week
t2 = t[t.ends_at<=TODAY_END].copy(); t2["conv"]=t2.outcome.eq("converted")
print("8 matured trial conversion by week:", checks.stable_over_time(t2,"started_at","conv",freq="W-SUN",min_rows=20)["summary"])
# trial converts: payment pattern
tc = d[d.has_trial & (d.plan=="monthly")]
pp = first[first.subscription_id.isin(tc.subscription_id)]
print("trial-convert monthly payment day offsets (counts):", pp.day.value_counts().sort_index().head(8).to_dict())
