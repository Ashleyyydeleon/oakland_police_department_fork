# Manpower utilization and dispatch wait, July 2024

Code and tables behind the manpower numbers in the draft write-up "Reducing 911 wait times: what the manpower data shows", for example *regular-watch patrol cars are on calls 78% of the time and free 3.9%*, and *P2 calls wait a median 93 / 31 / 12 minutes when 0 / 1 / 2+ cars are free in their Area*.

## Why it is in Box
Box is the team's record for data and analysis outputs. The raw log is already here (`Data Collection (Officer) / Our Data / Unit Status Logs (Manpower)`); these are the tables we derived from it, so anyone can check a number in the write-up without running code. The scripts are also on GitHub (`patrol_response/manpower/analysis/manpower_utilization/`), where changes are versioned and reviewed.

## Why it is useful
- **Traceable:** every headline number links to a table and the exact definitions below.
- **Reusable:** point it at another month or the new CAD to test whether the pattern holds.
- **Next step:** the hourly and per-call tables are the inputs for an Area-level queue simulation.

## Files
| File | What it is |
|---|---|
| `manpower_utilization_and_dispatch_wait.py` | Main script: builds each car's status timeline, then hourly car states and dispatch wait vs free cars for every call. `ALL_LINE=1` runs the sensitivity check with every line-patrol car. |
| `manpower_time_use_and_stranded_capacity.py` | Run second: waits by hour, where car-time goes (hospital, jail), calls waiting while cars are free elsewhere. |
| `manpower_2024-07_hourly_patrol_car_states.csv` | Per hour of day, regular-watch cars: average cars logged on / free / on calls / other, and % of time no car is free. |
| `manpower_2024-07_call_dispatch_wait_vs_idle_cars.csv` | Per call (11,480 public P1 to P3 calls): `priority`, `area`, `hour`, `wait_min` (created to first dispatch), `travel_min`, `idle_area` / `idle_city` (cars free when the call was created). No names or addresses. |
| `..._all_line.csv` versions | Same two tables counting every line-patrol car. |

**Where things live:** Box has everything in this folder. GitHub has the code, this README and the two small hourly tables; the per-call tables (about 0.5 MB each) are in Box only.

**Rerun:** `python3 manpower_utilization_and_dispatch_wait.py` (then with `ALL_LINE=1`, then the second script). Needs the repo's `opd_paths.py` and a synced Box folder. Output goes to `./output` or the folder in `MANPOWER_OUT`.

## Definitions
- **Status row:** one car entering one status; the timestamp is when it **entered**, `Seconds_At_Status` how long it stayed until its next record.
- **Free:** status "available". **On calls:** "en route" plus "on scene". (Our reading of the codes; the file has no legend.)
- **Regular-watch cars:** line-patrol units with IDs 1xxx to 3xxx (the three watches), 193 units. The other 389 line-patrol units appear only in the `_all_line` checks.
- **Area:** from the beat in the unit ID (last two digits).

## Caveats
One month (1 to 29 July 2024, 18 to 19 July excluded), old CAD only. "Available", the ID pattern and the 389 other units are not confirmed by OPD. Counting all line cars, no car is free citywide 12% of the time instead of 47%; the Area-level result holds either way. Draft.

## Source
Unit status ("manpower") log, 1 to 29 July 2024 [provided to the Clinic by ___ on ___]; Box: `OPD / Data Collection / Data Collection (Officer) / Our Data / Unit Status Logs (Manpower) / Cleaned / manpower_2024-07_matched_with_code_meanings.csv`. CAD calls: `harmonized_calls_2021_2026.parquet`. Analysis: Public Interest Technology Clinic OPD team, Fall 2026.
