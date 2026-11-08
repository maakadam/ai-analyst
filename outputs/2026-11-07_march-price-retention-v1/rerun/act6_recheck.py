"""Recheck scratch: after window now Mar-Jul 2026. Aggregates only."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from helpers.checks import stable_over_time as sot
RUN = Path(__file__).resolve().parents[1]
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
tr = pd.read_csv(ROOT / "data/trials.csv")
mon = subs[subs.plan == "monthly"]
e = mon.dropna(subset=["end_date"])
e = e[(e.end_date >= "2025-10-01") & (e.end_date <= "2026-07-31")].copy()
e["canceled"] = e.status == "canceled"
e["midnight"] = e.end_date == e.end_date.dt.normalize()
last = pays.groupby("subscription_id").payment_date.max().rename("last_pay")
e = e.merge(last, left_on="subscription_id", right_index=True, how="left")
e["gap"] = (e.end_date.dt.normalize() - e.last_pay.dt.normalize()).dt.days
e["short"] = e.gap.between(0, 31)
for c in ["canceled", "midnight", "short"]:
    print(f"- {c} Oct25-Jul26: {sot(e, 'end_date', c)['summary']}")
ep = e[e.last_pay.notna()]
print(f"- gap days Oct25-Jul26: {sot(ep, 'end_date', 'gap')['summary']}")
old = ep[ep.start_date < "2025-01-01"]
print(f"- short gap pre-2025 starters: {sot(old, 'end_date', 'short', min_rows=15)['summary']}")
# Persistence of the after rate, from the result table
p = pd.read_csv(RUN / "data/churn_monthly_by_plan_tenure.csv")
p = p[(p.plan == "monthly") & (p.month >= "2025-10")]
t = p.groupby(["month", "band"])[["at_risk", "churned"]].sum()
t["rate"] = (t.churned / t.at_risk * 100).round(1)
print(t.rate.unstack().to_string())
c = p[p.cohort == "joined at $10"].groupby("month")[["at_risk", "churned"]].sum()
print("joined at $10, all bands, rate %:", (c.churned / c.at_risk * 100).round(2).to_dict())
# band mix of at-risk, before vs after
p["per"] = pd.cut(p.month.str.replace("-", "").astype(int), [202509, 202602, 202607, 202608], labels=["before", "after", "aug"])
mix = p.groupby(["per", "band"], observed=True).at_risk.sum().unstack()
print((mix.div(mix.sum(1), axis=0) * 100).round(1).to_string())
# Future group: monthly starts by month and source
ms = mon[(mon.start_date >= "2026-03-01") & (mon.start_date <= "2026-09-24")].copy()
ms["from_trial"] = ms.user_id.isin(tr[tr.outcome == "converted"].user_id)
ms["has_pay"] = ms.subscription_id.isin(pays.subscription_id)
print(ms.groupby(ms.start_date.dt.to_period("M"))[["from_trial", "has_pay"]].agg(["size", "sum"]).to_string())
