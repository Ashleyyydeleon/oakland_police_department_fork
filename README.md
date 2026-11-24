# Oakland Police Department (INFO 285)

Analysis of OPD 911 call demand and patrol response. Data lives in Box; code finds it with `opd_paths.py` (see `BOX_LAYOUT.md`).

```
opd_paths.py, box_utils.py      shared helpers (stay at the repo root)
OPD_box_example.ipynb           how to load Box files
data_prep/
  cad_calls/                    build the harmonized CAD calls table
  patrol_staffing/              build the patrol officers by Area table
  weather/                      fetch Oakland weather
call_demand/
  exploratory_analysis/         call volume, demand and P1 response EDA
  forecast/
    notebooks/                  demand forecast models
    models/                     negative binomial model scripts (v1-v4)
    evaluation/                 long-horizon evaluation
patrol_response/
  response_times/               response and travel times by beat
  staffing/                     patrol staffing vs demand
  manpower/
    cleaning/                   match Man_Power July 2024 unit logs to CAD
    analysis/                   incidents per unit, unit availability
  regression_discontinuity/     P1 shift starts and P2 peak hours
```

Notebooks and scripts in subfolders add the repo root to `sys.path` at the top of their import cell, so they run from any folder.
