"""Recheck: tenure mix by country/device in after_steady renewals, and in the active base. Aggregates only."""
import runpy, io, contextlib, pandas as pd
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g = runpy.run_path("outputs/2026-11-07_march-price-retention/rerun/analysis.py")
ren = g["ren"]
s = ren[ren.window == "after_steady"]
for dim in ["country", "device_type"]:
    t = pd.crosstab(s[dim], s.tenure, normalize="index").round(3) * 100
    print(dim, "tenure share % (after_steady renewals)\n", t.to_string())
b = ren[ren.window == "before_clean"]
print("before_clean renewals by tenure:", b.groupby("tenure", observed=True).size().to_dict())
