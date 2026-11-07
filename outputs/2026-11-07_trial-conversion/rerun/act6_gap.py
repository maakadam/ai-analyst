import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from helpers import checks
TODAY_END = pd.Timestamp("2026-09-24 23:59:59")
u = pd.read_csv(ROOT/"data/users.csv", parse_dates=["signup_date"])
s = pd.read_csv(ROOT/"data/subscriptions.csv", parse_dates=["start_date","end_date"])
t = pd.read_csv(ROOT/"data/trials.csv", parse_dates=["started_at"])
d = u.merge(s, on="user_id").merge(t[["user_id","trial_id"]], on="user_id", how="left")
d = d[d.trial_id.isna() & (d.signup_date>="2024-10-01") & (d.signup_date<=TODAY_END)]
d["gap"] = (d.start_date.dt.normalize()-d.signup_date.dt.normalize()).dt.days
d["per"] = d.signup_date.dt.to_period("M")
d["paid"] = d.plan.isin(["monthly","annual"])
g = d.groupby(["per"]).agg(n=("gap","size"), paid=("paid","mean"), med=("gap","median"), p90=("gap", lambda x: x.quantile(.9)), mx=("gap","max"), start_max=("start_date","max"))
print(g.round(2).to_string())
sch = d[d.start_date>TODAY_END]
print("scheduled non-trial starts: n", len(sch), "distinct start days", sch.start_date.dt.normalize().nunique(), "range", sch.start_date.min(), sch.start_date.max())
print(sch.groupby(sch.start_date.dt.normalize()).size().head(12).to_string())
# subset steady mix: US Web only, gap stability
for c in ["US"]:
    sub = d[(d.country==c)&d.paid]
    print("US payers gap:", checks.stable_over_time(sub,"signup_date","gap",freq="M")["summary"])
# monthly gap computed by signup date: is it censoring? start date relative to data end
d["days_to_end"] = (TODAY_END.normalize()-d.signup_date.dt.normalize()).dt.days
