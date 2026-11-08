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

ROOT = Path(__file__).resolve().parents[3]
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
                    "spike_block"]], on="subscription_id", how="inner")
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
        "diff_pp": diff * 100, "diff_low_pp": (diff - 1.96 * se) * 100,
        "diff_high_pp": (diff + 1.96 * se) * 100,
        "rel_change": diff / churn_a if churn_a else np.nan,
    }


# ---------------------------------------------------------------- headline
rows = []
for label, df in [("main (excl. 2025-09-17 block)", ren), ("incl. 2025-09-17 block", ren_all)]:
    for a, b in [("before", "after"), ("year_earlier", "after"), ("year_earlier", "before"),
                 ("before_clean", "after"), ("before_clean", "after_steady"),
                 ("before", "after_steady")]:
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
series = pd.DataFrame({
    "renewals_main": s_main.renewals, "churn_main": s_main.churns / s_main.renewals,
    "renewals_all": s_all.renewals, "churn_all": s_all.churns / s_all.renewals,
}).reset_index()
series.to_csv(OUT / "churn_by_due_month.csv", index=False)

# ---------------------------------------------------------------- segments
seg_rows = []
for dim in ["country", "device_type", "tenure"]:
    for val, df in ren.groupby(dim, observed=True):
        for a, b in [("before", "after"), ("year_earlier", "after"),
                     ("before_clean", "after_steady")]:
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
    parts = segments[(segments.dimension == dim) & (segments.baseline == "before")].renewals_cmp
    say(checks.parts_sum_to_total(parts, total_after))

# country x device cross, before vs after only
cross = []
for (c, d), df in ren.groupby(["country", "device_type"]):
    res = std_compare(df)
    if res:
        cross.append({"country": c, "device_type": d, **res})
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
base = base[~base.spike_block]
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


money_rows = money_for("before", "after") + money_for("before_clean", "after_steady")
money = pd.DataFrame(money_rows)
money.to_csv(OUT / "money_by_segment.csv", index=False)
m1 = money[money.baseline == "before"]
for dim in ["country", "device_type", "tenure"]:
    say(checks.parts_sum_to_total(m1[m1.dimension == dim].active_base_2026_07_31,
                                  m1[m1.dimension == "all"].active_base_2026_07_31.iloc[0]))

# ---------------------------------------------------------------- new starts
paid = subs[(subs.plan != "free") & ~subs.bulk_block].copy()
paid["start_month"] = paid.start_date.dt.to_period("M")
paid["window"] = None
for name in MAIN_WINDOWS:
    a, b = WINDOWS[name]
    paid.loc[(paid.start_date >= a) & (paid.start_date <= b), "window"] = name
starts_m = paid.groupby(["start_month", "plan"]).size().unstack(fill_value=0)
starts_m = starts_m.loc["2025-03":"2026-07"].reset_index()
starts_m["start_month"] = starts_m.start_month.astype(str)
starts_m["annual_share"] = starts_m.annual / (starts_m.annual + starts_m.monthly)
starts_m.to_csv(OUT / "new_paid_starts_by_month.csv", index=False)
months_in = {"year_earlier": 5, "before": 6, "after": 5}
sw = paid[paid.window.notna()].groupby(["window", "plan"]).size().unstack(fill_value=0)
sw["months"] = [months_in[w] for w in sw.index]
sw["monthly_per_month"] = sw.monthly / sw.months
sw["annual_per_month"] = sw.annual / sw.months
sw["annual_share"] = sw.annual / (sw.annual + sw.monthly)
n_a, n_b = sw.loc["after", ["annual", "monthly"]].sum(), sw.loc["before", ["annual", "monthly"]].sum()
p_a, p_b = sw.loc["after", "annual_share"], sw.loc["before", "annual_share"]
se_sh = np.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
sw["annual_share_diff_vs_before_pp"] = (sw.annual_share - p_b) * 100
sw.loc["after", "diff_low_pp"] = (p_a - p_b - 1.96 * se_sh) * 100
sw.loc["after", "diff_high_pp"] = (p_a - p_b + 1.96 * se_sh) * 100
sw["monthly_per_month_rel_vs_before"] = sw.monthly_per_month / sw.loc["before", "monthly_per_month"] - 1
sw.reset_index().to_csv(OUT / "new_paid_starts_by_window.csv", index=False)
sc = (paid[paid.window.isin(["before", "after"])].groupby(["country", "window", "plan"]).size()
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
charts.save(fig, CH / "churn_by_due_month.png")

sb = segments[segments.baseline == "before"]
ss = segments[segments.baseline == "before_clean"]
for dim, title_dim in [("country", "country"), ("device_type", "device"), ("tenure", "tenure (months)")]:
    d = sb[sb.dimension == dim]
    top = d.loc[d.diff_pp.idxmax(), "segment"]
    fig = charts.bar(d.segment, d.diff_pp * 10,
                     f"Extra churn after the increase by {title_dim}: largest in {top}",
                     highlight=top,
                     ylabel="extra churns per 1,000 renewals, tenure-matched",
                     source=SRC)
    charts.save(fig, CH / f"churn_rise_by_{dim}.png")

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
print("\nNEW PAID STARTS by window:")
print(sw.round(3).to_string())
print("\nANNUAL renewals:")
print(an.round(3).to_string())
print("\nBy tenure x window:")
print(by_ten.round(4).to_string())
