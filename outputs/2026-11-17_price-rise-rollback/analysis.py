"""March 2026 price increase and monthly-plan retention.

Reads the result CSVs in data/, derives churn rates before (renewals due Nov 2025 to Feb 2026, at $10)
and after (Mar to Jul 2026, at $12) by segment, runs the checks, projects 12-month revenue at $12
against a rollback to $10 per segment, and draws the charts.

Run from the repo root: poetry run python outputs/2026-11-17_price-rise-rollback/analysis.py
"""

import sys
from pathlib import Path

import matplotlib
import pandas as pd

# Titles and labels hold dollar amounts; stop matplotlib reading "$...$" as math.
matplotlib.rcParams["text.parse_math"] = False

RUN = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN.parents[1]))
from helpers import charts  # noqa: E402
from helpers.checks import parts_sum_to_total, stable_over_time  # noqa: E402

DATA, CHARTS = RUN / "data", RUN / "charts"
OLD_PRICE, NEW_PRICE, MONTHS = 10.0, 12.0, 12
SOURCE = "Source: public.payments, public.subscriptions, public.users; trial users left out"


def read(name):
    return pd.read_csv(DATA / f"{name}.csv", dtype={"due_month": str, "month": str})


def period(month):
    return "before" if month < "2026-03" else "after"


def rates(df, keys):
    """Churn rate per group: missed renewals over renewals due (missed_monthly_renewals / monthly_renewals_due)."""
    g = df.groupby(keys, as_index=False)[["renewals_due", "missed_renewals"]].sum()
    g["churn_rate"] = g["missed_renewals"] / g["renewals_due"]
    return g


def before_after(df, keys):
    """Before and after rates side by side, with the change in percentage points and relative percent."""
    g = rates(df, keys + ["period"])
    wide = g.pivot_table(index=keys, columns="period",
                         values=["renewals_due", "missed_renewals", "churn_rate"]).reset_index()
    wide.columns = ["_".join(c).strip("_") for c in wide.columns]
    wide["change_pp"] = (wide["churn_rate_after"] - wide["churn_rate_before"]) * 100
    wide["change_relative_pct"] = (wide["churn_rate_after"] / wide["churn_rate_before"] - 1) * 100
    return wide


def revenue_12m(base, churn, price):
    """Revenue over the next 12 months from a base of subscribers losing `churn` of the rest each month."""
    return sum(base * (1 - churn) ** t * price for t in range(1, MONTHS + 1))


def breakeven_churn(c0):
    """Monthly churn at $12 that gives the same 12-month revenue as $10 at churn c0 (bisection)."""
    target = revenue_12m(1, c0, OLD_PRICE)
    lo, hi = c0, 0.99
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if revenue_12m(1, mid, NEW_PRICE) > target else (lo, mid)
    return (lo + hi) / 2


def show(name, result):
    print(f"[{'ok' if result['ok'] else 'FAIL'}] {name}: {result['summary']}")


seg = read("renewals_by_segment")
seg["period"] = seg["due_month"].map(period)
seg["block_2025_09_17"] = seg["block_2025_09_17"].astype(str).str.lower() == "true"
prices = read("check_renewal_prices")
early = read("early_renewals_by_start_group")
early["period"] = early["due_month"].map(period)
at12 = read("existing_by_renewal_at_12")
annual = read("annual_churn_context")
regdev = read("renewals_by_region_device")
switch = read("check_plan_switch_and_fanout")

# ---- Checks -------------------------------------------------------------------------------
print("Checks")
by_month = seg.groupby("due_month")[["renewals_due", "missed_renewals"]].sum()
p = prices.set_index("due_month")
show("segments add to month totals (renewals due)",
     parts_sum_to_total(by_month["renewals_due"], p["renewals_due"].sum(), tolerance=0))
show("segments add to month totals (missed)",
     parts_sum_to_total(by_month["missed_renewals"], p["missed_renewals"].sum(), tolerance=0))
mismatch = (by_month - p[["renewals_due", "missed_renewals"]]).abs().sum().sum()
print(f"[{'ok' if mismatch == 0 else 'FAIL'}] every month of renewals_by_segment matches check_renewal_prices "
      f"(total absolute gap {mismatch})")
for dim in ("country", "device_type"):
    sub = regdev[(regdev[dim] != "all")]
    for per in ("before", "after"):
        months = p[[period(m) == per for m in p.index]]
        show(f"{dim} adds to total, {per}",
             parts_sum_to_total(sub.loc[sub["period"] == per, "renewals_due"], months["renewals_due"].sum(), tolerance=0))
after_existing = seg[(seg["period"] == "after") & (seg["start_group"] == "existing")]["renewals_due"].sum()
show("existing renewals by $12 renewal number add to existing after total",
     parts_sum_to_total(at12["renewals_due"], after_existing, tolerance=0))
price_ok = ((p.loc[p.index < "2026-03", ["min_renewal_charge", "max_renewal_charge"]] == OLD_PRICE).all().all()
            and (p.loc[p.index >= "2026-03", ["min_renewal_charge", "max_renewal_charge"]] == NEW_PRICE).all().all())
print(f"[{'ok' if price_ok else 'FAIL'}] every renewal before March was charged $10 and every one from March $12; "
      f"{int(p['renewals_paid_off_due_date'].sum())} renewals paid off their due date")
fan = switch["payment_rows_after_join"].sum() == switch["payment_rows_total"].iloc[0]
print(f"[{'ok' if fan else 'FAIL'}] payments join to subscriptions without dropping or repeating rows "
      f"({switch['payment_rows_after_join'].sum():,} of {switch['payment_rows_total'].iloc[0]:,})")
s = switch.set_index("plan")
print(f"[info] plan switches in payments: {int(s.loc['monthly', 'subs_with_100_charge'])} monthly subscriptions "
      f"charged $100, {int(s.loc['annual', 'subs_with_10_or_12_charge'])} annual charged $10 or $12, "
      "so switches cannot be seen and are not counted")
stab = rates(seg, ["due_month"]).rename(columns={"due_month": "period", "renewals_due": "n", "churn_rate": "level"})
# Churn rates are 1% to 6%, so the default 10-point tolerance would hide any step; use 1 point.
show("baseline churn stable Nov 2025 to Feb 2026",
     stable_over_time(stab[stab["period"] < "2026-03"], "monthly churn", tolerance=0.01))
show("churn across the whole window (a step here is the change being measured)",
     stable_over_time(stab, "monthly churn", tolerance=0.01))
print("    (renewal charges land exactly on their due date in every month, so a step is behaviour, not logging)")

# ---- Headline: overall and by month ---------------------------------------------------------
monthly = rates(seg, ["due_month"])
monthly.to_csv(DATA / "churn_by_month.csv", index=False)
overall = before_after(seg.assign(all="all"), ["all"])
overall.to_csv(DATA / "churn_overall.csv", index=False)
o = overall.iloc[0]
print("\nHeadline")
print(f"Monthly churn {o.churn_rate_before:.2%} before -> {o.churn_rate_after:.2%} after: "
      f"+{o.change_pp:.2f} pp ({o.change_relative_pct:+.0f}% relative)")

# ---- Segments: existing by tenure band, new subscribers --------------------------------------
seg["segment"] = seg["start_group"].where(seg["start_group"] == "new", "existing, " + seg["tenure_band"])
existing = before_after(seg[seg["start_group"] == "existing"], ["tenure_band"])
existing_noblock = before_after(seg[(seg["start_group"] == "existing") & ~seg["block_2025_09_17"]], ["tenure_band"])
existing.to_csv(DATA / "churn_existing_by_tenure.csv", index=False)
existing_noblock.to_csv(DATA / "churn_existing_by_tenure_no_block.csv", index=False)

# New subscribers like for like: their first three renewals at $12 against pre-March starters' first
# three renewals at $10 (2025-09-17 block left out in the query).
early_ba = before_after(early[(early["period"] == "before") | (early["start_group"] == "new")]
                        .assign(group="first three renewals"), ["group"])
early_by_n = before_after(early[(early["period"] == "before") | (early["start_group"] == "new")], ["renewal_number"])
early_by_n.to_csv(DATA / "churn_new_vs_prior_starters_by_renewal.csv", index=False)
early_ba.to_csv(DATA / "churn_new_vs_prior_starters.csv", index=False)

order = ["under 6 months", "6 to 12 months", "12 to 24 months", "over 24 months"]
existing = existing.set_index("tenure_band").loc[order].reset_index()
existing_noblock = existing_noblock.set_index("tenure_band").reindex(order).reset_index()
print("\nExisting subscribers by tenure band (before -> after, pp, relative)")
for _, r in existing.iterrows():
    nb = existing_noblock.set_index("tenure_band").loc[r.tenure_band]
    print(f"  {r.tenure_band:16s} {r.churn_rate_before:.2%} -> {r.churn_rate_after:.2%}  "
          f"+{r.change_pp:.2f} pp ({r.change_relative_pct:+.0f}%); without 2025-09-17 block "
          f"{nb.churn_rate_before:.2%} -> {nb.churn_rate_after:.2%}")
e = early_ba.iloc[0]
print(f"New subscribers, first three renewals: {e.churn_rate_before:.2%} for pre-March starters at $10 -> "
      f"{e.churn_rate_after:.2%} for starters at $12: +{e.change_pp:.2f} pp ({e.change_relative_pct:+.0f}%)")

at12["churn_rate"] = at12["missed_renewals"] / at12["renewals_due"]
at12_n = rates(at12, ["renewal_at_12"])
at12_n.to_csv(DATA / "churn_existing_by_renewal_at_12.csv", index=False)
print("Existing subscribers by how many $12 renewals they had faced: " + ", ".join(
    f"{r.renewal_at_12}: {r.churn_rate:.2%}" for _, r in at12_n.iterrows()))

annual["churn_rate"] = annual["annual_churned"] / annual["annual_at_month_start"]
annual["period"] = annual["month"].map(period)
ann = annual.groupby("period")[["annual_at_month_start", "annual_churned"]].sum()
ann["churn_rate"] = ann["annual_churned"] / ann["annual_at_month_start"]
ann.reset_index().to_csv(DATA / "annual_churn_before_after.csv", index=False)
print(f"Annual (context, no price change): {ann.loc['before', 'churn_rate']:.2%} before -> "
      f"{ann.loc['after', 'churn_rate']:.2%} after a month")

rd = []
for dim in ("country", "device_type"):
    sub = regdev[regdev[dim] != "all"].rename(columns={dim: "group"})
    t = before_after(sub, ["group"]).assign(dimension=dim)
    rd.append(t)
rd = pd.concat(rd)[["dimension", "group", "churn_rate_before", "churn_rate_after", "change_pp", "change_relative_pct",
                    "renewals_due_before", "renewals_due_after"]]
rd.to_csv(DATA / "churn_by_region_device.csv", index=False)
print("Region and device (context): " + "; ".join(
    f"{r.group} +{r.change_pp:.1f} pp" for _, r in rd.iterrows()))

# ---- Start cohorts: who moved, month by month since the rise ---------------------------------------
# Groups a rule could target by start date. The 2025-09-17 bulk block is its own group (it sits in
# different tenure bands before and after March). "new" started at $12 from 2026-03-01.
COHORT_GROUP = {
    "2022-H1": "started 2022 to 2023", "2022-H2": "started 2022 to 2023",
    "2023-H1": "started 2022 to 2023", "2023-H2": "started 2022 to 2023",
    "2024-H1": "started 2024", "2024-H2": "started 2024",
    "2025-H1": "started 2025 (not the block)", "2025-H2": "started 2025 (not the block)",
    "2025-09-17 block": "2025-09-17 block",
    "2026-01 to 02": "started Jan to Feb 2026",
    "new (from 2026-03)": "new (started at $12)",
}
GROUPS = list(dict.fromkeys(COHORT_GROUP.values()))
coh = read("renewals_by_start_cohort")
show("start cohorts add to month totals (renewals due)",
     parts_sum_to_total(coh["renewals_due"], p["renewals_due"].sum(), tolerance=0))
show("start cohorts add to month totals (missed)",
     parts_sum_to_total(coh["missed_renewals"], p["missed_renewals"].sum(), tolerance=0))
coh["period"] = coh["due_month"].map(period)
coh["group"] = coh["start_cohort"].map(COHORT_GROUP)
coh_half = before_after(coh, ["start_cohort"])
coh_half.to_csv(DATA / "churn_by_start_cohort.csv", index=False)
coh_month = rates(coh, ["group", "due_month"])
coh_month.to_csv(DATA / "churn_by_group_and_month.csv", index=False)
print("\nStart cohorts (before -> after, pp)")
for _, r in coh_half.iterrows():
    print(f"  {r.start_cohort:20s} {r.churn_rate_before:.2%} -> {r.churn_rate_after:.2%}  {r.change_pp:+.2f} pp")
print("Churn by group and month since the rise (Mar, Apr, May, Jun, Jul)")
for g in GROUPS:
    m = coh_month[(coh_month["group"] == g) & (coh_month["due_month"] >= "2026-03")]
    print(f"  {g:30s} " + "  ".join(f"{x:.1%}" for x in m["churn_rate"]))

# ---- Money: keep $12 against roll back to $10, per group -----------------------------------------
# Rates per group: $10 = Nov 2025 to Feb 2026; $12 settled = May to Jul 2026 (main case, after the
# reaction set in); $12 average = Mar to Jul 2026 (includes the March renewal, before churn rose).
# New subscribers and Jan to Feb 2026 starters have little or no $10 history at the same stage, so
# their $10 rate is the pre-March starters' first-three-renewals rate (like for like, block left out).
# Base: renewals due in July 2026, the latest closed month. Assumes the whole churn rise is caused by
# the price, so a rollback returns each group to its $10 rate.
def group_rate(df):
    return df["missed_renewals"].sum() / df["renewals_due"].sum()


rows = []
for g in GROUPS:
    d = coh[coh["group"] == g]
    young = g in ("new (started at $12)", "started Jan to Feb 2026")
    c0 = e.churn_rate_before if young else group_rate(d[d["period"] == "before"])
    rows.append({
        "group": g,
        "base_jul_2026": d.loc[d["due_month"] == "2026-07", "renewals_due"].sum(),
        "churn_at_10": c0,
        "churn_at_10_source": "pre-March starters, first three renewals" if young else "own, Nov 2025 to Feb 2026",
        "churn_at_12_settled": group_rate(d[d["due_month"] >= "2026-05"]),
        "churn_at_12_mar_jul": group_rate(d[d["period"] == "after"]),
        # Observed so far: each renewal due Mar to Jul at $12 with the churn seen, against the same
        # renewals at $10 with the $10 churn rate (one month each, no compounding).
        "observed_mar_jul_at_12": ((d.loc[d["period"] == "after", "renewals_due"]
                                    - d.loc[d["period"] == "after", "missed_renewals"]) * NEW_PRICE).sum(),
        "counterfactual_mar_jul_at_10": (d.loc[d["period"] == "after", "renewals_due"] * (1 - c0) * OLD_PRICE).sum(),
    })
money = pd.DataFrame(rows)
money["observed_gain_mar_jul"] = money["observed_mar_jul_at_12"] - money["counterfactual_mar_jul_at_10"]
money["rollback_10_12m"] = money.apply(lambda r: revenue_12m(r.base_jul_2026, r.churn_at_10, OLD_PRICE), axis=1)
money["keep_12_12m_settled"] = money.apply(lambda r: revenue_12m(r.base_jul_2026, r.churn_at_12_settled, NEW_PRICE), axis=1)
money["keep_12_12m_mar_jul"] = money.apply(lambda r: revenue_12m(r.base_jul_2026, r.churn_at_12_mar_jul, NEW_PRICE), axis=1)
money["gain_12m_settled"] = money["keep_12_12m_settled"] - money["rollback_10_12m"]
money["gain_12m_mar_jul"] = money["keep_12_12m_mar_jul"] - money["rollback_10_12m"]
money["breakeven_churn_at_12"] = money["churn_at_10"].map(breakeven_churn)
money["headroom_pp_settled"] = (money["breakeven_churn_at_12"] - money["churn_at_12_settled"]) * 100
total = money[["base_jul_2026", "observed_mar_jul_at_12", "counterfactual_mar_jul_at_10", "observed_gain_mar_jul",
               "rollback_10_12m", "keep_12_12m_settled", "keep_12_12m_mar_jul", "gain_12m_settled",
               "gain_12m_mar_jul"]].sum()
money = pd.concat([money, pd.DataFrame([{"group": "all monthly", **total.to_dict()}])], ignore_index=True)
money.to_csv(DATA / "revenue_keep_vs_rollback_by_group.csv", index=False)
show("group bases add to July 2026 renewals due",
     parts_sum_to_total(money.loc[money["group"] != "all monthly", "base_jul_2026"],
                        p.loc["2026-07", "renewals_due"], tolerance=0))
print("\nKeep $12 minus roll back to $10, by group (July 2026 base)")
for _, r in money.iterrows():
    rates_txt = ("" if r.group == "all monthly" else
                 f"churn {r.churn_at_10:.2%} -> settled {r.churn_at_12_settled:.2%} (Mar-Jul {r.churn_at_12_mar_jul:.2%}), "
                 f"break-even {r.breakeven_churn_at_12:.2%}; ")
    print(f"  {r.group:30s} base {r.base_jul_2026:5,.0f}  {rates_txt}observed Mar-Jul {r.observed_gain_mar_jul:+,.0f}; "
          f"12 months settled {r.gain_12m_settled:+,.0f}, Mar-Jul rate {r.gain_12m_mar_jul:+,.0f}")

# ---- Charts -------------------------------------------------------------------------------------
def relabel(fig, values, fmt):
    """Rewrite the value labels on a bar chart with a format the helper does not offer."""
    ax = fig.axes[0]
    for t, v in zip([t for t in ax.texts], values):
        t.set_text(fmt.format(v))
    return fig


labels = monthly["due_month"].tolist()
charts.save(charts.line(
    labels, {"monthly plan": (monthly["churn_rate"] * 100).round(2).tolist(),
             "annual plan (no price change)": (annual["churn_rate"] * 100).round(2).tolist()},
    "Monthly-plan churn held in March, then rose to about 5% a month from May 2026; annual stayed flat",
    highlight="monthly plan", ylabel="Churn rate per month (%)", source=SOURCE), CHARTS / "churn_by_month.png")

after_months = [m for m in labels if m >= "2026-02"]
series = {}
for g in GROUPS:
    m = coh_month[coh_month["group"] == g].set_index("due_month")["churn_rate"]
    if all(x in m.index for x in after_months):
        series[g] = (m.reindex(after_months) * 100).round(2).tolist()
charts.save(charts.line(
    after_months, series,
    "Churn rose in every start group except 2024 starters and stayed well above its earlier level through July",
    highlight="started 2024",
    ylabel="Churn rate per month (%)", source=SOURCE), CHARTS / "churn_by_group_and_month.png")

ch = coh_half.set_index("start_cohort")
seg_rows = [(f"existing, {b}", existing_noblock.set_index("tenure_band").loc[b, "change_pp"]) for b in order]
seg_rows += [("2025-09-17 block", ch.loc["2025-09-17 block", "change_pp"]), ("new (started at $12)", e.change_pp)]
names, pp = [r[0] for r in seg_rows], [r[1] for r in seg_rows]
top = names[pp.index(max(pp))]
pd.DataFrame(seg_rows, columns=["segment", "change_pp"]).to_csv(DATA / "churn_change_by_segment.csv", index=False)
fig = charts.bar(names, [round(x, 2) for x in pp],
                 f"Churn rose in every tenure band, most for {top} subscribers (block shown on its own)",
                 highlight=top, ylabel="Change in monthly churn, before to after (pp)", source=SOURCE,
                 horizontal=True)
charts.save(relabel(fig, pp, "{:+.1f} pp"), CHARTS / "churn_change_by_segment.png")

mg = money[money["group"] != "all monthly"]
fig = charts.bar(mg["group"].tolist(), mg["gain_12m_settled"].round(0).tolist(),
                 "At settled churn, only 2024 starters earn more at $12 over 12 months",
                 highlight="started 2024", ylabel="12-month revenue, keep $12 minus roll back to $10 ($)",
                 source=SOURCE, horizontal=True)
fig.axes[0].margins(x=0.25)
charts.save(relabel(fig, mg["gain_12m_settled"].tolist(), "{:+,.0f}"), CHARTS / "revenue_keep_vs_rollback.png")
print("\nCharts saved to", CHARTS)
