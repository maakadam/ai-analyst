"""Second recheck scratch: inputs behind the new money rows. Aggregates only."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from helpers.checks import stable_over_time as sot
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
tr = pd.read_csv(ROOT / "data/trials.csv")
T = pd.Timestamp("2026-09-24")
conv = set(tr[tr.outcome == "converted"].user_id)
haspay = set(pays.subscription_id)
m = subs[subs.plan == "monthly"].copy()
m["start"], m["end"] = m.start_date.dt.normalize(), m.end_date.dt.normalize()
m.loc[m.end > T, "end"] = pd.NaT
m = m[(m.start <= T) & m.subscription_id.isin(haspay)]
m["trial"] = m.user_id.isin(conv)
# Base on 2026-09-24, 0-2 months band: who is in it
b = m[(m.start < T) & (m.end.isna() | (m.end >= T))].copy()
b["t0"] = ((T - b.start).dt.days / 30.4375).astype(int)
nb = b[b.t0 <= 2]
print("today 0-2 band:", len(nb), "trial converts:", int(nb.trial.sum()),
      "by start month:", nb.start.dt.to_period("M").value_counts().sort_index().to_dict())
# Paying monthly starts by month and source
s = m[m.start >= "2026-01-01"]
print(s.groupby([s.start.dt.to_period("M"), "trial"]).size().unstack(fill_value=0).to_string())
# Ends within 30 days of start, by start month and source (aggregates; recent months open)
s = s.assign(end30=s.end.notna() & ((s.end - s.start).dt.days <= 30))
mature = s[s.start <= T - pd.Timedelta(days=31)]
print("share ending within 30 days of start, matured starts:")
print(mature.groupby([mature.start.dt.to_period("M"), "trial"]).end30.agg(["size", "mean"]).round(3).to_string())
# Stability of 30-day early end for joined-at-$12 non-trial starters Mar-Aug
nt = mature[~mature.trial & (mature.start >= "2026-03-01")]
print("- early end, non-trial $12 starters:", sot(nt, "start", "end30", min_rows=20)["summary"])
# Stability of starts volume: non-trial paying starts as a yes/no share of all paid starts with payment
