import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path.cwd()))
from helpers import checks

AS_OF = pd.Timestamp("2026-09-24")
W0, W1 = pd.Timestamp("2025-11-01"), pd.Timestamp("2026-09-01")
subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pay = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])
last_pay = pay.groupby("subscription_id")["payment_date"].max().dt.normalize()
first_pay = pay.groupby("subscription_id")["payment_date"].min().dt.normalize()

for plan in ["monthly", "annual"]:
    e = subs[(subs.plan == plan) & (subs.end_date >= W0) & (subs.end_date < W1)].copy()
    e["gap"] = (e.end_date.dt.normalize() - e.subscription_id.map(last_pay)).dt.days
    e["fixed30"] = e["gap"] == 30
    e["gap_bucket"] = pd.cut(e["gap"], [-1e9, -1, 0, 15, 29, 30, 45, 1e9]).astype(str)
    e["tod"] = e.end_date != e.end_date.dt.normalize()
    e["status_v"] = e["status"]
    e["no_payment"] = e.subscription_id.map(last_pay).isna()
    for col, tol in [("fixed30", 0.25), ("fixed30", 0.05), ("tod", 0.25), ("tod", 0.10),
                     ("gap_bucket", 0.25), ("status_v", 0.25), ("no_payment", 0.05)]:
        print(plan, col, tol, checks.stable_over_time(e, "end_date", col, tolerance=tol)["summary"])

# payment amounts and gaps between payments, monthly plan
mp = pay.merge(subs[["subscription_id", "plan", "start_date"]], on="subscription_id")
mp = mp[(mp.plan == "monthly")].sort_values(["subscription_id", "payment_date"]).copy()
mp["gap"] = mp.groupby("subscription_id")["payment_date"].diff().dt.days
w = mp[(mp.payment_date >= W0) & (mp.payment_date < W1)].copy()
w["amount_is_12"] = w.amount_usd == 12
w["gap_28_31"] = w.gap.between(28, 31)
w["tod"] = w.payment_date != w.payment_date.dt.normalize()
for col in ["amount_is_12", "gap_28_31", "tod"]:
    print("payments", col, checks.stable_over_time(w, "payment_date", col)["summary"])
pa = mp[(mp.payment_date >= "2025-01-01") & (mp.payment_date < W1)].copy()
pa["gap_28_31"] = pa.gap.between(28, 31) | pa.gap.isna()
pa["tod"] = pa.payment_date != pa.payment_date.dt.normalize()
for col in ["gap_28_31", "tod"]:
    print("payments from Jan 2025", col, checks.stable_over_time(pa, "payment_date", col)["summary"])

# first-calendar-month cancellations, never at risk in the script
m = subs[(subs.plan == "monthly") & (subs.start_date <= AS_OF)].copy()
m["sm"] = m.start_date.dt.to_period("M")
m["same_month_end"] = m.end_date.notna() & (m.end_date.dt.to_period("M") == m["sm"])
g = m[(m.sm >= pd.Period("2025-11", "M")) & (m.sm <= pd.Period("2026-08", "M"))]
g = g.assign(period=(g.sm >= pd.Period("2026-03", "M")).map({True: "after", False: "before"}))
print("same-month enders by period:\n", g.groupby("period")["same_month_end"].agg(["size", "sum", "mean"]))
print("monthly starts by month:\n", g.groupby("sm").size().to_string())
# starters whose first payment is later than start (trial-converted?)
m["delay"] = (m.subscription_id.map(first_pay) - m.start_date.dt.normalize()).dt.days
m["delay_gt3"] = m["delay"] > 3
print("first payment > 3 days after start, by start month (last 8):\n",
      m[m.sm >= pd.Period("2026-01", "M")].groupby("sm")["delay_gt3"].mean().round(3).to_string())
