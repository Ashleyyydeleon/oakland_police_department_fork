"""Manpower (unit status log), July 2024: how often are patrol cars free, and do calls wait longer when none are?

Run:  python3 manpower_utilization_and_dispatch_wait.py            (regular-watch cars: main result)
      ALL_LINE=1 python3 manpower_utilization_and_dispatch_wait.py  (sensitivity: every line-patrol car)
Writes two tables per run to ./output (or the folder in env var MANPOWER_OUT).


Inputs (found by name via opd_paths): manpower_2024-07_matched_with_code_meanings.csv, harmonized_calls_2021_2026.parquet.
Status rows: the timestamp is the START of a status and Seconds_At_Status its duration (checked: duration == gap to the next row).
Scope: 1-29 July 2024 excluding 18-19 July (CAD outage), line-patrol cars. Old CAD only (OPD switched systems on 30 July).
"""
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

T0 = pd.Timestamp("2024-07-01"); NDAYS = 29; N = NDAYS * 86400
BAD_DAYS = {17, 18}                                     # day index of 18 and 19 July
d = pd.read_csv(DATA / "manpower_2024-07_matched_with_code_meanings.csv", low_memory=False)
d["t"] = pd.to_datetime(d.Manpower_Record_Time)
d["secs"] = pd.to_numeric(d.Seconds_At_Status.astype(str).str.replace(",", ""), errors="coerce")
d = d[d.secs.notna() & (d.secs > 0) & (d.secs < 86400)].copy()
import os
ALL_LINE = os.environ.get("ALL_LINE") == "1"           # sensitivity: every line-patrol car, not only the three regular watches (unit IDs 1xxx-3xxx)
pat = (d[d.unit_type.astype(str).str.startswith("line patrol")] if ALL_LINE else d[d.is_patrol == True]).copy()
print("MODE:", "ALL line-patrol cars" if ALL_LINE else "regular-watch line-patrol cars (is_patrol)", "| rows:", len(pat), "| unit types:", pat.unit_type.value_counts().to_dict())
# OPD call sign = watch digit + type letter + beat (e.g. 2L19 = Second Watch, line car, beat 19); Area comes from the beat
beat = pd.to_numeric(pat.Unit_ID.astype(str).str[-2:], errors="coerce")
AREA = {1: (1, 7), 2: (8, 13), 3: (14, 19), 4: (20, 25), 5: (26, 30), 6: (31, 35)}
pat["area"] = beat.map(lambda b: np.nan if pd.isna(b) else next((a for a, (lo, hi) in AREA.items() if lo <= b <= hi), np.nan))
print("rows with a usable beat/Area:", int(pat.area.notna().sum()), "of", len(pat)); pat = pat[pat.area.notna()]

def state(r):
    c, m = r.code_category, r.code_meaning
    if c == "log off": return None
    if c == "available": return "idle"
    if c in ("en route to call", "on scene"): return "on_call"
    if c in ("en route to facility", "at facility", "transporting a person"): return "facility_transport"
    if c == "officer-initiated": return "officer_initiated"
    return "station_other"                              # log on, at station, special assignment, status update, out of service
pat["state"] = [state(r) for r in pat[["code_category", "code_meaning"]].itertuples()]
pat = pat[pat.state.notna()]
pat["s0"] = ((pat.t - T0).dt.total_seconds()).astype(int)
pat["s1"] = (pat.s0 + pat.secs).astype(int).clip(upper=N)
pat = pat[(pat.s0 >= 0) & (pat.s0 < N)]

def count_series(rows):
    diff = np.zeros(N + 1, dtype=np.int32)
    np.add.at(diff, rows.s0.values, 1); np.add.at(diff, rows.s1.values, -1)
    return np.cumsum(diff[:N])
sec = np.arange(N); day = sec // 86400; hod = (sec % 86400) // 3600
ok = ~np.isin(day, list(BAD_DAYS))
res = {}
for name, sub in [("citywide", pat)] + [(f"area{a}", pat[pat.area == a]) for a in range(1, 7)]:
    on = count_series(sub); idle = count_series(sub[sub.state == "idle"])
    res[name] = dict(on=on, idle=idle, on_call=count_series(sub[sub.state == "on_call"]),
                     fac=count_series(sub[sub.state == "facility_transport"]), oi=count_series(sub[sub.state == "officer_initiated"]),
                     oth=count_series(sub[sub.state == "station_other"]))

print("\n=== 1. Citywide patrol cars by hour of day (average over 27 days) ===")
c = res["citywide"]; rows = []
for h in range(24):
    m = ok & (hod == h)
    on = c["on"][m].mean(); rows.append(dict(hour=h, logged_on=on, idle=c["idle"][m].mean(), pct_idle=100 * c["idle"][m].mean() / on,
                                                on_call=c["on_call"][m].mean(), facility=c["fac"][m].mean(), officer_init=c["oi"][m].mean(), other=c["oth"][m].mean(),
                                                pct_time_zero_idle=100 * (c["idle"][m] == 0).mean()))
hourly = pd.DataFrame(rows).round(1); print(hourly.to_string(index=False))
m = ok
print(f"\nAll hours: avg {c['on'][m].mean():.1f} patrol cars logged on; idle {c['idle'][m].mean():.1f} ({100*c['idle'][m].mean()/c['on'][m].mean():.1f}%); "
      f"on calls {100*c['on_call'][m].mean()/c['on'][m].mean():.0f}%; facility/transport {100*c['fac'][m].mean()/c['on'][m].mean():.0f}%; "
      f"officer-initiated {100*c['oi'][m].mean()/c['on'][m].mean():.0f}%; station/other {100*c['oth'][m].mean()/c['on'][m].mean():.0f}%.")
print(f"Share of time with NO idle patrol car citywide: {100*(c['idle'][m]==0).mean():.1f}%")
for a in range(1, 7):
    r = res[f"area{a}"]; print(f"Area {a}: avg on {r['on'][m].mean():.1f}, idle {r['idle'][m].mean():.2f}, share of time zero idle in Area: {100*(r['idle'][m]==0).mean():.0f}%")

# ---- 2. dispatch wait by idle units at the moment the call arrives
h = pd.read_parquet(DATA / "harmonized_calls_2021_2026.parquet", columns=["event_number", "beat", "call_source", "priority", "event_time", "dispatch_time", "arrival_time"])
h = h[(h.event_time >= T0) & (h.event_time < T0 + pd.Timedelta(days=NDAYS))].copy()
h = h[~h.call_source.astype(str).str.upper().str.startswith("FIELD")]             # officer-initiated calls dispatch themselves
h["priority"] = pd.to_numeric(h.priority, errors="coerce"); h = h[h.priority.isin([1, 2, 3])]
h["s"] = ((h.event_time - T0).dt.total_seconds()).astype(int); h = h[~np.isin(h.s // 86400, list(BAD_DAYS))]
h["wait_min"] = (h.dispatch_time - h.event_time).dt.total_seconds() / 60
h["travel_min"] = (h.arrival_time - h.dispatch_time).dt.total_seconds() / 60
h = h[(h.wait_min >= 0) & (h.wait_min < 24 * 60)]
h["area"] = pd.to_numeric(h.beat.astype(str).str.extract(r"^(\d+)")[0], errors="coerce").map(lambda b: np.nan if pd.isna(b) else next((a for a, (lo, hi) in {1: (1, 7), 2: (8, 13), 3: (14, 19), 4: (20, 25), 5: (26, 30), 6: (31, 35)}.items() if lo <= b <= hi), np.nan))
h = h[h.area.notna()]
h["idle_area"] = [res[f"area{int(a)}"]["idle"][s] for a, s in zip(h.area, h.s)]
h["idle_city"] = res["citywide"]["idle"][h.s.values]
bins = [-1, 0, 2, 5, 999]; labels = ["0", "1-2", "3-5", "6+"]
h["idle_bin_city"] = pd.cut(h.idle_city, bins, labels=labels)
h["idle_bin_area"] = pd.cut(h.idle_area, [-1, 0, 1, 999], labels=["0", "1", "2+"])
print("\n=== 2. Wait for dispatch (minutes) by patrol cars idle citywide at the moment the call is created ===")
t = h.groupby(["priority", "idle_bin_city"], observed=True).wait_min.agg(calls="size", median="median", p90=lambda s: s.quantile(.9)).round(1); print(t.to_string())
print("\n=== same, by patrol cars idle in the call's OWN Area ===")
t2 = h.groupby(["priority", "idle_bin_area"], observed=True).wait_min.agg(calls="size", median="median", p90=lambda s: s.quantile(.9)).round(1); print(t2.to_string())
print("\n=== Overall by priority: wait for dispatch vs travel (median minutes) ===")
print(h.groupby("priority").agg(calls=("wait_min", "size"), wait_med=("wait_min", "median"), wait_p90=("wait_min", lambda s: s.quantile(.9)), travel_med=("travel_min", "median")).round(1).to_string())
# share of calls created while no car idle in own Area / citywide
print(f"\nCalls created while NO patrol car idle in their Area: {100*(h.idle_area==0).mean():.0f}% (P1 {100*(h[h.priority==1].idle_area==0).mean():.0f}%, P2 {100*(h[h.priority==2].idle_area==0).mean():.0f}%, P3 {100*(h[h.priority==3].idle_area==0).mean():.0f}%)")
sfx = "_all_line" if ALL_LINE else ""
hourly.to_csv(OUT_DIR / f"manpower_2024-07_hourly_patrol_car_states{sfx}.csv", index=False)
h["hour"] = h.event_time.dt.hour
h[["priority", "area", "hour", "wait_min", "travel_min", "idle_area", "idle_city"]].to_csv(OUT_DIR / f"manpower_2024-07_call_dispatch_wait_vs_idle_cars{sfx}.csv", index=False)
