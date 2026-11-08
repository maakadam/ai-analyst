import pandas as pd
D = "outputs/2026-11-07_march-price-retention/data/"
m = pd.read_csv(D + "observed_revenue_by_due_month.csv")
o = pd.read_csv(D + "observed_revenue_mar_jul.csv")
s = m.groupby(["dimension", "segment"])[["observed_usd", "counterfactual_usd", "gain_usd"]].sum()
j = o.set_index(["dimension", "segment"])[["observed_mar_jul_usd", "counterfactual_10_baseline_churn_usd", "observed_gain_usd"]]
diff = (s.values - j.loc[s.index].values)
print("max abs diff month-sum vs total, per segment:", abs(diff).max().round(6))
allm = m[m.dimension == "all"].set_index("due_month").observed_usd
for dim in ["country", "device_type", "tenure"]:
    p = m[m.dimension == dim].groupby("due_month").observed_usd.sum()
    print(dim, "observed segments vs all per month, max diff:", (p - allm).abs().max())
print("months per segment:", m.groupby(["dimension", "segment"]).size().unique())
c = pd.read_csv(D + "churn_by_due_month.csv"); print(c.columns.tolist()); print(c.tail(8).to_string())
