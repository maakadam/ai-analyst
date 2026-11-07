import sys; from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
import pandas as pd
from helpers import checks
subs = pd.read_csv(ROOT/"data/subscriptions.csv", parse_dates=["start_date"])
pays = pd.read_csv(ROOT/"data/payments.csv", parse_dates=["payment_date"])
p = pays.merge(subs[["subscription_id","start_date"]], on="subscription_id")
p["day"] = (p.payment_date.dt.normalize()-p.start_date.dt.normalize()).dt.days
ids = set(p[(p.day>=0)&(p.day<=5)].subscription_id)
s = subs[subs.plan.isin(["monthly","annual"]) & (subs.start_date>="2025-01-01") & (subs.start_date<="2026-09-24")].copy()
s["charged_at_start"] = s.subscription_id.isin(ids)
print(checks.stable_over_time(s, "start_date", "charged_at_start", freq="M")["summary"])
ns = s[(s.start_date<"2025-09-01")|(s.start_date>="2025-10-01")]
print("excluding Sep 2025:", checks.stable_over_time(ns, "start_date", "charged_at_start", freq="M")["summary"])
