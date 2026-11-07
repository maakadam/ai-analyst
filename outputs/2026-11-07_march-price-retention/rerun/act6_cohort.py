"""Act 6 scratch: 1 March 2026 monthly base, subs with no payment rows by tenure band (counts only)."""
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
d0 = pd.Timestamp("2026-03-01")
s = subs[subs.plan == "monthly"].copy()
s["start"], s["end"] = s.start_date.dt.normalize(), s.end_date.dt.normalize()
c = s[(s.start < d0) & (s.end.isna() | (s.end >= d0))].copy()
t0 = ((d0 - c.start).dt.days / 30.4375).astype(int)
c["band"] = pd.cut(t0, [-1, 2, 5, 11, 23, 999], labels=["0-2", "3-5", "6-11", "12-23", "24+"])
c["no_pay"] = ~c.subscription_id.isin(pays.subscription_id)
c["no_pay_mar_aug"] = ~c.subscription_id.isin(pays[(pays.payment_date >= d0) & (pays.payment_date < "2026-09-01")].subscription_id)
print(c.groupby("band", observed=True)[["no_pay", "no_pay_mar_aug"]].agg(["size", "sum"]).to_string())
