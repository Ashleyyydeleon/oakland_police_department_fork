"""Second step (run AFTER manpower_utilization_and_dispatch_wait.py, both modes): stranded capacity, wait by hour,
where patrol-car time goes, supply vs demand by hour. Reads the tables the first script wrote to ./output."""
import os, sys
from pathlib import Path
# Find opd_paths.py (in the repo root) so files are located by name wherever they live in Box.
for _p in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
    if (_p / "opd_paths.py").exists():
        sys.path.insert(0, str(_p)); break
else:
    sys.path.insert(0, os.environ.get("OPD_REPO", "."))     # or set OPD_REPO to the folder holding opd_paths.py
from opd_paths import DATA
OUT_DIR = Path(os.environ.get("MANPOWER_OUT", Path(__file__).resolve().parent / "output")); OUT_DIR.mkdir(parents=True, exist_ok=True)
import numpy as np, pandas as pd
pd.set_option("display.width", 200)
for sfx, label in (("", "REGULAR-WATCH CARS (main)"), ("_all_line", "ALL LINE-PATROL CARS (sensitivity)")):
    c = pd.read_csv(OUT_DIR / f"manpower_2024-07_call_dispatch_wait_vs_idle_cars{sfx}.csv"); print("\n" + "#" * 8, label)
    for pr in (1, 2):
        x = c[c.priority == pr]
        a = x[(x.idle_area == 0) & (x.idle_city >= 3)]; b = x[(x.idle_area == 0) & (x.idle_city == 0)]; z = x[x.idle_area >= 1]
        print(f"P{pr}: median wait (min) | own Area empty but >=3 cars idle elsewhere: {a.wait_min.median():.1f} (n={len(a)}) | whole city empty: {b.wait_min.median():.1f} (n={len(b)}) | own Area has >=1 idle: {z.wait_min.median():.1f} (n={len(z)})")
    x = c[c.priority == 2]; y = x[(x.idle_area == 0) & (x.idle_city >= 3)]
    print(f"   P2 calls created with their Area empty but >=3 cars idle elsewhere: {100*len(y)/len(x):.0f}% of P2 calls ({len(y)} calls)")
    print("   wait by hour (median min):  P1:", c[c.priority == 1].groupby("hour").wait_min.median().round(1).to_dict())
c = pd.read_csv(OUT_DIR / "manpower_2024-07_call_dispatch_wait_vs_idle_cars.csv")
hr = pd.read_csv(OUT_DIR / "manpower_2024-07_hourly_patrol_car_states.csv")
t = pd.DataFrame({"P1_wait_med": c[c.priority == 1].groupby("hour").wait_min.median(), "P1_wait_p90": c[c.priority == 1].groupby("hour").wait_min.quantile(.9),
                  "P1_pct_over_10min": c[c.priority == 1].groupby("hour").wait_min.apply(lambda s: 100 * (s > 10).mean()),
                  "P2_wait_med": c[c.priority == 2].groupby("hour").wait_min.median(), "calls_per_day": c.groupby("hour").size() / 27}).round(1)
t["cars_on"] = hr.set_index("hour").logged_on; t["pct_zero_idle"] = hr.set_index("hour").pct_time_zero_idle
t["calls_per_car_hr"] = (t.calls_per_day / t.cars_on).round(2)
print("\n=== By hour of day: demand, supply, waits (regular-watch cars; calls = public P1-P3) ==="); print(t.to_string())
# what car time is spent on
d = pd.read_csv(DATA / "manpower_2024-07_matched_with_code_meanings.csv", low_memory=False, usecols=["Unit_ID", "is_patrol", "code_category", "code_meaning", "Seconds_At_Status", "Manpower_Record_Time"])
d["secs"] = pd.to_numeric(d.Seconds_At_Status.astype(str).str.replace(",", ""), errors="coerce"); d["t"] = pd.to_datetime(d.Manpower_Record_Time)
d = d[(d.is_patrol == True) & d.secs.notna() & (d.secs < 86400) & (~d.t.dt.day.isin([18, 19])) & (d.code_category != "log off")]
tot = d.secs.sum() / 3600 / 27
g = (d.groupby(["code_category", "code_meaning"]).secs.sum() / 3600 / 27).sort_values(ascending=False)
print(f"\n=== Where regular-watch patrol-car time goes (car-hours per day; total {tot:.0f} = {tot/24:.1f} cars logged on all day) ===")
print(g.head(14).round(1).to_string())
print("\nfacility+transport+special assignment+hospital guard etc. (non-call, non-idle) hours/day:")
nc = d[d.code_category.isin(["en route to facility", "at facility", "transporting a person", "special assignment"])]
print((nc.groupby("code_meaning").secs.sum() / 3600 / 27).sort_values(ascending=False).round(2).head(10).to_string()); print("total:", round(nc.secs.sum() / 3600 / 27, 1), "car-hours/day =", round(nc.secs.sum() / 3600 / 27 / 24, 2), "cars around the clock")
