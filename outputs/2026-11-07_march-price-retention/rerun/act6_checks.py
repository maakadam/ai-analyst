"""Act 6 scratch checks: is the input data recorded the same way across the window? Aggregates only."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from helpers.checks import stable_over_time as sot

subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
W0, W1 = "2025-10-01", "2026-08-31"
def p(name, r):
    print(f"- {name}: {r['summary']} breaks={r['breaks']}")

mon = subs[subs.plan == "monthly"].copy()
ended = mon.dropna(subset=["end_date"])
ended = ended[(ended.end_date >= W0) & (ended.end_date <= W1)].copy()
ended["midnight"] = ended.end_date == ended.end_date.dt.normalize()
p("monthly end_date midnight share, Oct25-Aug26", sot(ended, "end_date", "midnight"))
p("monthly end status (canceled vs expired)", sot(ended, "end_date", "status"))
for st in ["expired", "canceled"]:
    s = ended[ended.status == st]
    print(f"  n {st}={len(s)}")
    p(f"  midnight share, status={st}", sot(s, "end_date", "midnight"))
# gap: last payment to end date
last = pays.groupby("subscription_id").payment_date.max().rename("last_pay")
e2 = ended.merge(last, left_on="subscription_id", right_index=True, how="left")
e2["has_pay"] = e2.last_pay.notna()
p("ended monthly with any payment", sot(e2, "end_date", "has_pay"))
e3 = e2[e2.has_pay].copy()
e3["gap_days"] = (e3.end_date.dt.normalize() - e3.last_pay.dt.normalize()).dt.days
p("days from last payment to end_date", sot(e3, "end_date", "gap_days"))
e3["gap_le_31"] = e3.gap_days.between(0, 31)
p("end within 31 days of last payment", sot(e3, "end_date", "gap_le_31"))
# steady subset: started before Sep 2025, not the spike, tenure >=12m mix
old = e2[e2.start_date < "2025-01-01"]
print(f"  n old starters ended={len(old)}")
p("  midnight share, pre-2025 starters", sot(old, "end_date", "midnight"))
# start-date-time format as a recording marker
ms = mon[(mon.start_date >= "2025-01-01") & (mon.start_date <= W1)].copy()
ms["midnight_start"] = ms.start_date == ms.start_date.dt.normalize()
p("monthly start_date midnight share 2025-01..2026-08", sot(ms, "start_date", "midnight_start"))
# amounts
mp = pays.merge(subs[["subscription_id", "plan"]], on="subscription_id")
mpm = mp[(mp.plan == "monthly") & (mp.payment_date >= "2025-01-01") & (mp.payment_date <= W1)]
p("monthly payment amount (share holding mode)", sot(mpm, "payment_date", "amount_usd"))
# payments per active monthly sub per month (double charges)
mpm2 = mpm.assign(m=mpm.payment_date.dt.to_period("M"))
dup = mpm2.groupby(["subscription_id", "m"]).size().rename("n").reset_index()
dup["double"] = dup.n > 1
dup["d"] = dup.m.dt.start_time
p("monthly sub-months with two charges", sot(dup[dup.d >= "2025-01-01"], "d", "double"))
# Annual comparison group: annual ends
ae = subs[(subs.plan == "annual")].dropna(subset=["end_date"])
ae = ae[(ae.end_date >= W0) & (ae.end_date <= W1)].copy()
ae["midnight"] = ae.end_date == ae.end_date.dt.normalize()
print(f"  n annual ended in window={len(ae)}")
# Mix: monthly starts per month, and Sep 2025 spike
ms_all = mon[(mon.start_date >= "2025-01-01")]
print("monthly starts per month:", ms_all.start_date.dt.to_period("M").value_counts().sort_index().to_dict())
# Future group: trials feeding monthly since Aug 2026, Sep 2026 no-payment
tr = pd.read_csv(ROOT / "data/trials.csv", parse_dates=["started_at"])
mon_recent = mon[mon.start_date >= "2026-06-01"].copy()
mon_recent["from_trial"] = mon_recent.user_id.isin(tr[tr.outcome == "converted"].user_id)
mon_recent["has_pay"] = mon_recent.subscription_id.isin(pays.subscription_id)
print("recent monthly starts by month, from trial, has payment:")
print(mon_recent.groupby(mon_recent.start_date.dt.to_period("M"))[["from_trial", "has_pay"]].agg(["size", "sum"]).to_string())
