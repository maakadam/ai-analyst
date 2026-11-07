"""Are the 14-day trials converting well enough to keep them next quarter?

Run from the repo root: poetry run python outputs/2026-11-07_trial-conversion/analysis.py

Method (see frame.md, plan approved by the user on 2026-11-07):
- Outcome: the share of signups who end up on a paid plan (monthly or annual). Pre-trial payers
  take a median of about 45 days to pay, so a fixed 30-day measure would favour trials on timing.
- Main comparison: trial users against non-trial signups from the same signup days. About half of
  signups since 2026-08-01 got a trial. Only trials whose 14-day window ended by 2026-09-24 count,
  so the window is signups 2026-08-01 to 2026-09-10 for both groups (quirk "Trials mature late").
- Second baseline: weekly paid share of signups 2026-03-01 to 2026-07-31 (same $12 price).
- Seasonality: Aug 2025 against Mar-Jul 2025 (before the Sep 2025 spike).
- Scheduled starts after 2026-09-24 (quirk "Future start dates") count as paid in the main read,
  because the plan is already set; a sensitivity counts only starts on or before 2026-09-24.
- Retention (warning sign only): share of monthly starts charged again on day 30, for starts old
  enough to have reached day 30. Read from payments, not end dates, so the October 2025 end-date
  recording change does not enter.
- Money: extra paying subscribers and revenue next quarter (13 weeks), with trials kept for about
  half of signups as now and for all signups; low, central and high cases with stated assumptions.
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

TODAY_END = pd.Timestamp("2026-09-24 23:59:59")
TODAY = pd.Timestamp("2026-09-24")
TRIAL_START = pd.Timestamp("2026-08-01")
MATURE_LAST_SIGNUP = TODAY - pd.Timedelta(days=14)  # 2026-09-10: trial window closed by today
BASE_START, BASE_END = pd.Timestamp("2026-03-01"), pd.Timestamp("2026-07-31")
SEAS_START, SEAS_END = pd.Timestamp("2025-03-01"), pd.Timestamp("2025-08-31")
WEEKS_PER_QUARTER = 13
PAID = ["monthly", "annual"]
SOURCE = "Source: users, subscriptions, trials, payments; data to 2026-09-24"


def share_ci(k, n, z=1.96):
    """Share with a Wilson 95% interval (holds up for small groups and shares near 0 or 1)."""
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, centre - half, centre + half


def say(text):
    print(text)


# ---------- Load ----------
users = pd.read_csv(ROOT / "data/users.csv", parse_dates=["signup_date"])
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
trials = pd.read_csv(ROOT / "data/trials.csv", parse_dates=["started_at", "ends_at", "outcome_at"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])

say("== Checks ==")
fo1 = checks.join_fan_out(users, subs, "user_id")
fo2 = checks.join_fan_out(users, trials, "user_id")
say(fo1["summary"])
say(fo2["summary"])
assert fo1["ok"] and fo2["ok"]

d = users.merge(subs, on="user_id", how="left").merge(trials, on="user_id", how="left")
assert len(d) == len(users)
d["signup_day"] = d.signup_date.dt.normalize()
d["has_trial"] = d.trial_id.notna()
d["paid"] = d.plan.isin(PAID)
d["paid_started"] = d.paid & (d.start_date <= TODAY_END)
d["scheduled_paid"] = d.paid & (d.start_date > TODAY_END)
d["week"] = d.signup_day.dt.to_period("W-SUN")

# Trials start on the signup date (checked in code).
gap_days = (d.loc[d.has_trial, "started_at"].dt.normalize() - d.loc[d.has_trial, "signup_day"]).dt.days
say(f"Trial start minus signup date: min {gap_days.min()} days, max {gap_days.max()} days.")

# ---------- Trial era window ----------
era = d[(d.signup_day >= TRIAL_START) & (d.signup_day <= TODAY)]
say(checks.date_boundaries(era, "signup_date", freq="W-SUN")["summary"])
tr_all = era[era.has_trial]
mat = checks.matured_only(tr_all, "ends_at", as_of=TODAY_END)
say(mat["summary"])
matured = mat["kept"]
open_in_matured = int(matured.outcome.isna().sum())
say(f"Matured trials with no outcome: {open_in_matured} (should be 0).")
assert open_in_matured == 0
last_matured_signup = matured.signup_day.max()
say(f"Last signup day with a matured trial: {last_matured_signup.date()}.")

win = era[era.signup_day <= MATURE_LAST_SIGNUP]
trial_grp = win[win.has_trial]
assert trial_grp.outcome.notna().all()
non_grp = win[~win.has_trial]
assert non_grp.plan.notna().all(), "every non-trial signup should have a subscription row"

# Trial outcome agrees with plan
agree = pd.crosstab(trial_grp.outcome, trial_grp.plan)
agree.to_csv(OUT / "trial_outcome_vs_plan.csv")
assert ((trial_grp.outcome == "converted") == trial_grp.paid).all()

# Recording check: is the paid outcome recorded the same way across signup months?
nt_hist = d[(~d.has_trial) & (d.signup_day >= "2025-01-01") & (d.signup_day <= TODAY)]
stab = checks.stable_over_time(nt_hist, "signup_date", "paid", freq="M")
say(stab["summary"])
stab["level_by_period"].rename("paid_share").to_csv(OUT / "paid_share_by_signup_month_non_trial.csv")

# ---------- Main comparison ----------
say("\n== Main comparison: signups 2026-08-01 to 2026-09-10 ==")
rows = []
for name, g in [("Trial users", trial_grp), ("Non-trial signups, same days", non_grp)]:
    n, k, k_started = len(g), int(g.paid.sum()), int(g.paid_started.sum())
    p, lo, hi = share_ci(k, n)
    rows.append({"group": name, "signups": n, "paid": k, "paid_share": p, "ci_low": lo, "ci_high": hi,
                 "paid_started_by_2026_09_24": k_started,
                 "scheduled_paid": int(g.scheduled_paid.sum())})
base = d[(d.signup_day >= BASE_START) & (d.signup_day <= BASE_END)]
assert not base.has_trial.any()
n, k = len(base), int(base.paid.sum())
p, lo, hi = share_ci(k, n)
rows.append({"group": "Signups Mar-Jul 2026 (before trials)", "signups": n, "paid": k, "paid_share": p,
             "ci_low": lo, "ci_high": hi, "paid_started_by_2026_09_24": int(base.paid_started.sum()),
             "scheduled_paid": int(base.scheduled_paid.sum())})
main = pd.DataFrame(rows)
main.to_csv(OUT / "paid_share_by_group.csv", index=False)

pt, pn, pb = main.paid_share.iloc[0], main.paid_share.iloc[1], main.paid_share.iloc[2]
nt, nn = main.signups.iloc[0], main.signups.iloc[1]
lift_pp = pt - pn
se_diff = np.sqrt(pt * (1 - pt) / nt + pn * (1 - pn) / nn)
lift = pd.DataFrame([
    {"comparison": "Trial vs non-trial, same days", "trial_share": pt, "comparison_share": pn,
     "diff_pp": 100 * lift_pp, "diff_pp_ci_low": 100 * (lift_pp - 1.96 * se_diff),
     "diff_pp_ci_high": 100 * (lift_pp + 1.96 * se_diff), "relative_pct": 100 * (pt / pn - 1)},
    {"comparison": "Trial vs Mar-Jul 2026 signups", "trial_share": pt, "comparison_share": pb,
     "diff_pp": 100 * (pt - pb), "diff_pp_ci_low": np.nan, "diff_pp_ci_high": np.nan,
     "relative_pct": 100 * (pt / pb - 1)},
    {"comparison": "Non-trial (same days) vs Mar-Jul 2026 signups", "trial_share": pn, "comparison_share": pb,
     "diff_pp": 100 * (pn - pb), "diff_pp_ci_low": np.nan, "diff_pp_ci_high": np.nan,
     "relative_pct": 100 * (pn / pb - 1)},
])
# No "started by 2026-09-24" sensitivity: most non-trial payers in the window start on the
# 2026-09-25 batch start date (review A2), so that cut measures timing, not conversion.

# Are plans on a batched, not-yet-started row firm? (review A1). Start dates are set in batches
# (quirk "Batched start dates"); check how many paid plans on the earlier batch days were charged.
pays_first = pays.merge(subs[["subscription_id", "start_date"]], on="subscription_id")
pays_first["day"] = (pays_first.payment_date.dt.normalize() - pays_first.start_date.dt.normalize()).dt.days
charged_ids = set(pays_first[(pays_first.day >= 0) & (pays_first.day <= 5)].subscription_id)
d["charged_at_start"] = d.subscription_id.isin(charged_ids)
d["start_day"] = d.start_date.dt.normalize()
firm_rows = []
for day in ["2025-09-17", "2026-07-30", "2026-09-25"]:
    g = d[(d.start_day == day) & d.paid]
    firm_rows.append({"batch_start_day": day, "paid_plans": len(g),
                      "charged_at_start": int(g.charged_at_start.sum()),
                      "share_charged": g.charged_at_start.mean(),
                      "signups_from": g.signup_day.min().date(), "signups_to": g.signup_day.max().date(),
                      "charge_observable_by_2026_09_24": pd.Timestamp(day) <= TODAY})
firm = pd.DataFrame(firm_rows)
firm.to_csv(OUT / "batch_start_firmness.csv", index=False)
past = firm[firm.charge_observable_by_2026_09_24]
worst_firm = past.share_charged.min()
for _, r in firm.iterrows():
    say(f"Batch start {r.batch_start_day}: {r.share_charged:.1%} of {r.paid_plans:,} paid plans charged at start "
        f"(signups {r.signups_from} to {r.signups_to})")

# Sensitivity 1: non-trial plans not yet started are paid only at the worst past batch rate.
nt_started = int(non_grp.paid_started.sum())
nt_sched = int(non_grp.scheduled_paid.sum())
pn_low = (nt_started + worst_firm * nt_sched) / len(non_grp)
lift.loc[len(lift)] = {"comparison": f"Sensitivity: trial vs non-trial, plans not yet started firm at {worst_firm:.0%} (worst past batch)",
                       "trial_share": pt, "comparison_share": pn_low, "diff_pp": 100 * (pt - pn_low),
                       "diff_pp_ci_low": np.nan, "diff_pp_ci_high": np.nan, "relative_pct": 100 * (pt / pn_low - 1)}
# Sensitivity 2: Mar-Jul 2026 baseline counting only plans charged at start (no unpaid plans).
pb_charged = (base.paid & base.subscription_id.isin(charged_ids)).sum() / len(base)
_, lo_b, hi_b = share_ci((base.paid & base.subscription_id.isin(charged_ids)).sum(), len(base))
se_b = np.sqrt(pt * (1 - pt) / nt + pb_charged * (1 - pb_charged) / len(base))
lift.loc[len(lift)] = {"comparison": "Sensitivity: trial vs Mar-Jul 2026 signups, charged plans only",
                       "trial_share": pt, "comparison_share": pb_charged, "diff_pp": 100 * (pt - pb_charged),
                       "diff_pp_ci_low": 100 * (pt - pb_charged - 1.96 * se_b),
                       "diff_pp_ci_high": 100 * (pt - pb_charged + 1.96 * se_b),
                       "relative_pct": 100 * (pt / pb_charged - 1)}
say(f"Trial users charged at start: {trial_grp.subscription_id.isin(charged_ids).sum()} of {int(trial_grp.paid.sum())} converts")
lift.to_csv(OUT / "lift.csv", index=False)
for _, r in main.iterrows():
    say(f"{r.group}: {r.paid_share:.1%} end up paid ({r.paid:,} of {r.signups:,}; 95% CI {r.ci_low:.1%} to {r.ci_high:.1%})")
for _, r in lift.iterrows():
    ci = f", 95% CI {r.diff_pp_ci_low:+.1f} to {r.diff_pp_ci_high:+.1f} pp" if pd.notna(r.diff_pp_ci_low) else ""
    say(f"{r.comparison}: {r.diff_pp:+.1f} percentage points{ci}; {r.relative_pct:+.1f}% relative")

# ---------- Weekly ----------
say("\n== Weekly ==")
wk = win.groupby(["week", "has_trial"]).agg(signups=("user_id", "size"), paid=("paid", "sum")).reset_index()
wk["paid_share"] = wk.paid / wk.signups
wk_w = wk.pivot(index="week", columns="has_trial", values=["signups", "paid", "paid_share"])
wk_w.columns = [f"{a}_{'trial' if b else 'non_trial'}" for a, b in wk_w.columns]
wk_w["first_day"] = [max(w.start_time, TRIAL_START).date() for w in wk_w.index]
wk_w["last_day"] = [min(w.end_time.normalize(), MATURE_LAST_SIGNUP).date() for w in wk_w.index]
wk_w["diff_pp"] = 100 * (wk_w.paid_share_trial - wk_w.paid_share_non_trial)
wk_w.to_csv(OUT / "weekly_trial_vs_non_trial.csv")
bw = base.groupby("week").agg(signups=("user_id", "size"), paid=("paid", "sum"))
bw["paid_share"] = bw.paid / bw.signups
# Keep whole weeks only (Monday to Sunday inside the window), not weeks picked by a signup count.
bw = bw[[(w.start_time >= BASE_START) and (w.end_time.normalize() <= BASE_END) for w in bw.index]]
bw.to_csv(OUT / "weekly_baseline_mar_jul_2026.csv")
b_lo, b_hi = bw.paid_share.min(), bw.paid_share.max()
full = wk_w[[(w.start_time >= TRIAL_START) and (w.end_time.normalize() <= MATURE_LAST_SIGNUP) for w in wk_w.index]]
say(f"Baseline weekly paid share (Mar-Jul 2026, {len(bw)} full weeks): {b_lo:.1%} to {b_hi:.1%}")
say(f"Trial-user weekly paid share ({len(full)} whole weeks): {full.paid_share_trial.min():.1%} to {full.paid_share_trial.max():.1%}")
say(f"Non-trial weekly paid share, same weeks: {full.paid_share_non_trial.min():.1%} to {full.paid_share_non_trial.max():.1%}")
weeks_above = int((full.paid_share_trial > b_hi).sum())
weeks_trial_higher = int((full.diff_pp > 0).sum())
say(f"Weeks where trial users beat the highest baseline week: {weeks_above} of {len(full)}; "
    f"weeks where trial users beat same-week non-trial signups: {weeks_trial_higher} of {len(full)}")
pd.DataFrame([{"baseline_week_min": b_lo, "baseline_week_max": b_hi, "baseline_weeks": len(bw),
               "trial_weeks": len(full), "trial_weeks_above_baseline_max": weeks_above,
               "trial_weeks_above_same_week_non_trial": weeks_trial_higher,
               "trial_week_min": full.paid_share_trial.min(), "trial_week_max": full.paid_share_trial.max(),
               "non_trial_week_min": full.paid_share_non_trial.min(),
               "non_trial_week_max": full.paid_share_non_trial.max()}]).to_csv(OUT / "weekly_summary.csv", index=False)

# ---------- Seasonality ----------
say("\n== Seasonality (2025, before trials and before the Sep 2025 spike) ==")
s25 = d[(d.signup_day >= SEAS_START) & (d.signup_day <= SEAS_END)].copy()
s25["month"] = s25.signup_day.dt.to_period("M")
sm = s25.groupby("month").agg(signups=("user_id", "size"), paid=("paid", "sum"))
sm["paid_share"] = sm.paid / sm.signups
sm.to_csv(OUT / "seasonality_2025.csv")
mj = sm.loc[pd.period_range("2025-03", "2025-07", freq="M")]
mj_share = mj.paid.sum() / mj.signups.sum()
aug_share = sm.loc[pd.Period("2025-08", "M"), "paid_share"]
say(f"Aug 2025 paid share {aug_share:.1%} vs Mar-Jul 2025 {mj_share:.1%}: {100*(aug_share-mj_share):+.1f} pp "
    f"(Mar-Jul monthly range {mj.paid_share.min():.1%} to {mj.paid_share.max():.1%})")
pd.DataFrame([{"aug_2025": aug_share, "mar_jul_2025": mj_share, "diff_pp": 100 * (aug_share - mj_share),
               "mar_jul_month_min": mj.paid_share.min(), "mar_jul_month_max": mj.paid_share.max()}]
             ).to_csv(OUT / "seasonality_summary.csv", index=False)

# ---------- Volume and mix ----------
say("\n== Volume and mix ==")
base_weeks = (BASE_END - BASE_START).days / 7 + 1 / 7
era_weeks = (MATURE_LAST_SIGNUP - TRIAL_START).days / 7 + 1 / 7
vol = pd.DataFrame([
    {"period": "Mar-Jul 2026", "group": "All signups", "signups_per_week": len(base) / base_weeks,
     "paid_per_week": base.paid.sum() / base_weeks},
    {"period": "Aug 1-Sep 10 2026", "group": "Trial users", "signups_per_week": len(trial_grp) / era_weeks,
     "paid_per_week": trial_grp.paid.sum() / era_weeks},
    {"period": "Aug 1-Sep 10 2026", "group": "Non-trial signups", "signups_per_week": len(non_grp) / era_weeks,
     "paid_per_week": non_grp.paid.sum() / era_weeks},
    {"period": "Aug 1-Sep 10 2026", "group": "All signups", "signups_per_week": len(win) / era_weeks,
     "paid_per_week": win.paid.sum() / era_weeks},
])
vol.to_csv(OUT / "volume_per_week.csv", index=False)
pst = checks.parts_sum_to_total(vol.paid_per_week.iloc[1:3], vol.paid_per_week.iloc[3])
say("Paid per week, trial + non-trial vs all: " + pst["summary"])
sst = checks.parts_sum_to_total([len(trial_grp), len(non_grp)], len(win))
say("Signups, trial + non-trial vs all: " + sst["summary"])
assert pst["ok"] and sst["ok"]
for _, r in vol.iterrows():
    say(f"{r.period}, {r.group}: {r.signups_per_week:,.0f} signups/week, {r.paid_per_week:,.0f} paid/week")
say(f"Trial share of signups, Aug 1-Sep 10: {len(trial_grp)/len(win):.1%}")

mix_rows = []
for name, g in [("Trial users", trial_grp), ("Non-trial signups, same days", non_grp),
                ("Signups Mar-Jul 2026", base)]:
    for col in ["country", "device_type"]:
        for val, sh in g[col].value_counts(normalize=True).items():
            mix_rows.append({"group": name, "attribute": col, "value": val, "share_of_signups": sh})
    for val, sh in g[g.paid].plan.value_counts(normalize=True).items():
        mix_rows.append({"group": name, "attribute": "plan_of_payers", "value": val, "share_of_signups": sh})
mix = pd.DataFrame(mix_rows)
mix.to_csv(OUT / "mix.csv", index=False)
mx = mix.pivot_table(index=["attribute", "value"], columns="group", values="share_of_signups")
mx["trial_minus_non_trial_pp"] = 100 * (mx["Trial users"] - mx["Non-trial signups, same days"])
say(f"Largest country/device mix gap, trial vs non-trial: "
    f"{mx.loc[['country','device_type'],'trial_minus_non_trial_pp'].abs().max():.1f} pp")
say(f"Annual share of payers: trial {mx.loc[('plan_of_payers','annual'),'Trial users']:.1%}, "
    f"non-trial {mx.loc[('plan_of_payers','annual'),'Non-trial signups, same days']:.1%}, "
    f"Mar-Jul 2026 {mx.loc[('plan_of_payers','annual'),'Signups Mar-Jul 2026']:.1%}")

# Segment lift by country and device (parts check: segments add back to the window)
seg_rows = []
for col in ["country", "device_type", "plan"]:
    if col == "plan":
        continue
    for val, g in win.groupby(col):
        t_, n_ = g[g.has_trial], g[~g.has_trial]
        seg_rows.append({"attribute": col, "value": val, "trial_signups": len(t_), "trial_paid_share": t_.paid.mean(),
                         "non_trial_signups": len(n_), "non_trial_paid_share": n_.paid.mean(),
                         "diff_pp": 100 * (t_.paid.mean() - n_.paid.mean())})
seg = pd.DataFrame(seg_rows)
seg.to_csv(OUT / "lift_by_segment.csv", index=False)
for col in ["country", "device_type"]:
    s_ = seg[seg.attribute == col]
    chk = checks.parts_sum_to_total(s_.trial_signups + s_.non_trial_signups, len(win))
    say(f"{col} segments vs window: " + chk["summary"])
    assert chk["ok"]
say("Lift by segment (pp): " + "; ".join(f"{r.value} {r.diff_pp:+.1f}" for _, r in seg.iterrows()))

# ---------- Retention: second monthly charge ----------
say("\n== Retention warning sign: charged again on day 30 ==")
pays = pays.merge(subs[["subscription_id", "start_date"]], on="subscription_id", how="left")
pays["day"] = (pays.payment_date.dt.normalize() - pays.start_date.dt.normalize()).dt.days
# Monthly charges fall on day 0, 30 and 60 after the start; day 28 to 32 catches the second one.
second = pays[(pays.day >= 28) & (pays.day <= 32)].subscription_id.unique()
first = pays[(pays.day >= 0) & (pays.day <= 5)].subscription_id.unique()
mon = d[(d.plan == "monthly")].copy()
mon["start_day"] = mon.start_date.dt.normalize()
mon["charged_day0"] = mon.subscription_id.isin(first)
mon["charged_day30"] = mon.subscription_id.isin(second)
due = TODAY - pd.Timedelta(days=32)  # starts that have passed the whole day-28-to-32 window
groups = {
    "Trial converts": mon[mon.has_trial & (mon.start_day <= due)],
    "Non-trial monthly starts, Aug 2026": mon[~mon.has_trial & (mon.start_day >= TRIAL_START) & (mon.start_day <= due)],
    "Monthly starts Mar-Jul 2026": mon[(mon.start_day >= BASE_START) & (mon.start_day <= BASE_END)],
}
ret_rows = []
for name, g in groups.items():
    n = len(g)
    p, lo, hi = share_ci(g.charged_day30.sum(), n) if n else (np.nan,) * 3
    ret_rows.append({"group": name, "monthly_starts": n, "charged_day0": g.charged_day0.mean() if n else np.nan,
                     "charged_day30": int(g.charged_day30.sum()), "share_charged_day30": p, "ci_low": lo, "ci_high": hi,
                     "start_from": g.start_day.min().date() if n else None, "start_to": g.start_day.max().date() if n else None})
ret = pd.DataFrame(ret_rows)
ret.to_csv(OUT / "second_charge.csv", index=False)
for _, r in ret.iterrows():
    say(f"{r.group}: {r.share_charged_day30:.1%} charged again around day 30 ({r.charged_day30} of {r.monthly_starts}, "
        f"starts {r.start_from} to {r.start_to}; 95% CI {r.ci_low:.1%} to {r.ci_high:.1%})")

# ---------- Money ----------
say("\n== Money: next quarter (13 weeks) ==")
# Revenue per new payer in the first 90 days, from Mar-Jun 2026 direct paid starts (90 days observed).
rev_base = d[d.paid & (d.start_date >= BASE_START) & (d.start_date <= TODAY - pd.Timedelta(days=90))]
p90 = pays[(pays.day >= 0) & (pays.day < 90)].groupby("subscription_id").amount_usd.sum()
rev_base = rev_base.assign(rev90=rev_base.subscription_id.map(p90).fillna(0))
rev90 = rev_base.groupby("plan").rev90.mean()
rev90.rename("revenue_first_90_days_per_payer").to_csv(OUT / "revenue_90d_per_payer.csv")
say(f"90-day revenue per payer, Mar-Jun 2026 starts: monthly ${rev90['monthly']:.2f}, annual ${rev90['annual']:.2f}")
annual_mix = trial_grp[trial_grp.paid].plan.eq("annual").mean()
r_row = ret[ret.group == "Monthly starts Mar-Jul 2026"].iloc[0]
QUARTER_DAYS = 7 * WEEKS_PER_QUARTER


def in_quarter_value(r_month):
    """Revenue that lands inside the quarter per extra payer, signups spread evenly over it.

    A trial payer starts paying on day 14 after signup; monthly charges follow every 30 days, each
    one kept at r_month of the one before; annual pays $100 at the start.
    """
    vals = []
    for s_day in range(QUARTER_DAYS):
        start = s_day + 14
        monthly = sum(12 * r_month ** k for k in range(3) if start + 30 * k < QUARTER_DAYS)
        annual = 100.0 if start < QUARTER_DAYS else 0.0
        vals.append(annual_mix * annual + (1 - annual_mix) * monthly)
    return float(np.mean(vals))


share_now = len(trial_grp) / len(win)
volume = {"Low": len(base) / base_weeks, "Central": len(win) / era_weeks, "High": len(win) / era_weeks}
lift_case = {"Low": lift.diff_pp_ci_low.iloc[0] / 100, "Central": lift_pp, "High": lift.diff_pp_ci_high.iloc[0] / 100}
ret_case = {"Low": r_row.ci_low, "Central": r_row.share_charged_day30, "High": r_row.share_charged_day30}
cases = []
for coverage, cov_share in [("Trials for about half of signups, as now", share_now), ("Trials for all signups", 1.0)]:
    for case in ["Low", "Central", "High"]:
        trial_signups_q = volume[case] * cov_share * WEEKS_PER_QUARTER
        extra_payers = lift_case[case] * trial_signups_q
        v_q = in_quarter_value(ret_case[case])
        v_90 = annual_mix * rev90["annual"] + (1 - annual_mix) * rev90["monthly"]
        cases.append({"coverage": coverage, "case": case, "signups_per_week": volume[case],
                      "trial_share_of_signups": cov_share, "trial_signups_per_quarter": trial_signups_q,
                      "lift_pp": 100 * lift_case[case], "extra_payers_per_quarter": extra_payers,
                      "annual_share_of_payers": annual_mix, "monthly_keep_rate": ret_case[case],
                      "revenue_in_quarter_per_extra_payer": v_q,
                      "extra_revenue_in_quarter": extra_payers * v_q,
                      "revenue_first_90_days_per_extra_payer": v_90,
                      "extra_revenue_first_90_days": extra_payers * v_90})
money = pd.DataFrame(cases)
money.to_csv(OUT / "money_next_quarter.csv", index=False)
pd.DataFrame([
    {"assumption": "Quarter length", "value": f"{WEEKS_PER_QUARTER} weeks, signups spread evenly"},
    {"assumption": "Signups per week, low", "value": f"{volume['Low']:.0f} (Mar-Jul 2026 rate)"},
    {"assumption": "Signups per week, central and high", "value": f"{volume['Central']:.0f} (Aug 1-Sep 10 2026 rate)"},
    {"assumption": "Lift", "value": "low and high are the 95% interval of the same-day trial vs non-trial gap"},
    {"assumption": "Trials for all signups", "value": "the same lift applies to the half who get no trial today"},
    {"assumption": "Plan mix", "value": f"{annual_mix:.1%} annual, as among trial converts"},
    {"assumption": "Prices", "value": "$12 monthly, $100 annual"},
    {"assumption": "Monthly keep rate", "value": "share of Mar-Jul 2026 monthly starts charged again on day 30 (low: bottom of its 95% interval)"},
    {"assumption": "Not counted", "value": "earlier payment by trial converts (day 14) against non-trial payers; any cost of running trials"},
]).to_csv(OUT / "money_assumptions.csv", index=False)
for _, r in money.iterrows():
    say(f"{r.coverage}, {r.case}: {r.trial_signups_per_quarter:,.0f} trial signups x {r.lift_pp:+.1f} pp -> "
        f"{r.extra_payers_per_quarter:+,.0f} payers; ${r.extra_revenue_in_quarter:+,.0f} inside the quarter, "
        f"${r.extra_revenue_first_90_days:+,.0f} over their first 90 days")

# ---------- Charts ----------
labels = ["Trial users", "Non-trial,\nsame days", "Before trials\n(Mar-Jul 2026)"]
fig = charts.bar(labels, list(100 * main.paid_share), highlight="Trial users",
                 title=f"Trial users end up paying {lift.diff_pp.iloc[0]:+.0f} pp more often than same-day non-trial signups",
                 ylabel="% of signups on a paid plan", source=SOURCE)
charts.save(fig, CH / "paid_share_by_group.png")
x = [str(w.start_time.date()) for w in full.index]
fig = charts.line(x, {"Trial users": list(100 * full.paid_share_trial),
                      "Non-trial signups": list(100 * full.paid_share_non_trial),
                      "Best week before trials": [100 * b_hi] * len(x)},
                  highlight="Trial users",
                  title="Trial users beat same-week non-trial signups and the best pre-trial week in every whole week",
                  ylabel="% of signups on a paid plan", source=SOURCE)
charts.save(fig, CH / "weekly_paid_share.png")
say("\nCharts saved.")
