"""Did the March 2026 price increase hurt retention, and for whom?

Run from the repo root:  poetry run python outputs/2026-11-07_march-price-retention-v3/analysis.py
Reads data/*.csv (never writes there). Writes result tables to ./data and charts to ./charts
inside this run folder. Prints aggregates only.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.cwd()   # run from the repo root, so a copy of this script in rerun/ reads the same data
assert (ROOT / "data" / "subscriptions.csv").exists(), "Run from the repo root: poetry run python outputs/<run>/analysis.py"
sys.path.insert(0, str(ROOT))
from helpers import charts, checks  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
CH = RUN / "charts"
OUT.mkdir(exist_ok=True)
CH.mkdir(exist_ok=True)

AS_OF = pd.Timestamp("2026-09-24")          # analysis date from AGENTS.md, never the real date
CHANGE = pd.Period("2026-03", "M")         # monthly price $10 -> $12
BASE_MONTHS = pd.period_range("2025-10", "2026-02", freq="M")   # end dates recorded the same way
POST_MONTHS = pd.period_range("2026-03", "2026-08", freq="M")   # last closed month is August 2026
SEASON_MONTHS = pd.period_range("2025-03", "2025-08", freq="M") # same season a year earlier, recorded differently
ALL_MONTHS = pd.period_range("2025-01", "2026-08", freq="M")    # payments start 2025-01
OLD_PRICE, NEW_PRICE = 10.0, 12.0
TENURE_BANDS = [(-1, 2, "0-2 months"), (2, 5, "3-5 months"), (5, 11, "6-11 months"), (11, 10_000, "12+ months")]


def save(df, name):
    df.to_csv(OUT / f"{name}.csv", index=False)
    return df


def say(text):
    print(text)


# ---------------------------------------------------------------- 1. Load
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
users = pd.read_csv(ROOT / "data/users.csv", parse_dates=["signup_date"])
trials = pd.read_csv(ROOT / "data/trials.csv", parse_dates=["started_at", "ends_at", "outcome_at"])

say("== Checks on inputs")
for df, col in [(subs, "start_date"), (pays, "payment_date")]:
    say("  " + checks.date_boundaries(df, col)["summary"])
say("  " + checks.join_fan_out(subs, users, "user_id")["summary"])

# Compare on dates, not timestamps (timestamps everywhere quirk).
subs["start_day"] = subs["start_date"].dt.normalize()
subs["end_day"] = subs["end_date"].dt.normalize()

# ---------------------------------------------------------------- 2. Population and exclusions
excl = []
n0 = len(subs)
paid = subs[subs["plan"] != "free"].copy()
excl.append({"step": "free plans (never end; quirk)", "rows_removed": n0 - len(paid), "rows_left": len(paid)})
n1 = len(paid)
paid = paid[paid["start_day"] <= AS_OF]
excl.append({"step": "starts after 2026-09-24 (scheduled starts; quirk)", "rows_removed": n1 - len(paid), "rows_left": len(paid)})

pay_agg = pays.groupby("subscription_id").agg(
    n_payments=("payment_id", "size"),
    last_payment=("payment_date", "max"),
    main_method=("method", lambda m: m.value_counts().index[0]),
).reset_index()
say("  " + checks.join_fan_out(paid, pay_agg, "subscription_id")["summary"])
paid = paid.merge(pay_agg, on="subscription_id", how="left")
paid["n_payments"] = paid["n_payments"].fillna(0)
# A subscription that never paid but was live while payments are recorded (2025 onward) is not a paying
# subscriber. Subscriptions that ended before February 2025 can have no payments because the export starts
# on 2025-01-01 and their last payment fell in 2024.
live_2025 = paid["end_day"].isna() | (paid["end_day"] >= pd.Timestamp("2025-02-01"))
never_paid = (paid["n_payments"] == 0) & live_2025 & (paid["start_day"] < pd.Timestamp("2026-09-01"))
excl.append({"step": "never paid while payments were recorded (not paying subscribers)",
             "rows_removed": int(never_paid.sum()), "rows_left": int(len(paid) - never_paid.sum())})
never_paid_by_cohort = (paid[never_paid].groupby(paid["start_day"].dt.to_period("M").astype(str))
                        .size().rename("never_paid").reset_index().rename(columns={"start_day": "start_month"}))
save(never_paid_by_cohort, "never_paid_by_start_month")
paid = paid[~never_paid].copy()
paid = paid.merge(users[["user_id", "country", "device_type", "signup_date"]], on="user_id", how="left")
paid["main_method"] = paid["main_method"].fillna("none recorded")
# Is payment method a customer attribute? If one subscription pays with several methods, it is not.
meth = pays.groupby("subscription_id")["method"].agg(n_payments="size", n_methods="nunique").reset_index()
meth["payments_band"] = pd.cut(meth["n_payments"], [0, 1, 3, 6, 12, 1000], labels=["1", "2-3", "4-6", "7-12", "13+"])
meth_chk = meth.groupby("payments_band", observed=True).agg(subscriptions=("subscription_id", "size"),
                                                          mean_distinct_methods=("n_methods", "mean")).reset_index()
save(meth_chk, "payment_method_per_subscription_check")
say(f"  Payment method: subscriptions with 13+ payments used {meth_chk.mean_distinct_methods.iloc[-1]:.1f} methods on "
    f"average, so method is drawn per payment, not a customer attribute; not used as a segment.")
paid["start_month"] = paid["start_day"].dt.to_period("M")
paid["cohort"] = np.where(paid["start_month"] < CHANGE, "existing (started before Mar 2026)",
                          "new (started Mar 2026 or later)")
paid["sept_2025_cohort"] = paid["start_month"] == pd.Period("2025-09", "M")
save(pd.DataFrame(excl), "exclusions")
say(f"  Paid subscriptions kept: {len(paid):,} (monthly {int((paid.plan == 'monthly').sum()):,}, "
    f"annual {int((paid.plan == 'annual').sum()):,})")

# ---------------------------------------------------------------- 3. Recording of end dates (corrections.md)
ended = paid[paid["end_day"].notna() & (paid["end_day"] <= AS_OF) & (paid["plan"] == "monthly")].copy()
ended = ended[ended["end_day"] >= pd.Timestamp("2025-02-01")]
ended["end_has_time"] = ended["end_date"] != ended["end_day"]
ended["days_last_pay_to_end"] = (ended["end_day"] - ended["last_payment"].dt.normalize()).dt.days
stab = []
for col in ["end_has_time", "days_last_pay_to_end"]:
    r = checks.stable_over_time(ended.dropna(subset=[col]), "end_day", col)
    say("  " + r["summary"])
    stab.append({"field": col, "first_break": r["first_break"], "breaks": ";".join(r["breaks"]), "summary": r["summary"]})
    # Within the chosen baseline and after-period only
    sub = ended[ended["end_day"] >= pd.Timestamp("2025-10-01")].dropna(subset=[col])
    r2 = checks.stable_over_time(sub, "end_day", col)
    say("  (Oct 2025 onward) " + r2["summary"])
    stab.append({"field": col + " (Oct 2025 onward)", "first_break": r2["first_break"],
                 "breaks": ";".join(r2["breaks"]), "summary": r2["summary"]})
# Recording or behaviour? Rerun the April 2026 check on subsets whose mix is steady. A step in every subset
# at once points to logging; a step only where people react to the price points to behaviour.
ended["tenure_at_end_m"] = ((ended["end_day"] - ended["start_day"]).dt.days // 30.44).astype(int)
subsets = {
    "started before Sep 2025 (no spike, no new subscribers)": ended["start_day"] < pd.Timestamp("2025-09-01"),
    "September 2025 cohort only": ended["sept_2025_cohort"],
    "tenure at end 12+ months": ended["tenure_at_end_m"] >= 12,
    "tenure at end under 6 months": ended["tenure_at_end_m"] < 6,
}
for name, mask in subsets.items():
    for col in ["end_has_time", "days_last_pay_to_end"]:
        sub = ended[mask & (ended["end_day"] >= pd.Timestamp("2025-10-01"))].dropna(subset=[col])
        r = checks.stable_over_time(sub, "end_day", col)
        say(f"  [{name}] " + r["summary"])
        stab.append({"field": f"{col} [{name}], Oct 2025 onward", "first_break": r["first_break"],
                     "breaks": ";".join(r["breaks"]), "summary": r["summary"]})
# Pre-October 2025: end date is a fixed 30 days after the last payment, with no time of day.
pre = ended[ended["end_day"] < pd.Timestamp("2025-10-01")]
stab.append({"field": "share of ends exactly 30 days after the last payment, Feb-Sep 2025",
             "first_break": None, "breaks": "",
             "summary": f"{(pre['days_last_pay_to_end'] == 30).mean():.0%} of {len(pre):,} ends"})
post_ = ended[ended["end_day"] >= pd.Timestamp("2025-10-01")]
stab.append({"field": "share of ends exactly 30 days after the last payment, Oct 2025 onward",
             "first_break": None, "breaks": "",
             "summary": f"{(post_['days_last_pay_to_end'] == 30).mean():.0%} of {len(post_):,} ends"})
save(pd.DataFrame(stab), "end_date_recording_checks")
rec = ended.groupby(ended["end_day"].dt.to_period("M")).agg(
    ended=("subscription_id", "size"),
    share_with_time_of_day=("end_has_time", "mean"),
    median_days_last_payment_to_end=("days_last_pay_to_end", "median"),
).reset_index().rename(columns={"end_day": "end_month"})
rec["end_month"] = rec["end_month"].astype(str)
save(rec, "end_date_recording_by_month")

# ---------------------------------------------------------------- 4. Subscriber-months at risk
# At risk in month M: started before M began and had not ended before M began. Churned in M: ended in M.
rows = []
for m in ALL_MONTHS:
    ms, me = m.start_time, m.end_time.normalize()
    at = paid[(paid["start_day"] < ms) & (paid["end_day"].isna() | (paid["end_day"] >= ms))]
    tenure = ((ms - at["start_day"]).dt.days // 30.44).astype(int)
    d = at[["subscription_id", "plan", "country", "device_type", "main_method", "cohort", "sept_2025_cohort"]].copy()
    d["month"] = m
    d["tenure_m"] = tenure.values
    d["churned"] = (at["end_day"] <= me).values
    rows.append(d)
sm = pd.concat(rows, ignore_index=True)
sm["tenure_band"] = pd.cut(sm["tenure_m"], [b[0] for b in TENURE_BANDS] + [TENURE_BANDS[-1][1]],
                           labels=[b[2] for b in TENURE_BANDS])
sm["period"] = np.select([sm["month"].isin(BASE_MONTHS), sm["month"].isin(POST_MONTHS),
                          sm["month"].isin(SEASON_MONTHS)],
                         ["baseline Oct 2025-Feb 2026", "after Mar-Aug 2026", "same season Mar-Aug 2025"], "other")
closed = checks.matured_only(pd.DataFrame({"month_end": [m.end_time for m in ALL_MONTHS]}), "month_end", AS_OF)
say("  " + closed["summary"])
say(f"  Subscriber-months built: {len(sm):,}")

BASE, POST, SEASON = "baseline Oct 2025-Feb 2026", "after Mar-Aug 2026", "same season Mar-Aug 2025"


def rate_table(df, keys):
    g = df.groupby(keys, observed=True).agg(sub_months=("churned", "size"), churned=("churned", "sum")).reset_index()
    g["churn_rate"] = g["churned"] / g["sub_months"]
    return g


def two_prop(r1, n1, r2, n2):
    se = np.sqrt(r1 * (1 - r1) / n1 + r2 * (1 - r2) / n2)
    return se


def compare(df, base_label=BASE, post_label=POST, std_weights=None):
    """Baseline vs after churn for df, raw and at the same tenure (after rates on baseline tenure mix)."""
    b = df[df["period"] == base_label]
    a = df[df["period"] == post_label]
    rb, ra = b["churned"].mean(), a["churned"].mean()
    nb, na = len(b), len(a)
    bb = rate_table(b, ["tenure_band"]).set_index("tenure_band")
    ab = rate_table(a, ["tenure_band"]).set_index("tenure_band")
    w = std_weights if std_weights is not None else bb["sub_months"] / bb["sub_months"].sum()
    common = [t for t in w.index if t in bb.index and t in ab.index]
    w = w.loc[common] / w.loc[common].sum()
    adj_b = float((bb.loc[common, "churn_rate"] * w).sum())
    adj_a = float((ab.loc[common, "churn_rate"] * w).sum())
    var = (w ** 2 * (bb.loc[common, "churn_rate"] * (1 - bb.loc[common, "churn_rate"]) / bb.loc[common, "sub_months"]
                     + ab.loc[common, "churn_rate"] * (1 - ab.loc[common, "churn_rate"]) / ab.loc[common, "sub_months"])).sum()
    se_adj = float(np.sqrt(var))
    # Expected after-period churners if each tenure band had kept its baseline rate.
    exp = float((ab.loc[common, "sub_months"] * bb.loc[common, "churn_rate"]).sum())
    act = float(ab.loc[common, "churned"].sum())
    return {
        "baseline_sub_months": nb, "after_sub_months": na,
        "baseline_churn": rb, "after_churn": ra,
        "change_pp": (ra - rb) * 100, "change_rel_pct": (ra / rb - 1) * 100 if rb else np.nan,
        "baseline_churn_same_tenure": adj_b, "after_churn_same_tenure": adj_a,
        "change_same_tenure_pp": (adj_a - adj_b) * 100,
        "change_same_tenure_rel_pct": (adj_a / adj_b - 1) * 100 if adj_b else np.nan,
        "ci95_low_pp": (adj_a - adj_b - 1.96 * se_adj) * 100, "ci95_high_pp": (adj_a - adj_b + 1.96 * se_adj) * 100,
        "se_same_tenure_pp": se_adj * 100,
        "after_churners": act, "expected_churners_at_baseline_rates": exp, "excess_churners": act - exp,
    }


# ---------------------------------------------------------------- 5. Headline
say("\n== Headline: monthly plan churn per month")
mon = sm[sm["plan"] == "monthly"]
ann = sm[sm["plan"] == "annual"]
head = []
for plan, df in [("monthly", mon), ("annual", ann)]:
    r = compare(df)
    head.append({"plan": plan, "baseline": BASE, **r})
    if plan == "monthly":
        r_season = compare(df, base_label=SEASON)
        head.append({"plan": plan, "baseline": SEASON + " (end dates recorded differently)", **r_season})
        r_nosept = compare(df[~df["sept_2025_cohort"]])
        head.append({"plan": plan, "baseline": BASE + ", without the Sept 2025 cohort", **r_nosept})
headline = save(pd.DataFrame(head), "headline_churn")
hm = headline.iloc[0]
say(f"  Monthly churn: {hm.baseline_churn:.2%} a month ({BASE}) -> {hm.after_churn:.2%} ({POST}): "
    f"{hm.change_pp:+.1f} pp, {hm.change_rel_pct:+.0f}% relative.")
say(f"  Same tenure mix: {hm.baseline_churn_same_tenure:.2%} -> {hm.after_churn_same_tenure:.2%}: "
    f"{hm.change_same_tenure_pp:+.1f} pp (95% {hm.ci95_low_pp:+.1f} to {hm.ci95_high_pp:+.1f}), "
    f"{hm.change_same_tenure_rel_pct:+.0f}% relative.")
for _, r in headline.iloc[1:].iterrows():
    say(f"  {r.plan} vs {r.baseline}: {r.baseline_churn:.2%} -> {r.after_churn:.2%}, same tenure "
        f"{r.change_same_tenure_pp:+.1f} pp ({r.change_same_tenure_rel_pct:+.0f}% relative)")

# Monthly series, both plans
series = rate_table(sm[sm["plan"].isin(["monthly", "annual"])], ["plan", "month"])
series["month"] = series["month"].astype(str)
save(series, "churn_by_month")
piv = series.pivot(index="month", columns="plan", values="churn_rate") * 100
fig = charts.line(pd.to_datetime(piv.index), {"Monthly plan": piv["monthly"], "Annual plan": piv["annual"]},
                  "Monthly-plan churn more than doubled from March 2026; annual-plan churn did not move",
                  highlight="Monthly plan", ylabel="Churn, % of subscribers per month",
                  source="Source: subscriptions, payments; paid subscribers active at month start")
charts.save(fig, CH / "churn_by_month.png")

by_tenure = rate_table(mon[mon["period"].isin([BASE, POST, SEASON])], ["period", "tenure_band"])
save(by_tenure, "monthly_churn_by_tenure")

# ---------------------------------------------------------------- 6. Has the rate held? (existing subscribers)
say("\n== Churn by month since the change, monthly subscribers who started before March 2026")
ex = mon[(mon["cohort"].str.startswith("existing")) & (mon["month"] >= CHANGE)]
held = rate_table(ex, ["month", "tenure_band"])
held["month"] = held["month"].astype(str)
save(held, "existing_churn_by_month_since_change_tenure")
held_all = rate_table(ex, ["month"])
held_all["months_since_change"] = range(len(held_all))
held_all["month"] = held_all["month"].astype(str)
base_ex = mon[(mon["period"] == BASE)]["churned"].mean()
held_all["baseline_churn_all_tenures"] = base_ex
# Excess over baseline at the same tenure, month by month: actual churners / churners expected at baseline
# band rates. Existing subscribers age through the bands, so raw rates alone would drift down.
bb_rates = rate_table(mon[mon.period == BASE], ["tenure_band"]).set_index("tenure_band")["churn_rate"]
exp_m = ex.groupby("month")["tenure_band"].apply(lambda b: b.map(bb_rates).astype(float).sum()).values
held_all["expected_at_baseline_rates"] = exp_m
held_all["ratio_to_baseline_same_tenure"] = held_all["churned"] / held_all["expected_at_baseline_rates"]
# March is a transition month (cancellations set before the first $12 charge), so the trend starts in April.
r_ = held_all.set_index("month")["ratio_to_baseline_same_tenure"]
early, late = r_.loc["2026-04":"2026-05"].mean(), r_.loc["2026-07":"2026-08"].mean()
trend = "steady" if abs(late - early) < 0.15 * early else ("fading" if late < early else "still rising")
held_all["trend_label"] = trend
held_all["trend_rule"] = "Apr-May vs Jul-Aug 2026 ratio to baseline at same tenure; within 15% = steady"
save(held_all, "existing_churn_by_month_since_change")
say(f"  Churn as a multiple of baseline at the same tenure: Apr-May 2026 {early:.2f}x, Jul-Aug 2026 {late:.2f}x: {trend}.")

# Subscriptions that end in the month they start are never at risk above (they start after the month began).
# Show them separately, by start period, so early losses of new subscribers are not hidden.
mstart = paid[(paid.plan == "monthly")].copy()
mstart["ended_in_start_month"] = mstart["end_day"].notna() & (mstart["end_day"].dt.to_period("M") == mstart["start_month"])
mstart["period"] = np.select([mstart.start_month.isin(BASE_MONTHS), mstart.start_month.isin(POST_MONTHS)], [BASE, POST], "other")
same_month = mstart[mstart.period != "other"].groupby("period").agg(
    starts=("subscription_id", "size"), ended_in_start_month=("ended_in_start_month", "sum")).reset_index()
same_month["share"] = same_month["ended_in_start_month"] / same_month["starts"]
save(same_month, "new_starts_ended_in_start_month")
say("  Ended in their start month (not in the churn rates): " + "; ".join(
    f"{r.period}: {r.ended_in_start_month:,} of {r.starts:,}" for r in same_month.itertuples()))

# ---------------------------------------------------------------- 7. Segments
say("\n== Segments (monthly plan, same-tenure change in pp, baseline -> after)")
seg_rows = []
SEG_DIMS = ["tenure_band", "cohort", "country", "device_type"]
mb = mon[mon["period"].isin([BASE, POST])]
overall = compare(mon)
w_all = rate_table(mb[mb["period"] == BASE], ["tenure_band"]).set_index("tenure_band")["sub_months"]
w_all = w_all / w_all.sum()
for dim in SEG_DIMS:
    for val, g in mb.groupby(dim, observed=True):
        rest = mb[mb[dim] != val]
        if dim == "tenure_band":
            # Within one band tenure is already held; compare raw rates.
            b, a = g[g.period == BASE].churned, g[g.period == POST].churned
            rb_, ra_ = b.mean(), a.mean()
            r = {"baseline_sub_months": len(b), "after_sub_months": len(a), "baseline_churn": rb_, "after_churn": ra_,
                 "change_pp": (ra_ - rb_) * 100, "change_rel_pct": (ra_ / rb_ - 1) * 100,
                 "baseline_churn_same_tenure": rb_, "after_churn_same_tenure": ra_,
                 "change_same_tenure_pp": (ra_ - rb_) * 100, "change_same_tenure_rel_pct": (ra_ / rb_ - 1) * 100,
                 "se_same_tenure_pp": two_prop(rb_, len(b), ra_, len(a)) * 100,
                 "after_churners": a.sum(), "expected_churners_at_baseline_rates": rb_ * len(a),
                 "excess_churners": a.sum() - rb_ * len(a)}
            b2, a2 = rest[rest.period == BASE].churned, rest[rest.period == POST].churned
            rest_change = (a2.mean() - b2.mean()) * 100
            rest_se = two_prop(b2.mean(), len(b2), a2.mean(), len(a2)) * 100
        elif dim == "cohort" and str(val).startswith("new"):
            # New subscribers have no baseline months; compare with baseline subscribers at the same tenure.
            post_g = g[g.period == POST]
            bands = post_g["tenure_band"].value_counts(normalize=True)
            r = compare(pd.concat([mb[mb.period == BASE], post_g]), std_weights=bands)
            rest_r = compare(pd.concat([mb[mb.period == BASE], rest[rest.period == POST]]), std_weights=bands)
            rest_change, rest_se = rest_r["change_same_tenure_pp"], rest_r["se_same_tenure_pp"]
        else:
            r = compare(g, std_weights=w_all)
            rest_r = compare(rest, std_weights=w_all)
            rest_change, rest_se = rest_r["change_same_tenure_pp"], rest_r["se_same_tenure_pp"]
        if "ci95_low_pp" not in r:
            r["ci95_low_pp"] = r["change_same_tenure_pp"] - 1.96 * r["se_same_tenure_pp"]
            r["ci95_high_pp"] = r["change_same_tenure_pp"] + 1.96 * r["se_same_tenure_pp"]
        z = (r["change_same_tenure_pp"] - rest_change) / np.sqrt(r["se_same_tenure_pp"] ** 2 + rest_se ** 2)
        stands = "larger rise than the rest" if z > 1.96 else ("smaller rise than the rest" if z < -1.96 else "in line with the rest")
        seg_rows.append({"dimension": dim, "group": str(val), **r, "rest_change_same_tenure_pp": rest_change,
                         "z_vs_rest": z, "stands_out": stands})
seg = pd.DataFrame(seg_rows)
# Existing and new are each other's "rest"; new has no baseline months, so use each one's own same-tenure change.
ci = seg.index[seg.dimension == "cohort"]
if len(ci) == 2:
    a_, b_ = ci
    for i, j in [(a_, b_), (b_, a_)]:
        seg.loc[i, "rest_change_same_tenure_pp"] = seg.loc[j, "change_same_tenure_pp"]
        z = (seg.loc[i, "change_same_tenure_pp"] - seg.loc[j, "change_same_tenure_pp"]) / np.sqrt(
            seg.loc[i, "se_same_tenure_pp"] ** 2 + seg.loc[j, "se_same_tenure_pp"] ** 2)
        seg.loc[i, "z_vs_rest"] = z
        seg.loc[i, "stands_out"] = ("larger rise than the rest" if z > 1.96 else
                                    "smaller rise than the rest" if z < -1.96 else "in line with the rest")
# Sensitivity: new subscribers against a baseline without the September 2025 spike cohort.
post_new = mb[(mb.period == POST) & mb.cohort.str.startswith("new")]
r_ns = compare(pd.concat([mb[(mb.period == BASE) & ~mb.sept_2025_cohort], post_new]),
               std_weights=post_new["tenure_band"].value_counts(normalize=True))
seg = pd.concat([seg, pd.DataFrame([{"dimension": "cohort (sensitivity)",
                                     "group": "new, baseline without Sept 2025 cohort", **r_ns,
                                     "stands_out": "not tested (sensitivity)"}])], ignore_index=True)
seg = save(seg, "segments_churn_change")
for _, r in seg.iterrows():
    say(f"  {r.dimension:12s} {r.group:38s} {r.baseline_churn_same_tenure:6.2%} -> {r.after_churn_same_tenure:6.2%} "
        f"{r.change_same_tenure_pp:+5.1f} pp (95% {r.ci95_low_pp:+.1f} to {r.ci95_high_pp:+.1f})  "
        f"rest {r.rest_change_same_tenure_pp:+5.1f} pp  {r.stands_out}")
# Parts sum to totals: each dimension's subscriber-months and churners add back to the whole.
for dim in SEG_DIMS:
    s_ = seg[seg.dimension == dim]
    c1 = checks.parts_sum_to_total(s_["after_sub_months"], overall["after_sub_months"])
    c2 = checks.parts_sum_to_total(s_["after_churners"], overall["after_churners"])
    say(f"  parts {dim}: " + c1["summary"] + " Churners: " + c2["summary"])

for dim, title in [("country", "Churn rose in every region, least in the US"),
                   ("device_type", "Churn rose on every device, most on Web and least on iOS"),
                   ("tenure_band", "Churn rose at every tenure, most in the first months")]:
    s_ = seg[seg.dimension == dim]
    hi = s_.loc[s_["stands_out"] == "larger rise than the rest", "group"].tolist()
    fig = charts.bar(s_["group"], s_["change_same_tenure_pp"] * 10, title, highlight=hi,
                     ylabel="Rise in churn, extra cancellations per 1,000 subscribers a month",
                     source="Same tenure, Mar-Aug 2026 vs Oct 2025-Feb 2026; highlighted = differs from the rest beyond noise")
    charts.save(fig, CH / f"churn_rise_by_{dim}.png")

# ---------------------------------------------------------------- 8. Money at stake
say("\n== Money at stake (monthly plan)")
pays["month"] = pays["payment_date"].dt.to_period("M")
mp = pays.merge(paid[["subscription_id", "plan", "country", "device_type", "main_method", "cohort"]],
                on="subscription_id", how="inner")
mp = mp[(mp["plan"] == "monthly") & mp["month"].isin(POST_MONTHS)]


def observed_money(group_mask_sm, group_mask_pay, label_dim, label):
    """Observed Mar-Aug 2026: price gain on payments taken vs revenue lost to excess churn."""
    gpay = mp[group_mask_pay]
    price_gain = float(((gpay["amount_usd"] - OLD_PRICE).clip(lower=0)).sum())
    g = mon[group_mask_sm]
    # Excess churners per after month at the same tenure, then months of $10 lost until the end of August.
    bb = rate_table(mon[mon.period == BASE], ["tenure_band"]).set_index("tenure_band")["churn_rate"]
    lost_months = 0.0
    excess_total = 0.0
    for i, m in enumerate(POST_MONTHS):
        gm = g[g["month"] == m]
        exp = gm.groupby("tenure_band", observed=True)["churned"].size().mul(bb).sum()
        exc = gm["churned"].sum() - exp
        excess_total += exc
        lost_months += exc * (len(POST_MONTHS) - 1 - i)   # months left in the window after churning
    churn_cost = lost_months * OLD_PRICE
    return {"dimension": label_dim, "group": label, "payments_at_new_price": int((gpay["amount_usd"] == NEW_PRICE).sum()),
            "price_gain_usd": price_gain, "excess_churners": excess_total,
            "revenue_lost_to_excess_churn_usd": churn_cost, "net_effect_usd": price_gain - churn_cost}


money_obs = [observed_money(pd.Series(True, index=mon.index), pd.Series(True, index=mp.index), "all", "all monthly subscribers")]
for dim in ["cohort", "country", "device_type"]:
    for val in sorted(mon[dim].dropna().unique()):
        money_obs.append(observed_money(mon[dim] == val, mp[dim] == val, dim, val))
money_obs = save(pd.DataFrame(money_obs), "money_observed_mar_aug_2026")
mo = money_obs.iloc[0]
say(f"  Observed Mar-Aug 2026: +${mo.price_gain_usd:,.0f} from the $2 rise, -${mo.revenue_lost_to_excess_churn_usd:,.0f} "
    f"lost to {mo.excess_churners:,.0f} extra cancellations, net ${mo.net_effect_usd:+,.0f}.")

# Projection, tenure-aware: each subscriber ages through the tenure bands and churns at that band's rate.
# Keep: $12 with after-period band rates. Roll back: $10 with baseline band rates (the group's own where it
# has 300+ subscriber-months in a band, else all monthly subscribers'). Starts September 2026.
sep = pd.Period("2026-09", "M")
active_sep = paid[(paid.plan == "monthly") & (paid["start_day"] < sep.start_time)
                  & (paid["end_day"].isna() | (paid["end_day"] >= sep.start_time))].copy()
active_sep["tenure_m"] = ((sep.start_time - active_sep["start_day"]).dt.days // 30.44).astype(int)
# New monthly starts per month for the inflow: the median of October 2025 to June 2026, before the July 2026
# jump and the trial-fed starts from August 2026 (see new_monthly_starts_mix).
starts = paid[(paid.plan == "monthly")].groupby("start_month").size()
INFLOW_MONTHS = pd.period_range("2025-10", "2026-06", freq="M")
inflow_all = float(starts.reindex(INFLOW_MONTHS).median())
inflow_share = paid[(paid.plan == "monthly") & paid.start_month.isin(INFLOW_MONTHS)]
HORIZONS = [6, 12, 24]


def band_of(t):
    for lo_, hi_, lab in TENURE_BANDS:
        if lo_ < t <= hi_:
            return lab
    return TENURE_BANDS[-1][2]


def band_rates(df):
    t = rate_table(df, ["period", "tenure_band"])
    return {p: t[t.period == p].set_index("tenure_band") for p in [BASE, POST]}


ALL_RATES = band_rates(mb)


def rates_for(df):
    own = band_rates(df)
    out = {}
    for p in [BASE, POST]:
        out[p] = {}
        for b in [x[2] for x in TENURE_BANDS]:
            if b in own[p].index and own[p].loc[b, "sub_months"] >= 300:
                out[p][b] = float(own[p].loc[b, "churn_rate"])
            else:
                out[p][b] = float(ALL_RATES[p].loc[b, "churn_rate"])
    return out


def simulate(tenures, inflow, rates, price, months):
    """Revenue over `months` from a base with these tenures plus `inflow` new starts a month."""
    pop = pd.Series(tenures).value_counts().astype(float).to_dict()
    rev = 0.0
    for _ in range(months):
        pop[0] = pop.get(0, 0.0) + inflow
        rev += sum(pop.values()) * price
        pop = {t + 1: n * (1 - rates[band_of(t)]) for t, n in pop.items()}
    return rev


proj = []
groups = [("all", "all monthly subscribers", mb, active_sep, inflow_all, True),
          ("all", "existing base only (no new starts)", mb, active_sep, 0.0, True),
          ("all", "new starts only (one year of starts)", mb, active_sep.iloc[0:0], inflow_all, True)]
for dim in ["country", "device_type"]:
    for val in sorted(mb[dim].dropna().unique()):
        share = float((inflow_share[dim] == val).mean())
        groups.append((dim, val, mb[mb[dim] == val], active_sep[active_sep[dim] == val], inflow_all * share, False))
for dim, val, df, base_df, inflow, _ in groups:
    r = rates_for(df)
    row = {"dimension": dim, "group": val, "active_2026_09_01": len(base_df), "new_starts_per_month": inflow,
           **{f"after_churn_{k}": v for k, v in r[POST].items()},
           **{f"baseline_churn_{k}": v for k, v in r[BASE].items()}}
    for h in HORIZONS:
        keep = simulate(base_df["tenure_m"].tolist(), inflow, r[POST], NEW_PRICE, h)
        back = simulate(base_df["tenure_m"].tolist(), inflow, r[BASE], OLD_PRICE, h)
        row[f"revenue_keep_12_{h}m_usd"] = keep
        row[f"revenue_rollback_10_{h}m_usd"] = back
        row[f"rollback_gain_{h}m_usd"] = back - keep
    proj.append(row)
proj = save(pd.DataFrame(proj), "money_projection")
p0 = proj.iloc[0]
say(f"  Projection from Sep 2026: {p0.active_2026_09_01:,} monthly subscribers plus {inflow_all:.0f} new starts a month.")
for _, r in proj.iterrows():
    say(f"  {r.dimension:12s} {r.group:38s} rollback gain: 6m ${r.rollback_gain_6m_usd:+,.0f}, "
        f"12m ${r.rollback_gain_12m_usd:+,.0f}, 24m ${r.rollback_gain_24m_usd:+,.0f}")

# Break-even: how much would monthly churn have to rise, in every band, for $12 to lose money over 12 months?
lo, hi = 0.0, 0.5
rb_all = rates_for(mb)[BASE]
for _ in range(60):
    mid = (lo + hi) / 2
    keep = simulate(active_sep["tenure_m"].tolist(), inflow_all, {k: v + mid for k, v in rb_all.items()}, NEW_PRICE, 12)
    back = simulate(active_sep["tenure_m"].tolist(), inflow_all, rb_all, OLD_PRICE, 12)
    lo, hi = (mid, hi) if keep > back else (lo, mid)
be = save(pd.DataFrame([{"horizon_months": 12, "observed_rise_same_tenure_pp": hm.change_same_tenure_pp,
                         "break_even_rise_pp": lo * 100}]), "break_even_churn_rise")
say(f"  Break-even over 12 months: $12 keeps more revenue unless churn rises by more than {lo * 100:.1f} pp a month "
    f"in every tenure band; observed same-tenure rise {hm.change_same_tenure_pp:.1f} pp.")

cats = [f"{h} months" for h in HORIZONS]
fig = charts.bar(cats, [proj.iloc[0][f"rollback_gain_{h}m_usd"] / 1000 for h in HORIZONS],
                 "A full rollback loses revenue in the first year and gains it only in the second",
                 ylabel="Revenue from rolling back to $10 vs keeping $12, $ thousand",
                 source="Monthly subscribers active on 2026-09-01 plus new starts at the Oct 2025-Jun 2026 median")
charts.save(fig, CH / "rollback_gain_by_horizon.png")
fig = charts.bar(["Existing base", "New starts (one year)"],
                 [proj.iloc[1]["rollback_gain_12m_usd"] / 1000, proj.iloc[2]["rollback_gain_12m_usd"] / 1000],
                 "Over 12 months a rollback loses money on the existing base and only breaks even on new starts",
                 highlight="New starts (one year)", ylabel="Revenue from rolling back to $10 vs keeping $12, $ thousand",
                 source="Tenure-aware projection, Sep 2026-Aug 2027")
charts.save(fig, CH / "rollback_gain_existing_vs_new.png")

# ---------------------------------------------------------------- 9. Is the forward group the same people?
say("\n== New monthly subscribers: who they are")
nm = paid[(paid.plan == "monthly") & (paid["start_month"] >= pd.Period("2025-06", "M"))].copy()
nm["from_trial"] = nm["user_id"].isin(trials["user_id"])
mix = nm.groupby("start_month").agg(starts=("subscription_id", "size"), from_trial=("from_trial", "mean"),
                                    us=("country", lambda c: (c == "US").mean()),
                                    web=("device_type", lambda c: (c == "Web").mean())).reset_index()
mix["start_month"] = mix["start_month"].astype(str)
save(mix, "new_monthly_starts_mix")
say(f"  Monthly starts, median Oct 2025-Jun 2026: {mix.set_index('start_month').loc['2025-10':'2026-06', 'starts'].median():.0f}; "
    f"Jul 2026: {mix.set_index('start_month').loc['2026-07', 'starts']:.0f}; Aug 2026: "
    f"{mix.set_index('start_month').loc['2026-08', 'starts']:.0f} ({mix.set_index('start_month').loc['2026-08', 'from_trial']:.0%} from trials).")

say(f"\nResults in {OUT.relative_to(ROOT)}, charts in {CH.relative_to(ROOT)}")
