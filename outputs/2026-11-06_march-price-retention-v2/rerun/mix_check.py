import pandas as pd
subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
users = pd.read_csv("data/users.csv")
m = subs[(subs.plan == "monthly") & (subs.start_date <= "2026-09-24")].merge(users[["user_id", "country", "device_type"]], on="user_id")
m["sm"] = m.start_date.dt.to_period("M").astype(str)
m = m[m.sm.between("2025-11", "2026-08")]
m["grp"] = m.sm.where(m.sm.isin(["2026-07", "2026-08"]), m.sm.where(m.sm < "2026-03", "x").map(lambda s: "Nov-Feb" if s != "x" else "Mar-Jun"))
for col in ["country", "device_type"]:
    print(pd.crosstab(m.grp, m[col], normalize="index").round(2))
# cancel within 60 days of start, for starts with 60 days observed
m["c60"] = m.end_date.notna() & ((m.end_date - m.start_date).dt.days <= 60)
o = m[m.start_date <= pd.Timestamp("2026-09-24") - pd.Timedelta(days=60)]
print(o.groupby("grp")["c60"].agg(["size", "mean"]).round(3))
