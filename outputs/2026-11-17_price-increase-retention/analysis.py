"""March 2026 price increase and retention.

Reads the result CSVs in data/, derives before/after churn, the splits, the new-start comparison,
the plan mix and the money at stake, saves each derived table to data/ and prints every check.
Run from the repo root: poetry run python outputs/2026-11-17_price-increase-retention/analysis.py
"""

import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN.parents[1]))
from helpers import charts  # noqa: E402
from helpers.checks import parts_sum_to_total, stable_over_time  # noqa: E402

DATA, CHARTS = RUN / "data", RUN / "charts"
OLD_PRICE, NEW_PRICE = 10.0, 12.0
BREAK_EVEN_REL = NEW_PRICE / OLD_PRICE - 1  # 20% relative: long-run revenue is price / churn
MIN_RENEWALS = 300  # minimum renewals per window for a split to count as a finding
HORIZON = 12  # months for the money at stake
Z = 1.96


def read(name):
    df = pd.read_csv(DATA / f"{name}.csv")
    for col in [c for c in df.columns if c in ("due_month", "start_month", "payment_month", "month_start")]:
        df[col] = pd.to_datetime(df[col], utc=True).dt.tz_localize(None)
    return df


def window(month):
    if month < pd.Timestamp("2026-03-01"):
        return "before"
    return "after"


def rates(df, keys):
    g = df.groupby(keys, as_index=False)[["renewals_due", "missed_renewals"]].sum()
    g["churn_rate"] = g["missed_renewals"] / g["renewals_due"]
    return g


def compare(before_n, before_x, after_n, after_x):
    """Before/after churn with the change in percentage points, relative percent and a 95% CI on the pp change."""
    pb, pa = before_x / before_n, after_x / after_n
    se = ((pb * (1 - pb) / before_n) + (pa * (1 - pa) / after_n)) ** 0.5
    return {
        "renewals_before": before_n, "churn_before": pb,
        "renewals_after": after_n, "churn_after": pa,
        "change_pp": (pa - pb) * 100,
        "change_pp_ci_low": (pa - pb - Z * se) * 100,
        "change_pp_ci_high": (pa - pb + Z * se) * 100,
        "change_relative": pa / pb - 1 if pb else float("nan"),
    }


def revenue_path(price, churn, months):
    """Expected revenue per subscriber by month: pays now, and again each month it survives the renewal."""
    return pd.Series([price * (1 - churn) ** k for k in range(months)]).cumsum()


def money(churn_before, churn_after, group_size):
    old = revenue_path(OLD_PRICE, churn_before, 120)
    new = revenue_path(NEW_PRICE, churn_after, 120)
    behind = new < old
    crossover = int(behind.idxmax()) + 1 if behind.any() else None
    gain_12m = new[HORIZON - 1] - old[HORIZON - 1]
    return {
        "revenue_12m_at_10_old_churn": old[HORIZON - 1],
        "revenue_12m_at_12_new_churn": new[HORIZON - 1],
        "gain_12m_per_subscriber": gain_12m,
        "group_size": group_size,
        "gain_12m_group": gain_12m * group_size,
        "lifetime_revenue_at_10_old_churn": OLD_PRICE / churn_before,
        "lifetime_revenue_at_12_new_churn": NEW_PRICE / churn_after,
        "months_until_12_falls_behind": crossover,
    }


checks = []


def check(name, ok, summary):
    checks.append({"check": name, "ok": bool(ok), "summary": summary})
    print(f"[{'ok' if ok else 'FAIL'}] {name}: {summary}")


# ---------------------------------------------------------------- inputs
analysis_date = read("analysis_date")["analysis_date"].iloc[0]
by_month = read("churn_by_due_month")
seg = read("churn_by_segment_month")
new_starts = read("new_start_churn_by_renewal")
annual = read("annual_churn_by_month")
price = read("check_price_charged")
starts = read("new_paid_starts_by_month")
gaps = pd.read_csv(DATA / "check_payment_gap_stability.csv")
joins = pd.read_csv(DATA / "check_joins_and_edges.csv").iloc[0]
totals = pd.read_csv(DATA / "check_csv_totals.csv").iloc[0]
print(f"Analysis date: {analysis_date[:10]}")

by_month["window"] = by_month["due_month"].map(window)
seg["window"] = seg["due_month"].map(window)

# ---------------------------------------------------------------- checks
check("csv_totals",
      len(by_month) == totals["due_month_groups"]
      and by_month["renewals_due"].sum() == totals["renewals_due_total"]
      and by_month["missed_renewals"].sum() == totals["missed_total"],
      f"churn_by_due_month has {len(by_month)} rows, {by_month['renewals_due'].sum():,} renewals and "
      f"{by_month['missed_renewals'].sum():,} missed; the source gives {totals['due_month_groups']}, "
      f"{totals['renewals_due_total']:,} and {totals['missed_total']:,}.")

organic_existing = by_month[(by_month["customer_type"] == "existing") & (by_month["block_flag"] == "organic")]
for dim, part in seg.groupby("dimension"):
    r = parts_sum_to_total(part["renewals_due"], organic_existing["renewals_due"].sum(), tolerance=0)
    m = parts_sum_to_total(part["missed_renewals"], organic_existing["missed_renewals"].sum(), tolerance=0)
    check(f"segments_sum_{dim}", r["ok"] and m["ok"], f"renewals: {r['summary']} Missed: {m['summary']}")

monthly_prices = price[price["plan"] == "monthly"]
wrong = monthly_prices[((monthly_prices["payment_month"] < "2026-03-01") & (monthly_prices["amount_usd"] != OLD_PRICE))
                       | ((monthly_prices["payment_month"] >= "2026-03-01") & (monthly_prices["amount_usd"] != NEW_PRICE))]
annual_prices = price[price["plan"] == "annual"]
check("price_charged", wrong.empty and (annual_prices["amount_usd"] == 100).all(),
      f"every monthly charge is $10 before 2026-03-01 and $12 from then ({len(wrong)} month-price rows off); "
      f"annual is $100 throughout, so every monthly subscriber was treated and none was grandfathered.")

stab = stable_over_time(gaps[["period", "n", "level"]], "Next charge exactly 30 days after the last", kind="share")
check("renewal_outcome_stable", stab["ok"],
      stab["summary"] + f" Gaps range {gaps['min_gap_days'].min()} to {gaps['max_gap_days'].max()} days.")

check("joins_do_not_fan_out",
      joins["monthly_payment_rows"] == joins["monthly_payment_rows_after_subscriptions_join"]
      == joins["monthly_payment_rows_after_users_join"],
      f"{joins['monthly_payment_rows']:,} monthly payment rows before and after both joins.")
check("trial_exclusion", joins["monthly_subs_with_trial_starting_before_aug"] == 0,
      "no monthly subscription starting before 2026-08-01 has a trial record, so dropping trial users removes nobody in the window.")
check("window_edges_closed",
      str(joins["first_due_in_window"])[:10] == "2025-11-01" and str(joins["last_due_in_window"])[:10] == "2026-07-31"
      and pd.Timestamp("2026-07-31") + pd.Timedelta(days=30) < pd.Timestamp(analysis_date[:10]),
      f"renewals due {str(joins['first_due_in_window'])[:10]} to {str(joins['last_due_in_window'])[:10]}; the last one's next "
      f"charge would fall by 2026-08-30, before the analysis date {analysis_date[:10]}, so every renewal is decided.")

pd.DataFrame(checks).to_csv(DATA / "checks_summary.csv", index=False)

# ---------------------------------------------------------------- headline: existing subscribers
monthly = rates(by_month, ["due_month", "customer_type", "block_flag"])
monthly.to_csv(DATA / "churn_rate_by_due_month.csv", index=False)

headline_rows = []
for label, df in [("organic existing", organic_existing),
                  ("2025-09-17 block", by_month[by_month["block_flag"] == "block_2025_09_17"])]:
    b = df[df["window"] == "before"]
    for after_label, a in [("Mar-Jul 2026", df[df["window"] == "after"]),
                           ("Mar 2026 only", df[df["due_month"] == "2026-03-01"]),
                           ("Apr-Jul 2026", df[df["due_month"] >= "2026-04-01"])]:
        row = compare(b["renewals_due"].sum(), b["missed_renewals"].sum(), a["renewals_due"].sum(), a["missed_renewals"].sum())
        headline_rows.append({"group": label, "after_window": after_label, **row,
                              "above_break_even": row["change_relative"] > BREAK_EVEN_REL})
headline = pd.DataFrame(headline_rows)
headline.to_csv(DATA / "headline_churn.csv", index=False)

# ---------------------------------------------------------------- splits (organic existing)
seg_rows = []
july_size = seg[seg["due_month"] == "2026-07-01"].set_index(["dimension", "segment"])["renewals_due"]
for (dim, s), part in seg.groupby(["dimension", "segment"]):
    b, a = part[part["window"] == "before"], part[part["window"] == "after"]
    row = compare(b["renewals_due"].sum(), b["missed_renewals"].sum(), a["renewals_due"].sum(), a["missed_renewals"].sum())
    row.update(money(row["churn_before"], row["churn_after"], july_size[(dim, s)]))
    seg_rows.append({"dimension": dim, "segment": s, **row,
                     "big_enough": min(row["renewals_before"], row["renewals_after"]) >= MIN_RENEWALS,
                     "above_break_even": row["change_relative"] > BREAK_EVEN_REL})
segments = pd.DataFrame(seg_rows)
segments.to_csv(DATA / "churn_by_segment.csv", index=False)

# ---------------------------------------------------------------- new starts at the same renewal number
ns = new_starts.assign(churn_rate=new_starts["missed_renewals"] / new_starts["renewals_due"])
ns.to_csv(DATA / "new_start_churn_rate_by_renewal.csv", index=False)
before_ns = ns[ns["cohort"] == "starts_nov25_jan26_at_10"].set_index("renewal_number")
after_ns = ns[ns["cohort"] == "starts_mar26_jun26_at_12"].set_index("renewal_number")
shared = before_ns.index.intersection(after_ns.index)  # renewals 1 to 3
# Standardise both cohorts to the $12 cohort's mix of renewal numbers, so tenure mix cannot drive the gap.
weights = after_ns.loc[shared, "renewals_due"] / after_ns.loc[shared, "renewals_due"].sum()
ns_before_rate = float((before_ns.loc[shared, "churn_rate"] * weights).sum())
ns_after_rate = float((after_ns.loc[shared, "churn_rate"] * weights).sum())
ns_row = compare(before_ns.loc[shared, "renewals_due"].sum(), before_ns.loc[shared, "missed_renewals"].sum(),
                 after_ns.loc[shared, "renewals_due"].sum(), after_ns.loc[shared, "missed_renewals"].sum())
starts["window"] = starts["start_month"].map(window)
monthly_starts = starts[starts["plan"] == "monthly"]
avg_new_monthly_starts = monthly_starts[monthly_starts["window"] == "after"]["new_paid_starts"].mean()
new_start_summary = pd.DataFrame([{
    "group": "new monthly starts, renewals 1 to 3",
    **ns_row,
    "churn_before_standardised": ns_before_rate, "churn_after_standardised": ns_after_rate,
    "change_relative_standardised": ns_after_rate / ns_before_rate - 1,
    "above_break_even": ns_after_rate / ns_before_rate - 1 > BREAK_EVEN_REL,
    **money(ns_before_rate, ns_after_rate, avg_new_monthly_starts),
}])
new_start_summary.to_csv(DATA / "new_start_summary.csv", index=False)

# ---------------------------------------------------------------- plan mix and annual reference
mix = starts.pivot_table(index="window", columns="plan", values="new_paid_starts", aggfunc="sum")
months_per_window = starts.groupby("window")["start_month"].nunique()
mix_table = pd.DataFrame({
    "months": months_per_window,
    "monthly_starts_per_month": mix["monthly"] / months_per_window,
    "annual_starts_per_month": mix["annual"] / months_per_window,
    "annual_share": mix["annual"] / (mix["annual"] + mix["monthly"]),
}).reindex(["before", "after"]).reset_index()
mix_table.to_csv(DATA / "new_paid_start_mix.csv", index=False)

annual["window"] = annual["month_start"].map(window)
ann = annual.groupby("window")[["annual_at_month_start", "annual_churned", "annual_anniversaries_in_month",
                                "annual_churned_at_anniversary"]].sum().reindex(["before", "after"])
ann["monthly_churn_rate"] = ann["annual_churned"] / ann["annual_at_month_start"]
ann["churn_at_anniversary"] = ann["annual_churned_at_anniversary"] / ann["annual_anniversaries_in_month"]
ann.reset_index().to_csv(DATA / "annual_reference.csv", index=False)

# ---------------------------------------------------------------- money for the whole monthly base
oe = headline[(headline["group"] == "organic existing") & (headline["after_window"] == "Mar-Jul 2026")].iloc[0]
oe_late = headline[(headline["group"] == "organic existing") & (headline["after_window"] == "Apr-Jul 2026")].iloc[0]
july_base = organic_existing[organic_existing["due_month"] == "2026-07-01"]["renewals_due"].sum()
money_rows = [
    {"group": "organic existing, Mar-Jul churn", **money(oe["churn_before"], oe["churn_after"], july_base)},
    {"group": "organic existing, Apr-Jul churn", **money(oe_late["churn_before"], oe_late["churn_after"], july_base)},
    {"group": "new monthly starts, one month's cohort", **money(ns_before_rate, ns_after_rate, avg_new_monthly_starts)},
]
money_table = pd.DataFrame(money_rows)
money_table.to_csv(DATA / "money_at_stake.csv", index=False)

# Revenue path per subscriber, to show when $12 falls behind $10.
path = pd.DataFrame({
    "month": range(1, 37),
    "at_10_old_churn": revenue_path(OLD_PRICE, oe["churn_before"], 36).values,
    "at_12_new_churn": revenue_path(NEW_PRICE, oe["churn_after"], 36).values,
})
path.to_csv(DATA / "revenue_path_existing.csv", index=False)

# ---------------------------------------------------------------- charts
oe_m = monthly[(monthly["customer_type"] == "existing") & (monthly["block_flag"] == "organic")].sort_values("due_month")
labels = oe_m["due_month"].dt.strftime("%b %y")
charts.save(charts.line(
    labels, {"Existing subscribers": (oe_m["churn_rate"] * 100).round(2)},
    "Churn at renewal rose from about 1.3% to 3-5% a month once renewals followed a $12 charge",
    highlight="Existing subscribers", ylabel="Missed renewals, % of renewals due",
    source="Organic existing monthly subscribers, renewals due Nov 2025 to Jul 2026. sql/churn_by_due_month.sql"),
    CHARTS / "churn_by_due_month.png")

s = segments.assign(name=segments["dimension"].str.replace("_", " ") + ": " + segments["segment"])
s = s.sort_values("change_relative", ascending=False)
charts.save(charts.bar(
    s["name"], (s["change_relative"] * 100).round(0),
    "Every group's churn rose far past the 20% break-even line, so no group stands out for a rollback",
    highlight=list(s["name"].head(3)), ylabel="Relative rise in churn, Mar-Jul vs Nov-Feb (%)", horizontal=True,
    source="Break-even for a $10 to $12 rise is +20% relative. sql/churn_by_segment_month.sql"),
    CHARTS / "churn_rise_by_segment.png")

charts.save(charts.line(
    [f"Renewal {n}" for n in shared],
    {"Started Nov-Jan at $10": (before_ns.loc[shared, "churn_rate"] * 100).round(1),
     "Started Mar-Jun at $12": (after_ns.loc[shared, "churn_rate"] * 100).round(1)},
    "New subscribers who joined at $12 churn several times more at the same renewal",
    highlight="Started Mar-Jun at $12", ylabel="Missed renewals, % of renewals due",
    source="New monthly starts, no trial record. sql/new_start_churn_by_renewal.sql"),
    CHARTS / "new_start_churn_by_renewal.png")

charts.save(charts.line(
    path["month"], {"$10 at old churn": path["at_10_old_churn"].round(1), "$12 at new churn": path["at_12_new_churn"].round(1)},
    f"$12 earns more for about {money_rows[0]['months_until_12_falls_behind'] - 1} months, then falls behind $10 for good",
    highlight="$12 at new churn", ylabel="Cumulative revenue per subscriber ($)",
    source="Expected revenue per existing subscriber at steady churn. data/revenue_path_existing.csv"),
    CHARTS / "revenue_path_existing.png")

# ---------------------------------------------------------------- report
pd.set_option("display.width", 200)
print("\nHeadline churn at renewal:")
print(headline[["group", "after_window", "churn_before", "churn_after", "change_pp", "change_pp_ci_low",
                "change_pp_ci_high", "change_relative"]].round(4).to_string(index=False))
print("\nSplits (organic existing, Nov-Feb vs Mar-Jul):")
print(segments[["dimension", "segment", "churn_before", "churn_after", "change_pp", "change_relative", "big_enough",
                "gain_12m_per_subscriber", "months_until_12_falls_behind"]].round(4).to_string(index=False))
print("\nNew starts:")
print(new_start_summary[["churn_before_standardised", "churn_after_standardised", "change_relative_standardised",
                         "gain_12m_per_subscriber", "months_until_12_falls_behind"]].round(4).to_string(index=False))
print("\nNew paid start mix:")
print(mix_table.round(3).to_string(index=False))
print("\nAnnual reference:")
print(ann[["monthly_churn_rate", "churn_at_anniversary"]].round(4).to_string())
print("\nMoney at stake (12 months):")
print(money_table.round(2).to_string(index=False))
failed = [c["check"] for c in checks if not c["ok"]]
print(f"\nChecks: {len(checks) - len(failed)} of {len(checks)} passed" + (f"; failed: {failed}" if failed else ""))
