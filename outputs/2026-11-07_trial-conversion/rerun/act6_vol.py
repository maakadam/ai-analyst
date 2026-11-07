from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
u = pd.read_csv(ROOT/"data/users.csv", parse_dates=["signup_date"])
s = pd.read_csv(ROOT/"data/subscriptions.csv", parse_dates=["start_date"])
x = u[(u.signup_date>="2026-07-24")&(u.signup_date<"2026-08-05")]
print(x.groupby(x.signup_date.dt.date).size().to_string())
f = s[s.start_date>"2026-09-24 23:59:59"]
print("start after today by plan:", f.plan.value_counts().to_dict())
