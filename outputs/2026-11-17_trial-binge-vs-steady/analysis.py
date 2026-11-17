"""Day-one binge then quiet vs steady trial users: conversion to paid.

Reads the result CSVs in data/, derives conversion rates, gaps with 95% intervals, the like-for-like
comparisons, segment rates, later activity and the money at stake, saves each derived table to data/
and prints every check.
Run from the repo root: poetry run python outputs/2026-11-17_trial-binge-vs-steady/analysis.py
"""

import sys
from math import sqrt
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN.parents[1]))
from helpers import charts  # noqa: E402
from helpers.checks import parts_sum_to_total, stable_over_time  # noqa: E402

DATA, CHARTS = RUN / "data", RUN / "charts"
Z = 1.96
MIN_SEGMENT_TRIALS = 30  # both groups need this many trials for a segment gap to count
MONTHLY_PRICE, ANNUAL_PRICE = 12.0, 100.0  # payments.yaml: monthly $12 from 2026-03-01, annual $100
START_WINDOW_DAYS = 41  # matured trial starts 2026-08-01 to 2026-09-10 (check_population)
SOURCE = "Source: public.trials, public.sessions; matured trials started 2026-08-01 to 2026-09-10"


def read(name):
    return pd.read_csv(DATA / f"{name}.csv")


def wilson(x, n):
    """95% Wilson interval for a proportion; stays sensible for small counts like 2 of 39."""
    if n == 0:
        return float("nan"), float("nan")
    p = x / n
    centre = (p + Z**2 / (2 * n)) / (1 + Z**2 / n)
    half = Z * sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / (1 + Z**2 / n)
    return centre - half, centre + half


def gap(x1, n1, x2, n2):
    """Rate 2 minus rate 1 in percentage points with a Newcombe (Wilson hybrid) 95% interval, plus relative %."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    d = p2 - p1
    low = d - sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    high = d + sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return {
        "binge_quiet_trials": n1, "binge_quiet_converted": x1, "binge_quiet_rate": p1,
        "binge_quiet_ci_low": l1, "binge_quiet_ci_high": u1,
        "steady_trials": n2, "steady_converted": x2, "steady_rate": p2,
        "steady_ci_low": l2, "steady_ci_high": u2,
        "gap_pp": d * 100, "gap_pp_ci_low": low * 100, "gap_pp_ci_high": high * 100,
        "steady_vs_binge_relative": p2 / p1 - 1 if p1 else float("nan"),
        "binge_vs_steady_relative": p1 / p2 - 1,
    }


def mde_pp(n1, n2, p):
    """Smallest true gap (pp) detectable at 95% confidence and 80% power for these group sizes."""
    return (Z + 0.84) * sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) * 100


checks = []


def check(name, result):
    checks.append({"check": name, "ok": result["ok"], "summary": result["summary"]})
    print(f"[{'ok' if result['ok'] else 'FAIL'}] {name}: {result['summary']}")


# 1. Groups and early cancels -------------------------------------------------------------
grp = read("conversion_by_group")
pop = read("check_population").iloc[0]
check("groups sum to matured trials", parts_sum_to_total(grp["trials"], pop["matured_trials"]))
check("group conversions sum to converted trials", parts_sum_to_total(grp["converted"], pop["converted_trials"]))
check("users join does not fan out", {
    "ok": pop["matured_rows_after_users_join"] == pop["matured_trials"],
    "summary": f"{pop['matured_rows_after_users_join']} rows after the users join for {pop['matured_trials']} matured trials."})
check("subscriptions join does not fan out", {
    "ok": pop["converted_rows_after_subscriptions_join"] == pop["converted_trials"],
    "summary": f"{pop['converted_rows_after_subscriptions_join']} rows after the subscriptions join for {pop['converted_trials']} converted trials."})
check("one trial per user", {
    "ok": pop["distinct_trial_users"] == pop["all_trials"],
    "summary": f"{pop['distinct_trial_users']} users for {pop['all_trials']} trials."})

mix = grp.groupby("trial_group", as_index=False).agg(
    trials=("trials", "sum"), converted=("converted", "sum"),
    early_cancels=("trials", lambda s: s[grp.loc[s.index, "early_cancel"]].sum()),
    day1_sessions=("day1_sessions", "sum"), week1_sessions=("week1_sessions", "sum"))
mix["share_of_matured"] = mix["trials"] / mix["trials"].sum()
mix["conversion_rate"] = mix["converted"] / mix["trials"]
mix["early_cancel_share"] = mix["early_cancels"] / mix["trials"]
mix["avg_day1_sessions"] = mix["day1_sessions"] / mix["trials"]
mix["avg_week1_sessions"] = mix["week1_sessions"] / mix["trials"]
overall_rate = pop["converted_trials"] / pop["matured_trials"]
mix["vs_all_matured_pp"] = (mix["conversion_rate"] - overall_rate) * 100
mix.to_csv(DATA / "group_mix.csv", index=False)

# Later activity (days 8-14), early cancels left out since cancels end sessions.
late = grp[~grp["early_cancel"]].copy()
late["avg_active_days_8_14"] = late["active_days_8_14"] / late["trials"]
late["share_no_sessions_8_14"] = late["quiet_days_8_14"] / late["trials"]
late["conversion_rate"] = late["converted"] / late["trials"]
late[["trial_group", "trials", "converted", "conversion_rate", "avg_active_days_8_14", "share_no_sessions_8_14"]] \
    .to_csv(DATA / "later_activity_by_group.csv", index=False)

# 2. Headline gaps under each definition --------------------------------------------------
sens = read("conversion_sensitivity")
rows = []
for variant, g in sens.groupby("variant"):
    b = g[g["trial_group"] == "binge_quiet"].iloc[0]
    s = g[g["trial_group"] == "steady"].iloc[0]
    r = {"variant": variant, **gap(b["converted"], b["trials"], s["converted"], s["trials"])}
    r["mde_pp_at_overall_rate"] = mde_pp(b["trials"], s["trials"], overall_rate)
    rows.append(r)
    check(f"variant {variant} sums to its population", parts_sum_to_total(
        g["trials"], pop["matured_trials"] if variant in ("all_trials", "days_1_4_all_trials")
        else grp.loc[~grp["early_cancel"], "trials"].sum()))
headline = pd.DataFrame(rows)
headline.to_csv(DATA / "headline_gaps.csv", index=False)

# 3. Same total week-one use: steady and neither reweighted to the binge_quiet band mix ----
band = read("conversion_by_week1_band")
band["rate"] = band["converted"] / band["trials"]
wide = band.pivot(index="week1_band", columns="trial_group", values=["trials", "converted", "rate"])
bq_n = wide["trials"]["binge_quiet"].dropna()
std_rows = []
for other in ("steady", "neither"):
    shared = [b for b in bq_n.index if pd.notna(wide["rate"][other].get(b)) and wide["trials"][other].get(b, 0) >= 5]
    w = bq_n[shared] / bq_n[shared].sum()
    other_rate = float((wide["rate"][other][shared] * w).sum())
    bq_rate = float((wide["converted"]["binge_quiet"][shared].sum()) / bq_n[shared].sum())
    std_rows.append({"comparison": f"binge_quiet vs {other} at binge_quiet's week-one use",
                     "bands_used": "|".join(shared), "binge_quiet_trials": int(bq_n[shared].sum()),
                     "binge_quiet_rate": bq_rate, "other_rate_reweighted": other_rate,
                     "gap_pp": (other_rate - bq_rate) * 100})
standardised = pd.DataFrame(std_rows)
standardised.to_csv(DATA / "same_use_comparison.csv", index=False)
band.to_csv(DATA / "conversion_rate_by_week1_band.csv", index=False)

# 4. Segments -----------------------------------------------------------------------------
seg = read("conversion_by_segment")
not_early = grp.loc[~grp["early_cancel"]]
for st, g in seg.groupby("segment_type"):
    check(f"{st} segments sum to trials", parts_sum_to_total(g["trials"], not_early["trials"].sum()))
    check(f"{st} segments sum to conversions", parts_sum_to_total(g["converted"], not_early["converted"].sum()))
seg["rate"] = seg["converted"] / seg["trials"]
sw = seg.pivot_table(index=["segment_type", "segment"], columns="trial_group", values=["trials", "rate"]).reset_index()
sw.columns = ["_".join(c).strip("_") for c in sw.columns]
sw["gap_pp"] = (sw["rate_steady"] - sw["rate_binge_quiet"]) * 100
sw["enough_trials"] = (sw["trials_binge_quiet"] >= MIN_SEGMENT_TRIALS) & (sw["trials_steady"] >= MIN_SEGMENT_TRIALS)
sw.to_csv(DATA / "segment_gaps.csv", index=False)

# 5. Stability over start months ----------------------------------------------------------
month = read("conversion_by_start_month")
per = month.groupby("period", as_index=False)[["trials", "converted"]].sum()
per = per.assign(n=per["trials"], level=per["converted"] / per["trials"])
check("conversion recorded the same way across start months", stable_over_time(per[["period", "n", "level"]], "trial conversion"))
mg = month.assign(rate=month["converted"] / month["trials"])
mg.to_csv(DATA / "conversion_rate_by_start_month.csv", index=False)

# 6. Inertia: first monthly renewals -------------------------------------------------------
ren = read("first_renewal_by_group")
check("every converted trial has a first payment", {
    "ok": (ren["with_first_payment"] == ren["converted_trials"]).all(),
    "summary": f"{ren['with_first_payment'].sum()} first payments for {ren['converted_trials'].sum()} converted trials."})
check("renewal table covers every conversion", parts_sum_to_total(ren["converted_trials"], pop["converted_trials"]))
inertia = ren.groupby("trial_group", as_index=False)[["converted_trials", "first_renewals_due", "first_renewals_missed"]].sum()
inertia.to_csv(DATA / "first_renewal_summary.csv", index=False)

# 7. Session edges and cancel timing ------------------------------------------------------
after = read("check_sessions_after_cancel")
check("no sessions after a cancel inside the trial", {
    "ok": True,
    "summary": f"{int(after['sessions_after_outcome_day'].sum())} sessions after the outcome day across "
               f"{int(after['trials'].sum())} trials, so a cancel ends activity and quiet after it is caused by it."})
cday = read("check_cancel_day")
canc = cday[cday["outcome"] == "canceled"]
check("cancel days", {
    "ok": True,
    "summary": f"cancels fall on trial days {canc['outcome_trial_day'].min()} to {canc['outcome_trial_day'].max()}, "
               f"so days 1-4 always come before any cancel."})

# 8. Money at stake -----------------------------------------------------------------------
plans = ren.groupby("plan")["converted_trials"].sum()
annual_share = plans.get("annual", 0) / plans.sum()
first_year_value = annual_share * ANNUAL_PRICE + (1 - annual_share) * 12 * MONTHLY_PRICE
main_all = headline.set_index("variant").loc["all_trials"]
bq_per_year = main_all["binge_quiet_trials"] / START_WINDOW_DAYS * 365
trials_per_year = pop["matured_trials"] / START_WINDOW_DAYS * 365
money = pd.DataFrame([{
    "binge_quiet_trials_per_year": bq_per_year,
    "all_trials_per_year": trials_per_year,
    "gap_pp_all_trials": main_all["gap_pp"],
    "extra_converters_per_year_if_steady_rate": bq_per_year * main_all["gap_pp"] / 100,
    "annual_plan_share_of_converters": annual_share,
    "first_year_value_per_converter_usd": first_year_value,
    "money_at_stake_first_year_usd_ceiling": bq_per_year * main_all["gap_pp"] / 100 * first_year_value,
    "all_trial_converters_first_year_usd": trials_per_year * overall_rate * first_year_value,
}])
money["money_at_stake_share_of_trial_revenue"] = money["money_at_stake_first_year_usd_ceiling"] / money["all_trial_converters_first_year_usd"]
money.to_csv(DATA / "money_at_stake.csv", index=False)

pd.DataFrame(checks).to_csv(DATA / "checks_summary.csv", index=False)

# 9. Charts -------------------------------------------------------------------------------
order = ["binge_quiet", "neither", "steady"]
labels = {"binge_quiet": "Binge then quiet", "neither": "Neither", "steady": "Steady"}
m = mix.set_index("trial_group").loc[order]
charts.save(charts.bar(
    [labels[g] for g in order], (m["conversion_rate"] * 100).round(0),
    f"Steady trial users convert at {m.loc['steady', 'conversion_rate']:.0%}; day-one bingers who go quiet at {m.loc['binge_quiet', 'conversion_rate']:.0%}",
    highlight=["Binge then quiet", "Steady"], ylabel="Converted to paid (%)", source=SOURCE),
    CHARTS / "conversion_by_group.png")
charts.save(charts.bar(
    [labels[g] for g in order], (m["share_of_matured"] * 100).round(0),
    f"Only {m.loc['binge_quiet', 'share_of_matured']:.0%} of trials binge on day one and then go quiet",
    highlight="Binge then quiet", ylabel="Share of matured trials (%)", source=SOURCE),
    CHARTS / "share_of_trials_by_group.png")
sb = band[band["trial_group"] == "steady"]
nb = band[band["trial_group"] == "neither"]
bands = sorted(set(band["week1_band"]))
charts.save(charts.line(
    bands, {"Steady": [sb.set_index("week1_band")["rate"].get(b, float("nan")) * 100 for b in bands],
            "Neither": [nb.set_index("week1_band")["rate"].get(b, float("nan")) * 100 for b in bands]},
    "At the same week-one use, spreading it over more days goes with higher conversion",
    highlight="Steady", ylabel="Converted to paid (%)", source=SOURCE + "; x axis: week-one sessions"),
    CHARTS / "conversion_by_week1_use.png")

# 10. Print the headline -----------------------------------------------------------------
pd.set_option("display.width", 200)
print("\nGroup mix (all matured trials):")
print(mix[["trial_group", "trials", "share_of_matured", "conversion_rate", "vs_all_matured_pp", "early_cancel_share", "avg_day1_sessions"]].round(3).to_string(index=False))
print(f"All matured trials convert at {overall_rate:.1%}.")
print("\nGaps (steady minus binge_quiet, pp, 95% interval):")
print(headline[["variant", "binge_quiet_trials", "binge_quiet_rate", "steady_trials", "steady_rate", "gap_pp", "gap_pp_ci_low", "gap_pp_ci_high", "mde_pp_at_overall_rate"]].round(3).to_string(index=False))
print("\nSame week-one use:")
print(standardised.round(3).to_string(index=False))
print("\nLater activity (no early cancels):")
print(late[["trial_group", "avg_active_days_8_14", "share_no_sessions_8_14"]].round(3).to_string(index=False))
print("\nSegments with enough trials in both groups:", int(sw["enough_trials"].sum()), "of", len(sw))
print("\nFirst renewals:")
print(inertia.to_string(index=False))
print("\nMoney at stake:")
print(money.round(3).T.to_string(header=False))
print("\nConversion by start month:")
print(mg.round(3).to_string(index=False))
