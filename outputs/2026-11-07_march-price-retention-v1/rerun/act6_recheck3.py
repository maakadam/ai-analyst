"""Recheck 3: volume and source of new monthly starters feeding the newest band (aggregates only)."""
import pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
trials = pd.read_csv(ROOT / "data/trials.csv")
TODAY = pd.Timestamp("2026-09-24")
m = subs[(subs.plan == "monthly") & (subs.start_date.dt.normalize() <= TODAY)].copy()
m["month"] = m.start_date.dt.to_period("M")
m["trial"] = m.user_id.isin(trials.user_id)
m["has_pay"] = m.subscription_id.isin(pays.subscription_id)
x = m[m.month >= pd.Period("2026-01", "M")]
print(x.groupby(["month", "trial", "has_pay"]).size().unstack(["trial", "has_pay"], fill_value=0).to_string())
# daily-ish: Sept starts by week, no-payment non-trial
s = m[(m.month == pd.Period("2026-09", "M"))]
print(s.groupby([s.start_date.dt.isocalendar().week, "trial", "has_pay"]).size().unstack(["trial", "has_pay"], fill_value=0).to_string())
# Aug non-trial starts with payment: share whose first payment is on start day
a = m[(m.month == pd.Period("2026-08", "M")) & ~m.trial]
print("Aug non-trial monthly starts:", len(a), "with payment:", a.has_pay.sum())
