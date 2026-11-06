"""Did the March 2026 monthly price increase ($10 to $12) hurt retention, and for whom?

Plan: see plan.md (plus a Sep 2025-Feb 2026 baseline as sensitivity) in this folder. Run from the repo root:
    poetry run python outputs/2026-11-06_march-price-retention/analysis.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from helpers import charts, checks  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
CH = RUN / "charts"
OUT.mkdir(exist_ok=True)
CH.mkdir(exist_ok=True)

AS_OF = pd.Timestamp("2026-09-24")  # data end, treated as today
INCREASE = pd.Timestamp("2026-03-01")
OLD_PRICE, NEW_PRICE = 10.0, 12.0
BANDS = [(0, 2, "0-2m"), (3, 5, "3-5m"), (6, 11, "6-11m"), (12, 23, "12-23m"), (24, 10_000, "24m+")]
BAND_ORDER = [b[2] for b in BANDS]
SOURCE = "Source: Beam subscriptions, users; monthly churn per closed month"

# Periods (closed months only)
MONTHS = pd.period_range("2025-03", "2026-08", freq="M")
PERIOD = {}
for m in MONTHS:
    if m >= pd.Period("2026-03", "M"):
        PERIOD[m] = "after"
    else:
        PERIOD[m] = "before"
YOY = set(pd.period_range("2025-03", "2025-08", freq="M"))

# ---------------------------------------------------------------- load
subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
users = pd.read_csv("data/users.csv", parse_dates=["signup_date"])
pay = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])

# Compare on dates, not timestamps (quirk: Timestamps everywhere)
subs["start_date"] = subs["start_date"].dt.normalize()
subs["end_date"] = subs["end_date"].dt.normalize()

print("CHECKS")
fan = checks.join_fan_out(subs, users[["user_id", "country", "device_type"]], "user_id")
print(" join subscriptions->users:", fan["summary"])
subs = subs.merge(users[["user_id", "country", "device_type"]], on="user_id", how="left")

print(" payments:", checks.date_boundaries(pay, "payment_date")["summary"])
months_df = pd.DataFrame({"month_end": [m.end_time.normalize() for m in MONTHS]})
mat = checks.matured_only(months_df, "month_end", as_of=AS_OF)
print(" months:", mat["summary"])
assert mat["dropped"] == 0

# Exclude free plans (never end) and scheduled starts after today
future = int((subs["start_date"] > AS_OF).sum())
paid = subs[(subs["plan"] != "free") & (subs["start_date"] <= AS_OF)].copy()
print(f" excluded {future:,} subscriptions starting after {AS_OF.date()} and all free plans")
same_month = paid[(paid["end_date"].notna())
                  & (paid["end_date"].dt.to_period("M") == paid["start_date"].dt.to_period("M"))]
print(f" subscriptions that start and end in the same month (never at risk, not counted): {len(same_month):,}")

paid["spike_cohort"] = paid["start_date"].dt.to_period("M") == pd.Period("2025-09", "M")


def band_of(t):
    for lo, hi, name in BANDS:
        if lo <= t <= hi:
            return name
    return None


# ---------------------------------------------------------------- subscriber-months
rows = []
for m in MONTHS:
    ms, nxt = m.start_time, (m + 1).start_time
    at_risk = paid[(paid["start_date"] < ms) & (paid["end_date"].isna() | (paid["end_date"] >= ms))]
    churned = at_risk["end_date"].notna() & (at_risk["end_date"] < nxt)
    tenure = np.floor((ms - at_risk["start_date"]).dt.days / 30.4375).astype(int)
    rows.append(pd.DataFrame({
        "month": m, "plan": at_risk["plan"].values, "country": at_risk["country"].values,
        "device": at_risk["device_type"].values, "spike_cohort": at_risk["spike_cohort"].values,
        "tenure_band": [band_of(t) for t in tenure], "churned": churned.astype(int).values,
    }))
sm = pd.concat(rows, ignore_index=True)
sm["period"] = sm["month"].map(PERIOD)
sm["yoy_before"] = sm["month"].isin(YOY)

# Monthly series
series = (sm.groupby(["month", "plan"]).agg(at_risk=("churned", "size"), churned=("churned", "sum"))
          .reset_index())
series["churn_rate"] = series["churned"] / series["at_risk"]
series.to_csv(OUT / "monthly_churn_series.csv", index=False)

mon = sm[sm["plan"] == "monthly"]


def cells(df, seg):
    keys = ([seg] if seg else []) + ["tenure_band"]
    g = df.groupby(keys + ["period"]).agg(at_risk=("churned", "size"), churned=("churned", "sum"))
    return g.reset_index()


def standardised(df, seg, label_before="before"):
    """Before rate reweighted to the after-period tenure mix of each segment."""
    c = cells(df, seg)
    keys = [seg] if seg else []
    b = c[c["period"] == label_before].set_index(keys + ["tenure_band"])
    a = c[c["period"] == "after"].set_index(keys + ["tenure_band"])
    j = a.join(b, lsuffix="_after", rsuffix="_before", how="left")
    j["rate_before_band"] = j["churned_before"] / j["at_risk_before"]
    j["w"] = j["at_risk_after"] / j.groupby(level=keys or None)["at_risk_after"].transform("sum") \
        if keys else j["at_risk_after"] / j["at_risk_after"].sum()
    j["exp_churn"] = j["w"] * j["rate_before_band"]
    grp = j.groupby(level=keys) if keys else j.assign(_all="all").groupby("_all")
    out = grp.agg(at_risk_after=("at_risk_after", "sum"), churned_after=("churned_after", "sum"),
                  at_risk_before=("at_risk_before", "sum"), churned_before=("churned_before", "sum"),
                  rate_before_std=("exp_churn", "sum"))
    out["rate_after"] = out["churned_after"] / out["at_risk_after"]
    out["rate_before_crude"] = out["churned_before"] / out["at_risk_before"]
    out["change_pp"] = (out["rate_after"] - out["rate_before_std"]) * 100
    out["change_rel_pct"] = (out["rate_after"] / out["rate_before_std"] - 1) * 100
    # Approximate 95% interval for the rate ratio (Poisson, on log scale)
    se = np.sqrt(1 / out["churned_after"] + 1 / out["churned_before"])
    rr = out["rate_after"] / out["rate_before_std"]
    out["rel_low_pct"] = (rr * np.exp(-1.96 * se) - 1) * 100
    out["rel_high_pct"] = (rr * np.exp(1.96 * se) - 1) * 100
    # Lifetime revenue per subscriber is price / monthly churn
    out["lifetime_rev_ratio"] = (NEW_PRICE / out["rate_after"]) / (OLD_PRICE / out["rate_before_std"])
    out["below_breakeven"] = out["lifetime_rev_ratio"] < 1
    # Clearly below: even the low end of the churn rise exceeds the 20% price rise
    out["clearly_below"] = out["rel_low_pct"] > (NEW_PRICE / OLD_PRICE - 1) * 100
    return out.reset_index(), j.reset_index()


# ---------------------------------------------------------------- headline
overall, overall_bands = standardised(mon, None)
overall.to_csv(OUT / "headline_monthly_plan.csv", index=False)
o = overall.iloc[0]

yoy_df = mon[(mon["period"] == "after") | mon["yoy_before"]].copy()
yoy_df.loc[yoy_df["yoy_before"], "period"] = "before"
yoy, _ = standardised(yoy_df, None)
yoy.to_csv(OUT / "headline_monthly_plan_yoy.csv", index=False)
y = yoy.iloc[0]

RECENT = set(pd.period_range("2025-09", "2026-02", freq="M"))
rec_df = mon[(mon["period"] == "after") | mon["month"].isin(RECENT)]
recent, _ = standardised(rec_df, None)
recent.to_csv(OUT / "headline_monthly_plan_sep25_feb26.csv", index=False)
rc = recent.iloc[0]

nospike, _ = standardised(mon[~mon["spike_cohort"]], None)
nospike.to_csv(OUT / "headline_monthly_plan_no_sep2025_cohort.csv", index=False)
ns = nospike.iloc[0]

ann, _ = standardised(sm[sm["plan"] == "annual"], None)
ann.to_csv(OUT / "headline_annual_plan.csv", index=False)
an = ann.iloc[0]

# ---------------------------------------------------------------- segments
by_tenure = cells(mon, None).pivot_table(index="tenure_band", columns="period",
                                         values=["at_risk", "churned"], aggfunc="sum")
by_tenure.columns = [f"{a}_{b}" for a, b in by_tenure.columns]
by_tenure = by_tenure.reindex(BAND_ORDER)
by_tenure["rate_before"] = by_tenure["churned_before"] / by_tenure["at_risk_before"]
by_tenure["rate_after"] = by_tenure["churned_after"] / by_tenure["at_risk_after"]
by_tenure["change_pp"] = (by_tenure["rate_after"] - by_tenure["rate_before"]) * 100
by_tenure["change_rel_pct"] = (by_tenure["rate_after"] / by_tenure["rate_before"] - 1) * 100
se = np.sqrt(1 / by_tenure["churned_after"] + 1 / by_tenure["churned_before"])
rr = by_tenure["rate_after"] / by_tenure["rate_before"]
by_tenure["rel_low_pct"] = (rr * np.exp(-1.96 * se) - 1) * 100
by_tenure["rel_high_pct"] = (rr * np.exp(1.96 * se) - 1) * 100
by_tenure["lifetime_rev_ratio"] = 1.2 * by_tenure["rate_before"] / by_tenure["rate_after"]
by_tenure = by_tenure.reset_index()
by_tenure.to_csv(OUT / "segment_tenure.csv", index=False)

seg_tables = {}
for seg in ["country", "device"]:
    t, bands = standardised(mon, seg)
    t.to_csv(OUT / f"segment_{seg}.csv", index=False)
    bands.to_csv(OUT / f"segment_{seg}_by_tenure.csv", index=False)
    seg_tables[seg] = t
    for col in ["at_risk_after", "churned_after"]:
        r = checks.parts_sum_to_total(t[col], o[col])
        print(f" {seg} {col}:", r["summary"])
r = checks.parts_sum_to_total(by_tenure["at_risk_after"], o["at_risk_after"])
print(" tenure at_risk_after:", r["summary"])

mon2 = mon.assign(country_device=mon["country"] + " / " + mon["device"])
cd, _ = standardised(mon2, "country_device")
cd.to_csv(OUT / "segment_country_device.csv", index=False)

# ---------------------------------------------------------------- revenue context
p = pay.merge(subs[["subscription_id", "plan"]], on="subscription_id", how="left")
fan2 = checks.join_fan_out(pay, subs[["subscription_id", "plan"]], "subscription_id")
print(" join payments->subscriptions:", fan2["summary"])
p["month"] = p["payment_date"].dt.to_period("M")
rev = (p[(p["plan"] == "monthly") & p["month"].isin(MONTHS)]
       .groupby("month").agg(payments=("payment_id", "count"), revenue=("amount_usd", "sum"))
       .reset_index())
rev.to_csv(OUT / "monthly_plan_revenue.csv", index=False)
rev_before = rev[rev["month"].isin(pd.period_range("2025-09", "2026-02", freq="M"))]["revenue"].mean()
rev_after = rev[rev["month"].isin(pd.period_range("2026-03", "2026-08", freq="M"))]["revenue"].mean()
base = series[series["plan"] == "monthly"].set_index("month")["at_risk"]

# ---------------------------------------------------------------- charts
ms_ = series[series["plan"] == "monthly"]
an_ = series[series["plan"] == "annual"]
fig = charts.line(
    [str(m) for m in ms_["month"]],
    {"Monthly plan": (ms_["churn_rate"] * 100).round(2).tolist(),
     "Annual plan": (an_["churn_rate"] * 100).round(2).tolist()},
    title="Monthly-plan churn stepped up from April 2026; annual churn did not",
    highlight="Monthly plan", ylabel="Churn in month, % of subscribers at risk", source=SOURCE)
fig.axes[0].axvline(str(pd.Period("2026-03", "M")), color=charts.GRAY, linestyle=":")
fig.axes[0].tick_params(axis="x", rotation=45)
charts.save(fig, CH / "churn_by_month.png")

bt = by_tenure.set_index("tenure_band")
fig = charts.bar(BAND_ORDER, bt["change_rel_pct"].round(0).tolist(),
                 title="Churn rose at every tenure, most among the longest-tenured",
                 ylabel="Relative change in monthly churn, % (after vs before)",
                 highlight=[b for b in BAND_ORDER if bt.loc[b, "lifetime_rev_ratio"] < 1],
                 source=SOURCE)
fig.axes[0].axhline(20, color=charts.ACCENT, linestyle=":")
charts.save(fig, CH / "churn_change_by_tenure.png")

for seg, t in seg_tables.items():
    t = t.sort_values("change_rel_pct", ascending=False)
    fig = charts.bar(t[seg].tolist(), t["change_rel_pct"].round(0).tolist(),
                     title=f"Tenure-matched churn rise by {seg}: above the 20% break-even in "
                           f"{int(t['below_breakeven'].sum())} of {len(t)}",
                     ylabel="Relative change in monthly churn, % (tenure-matched)",
                     highlight=t.loc[t["below_breakeven"], seg].tolist(), source=SOURCE)
    fig.axes[0].axhline(20, color=charts.ACCENT, linestyle=":")
    charts.save(fig, CH / f"churn_change_by_{seg}.png")

# ---------------------------------------------------------------- headlines
def line_(label, r):
    return (f"{label}: {r['rate_after']:.2%} after vs {r['rate_before_std']:.2%} before (tenure-matched); "
            f"{r['change_pp']:+.2f} pp, {r['change_rel_pct']:+.0f}% relative "
            f"(95% approx {r['rel_low_pct']:+.0f}% to {r['rel_high_pct']:+.0f}%); "
            f"lifetime revenue ratio {r['lifetime_rev_ratio']:.2f}")

print("\nHEADLINES")
print(line_("Monthly plan, baseline Mar25-Feb26", o))
print(line_("Monthly plan, baseline Mar-Aug 2025", y))
print(line_("Monthly plan, baseline Sep25-Feb26", rc))
print(line_("Monthly plan, without Sep 2025 cohort", ns))
print(line_("Annual plan (price unchanged)", an))
print(f"Monthly subscribers at risk: Feb 2026 {base[pd.Period('2026-02','M')]:,} vs Aug 2026 {base[pd.Period('2026-08','M')]:,}")
print(f"Monthly-plan revenue per month: ${rev_after:,.0f} Mar-Aug 2026 vs ${rev_before:,.0f} Sep 2025-Feb 2026 "
      f"({(rev_after / rev_before - 1):+.1%} relative)")
print("\nBY TENURE (crude within band)")
for _, r in by_tenure.iterrows():
    print(f" {r['tenure_band']:>6}: {r['rate_before']:.2%} -> {r['rate_after']:.2%} "
          f"({r['change_pp']:+.2f} pp, {r['change_rel_pct']:+.0f}% rel, CI {r['rel_low_pct']:+.0f}% to "
          f"{r['rel_high_pct']:+.0f}%), revenue ratio {r['lifetime_rev_ratio']:.2f}, n_after={int(r['at_risk_after']):,}")
for seg, t in list(seg_tables.items()) + [("country_device", cd)]:
    print(f"\nBY {seg.upper()} (tenure-matched)")
    for _, r in t.sort_values("change_rel_pct", ascending=False).iterrows():
        print(f" {r[seg]:>14}: {r['rate_before_std']:.2%} -> {r['rate_after']:.2%} "
              f"({r['change_pp']:+.2f} pp, {r['change_rel_pct']:+.0f}% rel, CI {r['rel_low_pct']:+.0f}% to "
              f"{r['rel_high_pct']:+.0f}%), revenue ratio {r['lifetime_rev_ratio']:.2f}"
              f"{' BELOW' if r['below_breakeven'] else ''}{' CLEARLY' if r['clearly_below'] else ''}, "
              f"churned_after={int(r['churned_after'])}")
