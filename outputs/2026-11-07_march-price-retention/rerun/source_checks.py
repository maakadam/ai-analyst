"""Act 6 source-data checks for the review. Aggregates only."""
import pandas as pd
from helpers import checks
D = "data/"
subs = pd.read_csv(D+"subscriptions.csv", parse_dates=["start_date","end_date"])
pay = pd.read_csv(D+"payments.csv", parse_dates=["payment_date"])
trials = pd.read_csv(D+"trials.csv")
subs = subs[~subs.user_id.isin(set(trials.user_id))]
m = subs[subs.plan=="monthly"]
spike = m.start_date.dt.normalize()==pd.Timestamp("2025-09-17")
p = pay.merge(m[["subscription_id","start_date","end_date","status"]], on="subscription_id")
p = p.sort_values(["subscription_id","payment_date"])
p["next_gap"] = p.groupby("subscription_id").payment_date.shift(-1).sub(p.payment_date).dt.days
p["due"] = p.payment_date + pd.Timedelta(days=30)
p["churned"] = p.next_gap.isna()
p["spike"] = p.start_date.dt.normalize()==pd.Timestamp("2025-09-17")
w = p[(p.due>="2025-03-01")&(p.due<="2026-07-31 23:59:59")&~p.spike].copy()
w["ten"] = ((w.due-w.start_date).dt.days/30).round()
print("1 churn flag, all:", checks.stable_over_time(w,"due","churned")["summary"])
for lab, sub in [("tenure 13-24", w[(w.ten>12)&(w.ten<=24)]), ("tenure 25+", w[w.ten>24]),
                 ("started before 2024", w[w.start_date<"2024-01-01"]),
                 ("started 2024", w[(w.start_date>="2024-01-01")&(w.start_date<"2025-01-01")])]:
    r = checks.stable_over_time(sub,"due","churned")
    print(f"1 churn flag, {lab}:", r["summary"])
    print("   levels:", (r["level_by_period"]*100).round(2).to_dict())
# 2 payment/end-date consistency for churned monthly subs: gap last payment -> end_date
last = p.groupby("subscription_id").agg(last=("payment_date","max"), end=("end_date","first"), start=("start_date","first"))
last = last[last.end.notna() & (last.end<="2026-07-31 23:59:59") & (last.end>="2025-02-01")]
last["gap"] = (last.end-last["last"]).dt.days
print("2 gap last pay->end:", checks.stable_over_time(last.reset_index(),"end","gap")["summary"])
last["over31"] = last.gap>31
print("2 share ending >31d after last pay:", checks.stable_over_time(last.reset_index(),"end","over31")["summary"])
# 3 ended monthly subs without any payment, by end month (would be invisible churn)
mm = m[~spike & m.end_date.notna() & (m.end_date>="2025-03-01") & (m.end_date<="2026-08-31")].copy()
mm["has_pay"] = mm.subscription_id.isin(pay.subscription_id)
mm["old"] = mm.start_date < "2024-03-01"
t = mm.groupby([mm.end_date.dt.to_period("Q"), "old"]).has_pay.agg(["size","sum"])
print("3 ended monthly subs (excl spike) by end quarter x started before 2024-03: n, with payments\n", t.to_string())
# 4 subs whose first payment is far after start (payment history begins late = left truncated)
fp = p.groupby("subscription_id").agg(first=("payment_date","min"), start=("start_date","first"))
fp = fp[fp.start>="2025-01-01"]
print("4 subs started 2025+ whose first payment is >1 day after start:", int(((fp["first"]-fp.start).dt.days>1).sum()), "of", len(fp))
# 5 active-base completeness: subs active through a month (start before, end after or null) with a payment in that month
months = pd.period_range("2025-02","2026-07",freq="M")
rows=[]
pm = set(zip(p.subscription_id, p.payment_date.dt.to_period("M")))
for mo in months:
    s, e = mo.start_time, mo.end_time
    act = m[~spike & (m.start_date < s - pd.Timedelta(days=31)) & (m.end_date.isna() | (m.end_date > e + pd.Timedelta(days=31)))]
    rows.append({"month":str(mo),"active":len(act),"paid_share":sum((i,mo) in pm for i in act.subscription_id)/len(act)})
print("5 share of clearly-active monthly subs with a payment in the month:\n", pd.DataFrame(rows).round(4).to_string())
