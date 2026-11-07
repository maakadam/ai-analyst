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
d = u.merge(s, on="user_id", how="left").merge(t, on="user_id", how="left")
d["has_trial"] = d.trial_id.notna()
d["paid"] = d.plan.isin(["monthly","annual"])
d["gap"] = (d.start_date.dt.normalize() - d.signup_date.dt.normalize()).dt.days
w = d[(d.signup_date >= "2025-01-01") & (d.signup_date <= TODAY_END)]
nt = w[~w.has_trial]
ntp = nt[nt.paid]
print("1 paid flag, non-trial, monthly:", checks.stable_over_time(nt, "signup_date", "paid", freq="M")["summary"])
print("2 gap signup->paid start, non-trial payers:", checks.stable_over_time(ntp, "signup_date", "gap", freq="M")["summary"])
print("2b gap signup->start, non-trial free:", checks.stable_over_time(nt[nt.plan=="free"], "signup_date", "gap", freq="M")["summary"])
nt = nt.assign(start_after_today = nt.start_date > TODAY_END)
print("3 scheduled start share, non-trial:", checks.stable_over_time(nt, "signup_date", "start_after_today", freq="M")["summary"])
w = w.assign(signup_midnight = w.signup_date.dt.time.astype(str).eq("00:00:00"),
             start_midnight = w.start_date.dt.time.astype(str).eq("00:00:00"))
print("4 signup midnight share:", checks.stable_over_time(w, "signup_date", "signup_midnight", freq="M")["summary"])
print("5 start midnight share (paid):", checks.stable_over_time(w[w.paid], "signup_date", "start_midnight", freq="M")["summary"])
# gap quantiles by period (aggregate only)
ntp = ntp.assign(per=ntp.signup_date.dt.to_period("M"))
print(ntp.groupby("per").gap.describe(percentiles=[.5,.9])[["count","min","50%","90%","max"]].tail(9).to_string())
print("non-trial payers Aug1-Sep10 start max:", ntp[(ntp.signup_date>="2026-08-01")&(ntp.signup_date<"2026-09-11")].start_date.max())
# trials
tt = w[w.has_trial & w.outcome.notna()].copy()
tt["conv"] = tt.outcome.eq("converted")
print("6 trial conversion by week:", checks.stable_over_time(tt, "started_at", "conv", freq="W-SUN")["summary"])
tt["og"] = (tt.outcome_at - tt.started_at).dt.days
print("7 days to outcome by week:", checks.stable_over_time(tt, "started_at", "og", freq="W-SUN")["summary"])
print(tt.groupby("outcome").og.describe()[["count","min","50%","max"]].to_string())
c = tt[tt.conv]
c = c.assign(sg=(c.start_date.dt.normalize()-c.outcome_at.dt.normalize()).dt.days)
print("convert start minus outcome:", c.sg.describe()[["min","50%","max"]].to_dict())
# assignment checks on Aug1-Sep24 signups
era = w[w.signup_date >= "2026-08-01"].copy()
era["hour"] = era.signup_date.dt.hour
era["dow"] = era.signup_date.dt.dayofweek
era["odd"] = era.user_id % 2
for col in ["odd","dow"]:
    print("trial share by", col, era.groupby(col).has_trial.mean().round(3).to_dict())
print("trial share by hour band", era.groupby(pd.cut(era.hour,[-1,5,11,17,23])).has_trial.mean().round(3).to_dict())
print("midnight-signup trial share", era.groupby(era.signup_date.dt.time.astype(str).eq("00:00:00")).has_trial.agg(["mean","size"]).to_dict())
# volume: weekly signups Jun-Sep 2026
ww = w[w.signup_date>="2026-06-01"].groupby(w.signup_date.dt.to_period("W-SUN")).agg(n=("user_id","size"), tr=("has_trial","mean"))
print(ww.round(2).to_string())
