"""Did the March 2026 monthly price increase ($10 to $12) hurt retention, and for whom?

Run from the repo root: poetry run python outputs/2026-11-07_march-price-retention/analysis.py

Churn is measured per renewal from payments (quirk "End-date recording change"):
monthly charges fall exactly every 30 days, so each charge has a renewal due 30 days
later, and the subscriber churned at that renewal if no charge happened on it.
Nothing due after 2026-07-31 is used (trials launched 2026-08-01; user's request).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# The repo root is the nearest parent holding helpers/, so a copy deeper down still runs.
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "helpers").is_dir())
sys.path.insert(0, str(ROOT))
from helpers import charts, checks  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
CH = RUN / "charts"
OUT.mkdir(exist_ok=True)
CH.mkdir(exist_ok=True)

WINDOW_END = pd.Timestamp("2026-07-31 23:59:59")
WINDOWS = {  # renewal due dates
    "year_earlier": (pd.Timestamp("2025-03-01"), pd.Timestamp("2025-07-31 23:59:59")),
    "before": (pd.Timestamp("2025-09-01"), pd.Timestamp("2026-02-28 23:59:59")),
    "after": (pd.Timestamp("2026-03-01"), WINDOW_END),
    # Sensitivities (overlap the windows above): baseline without the Sep-Oct 2025
    # anomaly, and the level once churn settled after the increase.
    "before_clean": (pd.Timestamp("2025-11-01"), pd.Timestamp("2026-02-28 23:59:59")),
    "after_steady": (pd.Timestamp("2026-05-01"), WINDOW_END),
}
MAIN_WINDOWS = ["year_earlier", "before", "after"]
SPIKE_DAY = pd.Timestamp("2025-09-17")
BULK_DAYS = [SPIKE_DAY, pd.Timestamp("2026-07-30")]
TENURE_BINS = [0, 1, 3, 6, 12, 24, 10_000]
TENURE_LABELS = ["1", "2-3", "4-6", "7-12", "13-24", "25+"]
SRC = "Source: payments, subscriptions, users; analysis.py"


def say(check):
    print("CHECK:", check["summary"])
    return check


# ---------------------------------------------------------------- load
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pay = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])
users = pd.read_csv(ROOT / "data/users.csv", parse_dates=["signup_date"])
trials = pd.read_csv(ROOT / "data/trials.csv", parse_dates=["started_at"])

print("Trials start on", trials.started_at.min().date(), "(after window end, so none are used)")
trial_users = set(trials.user_id)

say(checks.join_fan_out(pay, subs, "subscription_id"))
say(checks.join_fan_out(subs, users, "user_id"))

subs = subs[~subs.user_id.isin(trial_users)]
subs = subs[subs.start_date <= WINDOW_END]
subs = subs.merge(users[["user_id", "country", "device_type"]], on="user_id", how="left")
subs["bulk_block"] = subs.start_date.dt.normalize().isin(BULK_DAYS)
subs["spike_block"] = subs.start_date.dt.normalize() == SPIKE_DAY

# ---------------------------------------------------------------- why payments, not end_date
m_end = subs[(subs.plan == "monthly") & subs.end_date.notna() & (subs.end_date <= WINDOW_END)].copy()
m_end["midnight"] = m_end.end_date.dt.time == pd.Timestamp("00:00").time()
say(checks.stable_over_time(m_end, "end_date", "midnight"))

p = pay.merge(subs[["subscription_id", "plan", "start_date", "country", "device_type",
                    "spike_block", "bulk_block"]], on="subscription_id", how="inner")
p = p.sort_values(["subscription_id", "payment_date"])
p["next_gap"] = p.groupby("subscription_id").payment_date.shift(-1).sub(p.payment_date).dt.days
p["prev_gap"] = p.groupby("subscription_id").payment_date.diff().dt.days
mp = p[p.plan == "monthly"]
say(checks.stable_over_time(mp.dropna(subset=["prev_gap"]), "payment_date", "prev_gap"))
assert set(mp.prev_gap.dropna().unique()) == {30.0}, "monthly charges are not all 30 days apart"

# ---------------------------------------------------------------- renewals
def renewals(plan, cycle_days):
    r = p[p.plan == plan].copy()
    r["due"] = r.payment_date + pd.Timedelta(days=cycle_days)
    r["churned"] = r.next_gap.isna()
    r["price_now"] = r.amount_usd
    r["tenure_m"] = ((r.due - r.start_date).dt.days / 30).round().astype(int)
    r["tenure"] = pd.cut(r.tenure_m, TENURE_BINS, labels=TENURE_LABELS, right=True)
    parts = []
    for name, (a, b) in WINDOWS.items():
        parts.append(r[(r.due >= a) & (r.due <= b)].assign(window=name))
    return pd.concat(parts, ignore_index=True)


ren_all = renewals("monthly", 30)
mat = checks.matured_only(ren_all, "due", as_of=WINDOW_END)
assert mat["dropped"] == 0
# A renewal due before payments begin cannot be seen; due dates start 2025-03-01, so all are visible.
say(checks.date_boundaries(ren_all[ren_all.window == "after"], "due"))
say(checks.date_boundaries(ren_all[ren_all.window == "before"], "due"))
ren = ren_all[~ren_all.spike_block]  # main: excludes the 2025-09-17 bulk block


def std_compare(df, a="before", b="after"):
    """Churn in window b against window a reweighted to b's tenure mix, with a 95% range."""
    g = df.groupby(["window", "tenure"], observed=True).churned.agg(["sum", "size"])
    if a not in g.index.get_level_values(0) or b not in g.index.get_level_values(0):
        return None
    ga, gb = g.loc[a], g.loc[b]
    bands = gb.index.intersection(ga.index)
    gb, ga = gb.loc[bands], ga.loc[bands]
    w = gb["size"] / gb["size"].sum()
    rb, ra = gb["sum"] / gb["size"], ga["sum"] / ga["size"]
    churn_b, churn_a = float((w * rb).sum()), float((w * ra).sum())
    var = (w**2 * (rb * (1 - rb) / gb["size"] + ra * (1 - ra) / ga["size"])).sum()
    se = float(np.sqrt(var))
    diff = churn_b - churn_a
    return {
        f"renewals_{a}": int(ga["size"].sum()), f"renewals_{b}": int(gb["size"].sum()),
        f"churns_{a}": int(ga["sum"].sum()), f"churns_{b}": int(gb["sum"].sum()),
        f"churn_{a}_tenure_matched": churn_a, f"churn_{b}": churn_b,
        f"churn_{a}_se": float(np.sqrt((w**2 * ra * (1 - ra) / ga["size"]).sum())),
        "diff_pp": diff * 100, "diff_low_pp": (diff - 1.96 * se) * 100,
        "diff_high_pp": (diff + 1.96 * se) * 100,
        "rel_change": diff / churn_a if churn_a else np.nan,
    }


# ---------------------------------------------------------------- headline
rows = []
for label, df in [("main (excl. 2025-09-17 block)", ren), ("incl. 2025-09-17 block", ren_all)]:
    # Main comparison first: clean baseline (Nov 2025-Feb 2026, outside the unexplained
    # Sep-Oct 2025 churn bump) against the settled level (May-Jul 2026).
    for a, b in [("before_clean", "after_steady"), ("before_clean", "after"),
                 ("before", "after"), ("before", "after_steady"),
                 ("year_earlier", "after"), ("year_earlier", "before")]:
        res = std_compare(df, a, b)
        rows.append({"sample": label, "baseline": a, "compared": b, **{
            k.replace(f"_{a}", "_base").replace(f"_{b}", "_cmp"): v for k, v in res.items()}})
headline = pd.DataFrame(rows)
headline.to_csv(OUT / "headline_churn.csv", index=False)

# raw by tenure band and window
by_ten = (ren[ren.window.isin(MAIN_WINDOWS)].groupby(["window", "tenure"], observed=True).churned.agg(renewals="size", churns="sum")
          .assign(churn=lambda d: d.churns / d.renewals).reset_index())
by_ten.to_csv(OUT / "churn_by_tenure_window.csv", index=False)

# monthly series
one = ren_all[ren_all.window.isin(MAIN_WINDOWS)].copy()
one["due_month"] = one.due.dt.to_period("M").astype(str)
ser = (one.groupby(["due_month", "spike_block"]).churned.agg(renewals="size", churns="sum")
       .reset_index())
s_main = ser[~ser.spike_block].set_index("due_month")
s_all = ser.groupby("due_month")[["renewals", "churns"]].sum()
all_months = pd.period_range("2025-03", "2026-07", freq="M").astype(str)
series = pd.DataFrame({
    "renewals_main": s_main.renewals, "churn_main": s_main.churns / s_main.renewals,
    "renewals_all": s_all.renewals, "churn_all": s_all.churns / s_all.renewals,
}).reindex(all_months).rename_axis("due_month").reset_index()  # 2025-08 is outside every window
series.to_csv(OUT / "churn_by_due_month.csv", index=False)

# ---------------------------------------------------------------- segments
seg_rows = []
for dim in ["country", "device_type", "tenure"]:
    for val, df in ren.groupby(dim, observed=True):
        for a, b in [("before_clean", "after_steady"), ("before_clean", "after"),
                     ("before", "after"), ("year_earlier", "after")]:
            res = std_compare(df, a, b)
            if res:
                seg_rows.append({"dimension": dim, "segment": str(val), "baseline": a,
                                 "compared": b, **{
                    k.replace(f"_{a}", "_base").replace(f"_{b}", "_cmp"): v
                    for k, v in res.items()}})
segments = pd.DataFrame(seg_rows)
segments.to_csv(OUT / "churn_by_segment.csv", index=False)

total_after = len(ren[ren.window == "after"])
for dim in ["country", "device_type", "tenure"]:
    parts = segments[(segments.dimension == dim) & (segments.baseline == "before")
                     & (segments.compared == "after")].renewals_cmp
    say(checks.parts_sum_to_total(parts, total_after))

# country x device cross, main comparison
cross = []
for (c, d), df in ren.groupby(["country", "device_type"]):
    res = std_compare(df, "before_clean", "after_steady")
    if res:
        cross.append({"country": c, "device_type": d, "baseline": "before_clean",
                      "compared": "after_steady", **{
                          k.replace("_before_clean", "_base").replace("_after_steady", "_cmp"): v
                          for k, v in res.items()}})
pd.DataFrame(cross).to_csv(OUT / "churn_country_x_device.csv", index=False)

# ---------------------------------------------------------------- money
def twelve_month_rev(price, churn):
    r = 1 - churn
    return price * sum(r**k for k in range(12))


def breakeven(churn_before):
    target = twelve_month_rev(10, churn_before)
    lo, hi = churn_before, 0.99
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if twelve_month_rev(12, mid) > target else (lo, mid)
    return mid


# active monthly base on 2026-07-31: charged in the 30 days up to it (one charge per 30 days)
base = mp[(mp.payment_date > WINDOW_END - pd.Timedelta(days=30)) & (mp.payment_date <= WINDOW_END)]
base = base[~base.bulk_block]  # drop both bulk blocks (2025-09-17, 2026-07-30): not measured
assert base.subscription_id.is_unique
def money_for(a, b):
    rows_ = []
    hrow = headline[(headline["sample"].str.startswith("main")) & (headline.baseline == a)
                    & (headline.compared == b)].iloc[0]
    seg_ab = segments[(segments.baseline == a) & (segments.compared == b)]
    for _, srow in pd.concat([
        pd.DataFrame([{"dimension": "all", "segment": "all",
                       **hrow[["churn_base_tenure_matched", "churn_cmp",
                               "diff_low_pp", "diff_high_pp"]].to_dict()}]),
        seg_ab,
    ]).iterrows():
        dim, val = srow.dimension, srow.segment
        if dim == "all":
            n = len(base)
        elif dim == "tenure":
            # tenure at the next renewal, banded the same way as renewals
            t = pd.cut(((base.payment_date + pd.Timedelta(days=30) - base.start_date).dt.days
                        / 30).round(), TENURE_BINS, labels=TENURE_LABELS)
            n = int((t.astype(str) == val).sum())
        else:
            n = int((base[dim] == val).sum())
        cb, ca = srow.churn_base_tenure_matched, srow.churn_cmp
        rev12 = n * twelve_month_rev(12, ca)
        rev10 = n * twelve_month_rev(10, cb)
        be = breakeven(cb)
        rows_.append({
            "baseline": a, "compared": b,
            "dimension": dim, "segment": val, "active_base_2026_07_31": n,
            "churn_before_tenure_matched": cb, "churn_after": ca,
            "breakeven_churn_at_12": be, "after_minus_breakeven_pp": (ca - be) * 100,
            "rev12m_keep_12_usd": rev12, "rev12m_rollback_10_usd": rev10,
            "gain_from_increase_usd": rev12 - rev10,
            # worst and best case inside the 95% range of the churn rise
            "gain_if_rise_at_upper_bound_usd": n * twelve_month_rev(
                12, cb + srow.diff_high_pp / 100) - rev10,
            "gain_if_rise_at_lower_bound_usd": n * twelve_month_rev(
                12, cb + srow.diff_low_pp / 100) - rev10,
        })
    return rows_


money_rows = (money_for("before_clean", "after_steady") + money_for("before_clean", "after")
              + money_for("before", "after"))
money = pd.DataFrame(money_rows)
money.to_csv(OUT / "money_by_segment.csv", index=False)

# ---------------------------------------------------------------- observed Mar-Jul 2026 revenue
# Existing base: monthly subscribers charged in the 30 days to 2026-02-28 (one charge each).
# Observed: what they actually paid on renewals due 2026-03-01 to 2026-07-31 (all at $12).
# Counterfactual: $10 on the same renewals if each had survived at the segment's
# tenure-matched Nov 2025-Feb 2026 churn.
feb_end = pd.Timestamp("2026-02-28 23:59:59")
b0 = mp[(mp.payment_date > feb_end - pd.Timedelta(days=30)) & (mp.payment_date <= feb_end)
        & ~mp.spike_block].copy()
assert b0.subscription_id.is_unique
b0["n_due"] = ((WINDOW_END - b0.payment_date).dt.days // 30).astype(int)
b0["tenure"] = pd.cut(((b0.payment_date + pd.Timedelta(days=30) - b0.start_date).dt.days / 30)
                      .round(), TENURE_BINS, labels=TENURE_LABELS).astype(str)
obs = mp[mp.subscription_id.isin(b0.subscription_id) & (mp.payment_date > feb_end)
         & (mp.payment_date <= WINDOW_END)]
assert (obs.amount_usd == 12).all()
paid_obs = obs.groupby("subscription_id").amount_usd.sum()
b0["observed_usd"] = b0.subscription_id.map(paid_obs).fillna(0)
seg_main = segments[(segments.baseline == "before_clean") & (segments.compared == "after_steady")]
def expected_by_month(g, r):
    """Expected renewals paid per due month for base g if each survives at rate r."""
    exp = {}
    for pdate, k_max in zip(g.payment_date, g.n_due):
        for k in range(1, k_max + 1):
            mth = str((pdate + pd.Timedelta(days=30 * k)).to_period("M"))
            exp[mth] = exp.get(mth, 0) + r**k
    return exp


def base_churn(dim, val):
    row = (headline.iloc[0] if dim == "all" else
           seg_main[(seg_main.dimension == dim) & (seg_main.segment == str(val))].iloc[0])
    return row.churn_base_tenure_matched, row.churn_base_se


# The 95% range comes from the uncertainty in the baseline churn the counterfactual uses:
# a higher baseline churn means fewer $10 renewals and so a larger gain.
obs_rows, due_rows = [], []
obs_m = obs.assign(due_month=obs.payment_date.dt.to_period("M").astype(str)) \
    .merge(b0[["subscription_id", "tenure"]], on="subscription_id")
for dim in ["all", "country", "device_type", "tenure"]:
    groups = [("all", b0)] if dim == "all" else list(b0.groupby(dim))
    for val, g in groups:
        cb, se_cb = base_churn(dim, val)
        e_mid, e_lo, e_hi = (expected_by_month(g, 1 - c)
                             for c in (cb, cb + 1.96 * se_cb, max(cb - 1.96 * se_cb, 0)))
        o = obs_m if dim == "all" else obs_m[obs_m[dim].astype(str) == str(val)]
        o = o.groupby("due_month").amount_usd.sum()
        observed_total = g.observed_usd.sum()
        obs_rows.append({
            "dimension": dim, "segment": str(val), "base_2026_02_28": len(g),
            "observed_mar_jul_usd": observed_total,
            "counterfactual_10_baseline_churn_usd": 10 * sum(e_mid.values()),
            "observed_gain_usd": observed_total - 10 * sum(e_mid.values()),
            "observed_gain_low_usd": observed_total - 10 * sum(e_hi.values()),
            "observed_gain_high_usd": observed_total - 10 * sum(e_lo.values()),
            "churn_base_used": cb,
        })
        for mth in sorted(e_mid):
            ob = float(o.get(mth, 0))
            due_rows.append({"dimension": dim, "segment": str(val), "due_month": mth,
                             "observed_usd": ob, "counterfactual_usd": 10 * e_mid[mth],
                             "gain_usd": ob - 10 * e_mid[mth],
                             "gain_low_usd": ob - 10 * e_hi[mth],
                             "gain_high_usd": ob - 10 * e_lo[mth]})
observed = pd.DataFrame(obs_rows)
by_due = pd.DataFrame(due_rows)
by_due.to_csv(OUT / "observed_revenue_by_due_month.csv", index=False)
tot = by_due[by_due.dimension == "all"]
say(checks.parts_sum_to_total(tot.gain_usd, float(observed_gain_all := (
    sum(r["observed_gain_usd"] for r in obs_rows if r["dimension"] == "all")))))
observed.to_csv(OUT / "observed_revenue_mar_jul.csv", index=False)
for dim in ["country", "device_type", "tenure"]:
    say(checks.parts_sum_to_total(observed[observed.dimension == dim].observed_mar_jul_usd,
                                  observed[observed.dimension == "all"].observed_mar_jul_usd.iloc[0]))
m1 = money[(money.baseline == "before_clean") & (money.compared == "after_steady")]
for dim in ["country", "device_type", "tenure"]:
    say(checks.parts_sum_to_total(m1[m1.dimension == dim].active_base_2026_07_31,
                                  m1[m1.dimension == "all"].active_base_2026_07_31.iloc[0]))

# ---------------------------------------------------------------- new starts
paid = subs[(subs.plan != "free") & ~subs.bulk_block].copy()
paid["start_month"] = paid.start_date.dt.to_period("M")
for name in MAIN_WINDOWS + ["before_clean"]:
    a, b = WINDOWS[name]
    paid[f"in_{name}"] = (paid.start_date >= a) & (paid.start_date <= b)
starts_m = paid.groupby(["start_month", "plan"]).size().unstack(fill_value=0)
starts_m = starts_m.loc["2025-03":"2026-07"].reset_index()
starts_m["start_month"] = starts_m.start_month.astype(str)
starts_m["annual_share"] = starts_m.annual / (starts_m.annual + starts_m.monthly)
starts_m.to_csv(OUT / "new_paid_starts_by_month.csv", index=False)
months_in = {"year_earlier": 5, "before": 6, "after": 5, "before_clean": 4}
sw = pd.DataFrame({w: paid[paid[f"in_{w}"]].plan.value_counts() for w in months_in}).T
sw.index.name = "window"
sw["months"] = pd.Series(months_in)
sw["monthly_per_month"] = sw.monthly / sw.months
sw["annual_per_month"] = sw.annual / sw.months
sw["annual_share"] = sw.annual / (sw.annual + sw.monthly)
p_a, n_a = sw.loc["after", "annual_share"], sw.loc["after", ["annual", "monthly"]].sum()
for base_w in ["year_earlier", "before_clean"]:
    p_b, n_b = sw.loc[base_w, "annual_share"], sw.loc[base_w, ["annual", "monthly"]].sum()
    se_sh = np.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
    sw.loc["after", f"annual_share_diff_vs_{base_w}_pp"] = (p_a - p_b) * 100
    sw.loc["after", f"annual_share_diff_vs_{base_w}_low_pp"] = (p_a - p_b - 1.96 * se_sh) * 100
    sw.loc["after", f"annual_share_diff_vs_{base_w}_high_pp"] = (p_a - p_b + 1.96 * se_sh) * 100
    sw.loc["after", f"monthly_per_month_rel_vs_{base_w}"] = (
        sw.loc["after", "monthly_per_month"] / sw.loc[base_w, "monthly_per_month"] - 1)
    # Poisson range on the ratio of monthly start rates
    lr = np.log(sw.loc["after", "monthly_per_month"] / sw.loc[base_w, "monthly_per_month"])
    se_lr = np.sqrt(1 / sw.loc["after", "monthly"] + 1 / sw.loc[base_w, "monthly"])
    sw.loc["after", f"monthly_per_month_rel_vs_{base_w}_low"] = np.exp(lr - 1.96 * se_lr) - 1
    sw.loc["after", f"monthly_per_month_rel_vs_{base_w}_high"] = np.exp(lr + 1.96 * se_lr) - 1
sw.reset_index().to_csv(OUT / "new_paid_starts_by_window.csv", index=False)
paid["window"] = np.where(paid.in_after, "after", np.where(paid.in_before_clean, "before_clean", None))
sc = (paid[paid.window.isin(["before_clean", "after"])].groupby(["country", "window", "plan"]).size()
      .unstack(fill_value=0).assign(annual_share=lambda d: d.annual / (d.annual + d.monthly))
      .reset_index())
sc.to_csv(OUT / "annual_share_by_country.csv", index=False)

# ---------------------------------------------------------------- annual background
ren_an = renewals("annual", 365)
an = ren_an[~ren_an.spike_block & ren_an.window.isin(MAIN_WINDOWS)].groupby("window").churned.agg(renewals="size", churns="sum")
an["churn"] = an.churns / an.renewals
an.reset_index().to_csv(OUT / "annual_renewals.csv", index=False)

# ---------------------------------------------------------------- charts
mar = series.set_index("due_month").churn_main
fig = charts.line(
    series.due_month, {"Monthly churn per renewal (%)": series.churn_main * 100},
    f"Churn held at {mar['2026-03']:.1%} at the first $12 renewal in March 2026, "
    f"then rose to {mar['2026-05':'2026-07'].mean():.1%} by May to July",
    highlight="Monthly churn per renewal (%)", ylabel="% of renewals not paid",
    source=SRC + " (excl. 2025-09-17 block)")
fig.axes[0].axvline(series.due_month.tolist().index("2026-03"), color="#333333", ls=":", lw=1)
fig.axes[0].tick_params(axis="x", labelrotation=45)
fig.axes[0].annotate("first $12 renewals", xy=(series.due_month.tolist().index("2026-03"), 0.95),
                     xycoords=("data", "axes fraction"), xytext=(-4, 0),
                     textcoords="offset points", ha="right", fontsize=9, color="#333333")
fig.subplots_adjust(bottom=0.25)
charts.save(fig, CH / "churn_by_due_month.png")

sb = segments[(segments.baseline == "before") & (segments.compared == "after")]
ss = segments[(segments.baseline == "before_clean") & (segments.compared == "after_steady")]
overall = headline.iloc[0].diff_pp
for dim, title_dim in [("country", "country"), ("device_type", "device"), ("tenure", "tenure (months)")]:
    d = ss[ss.dimension == dim]
    # "clearly" above or below: the 95% range excludes the overall rise
    above = d[d.diff_low_pp > overall].segment.tolist()
    below = d[d.diff_high_pp < overall].segment.tolist()
    parts_t = ([f"{', '.join(above)} clearly above"] if above else []) + \
              ([f"{', '.join(below)} clearly below"] if below else [])
    where = "; ".join(parts_t) if parts_t else "no group clearly differs from"
    fig = charts.bar(d.segment, d.diff_pp * 10,
                     f"Extra churn by {title_dim}: {where} the overall rise of {overall * 10:.0f} per 1,000",
                     highlight=above,
                     ylabel="extra churns per 1,000 renewals, tenure-matched",
                     source=SRC + "; Nov 2025-Feb 2026 vs May-Jul 2026; bars show 95% range")
    ax = fig.axes[0]
    ax.errorbar(range(len(d)), d.diff_pp * 10,
                yerr=[(d.diff_pp - d.diff_low_pp) * 10, (d.diff_high_pp - d.diff_pp) * 10],
                fmt="none", ecolor="#333333", capsize=4, lw=1)
    ax.axhline(overall * 10, color="#333333", ls=":", lw=1)
    ax.annotate("overall", xy=(1, overall * 10), xycoords=("axes fraction", "data"),
                xytext=(4, 0), textcoords="offset points", va="center", fontsize=9,
                color="#333333")
    charts.save(fig, CH / f"churn_rise_by_{dim}.png")

bd = by_due[by_due.dimension.isin(["all", "tenure"])]
months = sorted(bd.due_month.unique())
def gain_line(bands):
    sel = bd[(bd.dimension == "tenure") & bd.segment.isin(bands)]
    return sel.groupby("due_month").gain_usd.sum().reindex(months) / 1000


lines = {"All subscribers": bd[bd.dimension == "all"].set_index("due_month").gain_usd
         .reindex(months) / 1000,
         "Months 1-6": gain_line(["1", "2-3", "4-6"]),
         "Months 7-12": gain_line(["7-12"]),
         "Months 13+": gain_line(["13-24", "25+"])}
pd.DataFrame(lines).mul(1000).rename_axis("due_month").reset_index() \
    .to_csv(OUT / "observed_gain_by_due_month_grouped.csv", index=False)
first, last = lines["All subscribers"].iloc[0], lines["All subscribers"].iloc[-1]
fig = charts.line(months, lines,
                  f"Monthly gain from the increase fell from \\${first:.1f}k to \\${last:.1f}k; "
                  f"subscribers in months 1-6 were below zero by July",
                  highlight=["All subscribers", "Months 1-6"],
                  ylabel="\\$ thousands vs \\$10 at Nov-Feb churn",
                  source=SRC + "; base charged in the 30 days to 2026-02-28")
fig.axes[0].axhline(0, color="#333333", lw=0.8)
charts.save(fig, CH / "observed_gain_by_due_month.png")

# ---------------------------------------------------------------- rollback reach (sizing only)
# Who a first-year rollback would reach at the window end (2026-07-31), from payments only:
# monthly subscribers charged in the 30 days to that date. Trial users are already excluded
# and nothing after 2026-07-31 is read (user's request), so trial converters, which only
# exist from 2026-08-15, cannot be counted here.
live = mp[(mp.payment_date > WINDOW_END - pd.Timedelta(days=30))
          & (mp.payment_date <= WINDOW_END)].copy()
assert live.subscription_id.is_unique
live["group"] = np.where(live.spike_block, "bulk 2025-09-17 (not measured)",
                np.where(live.start_date.dt.normalize() == pd.Timestamp("2026-07-30"),
                         "bulk 2026-07-30 (not measured)", "organic, no trial (measured)"))
live["first_year"] = (live.payment_date + pd.Timedelta(days=30) - live.start_date).dt.days < 365
reach = live.groupby(["group", "first_year"]).size().unstack(fill_value=0) \
    .rename(columns={True: "first_year", False: "past_first_year"})
reach.reset_index().to_csv(OUT / "rollback_reach_2026_07_31.csv", index=False)
say(checks.parts_sum_to_total(reach[["first_year", "past_first_year"]].sum(axis=1), len(live)))

# ---------------------------------------------------------------- print aggregates
pd.set_option("display.width", 200)
h = headline.iloc[0]
print(f"\nHEADLINE: churn per renewal {h.churn_cmp:.2%} after vs {h.churn_base_tenure_matched:.2%} "
      f"before (tenure-matched): {h.diff_pp:+.2f} pp [{h.diff_low_pp:+.2f}, {h.diff_high_pp:+.2f}], "
      f"{h.rel_change:+.0%} relative; renewals {h.renewals_base:,} before, {h.renewals_cmp:,} after")
print(headline[["sample", "baseline", "compared", "churn_base_tenure_matched", "churn_cmp",
                "diff_pp", "diff_low_pp", "diff_high_pp", "rel_change"]].round(4).to_string())
print("\nSEGMENTS vs before:")
print(sb[["dimension", "segment", "renewals_cmp", "churn_base_tenure_matched", "churn_cmp",
          "diff_pp", "diff_low_pp", "diff_high_pp", "rel_change"]].round(4).to_string())
print("\nSEGMENTS steady after vs clean before:")
print(ss[["dimension", "segment", "renewals_cmp", "churn_base_tenure_matched", "churn_cmp",
          "diff_pp", "diff_low_pp", "diff_high_pp", "rel_change"]].round(4).to_string())
print("\nSEGMENTS vs year earlier:")
print(segments[segments.baseline == "year_earlier"][["dimension", "segment", "churn_base_tenure_matched",
      "churn_cmp", "diff_pp", "diff_low_pp", "diff_high_pp"]].round(4).to_string())
print("\nMONEY (12 months from 2026-07-31):")
print(money.round(3).to_string())
print("\nOBSERVED Mar-Jul 2026 revenue, existing base:")
print(observed.round(1).to_string())
print(by_due[by_due.dimension.isin(["all", "tenure"])].pivot_table(
    index=["dimension", "segment"], columns="due_month", values="gain_usd").round(0).to_string())
print("\nROLLBACK REACH on 2026-07-31 (monthly, sizing only):")
print(reach.to_string())
print("\nNEW PAID STARTS by window:")
print(sw.round(3).T.to_string())
print("\nANNUAL renewals:")
print(an.round(3).to_string())
print("\nBy tenure x window:")
print(by_ten.round(4).to_string())
