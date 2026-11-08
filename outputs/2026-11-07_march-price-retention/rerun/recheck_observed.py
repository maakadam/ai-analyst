"""Recheck of observed_revenue_mar_jul.csv: does a constant segment churn rate bias the counterfactual?
Aggregates only. Rebuilds the counterfactual with band-specific Nov-Feb churn that follows each
subscriber's tenure month by month, and the observed gain by due month."""
import pandas as pd, numpy as np
from pathlib import Path
ROOT = Path.cwd()
TB=[0,1,3,6,12,24,10_000]; TL=["1","2-3","4-6","7-12","13-24","25+"]
subs=pd.read_csv(ROOT/"data/subscriptions.csv",parse_dates=["start_date"])
pay=pd.read_csv(ROOT/"data/payments.csv",parse_dates=["payment_date"])
tr=pd.read_csv(ROOT/"data/trials.csv")
subs=subs[~subs.user_id.isin(set(tr.user_id))]
subs["spike"]=subs.start_date.dt.normalize()==pd.Timestamp("2025-09-17")
p=pay.merge(subs[["subscription_id","plan","start_date","spike"]],on="subscription_id")
p=p[(p.plan=="monthly")&~p.spike].sort_values(["subscription_id","payment_date"])
p["nxt"]=p.groupby("subscription_id").payment_date.shift(-1)
p["due"]=p.payment_date+pd.Timedelta(days=30)
p["tm"]=((p.due-p.start_date).dt.days/30).round()
p["band"]=pd.cut(p.tm,TB,labels=TL).astype(str)
p["churn"]=p.nxt.isna()
bc=p[(p.due>="2025-11-01")&(p.due<="2026-02-28 23:59:59")].groupby("band").churn.mean()
print("raw Nov-Feb churn by band:",bc.round(4).to_dict())
W=pd.Timestamp("2026-07-31 23:59:59"); F=pd.Timestamp("2026-02-28 23:59:59")
b0=p[(p.payment_date>F-pd.Timedelta(days=30))&(p.payment_date<=F)].copy()
b0["k"]=((W-b0.payment_date).dt.days//30).astype(int)
# path counterfactual
exp=0.0; rows=[]
for _,r in b0[["payment_date","start_date","k"]].iterrows(): pass
def surv_path(pd_,sd,k):
    s=1.0; out=[]
    for j in range(1,k+1):
        due=pd_+pd.Timedelta(days=30*j)
        band=str(pd.cut([round((due-sd).days/30)],TB,labels=TL)[0])
        s*=1-bc[band]; out.append((due.to_period("M"),s))
    return out
cf={}
for pd_,sd,k in zip(b0.payment_date,b0.start_date,b0.k):
    for m,s in surv_path(pd_,sd,k): cf[m]=cf.get(m,0)+10*s
obs=p[p.subscription_id.isin(b0.subscription_id)&(p.payment_date>F)&(p.payment_date<=W)]
om=obs.groupby(obs.payment_date.dt.to_period("M")).amount_usd.sum()
t=pd.DataFrame({"observed":om,"cf_path_10":pd.Series(cf)}); t["gain"]=t.observed-t.cf_path_10
print(t.round(0).to_string()); print("total path cf",round(sum(cf.values())),"observed",om.sum(),"gain",round(om.sum()-sum(cf.values())))
# segment 2-3 and 4-6 by start band
b0["band0"]=pd.cut(((b0.payment_date+pd.Timedelta(days=30)-b0.start_date).dt.days/30).round(),TB,labels=TL).astype(str)
for b in ["1","2-3","4-6","7-12"]:
    g=b0[b0.band0==b]; c=0
    for pd_,sd,k in zip(g.payment_date,g.start_date,g.k): c+=sum(10*s for _,s in surv_path(pd_,sd,k))
    o=obs[obs.subscription_id.isin(g.subscription_id)].amount_usd.sum()
    print(b,"n",len(g),"obs",o,"cf_path",round(c),"gain",round(o-c))
