"""Did the March 2026 monthly price increase ($10 to $12) hurt retention, and for whom?

Run from the repo root: poetry run python outputs/2026-11-07_march-price-retention-v1/analysis.py

Method (see frame.md):
- Monthly churn = paid subscriptions active at the start of a month that end during it.
- Split by plan and by tenure at the start of the month.
- Baseline Oct 2025 to Feb 2026 (after the October 2025 end-date recording change),
  after period Mar to Jul 2026. August 2026 end dates are recorded differently (all `canceled`,
  some ending one to two months after the last payment; review A1), so August is shown on its
  own and kept out of the after window. September 2026 is open: data ends on the 24th.
- Difference-in-differences: change in monthly churn minus the annual plan's change. The annual
  plan's all-tenure change is used for every monthly band, not the same-tenure annual change:
  annual customers leave only at renewal, so their per-band rates are near zero and noisy. The
  same-tenure annual change is saved alongside (did_monthly_vs_annual_by_tenure.csv).
- Start cohort: newer bands split into customers who joined at $10 (before 2026-03-01) and at $12.
- Independent check from payments: share of monthly payers in a month who pay again next month.
- Money: six months of revenue from monthly subscribers active on 2026-03-01, at $12 with the
  churn seen after the change, against $10 with baseline churn plus the annual plan's trend.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from helpers import charts, checks  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
CH = RUN / "charts"
OUT.mkdir(exist_ok=True)
TODAY = pd.Timestamp("2026-09-24")
BASE = pd.period_range("2025-10", "2026-02", freq="M")
POST = pd.period_range("2026-03", "2026-07", freq="M")
AUG = pd.period_range("2026-08", "2026-08", freq="M")
YEAR_BASE = pd.period_range("2024-10", "2025-02", freq="M")
YEAR_POST = pd.period_range("2025-03", "2025-08", freq="M")
MONTHS = pd.period_range("2024-10", "2026-08", freq="M")
BANDS = [(0, 2, "0-2 months"), (3, 5, "3-5 months"), (6, 11, "6-11 months"),
         (12, 23, "12-23 months"), (24, 999, "24+ months")]
BAND_ORDER = [b[2] for b in BANDS]
OLD_PRICE, NEW_PRICE = 10.0, 12.0
HORIZON = 6
INTRO_MONTHS = 3  # introductory price lasts for tenure months 0-2
RNG = np.random.default_rng(20260924)
N_BOOT = 1000
PRICE_DAY = pd.Timestamp("2026-03-01")
SOURCE = "Source: subscriptions.csv, payments.csv; analysis.py"
results_log = []


def band_of(months):
    out = pd.Series(index=months.index, dtype=object)
    for lo, hi, name in BANDS:
        out[(months >= lo) & (months <= hi)] = name
    return out


def log_check(name, res):
    print(f"[check] {name}: {res['summary']}")
    results_log.append({"check": name, "ok": res["ok"], "summary": res["summary"]})


# ---------------------------------------------------------------- load
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])

log_check("payments join onto subscriptions", checks.join_fan_out(
    pays, subs[["subscription_id", "plan", "start_date"]], "subscription_id"))
log_check("payment_date edges", checks.date_boundaries(pays, "payment_date"))
log_check("subscriptions end_date edges", checks.date_boundaries(subs.dropna(subset=["end_date"]), "end_date"))

# Compare on dates (quirk: timestamps everywhere).
subs["start"] = subs.start_date.dt.normalize()
subs["end"] = subs.end_date.dt.normalize()
# Free plans never end: out. Scheduled starts after today: out. Future end dates: still active.
paid = subs[(subs.plan != "free") & (subs.start <= TODAY)].copy()
paid.loc[paid.end > TODAY, "end"] = pd.NaT
has_pay = paid.subscription_id.isin(pays.subscription_id)
sep25 = paid.start.dt.to_period("M") == pd.Period("2025-09", "M")
print(f"Paid subscriptions: {len(paid):,} ({(paid.plan == 'monthly').sum():,} monthly, "
      f"{(paid.plan == 'annual').sum():,} annual); free plans excluded.")

# Recording check (correction 2026-11-06): how end dates are logged, by end month.
ended = subs.dropna(subset=["end_date"]).copy()
ended["midnight_time"] = ended.end_date == ended.end_date.dt.normalize()
stab = checks.stable_over_time(ended[ended.end_date >= "2024-01-01"], "end_date", "midnight_time")
log_check("end_date recording over time", stab)
stab["level_by_period"].rename("share_midnight").to_csv(OUT / "end_date_recording.csv")


# ---------------------------------------------------------------- monthly churn panel
def churn_panel(frame):
    rows = []
    for m in MONTHS:
        ms, me = m.start_time, m.end_time.normalize()
        at = frame[(frame.start < ms) & (frame.end.isna() | (frame.end >= ms))]
        months = ((ms - at.start).dt.days / 30.4375).astype(int)
        churned = at.end.notna() & (at.end <= me)
        g = pd.DataFrame({"plan": at.plan.values, "band": band_of(months).values,
                          "cohort": np.where(at.start < PRICE_DAY, "joined at $10", "joined at $12"),
                          "churned": churned.values})
        agg = g.groupby(["plan", "band", "cohort"]).churned.agg(at_risk="size", churned="sum").reset_index()
        agg["month"] = str(m)
        rows.append(agg)
    return pd.concat(rows, ignore_index=True)


panel = churn_panel(paid)
panel.to_csv(OUT / "churn_monthly_by_plan_tenure.csv", index=False)

# Parts sum to totals: band counts add back to the at-risk base per month.
tot = sum(((paid.start < m.start_time) & (paid.end.isna() | (paid.end >= m.start_time))).sum() for m in MONTHS)
log_check("tenure bands sum to the at-risk base", checks.parts_sum_to_total(panel.at_risk, tot))

by_plan = panel.groupby(["month", "plan"])[["at_risk", "churned"]].sum().reset_index()
by_plan["churn_rate"] = by_plan.churned / by_plan.at_risk
by_plan.to_csv(OUT / "churn_monthly_by_plan.csv", index=False)


def period_rates(pnl, periods, label):
    x = pnl[pnl.month.isin([str(p) for p in periods])]
    a = x.groupby(["plan", "band"])[["at_risk", "churned"]].sum()
    tot_ = x.groupby("plan")[["at_risk", "churned"]].sum()
    tot_["band"] = "All tenures"
    a = pd.concat([a.reset_index(), tot_.reset_index()])
    a["period"] = label
    return a


def did_table(pnl, base, post):
    r = pd.concat([period_rates(pnl, base, "before"), period_rates(pnl, post, "after")])
    w = r.pivot_table(index=["plan", "band"], columns="period", values=["at_risk", "churned"]).reset_index()
    w.columns = ["plan", "band", "at_risk_after", "at_risk_before", "churned_after", "churned_before"]
    w["rate_before"] = w.churned_before / w.at_risk_before
    w["rate_after"] = w.churned_after / w.at_risk_after
    w["change_pp"] = (w.rate_after - w.rate_before) * 100
    w["change_rel"] = w.rate_after / w.rate_before - 1
    w["se_pp"] = 100 * np.sqrt(w.rate_before * (1 - w.rate_before) / w.at_risk_before
                               + w.rate_after * (1 - w.rate_after) / w.at_risk_after)
    ann = w[(w.plan == "annual") & (w.band == "All tenures")].iloc[0]
    mon = w[w.plan == "monthly"].copy()
    mon["annual_change_pp"] = ann.change_pp
    same = w[w.plan == "annual"].set_index("band").change_pp
    mon["annual_same_tenure_change_pp"] = mon.band.map(same)
    mon["did_pp"] = mon.change_pp - ann.change_pp
    se = np.sqrt(mon.se_pp ** 2 + ann.se_pp ** 2)
    mon["did_lo_pp"], mon["did_hi_pp"] = mon.did_pp - 1.96 * se, mon.did_pp + 1.96 * se
    return w, mon


rates, did = did_table(panel, BASE, POST)
did["band"] = pd.Categorical(did.band, BAND_ORDER + ["All tenures"], ordered=True)
did = did.sort_values("band")
rates.to_csv(OUT / "churn_before_after_by_plan_tenure.csv", index=False)
did.to_csv(OUT / "did_monthly_vs_annual_by_tenure.csv", index=False)

# August 2026 on its own (recording differs; review A1), next to the after window.
aug = pd.concat([period_rates(panel, POST, "after (Mar-Jul 2026)"), period_rates(panel, AUG, "August 2026")])
aug["churn_rate"] = aug.churned / aug.at_risk
aug.to_csv(OUT / "churn_after_vs_august.csv", index=False)

# Start cohort: within each band, joined at $10 vs joined at $12, after window only.
coh = panel[(panel.plan == "monthly") & panel.month.isin([str(p) for p in POST])]
coh = coh.groupby(["band", "cohort"])[["at_risk", "churned"]].sum().reset_index()
coh["churn_rate"] = coh.churned / coh.at_risk
base_band = rates[(rates.plan == "monthly")].set_index("band").rate_before
coh["rate_before_all_joined_at_10"] = coh.band.map(base_band)
coh["change_pp"] = (coh.churn_rate - coh.rate_before_all_joined_at_10) * 100
coh.to_csv(OUT / "churn_after_by_tenure_and_start_cohort.csv", index=False)

# ---------------------------------------------------------------- payments-based retention (independent of end_date)
mp = pays.merge(paid[["subscription_id", "plan", "start"]], on="subscription_id")
mp = mp[mp.plan == "monthly"]
mp["m"] = mp.payment_date.dt.to_period("M")
pm = mp[["subscription_id", "m", "start"]].drop_duplicates(["subscription_id", "m"])
keys = set(zip(pm.subscription_id, pm.m))
pm["paid_next"] = [(s, m + 1) in keys for s, m in zip(pm.subscription_id, pm.m)]
pm["band"] = band_of(((pm.m.dt.start_time - pm.start).dt.days / 30.4375).astype(int).clip(lower=0)).values
# Last month that can be followed is July 2026: September 2026 is open.
pm = pm[pm.m <= pd.Period("2026-07", "M")]
pay_ret = pm.groupby(["m", "band"]).paid_next.agg(payers="size", paid_again="sum").reset_index()
pay_ret["m"] = pay_ret.m.astype(str)
pay_ret.to_csv(OUT / "payment_retention_monthly_by_tenure.csv", index=False)
pay_m = pm.groupby("m").paid_next.mean()


def pay_period(per, label):
    x = pm[pm.m.isin(per)]
    g = x.groupby("band").paid_next.agg(payers="size", paid_again="sum")
    g.loc["All tenures"] = [len(x), x.paid_next.sum()]
    g["stop_rate"] = 1 - g.paid_again / g.payers
    g["period"] = label
    return g.reset_index()


# Payment months: Feb 2026 payers are the last who renew at $10 (their next charge is $12),
# so the before window for "stopped paying next month" is Oct 2025 to Jan 2026.
PAY_BASE = pd.period_range("2025-10", "2026-01", freq="M")
PAY_TRANSITION = pd.period_range("2026-02", "2026-02", freq="M")
PAY_POST = pd.period_range("2026-03", "2026-07", freq="M")
pay_cmp = pd.concat([pay_period(PAY_BASE, "before"), pay_period(PAY_TRANSITION, "first $12 renewal"),
                     pay_period(PAY_POST, "after"),
                     pay_period(pd.period_range("2025-02", "2025-07", freq="M"), "a year earlier")])
pay_cmp.to_csv(OUT / "payment_stop_rate_by_period.csv", index=False)

# ---------------------------------------------------------------- seasonality: same months a year earlier
_, did_year = did_table(panel, YEAR_BASE, YEAR_POST)
did_year["band"] = pd.Categorical(did_year.band, BAND_ORDER + ["All tenures"], ordered=True)
did_year.sort_values("band").to_csv(OUT / "seasonality_year_earlier_did.csv", index=False)

# ---------------------------------------------------------------- robustness
robust = [did.assign(variant="main")]
for name, mask in [("without Sep 2025 starts", ~sep25), ("without paid subs that have no payments", has_pay)]:
    _, d = did_table(churn_panel(paid[mask]), BASE, POST)
    robust.append(d.assign(variant=name))
robust = pd.concat(robust)
robust["band"] = robust.band.astype(str)
robust[["variant", "band", "rate_before", "rate_after", "change_pp", "did_pp", "did_lo_pp", "did_hi_pp"]].to_csv(
    OUT / "robustness_did.csv", index=False)


# ---------------------------------------------------------------- money
# Two forms of a tenure-based rollback are sized (review A4):
#   1. Price cut for the monthly base on the analysis date (2026-09-24), by tenure band: $10 with
#      baseline churn plus the annual trend, against $12 with the churn seen after the change.
#   2. Introductory price: every new monthly starter pays $10 for their first 3 months, then $12.
# The 1 March 2026 base is also modelled over the six observed months, to check the model against
# months actually paid (review C1) and to show the observed answer next to the projected one.
# Money uses paying subscriptions only (review A2): rows with no payment would add months nobody paid.
MIN_CELL = 500  # smallest at-risk count for a joined-at-$12 rate to be used on its own
panel_pay = churn_panel(paid[has_pay])
POST_APR = pd.period_range("2026-04", "2026-07", freq="M")  # sensitivity: churn rises from April (review A5)
ann_shift = did.annual_change_pp.iloc[0] / 100  # annual plan's change, added to the baseline


def cells(pnl, periods, by_cohort):
    x = pnl[(pnl.plan == "monthly") & pnl.month.isin([str(p) for p in periods])]
    return x.groupby(["band", "cohort"] if by_cohort else "band")[["at_risk", "churned"]].sum()


def draw(cell, rng):
    """One bootstrap draw of a hazard table (binomial on each cell); rng=None returns the point rates."""
    p = cell.churned / cell.at_risk
    if rng is None:
        return p
    return rng.binomial(cell.at_risk, p) / cell.at_risk


def keep_hazard(band, joined_at_12, hp, hp12):
    """After-change monthly churn for a subscriber: the joined-at-$12 rate where that cell is large enough."""
    if joined_at_12 and (band, "joined at $12") in hp12.index and HP12_N.get(band, 0) >= MIN_CELL:
        return hp12[(band, "joined at $12")]
    return hp[band]


def band1(m):
    """Tenure band name for one tenure in months (fast scalar version of band_of)."""
    for lo, hi, name in BANDS:
        if lo <= m <= hi:
            return name


def months_alive(t0, joined12, horizon, hb, hp, hp12, rollback):
    """Expected paid months per subscriber over `horizon`, one charge a month while alive.

    Subscribers with the same starting tenure and price cohort share a path, so each path is
    computed once and mapped back.
    """
    key = pd.Series(list(zip(t0, joined12)))
    paths = {}
    for t, j in key.unique():
        alive, total = 1.0, 0.0
        for k in range(horizon):
            total += alive
            b = band1(t + k)
            hz = hb[b] + ann_shift if rollback else keep_hazard(b, j, hp, hp12)
            alive *= 1 - min(max(hz, 0), 1)
        paths[(t, j)] = total
    return key.map(paths).values


trial_users = set(pd.read_csv(ROOT / "data/trials.csv").user_id)


def base_at(day):
    b = paid[(paid.plan == "monthly") & has_pay & (paid.start < day) & (paid.end.isna() | (paid.end >= day))].copy()
    b["t0"] = ((day - b.start).dt.days / 30.4375).astype(int)
    b["band"] = band_of(b.t0).values
    b["joined12"] = b.start >= PRICE_DAY
    b["trial"] = b.user_id.isin(trial_users)
    return b


base_mar = base_at(PRICE_DAY)
base_today = base_at(TODAY)
print(f"Monthly paying base: {len(base_mar):,} on 2026-03-01, {len(base_today):,} on 2026-09-24 "
      f"(paid subscriptions with no payments left out).")

# New monthly starters a month, from the last complete month (August 2026), split by source
# (review A1): non-trial starts fell after July's one-month jump, and trial converts only exist
# from August. The Mar-Jul non-trial average is printed for context.
mstart = paid[(paid.plan == "monthly") & has_pay]
NEW_NONTRIAL_MARJUL = ((mstart.start >= PRICE_DAY) & (mstart.start < pd.Timestamp("2026-08-01"))
                       & ~mstart.user_id.isin(trial_users)).sum() / 5
NEW_NONTRIAL = ((mstart.start.dt.to_period("M") == pd.Period("2026-08", "M")) & ~mstart.user_id.isin(trial_users)).sum()
NEW_TRIAL = ((mstart.start.dt.to_period("M") == pd.Period("2026-08", "M")) & mstart.user_id.isin(trial_users)).sum()


def intro_total(horizon, starters, hb, hp, hp12):
    """Revenue over `horizon` months from `starters` new monthly customers a month: keep $12 vs $10 intro."""
    keep = intro = 0.0
    for entry in range(horizon):
        alive_k = alive_i = 1.0
        for k in range(horizon - entry):
            band = band1(k)
            hk = keep_hazard(band, True, hp, hp12)
            keep += NEW_PRICE * alive_k
            alive_k *= 1 - hk
            if k < INTRO_MONTHS:
                intro += OLD_PRICE * alive_i
                alive_i *= 1 - min(max(hb[band] + ann_shift, 0), 1)
            else:
                intro += NEW_PRICE * alive_i
                alive_i *= 1 - hk
    return starters * keep, starters * intro


def money(base, horizon, hb, hp, hp12, label):
    keep = months_alive(base.t0.values, base.joined12.values, horizon, hb, hp, hp12, rollback=False)
    roll = months_alive(base.t0.values, base.joined12.values, horizon, hb, hp, hp12, rollback=True)
    df = pd.DataFrame({"band": base.band.values, "keep": keep, "roll": roll})
    g = df.groupby("band").agg(subscribers=("keep", "size"), months_keep_12=("keep", "sum"),
                               months_rollback_10=("roll", "sum")).reset_index()
    g.loc[len(g)] = ["All tenures", len(df), df.keep.sum(), df.roll.sum()]
    # The newest band split by source (review A1). Trial converts get the non-trial $12 rate:
    # their own churn is not measurable yet (trials began 2026-08-01), so their rows are unmeasured.
    for src, mask in ([("0-2 months, trial converts (rate unmeasured)", base.trial.values),
                       ("0-2 months, non-trial", ~base.trial.values)] if label.startswith("base on 2026-09-24") else []):
        s = df[(df.band == "0-2 months").values & mask]
        g.loc[len(g)] = [src, len(s), s.keep.sum(), s.roll.sum()]
    g["revenue_keep_12"] = NEW_PRICE * g.months_keep_12
    g["revenue_rollback_10"] = OLD_PRICE * g.months_rollback_10
    g["form"] = label
    rows = [g]
    if label.startswith("base on 2026-09-24"):
        for name, n in [("Intro price, non-trial starters", NEW_NONTRIAL),
                        ("Intro price, trial converts (rate unmeasured)", NEW_TRIAL)]:
            k, i = intro_total(horizon, n, hb, hp, hp12)
            rows.append(pd.DataFrame([{"band": name, "subscribers": n * horizon, "months_keep_12": np.nan,
                                       "months_rollback_10": np.nan, "revenue_keep_12": k,
                                       "revenue_rollback_10": i,
                                       "form": label.replace("base on 2026-09-24", "introductory price, new starters")}]))
    out = pd.concat(rows, ignore_index=True)
    out["rollback_gain"] = out.revenue_rollback_10 - out.revenue_keep_12
    return out


cb = cells(panel_pay, BASE, False)
# Sensitivity (review A2): baseline churn without the September 2025 spike starters.
cb_nosep = cells(churn_panel(paid[has_pay & ~sep25]), BASE, False)
SCENARIOS = [("base on 2026-03-01, observed months", base_mar, POST, 6, cb),
             ("base on 2026-09-24", base_today, POST, 6, cb), ("base on 2026-09-24", base_today, POST, 12, cb),
             ("base on 2026-09-24, after window Apr-Jul", base_today, POST_APR, 6, cb),
             ("base on 2026-09-24, after window Apr-Jul", base_today, POST_APR, 12, cb),
             ("base on 2026-09-24, baseline without Sep 2025 starts", base_today, POST, 6, cb_nosep),
             ("base on 2026-09-24, baseline without Sep 2025 starts", base_today, POST, 12, cb_nosep)]
money_tables = []
for label, base, post, hz, cb in SCENARIOS:
    cp, cp12 = cells(panel_pay, post, False), cells(panel_pay, post, True)
    HP12_N = cp12.xs("joined at $12", level="cohort").at_risk.to_dict()
    point = money(base, hz, draw(cb, None), draw(cp, None), draw(cp12, None), label)
    sims = [money(base, hz, draw(cb, RNG), draw(cp, RNG), draw(cp12, RNG), label).set_index("band").rollback_gain
            for _ in range(N_BOOT)]
    sims = pd.concat(sims, axis=1)
    point["rollback_gain_lo"] = point.band.map(sims.quantile(0.025, axis=1))
    point["rollback_gain_hi"] = point.band.map(sims.quantile(0.975, axis=1))
    point["horizon_months"] = hz
    money_tables.append(point)
money_df = pd.concat(money_tables, ignore_index=True)

# Model check, per band (review C1): modelled $12 months for the 1 March base against months paid Mar-Aug.
MONEY_MONTHS = pd.period_range("2026-03", "2026-08", freq="M")
paid_m = (mp[mp.subscription_id.isin(base_mar.subscription_id) & mp.m.isin(MONEY_MONTHS)]
          .drop_duplicates(["subscription_id", "m"]).merge(base_mar[["subscription_id", "band"]])
          .groupby("band").size())
paid_m["All tenures"] = paid_m.sum()
mar = money_df[money_df.form == "base on 2026-03-01, observed months"].set_index("band")
model_ok = []
for band, r in mar.iterrows():
    res = checks.parts_sum_to_total([r.months_keep_12], paid_m[band], tolerance=0.05)
    log_check(f"modelled vs paid months, {band}", res)
    model_ok.append({"band": band, "modelled_months": r.months_keep_12, "paid_months": paid_m[band],
                     "paid_over_modelled": paid_m[band] / r.months_keep_12, "within_5pct": res["ok"]})
model_ok = pd.DataFrame(model_ok)
model_ok.to_csv(OUT / "money_model_vs_paid_by_tenure.csv", index=False)
# The model overstates paid months on the keep ($12) side in most bands, which leans against a
# rollback (review C1). Correct the keep side only by paid/modelled from the 1 March base; the
# newest-band splits and the intro rows take the 0-2 month factor. For the 1 March base the keep
# side is replaced by months actually paid.
factor = model_ok.set_index("band").paid_over_modelled
fband = money_df.band.where(money_df.band.isin(factor.index), "0-2 months")
money_df["paid_over_modelled"] = fband.map(factor)
money_df["revenue_keep_12_calibrated"] = money_df.revenue_keep_12 * money_df.paid_over_modelled
is_mar = money_df.form == "base on 2026-03-01, observed months"
money_df.loc[is_mar, "revenue_keep_12_calibrated"] = NEW_PRICE * money_df.loc[is_mar, "band"].map(paid_m)
money_df["rollback_gain_calibrated"] = money_df.revenue_rollback_10 - money_df.revenue_keep_12_calibrated
money_df["rollback_gain_calibrated_lo"] = money_df.rollback_gain_lo + money_df.rollback_gain_calibrated - money_df.rollback_gain
money_df.to_csv(OUT / "money_rollback_by_tenure.csv", index=False)

# Intro price over a range of new-starter volumes. The intro rows are linear in the number of
# starters a month, so the August-based gain (and its interval) scales to each complete month's
# non-trial volume from March to August 2026. September 2026 is open and left out.
vol = (mstart[(mstart.start >= PRICE_DAY) & (mstart.start < pd.Timestamp("2026-09-01"))
              & ~mstart.user_id.isin(trial_users)]
       .start.dt.to_period("M").value_counts().sort_index())
# Trials launched on 2026-08-01 and changed who starts without a trial (review A2): months before
# August describe the old non-trial group, and the $12 churn rate used for the intro rows was measured
# on it. August and September's pace describe the group a rollback would reach now.
sep_n = ((mstart.start.dt.to_period("M") == pd.Period("2026-09", "M")) & (mstart.start <= TODAY)
         & ~mstart.user_id.isin(trial_users)).sum()
SEP_PACE = sep_n * 30 / 24
intro_rows = money_df[money_df.form.str.startswith("introductory price")
                      & (money_df.band == "Intro price, non-trial starters")]
vr = []
for r in intro_rows.itertuples():
    per = 1 / NEW_NONTRIAL
    for m, n in list(vol.items()) + [("2026-09, first 24 days scaled to 30", SEP_PACE),
                                     ("median Mar-Aug", vol.median()), ("lowest", vol.min()), ("highest", vol.max())]:
        vr.append({"form": r.form, "horizon_months": r.horizon_months, "volume_month": str(m),
                   "before_trial_launch": str(m) < "2026-08" or str(m).startswith("median") or str(m) == "highest",
                   "starters_per_month": n, "rollback_gain": r.rollback_gain * per * n,
                   "rollback_gain_lo": r.rollback_gain_lo * per * n, "rollback_gain_hi": r.rollback_gain_hi * per * n,
                   "rollback_gain_calibrated": r.rollback_gain_calibrated * per * n})
intro_range = pd.DataFrame(vr)
intro_range.to_csv(OUT / "intro_price_by_starter_volume.csv", index=False)

for label in money_df.form.unique():
    for hz in money_df[money_df.form == label].horizon_months.unique():
        x = money_df[(money_df.form == label) & (money_df.horizon_months == hz) & money_df.band.isin(BAND_ORDER)]
        tot_ = money_df[(money_df.form == label) & (money_df.horizon_months == hz) & (money_df.band == "All tenures")]
        if len(tot_):
            log_check(f"money bands sum to total, {label}, {hz} months",
                      checks.parts_sum_to_total(x.rollback_gain, tot_.rollback_gain.iloc[0]))

# Has the extra churn among survivors held? Monthly churn for subscribers who joined at $10, by month.
held = panel[(panel.plan == "monthly") & (panel.cohort == "joined at $10")
             & panel.month.isin([str(p) for p in BASE.append(POST)])]
held = held.groupby("month")[["at_risk", "churned"]].sum().reset_index()
held["churn_rate"] = held.churned / held.at_risk
held.to_csv(OUT / "churn_by_month_joined_at_10.csv", index=False)

# Decision rule from the frame: extra churn clearly above zero AND $10 beats $12 (interval above zero).
did_s = did.assign(band=did.band.astype(str))
rob_apr = did_table(panel, BASE, POST_APR)[1]
rob_apr["band"] = rob_apr.band.astype(str)
robust_apr = rob_apr[["band", "did_pp", "did_lo_pp", "did_hi_pp"]].rename(
    columns=lambda c: c + "_apr_jul" if c != "band" else c)
robust_apr.to_csv(OUT / "did_after_window_apr_jul.csv", index=False)
rule = money_df.merge(did_s[["band", "did_pp", "did_lo_pp", "did_hi_pp"]], on="band", how="left")
# Introductory price acts on the newest band, so it carries the 0-2 month churn change.
first = did_s.set_index("band").loc["0-2 months"]
for c in ["did_pp", "did_lo_pp", "did_hi_pp"]:
    rule.loc[rule.form.str.startswith("introductory price"), c] = first[c]
# Apr-Jul scenarios carry the Apr-Jul churn change.
apr = rob_apr.set_index("band")
is_apr = rule.form.str.endswith("after window Apr-Jul")
for c in ["did_pp", "did_lo_pp", "did_hi_pp"]:
    rule.loc[is_apr & rule.band.isin(apr.index), c] = rule.loc[is_apr, "band"].map(apr[c])
    rule.loc[is_apr & rule.form.str.startswith("introductory price"), c] = apr.loc["0-2 months", c]
for c in ["did_pp", "did_lo_pp", "did_hi_pp"]:
    rule.loc[rule.band.str.startswith("0-2 months,"), c] = rule.loc[rule.band.str.startswith("0-2 months,"), "form"].map(
        lambda f: (apr if f.endswith("Apr-Jul") else did_s.set_index("band")).loc["0-2 months", c])
rule["churn_clearly_up"] = rule.did_lo_pp > 0
rule["rollback_pays"] = rule.rollback_gain_lo > 0
rule["rollback_recommended"] = rule.churn_clearly_up & rule.rollback_pays
rule["rollback_pays_if_keep_calibrated"] = rule.rollback_gain_calibrated_lo > 0
# A yes that holds only at 12 months, not at 6, rests on the projection: tentative.
six = rule[rule.horizon_months == 6].set_index(["form", "band"]).rollback_recommended
rule["tentative_projection_only"] = [
    bool(r.rollback_recommended and r.horizon_months == 12 and not six.get((r.form, r.band), False))
    for r in rule.itertuples()]
rule = rule[["form", "horizon_months", "band", "subscribers", "did_pp", "did_lo_pp", "did_hi_pp",
             "rollback_gain", "rollback_gain_lo", "rollback_gain_hi", "rollback_gain_calibrated",
             "rollback_gain_calibrated_lo", "churn_clearly_up", "rollback_pays", "rollback_recommended",
             "rollback_pays_if_keep_calibrated", "tentative_projection_only"]]
rule.to_csv(OUT / "decision_rule_by_tenure.csv", index=False)
pd.DataFrame(results_log).to_csv(OUT / "checks.csv", index=False)

# ---------------------------------------------------------------- charts
bp = by_plan.pivot(index="month", columns="plan", values="churn_rate").loc["2025-10":"2026-07"] * 100
charts.save(charts.line(bp.index, {"Monthly plan": bp.monthly, "Annual plan": bp.annual},
                        "Monthly-plan churn rose after the March 2026 price change; annual stayed flat",
                        highlight="Monthly plan", ylabel="Monthly churn, % of active (to July 2026)",
                        source=SOURCE + "; August 2026 left out (end dates recorded differently)"),
            CH / "churn_by_plan.png")
dd = did[did.band != "All tenures"]
up = [str(b) for b in dd.band[dd.did_lo_pp > 0]]
fig = charts.bar([str(b) for b in dd.band], dd.did_pp,
                 "Churn rose in every tenure group, least for 12-23 months",
                 highlight=up, ylabel="Change in monthly churn vs annual plan, pp (95% interval)", source=SOURCE)
ax = fig.axes[0]
for txt in list(ax.texts):
    txt.remove()
ax.errorbar(range(len(dd)), dd.did_pp, yerr=[dd.did_pp - dd.did_lo_pp, dd.did_hi_pp - dd.did_pp],
            fmt="none", ecolor=charts.TEXT, capsize=4, linewidth=1)
for i, v in enumerate(dd.did_pp):
    ax.annotate(f"{v:.1f}", (i, dd.did_hi_pp.iloc[i]), xytext=(0, 4), textcoords="offset points",
                ha="center", color=charts.TEXT)
charts.save(fig, CH / "did_by_tenure.png")
for old in CH.glob("rollback_gain_by_tenure_*m.png"):
    old.unlink()
for hz in (6, 12):
    mm = rule[(rule.form.isin(["base on 2026-09-24", "introductory price, new starters"]))
              & (rule.horizon_months == hz) & (rule.band != "All tenures")]
    order = {b: i for i, b in enumerate(BAND_ORDER + ["Intro price, non-trial starters",
                                                      "Intro price, trial converts (rate unmeasured)"])}
    mm = mm[mm.band.isin(order)].sort_values("band", key=lambda s: s.map(order))
    names = [f"Cut to $10, {b}" if b in BAND_ORDER else
             ("Intro $10, non-trial starters" if "non-trial" in b else "Intro $10, trial converts*")
             for b in mm.band]
    pays_ = [n for n, lo in zip(names, mm.rollback_gain_lo) if lo > 0]
    title = (f"Over {hz} months every rollback option loses revenue" if not pays_ else
             f"Projected over {hz} months, only the newest customers and an intro price gain (tentative)")
    fig = charts.bar(names, mm.rollback_gain.round(0), title, highlight=pays_, horizontal=True,
                     source=SOURCE + f"; {hz}-month revenue, rollback minus keep, $; blue = interval above zero; *churn rate unmeasured")
    lo_, hi_ = fig.axes[0].get_xlim()
    fig.axes[0].set_xlim(lo_ * 1.25, hi_ * 1.15)
    charts.save(fig, CH / f"rollback_gain_{hz}m.png")

# ---------------------------------------------------------------- headline print (aggregates only)
pd.set_option("display.width", 200)
print("\nMonthly churn, before (Oct 2025-Feb 2026) vs after (Mar-Jul 2026), pp = percentage points:")
print(rates[rates.band == "All tenures"][["plan", "rate_before", "rate_after", "change_pp", "change_rel"]].round(4).to_string(index=False))
print("\nAfter window vs August 2026 on its own (monthly, all tenures):")
print(aug[(aug.plan == "monthly") & (aug.band == "All tenures")][["period", "at_risk", "churned", "churn_rate"]].round(4).to_string(index=False))
print("\nAfter window by start cohort (monthly):")
print(coh.round(4).to_string(index=False))
print("\nMonthly plan by tenure, change minus annual change (DiD, pp, 95% interval):")
print(did[["band", "rate_before", "rate_after", "change_pp", "change_rel", "did_pp", "did_lo_pp", "did_hi_pp"]].round(4).to_string(index=False))
print("\nStopped paying next month (payments), monthly plan:")
print(pay_cmp[pay_cmp.band == "All tenures"][["period", "payers", "stop_rate"]].round(4).to_string(index=False))
print(pay_cmp.pivot(index="band", columns="period", values="stop_rate").round(4).to_string())
print("\nSame months a year earlier (DiD, pp; before the end-date recording change, context only):")
print(did_year[["band", "rate_before", "rate_after", "change_pp", "did_pp"]].round(4).to_string(index=False))
print("\nRobustness (DiD pp):")
print(robust.pivot(index="band", columns="variant", values="did_pp").round(3).to_string())
print("\nAfter window Apr-Jul 2026 (DiD pp):")
print(robust_apr.round(3).to_string(index=False))
print("\nMonthly churn, joined at $10, by month:")
print(held.round(4).to_string(index=False))
print(f"\nNew monthly starters a month: {NEW_NONTRIAL:.0f} non-trial and {NEW_TRIAL:.0f} trial converts in Aug 2026; "
      f"non-trial average Mar-Jul {NEW_NONTRIAL_MARJUL:.0f}.")
print("\nModel vs paid months (1 March base):")
print(model_ok.round(3).to_string(index=False))
print("\nIntro price, non-trial starters, by monthly volume (main scenario):")
print(intro_range[intro_range.form == "introductory price, new starters"].round(0).to_string(index=False))
print("\nMoney and decision rule (rollback gain = rollback revenue minus keep revenue, $):")
print(rule.drop(columns=["did_lo_pp", "did_hi_pp", "did_pp", "rollback_gain_hi"]).round(0).to_string(index=False))
