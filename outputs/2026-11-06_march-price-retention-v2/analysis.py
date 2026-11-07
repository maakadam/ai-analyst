"""Did the March 2026 monthly price increase ($10 to $12) hurt retention, and for whom? (v2)

Plan: see plan.md in this folder. Run from the repo root:
    poetry run python outputs/2026-11-06_march-price-retention-v2/analysis.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))  # run from the repo root
from helpers import charts, checks  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
CH = RUN / "charts"
OUT.mkdir(exist_ok=True)
CH.mkdir(exist_ok=True)

AS_OF = pd.Timestamp("2026-09-24")  # data end, treated as today
OLD_PRICE, NEW_PRICE = 10.0, 12.0
# Baseline starts in November 2025: October 2025 still holds some end dates recorded
# the old way (a fixed 30 days after the last payment). October is kept as a sensitivity.
BEFORE = pd.period_range("2025-11", "2026-02", freq="M")
OCTOBER = pd.Period("2025-10", "M")
AFTER = pd.period_range("2026-03", "2026-08", freq="M")
CHECK_FROM = pd.Timestamp("2025-03-01")
BANDS = [(0, 2, "0-2m"), (3, 5, "3-5m"), (6, 11, "6-11m"), (12, 23, "12-23m"), (24, 10_000, "24m+")]
BAND_ORDER = [b[2] for b in BANDS]
HORIZONS = [6, 12, 24]
BOOT = 200  # bootstrap resamples of subscribers
rng = np.random.default_rng(42)
SOURCE = "Source: Beam subscriptions, payments, users; closed months to Aug 2026"

# ---------------------------------------------------------------- load
subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
users = pd.read_csv("data/users.csv", parse_dates=["signup_date"])
pay = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])

print("CHECKS")
fan = checks.join_fan_out(subs, users[["user_id", "country", "device_type"]], "user_id")
print(" join subscriptions->users:", fan["summary"])
subs = subs.merge(users[["user_id", "country", "device_type"]], on="user_id", how="left")
fan2 = checks.join_fan_out(pay, subs[["subscription_id", "plan"]], "subscription_id")
print(" join payments->subscriptions:", fan2["summary"])
print(" payments:", checks.date_boundaries(pay, "payment_date")["summary"])
months_df = pd.DataFrame({"month_end": [m.end_time.normalize() for m in AFTER]})
mat = checks.matured_only(months_df, "month_end", as_of=AS_OF)
print(" after-period months:", mat["summary"])
assert mat["dropped"] == 0

# ---------------------------------------------------------------- is the baseline recorded like the after period?
last_pay = pay.groupby("subscription_id")["payment_date"].max().dt.normalize()
ended = subs[(subs["plan"] == "monthly") & (subs["end_date"] >= CHECK_FROM)
             & (subs["end_date"] <= AS_OF)].copy()
ended["days_after_last_payment"] = (ended["end_date"].dt.normalize()
                                    - ended["subscription_id"].map(last_pay)).dt.days
ended["has_time_of_day"] = ended["end_date"] != ended["end_date"].dt.normalize()
# The old recording put every end exactly 30 days after the last payment.
ended["fixed_30_day_end"] = ended["days_after_last_payment"] == 30
recording = []
for col, tol in [("fixed_30_day_end", 0.10), ("has_time_of_day", 0.25)]:
    full = checks.stable_over_time(ended, "end_date", col, tolerance=tol)
    window = checks.stable_over_time(
        ended[ended["end_date"] >= BEFORE[0].start_time], "end_date", col, tolerance=tol)
    print(f" {col}, from Mar 2025:", full["summary"])
    print(f" {col}, from Nov 2025:", window["summary"])
    recording.append({"field": col, "subset": "all monthly enders", "tolerance": tol,
                      "break_from_mar_2025": full["first_break"],
                      "stable_from_nov_2025": window["ok"]})
# The time-of-day share keeps moving after November because mid-cycle cancellations
# grow; test it among mid-cycle cancellations only, where it should be steady if
# the recording itself did not change again.
mid = ended[(ended["end_date"] >= BEFORE[0].start_time) & (ended["days_after_last_payment"] != 30)]
mid_check = checks.stable_over_time(mid, "end_date", "has_time_of_day")
print(" has_time_of_day among mid-cycle cancellations, from Nov 2025:", mid_check["summary"])
recording.append({"field": "has_time_of_day", "subset": "mid-cycle cancellations", "tolerance": 0.25,
                  "break_from_mar_2025": None, "stable_from_nov_2025": mid_check["ok"]})
# Stop if the field the baseline rests on is not stable inside the compared window.
assert recording[0]["stable_from_nov_2025"], "End dates change recording inside the window"
pd.DataFrame(recording).to_csv(OUT / "recording_check.csv", index=False)

# ---------------------------------------------------------------- population
# Compare on dates, not timestamps (quirk: Timestamps everywhere)
subs["start_date"] = subs["start_date"].dt.normalize()
subs["end_date"] = subs["end_date"].dt.normalize()
future = int((subs["start_date"] > AS_OF).sum())
paid = subs[(subs["plan"] != "free") & (subs["start_date"] <= AS_OF)].copy()
first_pay = pay.groupby("subscription_id")["payment_date"].min().dt.normalize()
paid["first_payment"] = paid["subscription_id"].map(first_pay)
print(f" excluded {future:,} subscriptions starting after {AS_OF.date()} and all free plans; "
      f"{len(paid):,} paid subscriptions remain")
start_m = paid["start_date"].dt.to_period("M")
paid["cohort"] = np.select(
    [start_m < pd.Period("2025-09", "M"), start_m == pd.Period("2025-09", "M"),
     start_m < pd.Period("2026-03", "M")],
    ["Started before Sep 2025", "Started Sep 2025 (spike)", "Started Oct 2025-Feb 2026"],
    default="Started after the increase")


def band_of(t):
    for lo, hi, name in BANDS:
        if lo <= t <= hi:
            return name
    return None


rows = []
unpaid_months = 0
for m in [OCTOBER] + list(BEFORE) + list(AFTER):
    ms, nxt = m.start_time, (m + 1).start_time
    active = paid[(paid["start_date"] < ms) & (paid["end_date"].isna() | (paid["end_date"] >= ms))]
    # Paying subscribers only: at least one payment on record before the month starts.
    at_risk = active[active["first_payment"] < ms]
    unpaid_months += len(active) - len(at_risk)
    tenure = np.floor((ms - at_risk["start_date"]).dt.days / 30.4375).astype(int)
    rows.append(pd.DataFrame({
        "month": m, "subscription_id": at_risk["subscription_id"].values,
        "plan": at_risk["plan"].values, "country": at_risk["country"].values,
        "device": at_risk["device_type"].values, "cohort": at_risk["cohort"].values,
        "tenure_band": [band_of(t) for t in tenure],
        "churned": (at_risk["end_date"].notna() & (at_risk["end_date"] < nxt)).astype(int).values,
    }))
sm = pd.concat(rows, ignore_index=True)
same_month = paid[paid["end_date"].notna()
                  & (paid["end_date"].dt.to_period("M") == paid["start_date"].dt.to_period("M"))]
for label, months in [("before", BEFORE), ("after", AFTER)]:
    n = int(same_month["start_date"].dt.to_period("M").isin(months).sum())
    print(f" not counted: {n} paid subscriptions that started and ended in the same month, {label} period")
print(f" excluded {unpaid_months:,} subscriber-months with no payment on record yet "
      f"({unpaid_months / (unpaid_months + len(sm)):.1%} of active paid-plan subscriber-months)")
sm["period"] = np.select([sm["month"].isin(AFTER), sm["month"].isin(BEFORE)],
                         ["after", "before"], default="october")
sm["w"] = 1.0

series = (sm.groupby(["month", "plan"]).agg(at_risk=("churned", "size"), churned=("churned", "sum"))
          .reset_index())
series["churn_rate"] = series["churned"] / series["at_risk"]
series.to_csv(OUT / "monthly_churn_series.csv", index=False)

sm_oct = sm.copy()
sm_oct.loc[sm_oct["period"] == "october", "period"] = "before"  # sensitivity: baseline from Oct 2025
sm = sm[sm["period"] != "october"]
mon = sm[sm["plan"] == "monthly"].copy()
ann = sm[sm["plan"] == "annual"].copy()


# ---------------------------------------------------------------- tenure-matched comparison
def band_rates(df):
    """Weighted subscriber-months and cancellations per tenure band and period."""
    g = (df.assign(c=df["churned"] * df["w"])
         .groupby(["tenure_band", "period"])[["w", "c"]].sum().unstack("period"))
    return g.reindex(BAND_ORDER)


def compare(df, pool):
    """After churn against before churn reweighted to the group's after tenure mix.

    A tenure band the group never reached before March has no before rate of its
    own; it takes the band rate of `pool` (all monthly subscribers) instead, and
    the share of after weight that needed this is reported.
    """
    a, own, pooled = band_rates(df), band_rates(df), band_rates(pool)
    n_after = a[("w", "after")].fillna(0)
    c_after = a[("c", "after")].fillna(0)
    own_n = own[("w", "before")].fillna(0) if ("w", "before") in own else n_after * 0
    own_c = own[("c", "before")].fillna(0) if ("c", "before") in own else n_after * 0
    use_own = own_n > 0
    rate_b = np.where(use_own, own_c / own_n.where(use_own, 1),
                      pooled[("c", "before")] / pooled[("w", "before")])
    w = n_after / n_after.sum()
    rate_before = float((w * rate_b).sum())
    rate_after = float(c_after.sum() / n_after.sum())
    return {
        "at_risk_after": float(n_after.sum()), "churned_after": float(c_after.sum()),
        "at_risk_before": float(own_n.sum()), "churned_before": float(own_c.sum()),
        "rate_before": rate_before, "rate_after": rate_after,
        "change_pp": (rate_after - rate_before) * 100,
        "change_rel_pct": (rate_after / rate_before - 1) * 100,
        "share_before_pooled": float(w[~use_own].sum()),
    }


def revenue_per_100(rate, price, months):
    """Cumulative revenue from 100 subscribers paying at the start of each month."""
    return 100 * price * sum((1 - rate) ** k for k in range(months))


def breakeven_month(rate_old, rate_new, limit=120):
    """First month where cumulative revenue at the new price falls below the old price."""
    for h in range(1, limit + 1):
        if revenue_per_100(rate_new, NEW_PRICE, h) < revenue_per_100(rate_old, OLD_PRICE, h):
            return h
    return None


GROUPS = [(dim, g) for dim in ["tenure_band", "cohort", "country", "device"]
          for g in sorted(mon[dim].dropna().unique())]
subs_ids = sm["subscription_id"].unique()


def band_churn(df):
    """Crude monthly churn per tenure band, before and after."""
    b = band_rates(df)
    return {per: (b[("c", per)] / b[("w", per)]).to_dict() for per in ["before", "after"]}


def follow_revenue(rates, price, start_month, months):
    """Revenue per 100 subscribers who are `start_month` months in, followed as they age through the bands."""
    alive, total = 100.0, 0.0
    for k in range(months):
        total += alive * price
        alive *= 1 - rates[band_of(start_month + k)]
    return total


START_MONTHS = {"0-2m": 0, "3-5m": 3, "6-11m": 6, "12-23m": 12, "24m+": 24}


def follow_all(bands):
    return {(name, h): follow_revenue(bands["after"], NEW_PRICE, t0, h)
            / follow_revenue(bands["before"], OLD_PRICE, t0, h) * 100
            for name, t0 in START_MONTHS.items() for h in HORIZONS}


def all_results(mon_, ann_):
    """Headline, annual and every group's rise against the rest, for one sample."""
    out = {"monthly": compare(mon_, mon_), "annual": compare(ann_, ann_)}
    out["follow"] = follow_all(band_churn(mon_))
    for dim, g in GROUPS:
        part, rest = mon_[mon_[dim] == g], mon_[mon_[dim] != g]
        out[(dim, g)] = (compare(part, mon_), compare(rest, mon_))
    return out


est = all_results(mon, ann)

# Bootstrap by subscriber: Poisson weights per subscriber keep all of one
# subscriber's months together, so repeat months are not counted as independent.
boot = []
for _ in range(BOOT):
    wmap = pd.Series(rng.poisson(1.0, len(subs_ids)), index=subs_ids)
    mb, ab = mon.assign(w=mon["subscription_id"].map(wmap)), ann.assign(w=ann["subscription_id"].map(wmap))
    boot.append(all_results(mb, ab))


def interval(values):
    lo, hi = np.nanpercentile(values, [2.5, 97.5])
    return float(lo), float(hi)


head, head_ann = est["monthly"], est["annual"]
for key, r in [("monthly", head), ("annual", head_ann)]:
    r["rel_low_pct"], r["rel_high_pct"] = interval([b[key]["change_rel_pct"] for b in boot])
    r["pp_low"], r["pp_high"] = interval([b[key]["change_pp"] for b in boot])
did_pp = head["change_pp"] - head_ann["change_pp"]
did_low, did_high = interval([b["monthly"]["change_pp"] - b["annual"]["change_pp"] for b in boot])
head_oct = compare(sm_oct[sm_oct["plan"] == "monthly"], sm_oct[sm_oct["plan"] == "monthly"])
pd.DataFrame([{"plan": "monthly", "baseline": "Nov 2025-Feb 2026", **head},
              {"plan": "annual", "baseline": "Nov 2025-Feb 2026", **head_ann},
              {"plan": "monthly", "baseline": "Oct 2025-Feb 2026 (sensitivity)", **head_oct}]).to_csv(
    OUT / "headline.csv", index=False)
pd.DataFrame([{"monthly_change_pp": head["change_pp"], "annual_change_pp": head_ann["change_pp"],
               "price_effect_pp": did_pp, "price_effect_low_pp": did_low,
               "price_effect_high_pp": did_high}]).to_csv(OUT / "headline_vs_annual.csv", index=False)

# ---------------------------------------------------------------- groups
seg_rows = []
for k, (dim, g) in enumerate(GROUPS):
    r, o = est[(dim, g)]
    ratio = lambda a, b: (a["rate_after"] / a["rate_before"]) / (b["rate_after"] / b["rate_before"])  # noqa: E731
    lo, hi = interval([(ratio(*b[(dim, g)]) - 1) * 100 for b in boot])
    rel_lo, rel_hi = interval([b[(dim, g)][0]["change_rel_pct"] for b in boot])
    rev = {f"rev_{h}m_new": revenue_per_100(r["rate_after"], NEW_PRICE, h) for h in HORIZONS}
    rev.update({f"rev_{h}m_old": revenue_per_100(r["rate_before"], OLD_PRICE, h) for h in HORIZONS})
    seg_rows.append({
        "dimension": dim, "group": g, **r, "rel_low_pct": rel_lo, "rel_high_pct": rel_hi,
        "rise_vs_rest_pct": (ratio(r, o) - 1) * 100,
        "rise_vs_rest_low_pct": lo, "rise_vs_rest_high_pct": hi,
        **rev,
        "breakeven_month": breakeven_month(r["rate_before"], r["rate_after"]),
    })
seg = pd.DataFrame(seg_rows)
# Revenue at 12 months per 100 at $10, with a bootstrap range; for country, device and
# cohort the group's churn is held at its after level, which is a mix of tenures.
r12 = []
for dim, g in GROUPS:
    vals = [revenue_per_100(b[(dim, g)][0]["rate_after"], NEW_PRICE, 12)
            / revenue_per_100(b[(dim, g)][0]["rate_before"], OLD_PRICE, 12) * 100 for b in boot]
    r12.append(interval(vals))
seg["rev12_index"] = seg["rev_12m_new"] / seg["rev_12m_old"] * 100
seg["rev12_low"], seg["rev12_high"] = [x[0] for x in r12], [x[1] for x in r12]
seg["rev12_call"] = np.select([seg["rev12_high"] < 100, seg["rev12_low"] > 100],
                              ["$12 earns less", "$12 earns more"], default="too close to call")

# Tenure: follow subscribers as they age into later bands (replaces holding churn fixed).
fol = est["follow"]
follow = pd.DataFrame([{
    "starting_tenure": name, "horizon_months": h, "projection": h > len(AFTER),
    "revenue_index_12_vs_10": fol[(name, h)],
    "low": interval([b["follow"][(name, h)] for b in boot])[0],
    "high": interval([b["follow"][(name, h)] for b in boot])[1],
} for name in START_MONTHS for h in HORIZONS])
follow["call"] = np.select([follow["high"] < 100, follow["low"] > 100],
                           ["$12 earns less", "$12 earns more"], default="too close to call")
follow.to_csv(OUT / "revenue_by_starting_tenure.csv", index=False)
seg["differs"] = np.select(
    [seg["rise_vs_rest_low_pct"] > 0, seg["rise_vs_rest_high_pct"] < 0],
    ["rose more than the rest", "rose less than the rest"], default="no clear difference")
print(f" groups tested against the rest: {len(GROUPS)}; ranges are 95% bootstrap ranges "
      f"over {BOOT} resamples of subscribers, not adjusted for testing {len(GROUPS)} groups")
seg["breakeven_month"] = seg["breakeven_month"].astype("Int64")
seg.to_csv(OUT / "groups.csv", index=False)

for dim in ["tenure_band", "cohort", "country", "device"]:
    d = seg[seg["dimension"] == dim]
    r = checks.parts_sum_to_total(d["at_risk_after"], head["at_risk_after"])
    print(f" {dim} at risk after:", r["summary"])

# Revenue, overall
rev = pd.DataFrame([{
    "horizon_months": h,
    "projection": h > len(AFTER),
    "revenue_per_100_at_12": revenue_per_100(head["rate_after"], NEW_PRICE, h),
    "revenue_per_100_at_10": revenue_per_100(head["rate_before"], OLD_PRICE, h),
} for h in HORIZONS])
rev["difference_pct"] = (rev["revenue_per_100_at_12"] / rev["revenue_per_100_at_10"] - 1) * 100
rev.to_csv(OUT / "revenue_horizons.csv", index=False)
be_all = breakeven_month(head["rate_before"], head["rate_after"])
pd.DataFrame([{"breakeven_month_overall": be_all}]).to_csv(OUT / "breakeven.csv", index=False)

# Realised revenue, monthly plan
p = pay.merge(subs[["subscription_id", "plan"]], on="subscription_id", how="left")
p["month"] = p["payment_date"].dt.to_period("M")
realised = (p[(p["plan"] == "monthly") & p["month"].isin(list(BEFORE) + list(AFTER))]
            .groupby("month")["amount_usd"].sum().rename("revenue").reset_index())
realised.to_csv(OUT / "monthly_plan_revenue.csv", index=False)

# ---------------------------------------------------------------- payment-based churn
# Independent of how end dates are recorded, and available from January 2025, so it
# shows the seasonal shape. A monthly payment counts as the last one if no further
# payment follows within 40 days; only payments with 40 days of data after them count.
mp = p[p["plan"] == "monthly"].sort_values(["subscription_id", "payment_date"]).copy()
mp["next_payment"] = mp.groupby("subscription_id")["payment_date"].shift(-1)
mp = mp[mp["payment_date"] + pd.Timedelta(days=40) <= AS_OF]
mp["lapsed"] = mp["next_payment"].isna() | (mp["next_payment"] - mp["payment_date"] > pd.Timedelta(days=40))
pay_churn = mp.groupby("month").agg(payments=("lapsed", "size"), lapsed=("lapsed", "sum")).reset_index()
pay_churn["lapse_rate"] = pay_churn["lapsed"] / pay_churn["payments"]
pay_churn.to_csv(OUT / "payment_lapse_series.csv", index=False)


def lapse(months):
    d = pay_churn[pay_churn["month"].isin(months)]
    return d["lapsed"].sum() / d["payments"].sum()


# August and September 2025 hold a burst of payment stops with no matching end date
# (the same period end dates changed recording), so they are left out of lapse baselines.
lapse_tbl = pd.DataFrame([
    {"comparison": "2025 shape: Mar-Jul 2025 vs Jan-Feb 2025",
     "before": lapse(pd.period_range("2025-01", "2025-02", freq="M")),
     "after": lapse(pd.period_range("2025-03", "2025-07", freq="M"))},
    {"comparison": "price, similar season: Mar-Aug 2026 vs Mar-Jul 2025",
     "before": lapse(pd.period_range("2025-03", "2025-07", freq="M")), "after": lapse(AFTER)},
    {"comparison": "price: Mar-Aug 2026 vs Nov 2025-Feb 2026",
     "before": lapse(BEFORE), "after": lapse(AFTER)},
])
lapse_tbl["change_pp"] = (lapse_tbl["after"] - lapse_tbl["before"]) * 100
lapse_tbl["change_rel_pct"] = (lapse_tbl["after"] / lapse_tbl["before"] - 1) * 100
lapse_tbl.to_csv(OUT / "payment_lapse_comparison.csv", index=False)

# ---------------------------------------------------------------- charts
ms_ = series[series["plan"] == "monthly"]
an_ = series[series["plan"] == "annual"]
fig = charts.line(
    [str(m) for m in ms_["month"]],
    {"Monthly plan": (ms_["churn_rate"] * 100).round(2).tolist(),
     "Annual plan": (an_["churn_rate"] * 100).round(2).tolist()},
    title="Monthly-plan churn more than doubled after the March increase; annual barely moved",
    highlight="Monthly plan", ylabel="Cancelled in month, % of subscribers", source=SOURCE)
fig.axes[0].axvline("2026-03", color=charts.GRAY, linestyle=":")
fig.axes[0].tick_params(axis="x", rotation=45)
charts.save(fig, CH / "churn_by_month.png")

t = seg[seg["dimension"] == "tenure_band"].set_index("group").reindex(BAND_ORDER)
# Bars show extra cancellations per 1,000 subscribers a month (percentage points x 10),
# so small changes stay readable with whole-number labels.
fig = charts.bar(
    BAND_ORDER, (t["change_pp"] * 10).round(0).tolist(),
    title="Churn rose least among subscribers of 12 to 23 months",
    highlight=["12-23m"],
    ylabel="Extra cancellations per 1,000 subscribers a month", source=SOURCE)
charts.save(fig, CH / "churn_change_by_tenure.png")

c = seg[seg["dimension"] == "cohort"].sort_values("change_pp", ascending=False)
fig = charts.bar(
    c["group"].tolist(), (c["change_pp"] * 10).round(0).tolist(), horizontal=True,
    title="Subscribers who joined at \\$12 cancel faster than earlier joiners did at the same tenure",
    highlight=c.loc[c["differs"] == "rose more than the rest", "group"].tolist(),
    ylabel=None, source=SOURCE + "; extra cancellations per 1,000 subscribers a month against Nov 2025-Feb 2026 "
    "at the same tenure; joiners after the increase and the Sep 2025 cohort are compared mostly "
    "with all subscribers' rates")
charts.save(fig, CH / "churn_change_by_cohort.png")

# Tenure only: countries and devices show no clear difference in the churn rise.
f12 = follow[follow["horizon_months"] == 12].set_index("starting_tenure").reindex(BAND_ORDER)
fig = charts.bar(
    BAND_ORDER, f12["revenue_index_12_vs_10"].round(0).tolist(),
    title="Over the next 12 months, \\$12 earns less than \\$10 only from brand-new subscribers",
    highlight=f12.index[f12["call"] == "$12 earns less"].tolist(),
    ylabel="12-month revenue at \\$12 per \\$100 at \\$10",
    source=SOURCE + "; by tenure at the start, following subscribers as they age; projection beyond 6 months")
fig.axes[0].axhline(100, color=charts.GRAY, linestyle=":")
charts.save(fig, CH / "revenue_12m_by_group.png")

# ---------------------------------------------------------------- headlines
print("\nHEADLINES")
print(f"Monthly plan churn: {head['rate_after']:.2%} a month Mar-Aug 2026 vs {head['rate_before']:.2%} "
      f"Nov 2025-Feb 2026 (tenure-matched): {head['change_pp']:+.2f} pp, {head['change_rel_pct']:+.0f}% "
      f"relative (approx {head['rel_low_pct']:+.0f}% to {head['rel_high_pct']:+.0f}%)")
print(f"Annual plan churn: {head_ann['rate_after']:.2%} vs {head_ann['rate_before']:.2%}: "
      f"{head_ann['change_pp']:+.2f} pp, {head_ann['change_rel_pct']:+.0f}% relative "
      f"(approx {head_ann['rel_low_pct']:+.0f}% to {head_ann['rel_high_pct']:+.0f}%)")
print(f"Price effect (monthly change minus annual change): {did_pp:+.2f} pp "
      f"(range {did_low:+.2f} to {did_high:+.2f} pp)")
print(f"Sensitivity, baseline from Oct 2025: {head_oct['rate_before']:.2%} -> {head_oct['rate_after']:.2%} "
      f"({head_oct['change_pp']:+.2f} pp, {head_oct['change_rel_pct']:+.0f}%)")
for _, r in lapse_tbl.iterrows():
    print(f"Payment lapse rate, {r['comparison']}: {r['before']:.2%} -> {r['after']:.2%} "
          f"({r['change_pp']:+.2f} pp, {r['change_rel_pct']:+.0f}%)")
for _, r in rev.iterrows():
    tag = " (projection)" if r["projection"] else ""
    print(f"Revenue per 100 subscribers over {r['horizon_months']} months{tag}: "
          f"${r['revenue_per_100_at_12']:,.0f} at $12 vs ${r['revenue_per_100_at_10']:,.0f} at $10 "
          f"({r['difference_pct']:+.0f}%)")
print(f"$12 stops out-earning $10 after month {be_all}")
print("\nREVENUE BY STARTING TENURE (following subscribers as they age)")
for _, r in follow.iterrows():
    print(f" {r['starting_tenure']:>6} over {r['horizon_months']:>2}m: {r['revenue_index_12_vs_10']:.0f} at $12 per "
          f"100 at $10 (range {r['low']:.0f}-{r['high']:.0f}) {r['call']}")
print("\nGROUPS (tenure-matched; rise vs everyone else)")
for _, r in seg.iterrows():
    print(f" {r['dimension']:>11} | {r['group']:<27} {r['rate_before']:.2%} -> {r['rate_after']:.2%} "
          f"({r['change_pp']:+.2f} pp, {r['change_rel_pct']:+.0f}%); vs rest {r['rise_vs_rest_pct']:+.0f}% "
          f"[{r['rise_vs_rest_low_pct']:+.0f}%, {r['rise_vs_rest_high_pct']:+.0f}%] {r['differs']}; "
          f"12m rev index {r['rev12_index']:.0f} ({r['rev12_low']:.0f}-{r['rev12_high']:.0f}) {r['rev12_call']}; breakeven {'none' if pd.isna(r['breakeven_month']) else 'month ' + str(r['breakeven_month'])}; "
          f"pooled before {r['share_before_pooled']:.0%}; n_after={int(r['at_risk_after']):,}")
