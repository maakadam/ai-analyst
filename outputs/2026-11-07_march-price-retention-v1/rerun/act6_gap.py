"""Act 6 scratch: is the April 2026 step in end_date vs last payment a recording change or mix? Aggregates only."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from helpers.checks import stable_over_time as sot
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
mon = subs[subs.plan == "monthly"].copy()
e = mon.dropna(subset=["end_date"])
e = e[(e.end_date >= "2025-10-01") & (e.end_date <= "2026-08-31")].copy()
last = pays.groupby("subscription_id").payment_date.max().rename("last_pay")
e = e.merge(last, left_on="subscription_id", right_index=True, how="left")
e["gap"] = (e.end_date.dt.normalize() - e.last_pay.dt.normalize()).dt.days
e["bucket"] = pd.cut(e.gap, [-999, -1, 31, 62, 9999], labels=["neg", "0-31", "32-62", "63+"]).astype(str)
e.loc[e.last_pay.isna(), "bucket"] = "no pay"
e["m"] = e.end_date.dt.to_period("M")
print(pd.crosstab(e.m, e.bucket).to_string())
e["coh"] = "other"
e.loc[e.start_date < "2025-01-01", "coh"] = "pre-2025"
e.loc[e.start_date.dt.to_period("M") == pd.Period("2025-09", "M"), "coh"] = "sep25 spike"
e.loc[e.start_date >= "2026-03-01", "coh"] = "post-increase start"
print(pd.crosstab(e.m, e.coh).to_string())
e["short"] = e.bucket == "0-31"
for c in ["pre-2025", "sep25 spike", "other"]:
    s = e[(e.coh == c) & e.last_pay.notna()]
    r = sot(s, "end_date", "short", min_rows=15)
    print(f"- short gap, {c} (n={len(s)}): {r['summary']} breaks={r['breaks']}")
# Aug 2026 canceled status: times
aug = e[e.m == pd.Period("2026-08", "M")]
print("Aug 2026 ends status:", aug.status.value_counts().to_dict())
# churn panel monthly: what share of baseline churners had 63+ gap
print("--- 63+ gap enders by start month (counts)")
g = e[e.bucket == "63+"]
print(g.start_date.dt.to_period("M").value_counts().sort_index().to_dict())
print("--- Aug 32-62 enders: last payment month counts")
a = e[(e.m == pd.Period("2026-08", "M")) & (e.bucket == "32-62")]
print(a.last_pay.dt.to_period("M").value_counts().to_dict())
print("--- Oct-Nov 2025 32-62 enders: status, last payment month")
b = e[(e.m <= pd.Period("2025-11", "M")) & (e.bucket == "32-62")]
print(b.status.value_counts().to_dict(), b.last_pay.dt.to_period("M").value_counts().to_dict())
print("--- end day-of-month vs start day-of-month equal share by end month")
e["same_dom"] = e.end_date.dt.day == e.start_date.dt.day
print(e.groupby("m").same_dom.mean().round(2).to_dict())
