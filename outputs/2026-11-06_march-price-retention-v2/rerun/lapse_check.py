import pandas as pd
subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
pay = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])
p = pay.merge(subs[["subscription_id", "plan", "end_date"]], on="subscription_id")
p = p[p.plan == "monthly"].sort_values(["subscription_id", "payment_date"])
p["next"] = p.groupby("subscription_id")["payment_date"].shift(-1)
p["m"] = p.payment_date.dt.to_period("M")
p = p[p.payment_date + pd.Timedelta(days=40) <= pd.Timestamp("2026-09-24")]
p["lapsed"] = p.next.isna() | ((p.next - p.payment_date).dt.days > 40)
p["resumed"] = p.lapsed & p.next.notna()
p["ended_within_45d"] = p.lapsed & p.end_date.notna() & ((p.end_date - p.payment_date).dt.days.between(0, 45))
print(p.groupby("m")[["lapsed", "resumed", "ended_within_45d"]].sum().loc["2025-06":"2026-02"].to_string())
