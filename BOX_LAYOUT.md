# Box folder layout (reorganised 2026-11-17) and how code finds files

Box: `OPD & TAN - Core Workspace/OPD - Oakland Police Dept/`

```
Data Collection (Police Officer)/Our Data/   CAD Calls · Patrol Staffing · Unit Status Logs (Manpower) · Geography and External · Reference Studies
Data Collection (Dispatcher)/Our Data/       911 Answer Speed · Dispatcher Staffing · Reference
Data Outputs/Graphs/                         Call Volume · P1 Response Time · Travel Time and Maps · Patrol Staffing · Dispatcher Story · Call-Taker Scheduling · Forecast Models · Slides
Data Outputs/Analysis/                       Notebooks · Notes · Tables
```
Each dataset folder is split into `Raw/` (as received), `Cleaned/` (made by us) and `Docs/` (data guides).
Every moved/renamed file is listed in `MOVED_FILES.csv` (OPD folder) and each top folder has a `_FOLDER_GUIDE.md`.

## Don't hard-code Box paths: use `opd_paths.py`
```python
from opd_paths import ROOT, DATA, OUT
df = pd.read_parquet(DATA / "harmonized_calls_2021_2026.parquet")   # finds the file wherever it lives
fig.savefig(OUT / "dispatch_p1_queue_vs_travel_by_hour.png")        # filed in the right Graphs/ subfolder
```
- Accepts a file's **old or new name** and falls back to older layouts, so older notebooks keep working.
- Finds Box on any machine (`BOX_ROOT` env var overrides; `OPD_ROOT` overrides the OPD folder).
- `python opd_paths.py` prints any known file it can't find (run it after pulling to confirm your Box sync is complete).
- New outputs are filed by name prefix (e.g. `p1_median_response_time_by_hour_by_area_2027.png` goes next to the 2026 chart).

## If your script or notebook stopped finding a file
1. `git pull` this repo (scripts were updated to use `opd_paths`), and make sure `opd_paths.py` is next to your script/notebook.
2. Replace any hand-built path (`"../Data/Our Data/..."`, `BOX_ROOT / ... / "Outputs"`) with `DATA / "name"` or `OUT / "name"`.
3. Still stuck? Look the old name up in `MOVED_FILES.csv`.
