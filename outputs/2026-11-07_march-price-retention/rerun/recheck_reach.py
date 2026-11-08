"""Recheck of rollback_reach_2026_09_24.csv and grouped gain table. Aggregates only."""
import pandas as pd
R = "outputs/2026-11-07_march-price-retention/"
AS_OF = pd.Timestamp("2026-09-24 23:59:59"); WE = pd.Timestamp("2026-07-31 23:59:59")
s = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
t = pd.read_csv("data/trials.csv", parse_dates=["started_at"])
s = s[s.plan == "monthly"]
tu = set(t.user_id)
s["trial"] = s.user_id.isin(tu)
s["day"] = s.start_date.dt.normalize()
bulk = s.day.isin([pd.Timestamp("2025-09-17"), pd.Timestamp("2026-07-30")])
live = s[s.end_date.isna() | (s.end_date > AS_OF)]
org = live[~live.trial & ~live.day.isin([pd.Timestamp("2025-09-17"), pd.Timestamp("2026-07-30")]) & (live.start_date <= AS_OF)]
print("organic live on 09-24:", len(org), "| started after 2026-07-31:", int((org.start_date > WE).sum()))
print("organic live that ended Aug-Sep 2026 would be... ended 2026-08-01..09-24 among organic pre-window:",
      int(((s.end_date > WE) & (s.end_date <= AS_OF) & ~s.trial & (s.start_date <= WE) & ~bulk).sum()))
tc = live[live.trial & (live.start_date <= AS_OF) & ~live.day.isin([pd.Timestamp("2026-07-30"), pd.Timestamp("2025-09-17")])]
print("trial converters live: n", len(tc), "start min", tc.start_date.min().date(), "max", tc.start_date.max().date())
sch = live[live.start_date > AS_OF]
print("scheduled after: n", len(sch), "of which trial users", int(sch.trial.sum()))
# grouped gain range (sum of band lows/highs, conservative)
d = pd.read_csv(R + "data/observed_revenue_by_due_month.csv")
d = d[(d.dimension == "tenure") & d.segment.isin(["1", "2-3", "4-6"])]
print(d.groupby("due_month")[["gain_usd", "gain_low_usd", "gain_high_usd"]].sum().round(0).to_string())
