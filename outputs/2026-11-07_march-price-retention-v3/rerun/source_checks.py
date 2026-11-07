import pandas as pd
from helpers.checks import stable_over_time
s = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
p = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])
s["sd"], s["ed"] = s.start_date.dt.normalize(), s.end_date.dt.normalize()
m = s[(s.plan == "monthly") & (s.sd <= "2026-09-24")]
pm = p[p.subscription_id.isin(m.subscription_id)]
print("amount:", stable_over_time(pm, "payment_date", "amount_usd")["summary"])
# churn per month for an old steady cohort (started before 2025-06), Mar 2025 - Feb 2026
old = m[m.sd < "2025-06-01"]
rows = []
for per in pd.period_range("2025-02", "2026-08", freq="M"):
    a = old[(old.sd < per.start_time) & (old.ed.isna() | (old.ed >= per.start_time))]
    rows.append((str(per), len(a), round((a.ed <= per.end_time.normalize()).mean() * 100, 2)))
print("old cohort churn % by month:", rows)
# status recording
e = m[m.ed.notna() & (m.ed <= "2026-09-24")].copy()
e["canceled"] = e.status == "canceled"
print("status:", stable_over_time(e, "ed", "canceled")["summary"])
# starts mix: share monthly among paid starts
pd_ = s[(s.plan != "free") & (s.sd <= "2026-09-24") & (s.sd >= "2025-01-01")].copy()
pd_["is_monthly"] = pd_.plan == "monthly"
print("plan mix of starts:", stable_over_time(pd_, "sd", "is_monthly")["summary"])
