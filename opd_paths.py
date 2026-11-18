"""opd_paths.py: the one place that knows where OPD files live in Box.

Why: the Box folders were reorganised (see MOVED_FILES.csv in the OPD folder). Scripts and notebooks that
build paths by hand break whenever folders move. Use this module instead:

    from opd_paths import ROOT, DATA, OUT
    df  = pd.read_parquet(DATA / "harmonized_calls_2021_2026.parquet")   # finds the file wherever it is
    fig.savefig(OUT / "dispatcher_story_1_phone_demand_vs_staffing_2024.png")  # goes to the right Graphs/ subfolder

* Works with the NEW layout and falls back to the OLD one, so it is safe before and after the move.
* Accepts a file's old name or its new name (e.g. "story_1_..." or "dispatcher_story_1_...").
* Finds Box on any machine (env var BOX_ROOT overrides; OPD_ROOT overrides the OPD folder itself).
* ROOT is the OPD folder (plain Path): ROOT / "cache" / "hourly_calls.parquet".

Check your setup:  python opd_paths.py --check
"""
import glob
import os
import sys
from pathlib import Path

# (old path, new path) relative to the OPD folder. Generated from the approved restructure plan.
_MOVES = [('Data Collection (Police Officer)/Our Data/2021-2026current - DATA GUIDE.md',
  'Data Collection (Police Officer)/Our Data/CAD Calls (Computer-Aided '
  'Dispatch)/Docs/cad_calls_2021-2026_DATA_GUIDE.md'),
 ('Data Collection (Police Officer)/Our Data/2021-2026current.xlsx',
  'Data Collection (Police Officer)/Our Data/CAD Calls (Computer-Aided Dispatch)/Raw/cad_calls_2021-2026_raw.xlsx'),
 ('Data Collection (Police Officer)/Our Data/2024_answer_time.csv',
  'Data Collection (Dispatcher)/Our Data/911 Answer '
  'Speed/Cleaned/911_answer_time_by_hour_2024-01-01_to_2024-06-21.csv'),
 ('Data Collection (Police Officer)/Our Data/911-answering-speed-2025-q4.pdf',
  'Data Collection (Dispatcher)/Our Data/911 Answer Speed/Raw/911_answer_speed_2025-q4.pdf'),
 ('Data Collection (Police Officer)/Our Data/911-answering-speed-2026-jan-july.pdf',
  'Data Collection (Dispatcher)/Our Data/911 Answer Speed/Raw/911_answer_speed_2026-jan-jul.pdf'),
 ('Data Collection (Police Officer)/Our Data/911_01Jan-21Jun2024_OPD_Average Call Duration.xls',
  'Data Collection (Dispatcher)/Our Data/911 Answer Speed/Raw/911_answer_time_by_month_2024-01-01_to_2024-06-21.xls'),
 ('Data Collection (Police Officer)/Our Data/ACSDT5Y2024.B16005-2026-09-28T213014.xlsx',
  'Data Collection (Police Officer)/Our Data/Geography and '
  'External/Raw/acs_2024_5yr_B16005_nativity_by_english_ability_downloaded_2026-09-28.xlsx'),
 ('Data Collection (Police Officer)/Our Data/ACSST5Y2024.S1601-2026-09-28T212909.xlsx',
  'Data Collection (Police Officer)/Our Data/Geography and '
  'External/Raw/acs_2024_5yr_S1601_language_spoken_at_home_downloaded_2026-09-28.xlsx'),
 ('Data Collection (Police Officer)/Our Data/Audit REPORT OPD 911 response times - GUIDE.md',
  'Data Collection (Dispatcher)/Our Data/Reference/Audit REPORT OPD 911 response times - GUIDE.md'),
 ('Data Collection (Police Officer)/Our Data/Audit REPORT OPD 911 response times.pdf',
  'Data Collection (Dispatcher)/Our Data/Reference/Audit REPORT OPD 911 response times.pdf'),
 ('Data Collection (Police Officer)/Our Data/CrimeWatch_Maps_Past_90-Days_20260903.csv',
  'Data Collection (Police Officer)/Our Data/Geography and External/Raw/crimewatch_past_90_days_2026-09-03.csv'),
 ('Data Collection (Police Officer)/Our Data/Man_Power_2024_July_matched.csv',
  'Data Collection (Police Officer)/Our Data/Unit Status Logs (Manpower)/Cleaned/manpower_2024-07_matched_v1.csv'),
 ('Data Collection (Police Officer)/Our Data/Man_Power_2024_July_matched_codes.csv',
  'Data Collection (Police Officer)/Our Data/Unit Status Logs '
  '(Manpower)/Cleaned/manpower_2024-07_matched_with_code_meanings.csv'),
 ('Data Collection (Police Officer)/Our Data/Man_Power_2024_July_matched_new.csv',
  'Data Collection (Police Officer)/Our Data/Unit Status Logs (Manpower)/Cleaned/manpower_2024-07_matched_v2.csv'),
 ('Data Collection (Police Officer)/Our Data/Man_Power_2024_analysis.md',
  'Data Collection (Police Officer)/Our Data/Unit Status Logs '
  '(Manpower)/Docs/manpower_2024_codes_and_transitions_analysis.md'),
 ('Data Collection (Police Officer)/Our Data/OPD Dispatcher Data.boxnote',
  'Data Collection (Dispatcher)/Our Data/Dispatcher Staffing/dispatcher_actual_staffing_notes.boxnote'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/CPSM_Oakland_Police_Data_Analysis_2020-12.pdf',
  'Data Collection (Police Officer)/Our Data/Reference Studies/CPSM_Oakland_Police_Data_Analysis_2020-12.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD '
  'Reports/OPD_Memo_Patrol_Staffing_and_Structure_2023-07-01_watch_schedule_by_Area.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol '
  'Staffing/Raw/OPD_Memo_Patrol_Staffing_and_Structure_2023-07-01_watch_schedule_by_Area.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Memo_asof_2022-03-31_Q1-2022.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Memo_asof_2022-03-31_Q1-2022.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Memo_asof_2022-09-30_Q3-2022.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Memo_asof_2022-09-30_Q3-2022.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Memo_asof_2022-12-31_Q4-2022.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Memo_asof_2022-12-31_Q4-2022.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Report_asof_2023-03-31_Q1-2023.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Report_asof_2023-03-31_Q1-2023.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Report_asof_2023-09-30_biannual.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Report_asof_2023-09-30_biannual.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD '
  'Reports/OPD_Staffing_Report_asof_2023-12-31_biannual_supplemental.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol '
  'Staffing/Raw/OPD_Staffing_Report_asof_2023-12-31_biannual_supplemental.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Report_asof_2024-03-15_supplemental.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol '
  'Staffing/Raw/OPD_Staffing_Report_asof_2024-03-15_supplemental.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Report_asof_2024-06-30_biannual.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Report_asof_2024-06-30_biannual.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Report_asof_2025-06-17_biannual.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Report_asof_2025-06-17_biannual.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/OPD_Staffing_Report_asof_2026-02-28_biannual.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Raw/OPD_Staffing_Report_asof_2026-02-28_biannual.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD '
  'Reports/OPD_Staffing_Report_supplemental_2023-09-20_no_patrol_table.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol '
  'Staffing/Raw/OPD_Staffing_Report_supplemental_2023-09-20_no_patrol_table.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD '
  'Reports/OPD_Staffing_Report_supplemental_2026-03-18_no_patrol_table.pdf',
  'Data Collection (Police Officer)/Our Data/Patrol '
  'Staffing/Raw/OPD_Staffing_Report_supplemental_2026-03-18_no_patrol_table.pdf'),
 ('Data Collection (Police Officer)/Our Data/OPD Reports/PFM_OPD_Staffing_Study_2024-12.pdf',
  'Data Collection (Police Officer)/Our Data/Reference Studies/PFM_OPD_Staffing_Study_2024-12.pdf'),
 ('Data Collection (Police Officer)/Our Data/Radio Codes & Disposition.pdf',
  'Data Collection (Dispatcher)/Our Data/Reference/Radio Codes & Disposition.pdf'),
 ('Data Collection (Police Officer)/Our Data/harmonized_calls_2021_2026.parquet',
  'Data Collection (Police Officer)/Our Data/CAD Calls (Computer-Aided '
  'Dispatch)/Cleaned/cad_calls_2021-2026_harmonized.parquet'),
 ('Data Collection (Police Officer)/Our Data/oakland_address_points.parquet',
  'Data Collection (Police Officer)/Our Data/Geography and External/Raw/oakland_address_points.parquet'),
 ('Data Collection (Police Officer)/Our Data/opd_patrol_officers_by_area - DATA GUIDE.md',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Docs/opd_patrol_officers_by_area - DATA GUIDE.md'),
 ('Data Collection (Police Officer)/Our Data/opd_patrol_officers_by_area.csv',
  'Data Collection (Police Officer)/Our Data/Patrol Staffing/Cleaned/opd_patrol_officers_by_area.csv'),
 ('Data Collection (Police Officer)/Our Data/opd_response_times.csv',
  'Data Collection (Police Officer)/Our Data/CAD Calls (Computer-Aided '
  'Dispatch)/Cleaned/cad_response_time_stats_by_year_2021-2026.csv'),
 ('Data Collection (Police Officer)/Our Data/weather_oakland_2024_2026.parquet',
  'Data Collection (Police Officer)/Our Data/Geography and External/Cleaned/weather_oakland_2024_2026.parquet'),
 ('Data Collection (Dispatcher)/Dispatcher Data + Demand Analysis.boxnote',
  'Data Outputs/Analysis/Notes/dispatcher_data_and_demand_analysis_notes.boxnote'),
 ('Data Outputs/2024_answer_vs_response_time_filtered.png',
  'Data Outputs/Graphs/P1 Response Time/Overview/2024_answer_vs_response_time_filtered.png'),
 ('Data Outputs/baseline_nb_model_test_week.png',
  'Data Outputs/Graphs/Forecast Models/forecast_baseline_nb_model_test_week.png'),
 ('Data Outputs/beat_20x_spatial_travel_and_incidents.png',
  'Data Outputs/Graphs/Travel Time and Maps/beat_20x_spatial_travel_and_incidents.png'),
 ('Data Outputs/beat_center_to_addresses_distribution.png',
  'Data Outputs/Graphs/Travel Time and Maps/beat_center_to_addresses_distribution.png'),
 ('Data Outputs/beat_center_to_addresses_map.png',
  'Data Outputs/Graphs/Travel Time and Maps/beat_center_to_addresses_map.png'),
 ('Data Outputs/beat_center_to_addresses_summary.csv',
  'Data Outputs/Analysis/Tables/Travel Time/beat_center_to_addresses_summary.csv'),
 ('Data Outputs/beat_center_to_addresses_times.parquet',
  'Data Outputs/Analysis/Tables/Travel Time/beat_center_to_addresses_times.parquet'),
 ('Data Outputs/beat_center_to_edge_summary.csv',
  'Data Outputs/Analysis/Tables/Travel Time/beat_center_to_edge_summary.csv'),
 ('Data Outputs/beat_center_to_edge_times.parquet',
  'Data Outputs/Analysis/Tables/Travel Time/beat_center_to_edge_times.parquet'),
 ('Data Outputs/beat_center_vs_closest_facility_map.png',
  'Data Outputs/Graphs/Travel Time and Maps/beat_center_vs_closest_facility_map.png'),
 ('Data Outputs/cad_2026_response_stages_by_beat.csv',
  'Data Outputs/Analysis/Tables/CAD Demand and Response Stages/cad_2026_response_stages_by_beat.csv'),
 ('Data Outputs/cad_2026_response_stages_by_priority.csv',
  'Data Outputs/Analysis/Tables/CAD Demand and Response Stages/cad_2026_response_stages_by_priority.csv'),
 ('Data Outputs/cad_2026_timing_quality.csv',
  'Data Outputs/Analysis/Tables/CAD Demand and Response Stages/cad_2026_timing_quality.csv'),
 ('Data Outputs/cad_demand_by_beat.csv',
  'Data Outputs/Analysis/Tables/CAD Demand and Response Stages/cad_demand_by_beat.csv'),
 ('Data Outputs/cad_demand_by_hour.csv',
  'Data Outputs/Analysis/Tables/CAD Demand and Response Stages/cad_demand_by_hour.csv'),
 ('Data Outputs/daily_call_volume_annual.png', 'Data Outputs/Graphs/Call Volume/daily_call_volume_annual.png'),
 ('Data Outputs/daily_call_volume_by_priority.png',
  'Data Outputs/Graphs/Call Volume/daily_call_volume_by_priority.png'),
 ('Data Outputs/daily_call_volume_combined.png', 'Data Outputs/Graphs/Call Volume/daily_call_volume_combined.png'),
 ('Data Outputs/dispatch_p1_queue_vs_travel_by_hour.png',
  'Data Outputs/Graphs/Dispatcher Story/dispatcher_story_4_p1_queue_vs_travel_by_hour.png'),
 ('Data Outputs/dispatch_queue_by_hour_by_area.png',
  'Data Outputs/Graphs/Dispatcher Story/dispatcher_story_supporting_queue_wait_by_hour_by_area.png'),
 ('Data Outputs/dispatch_staffing_vs_answer_speed.png',
  'Data Outputs/Graphs/Dispatcher Story/dispatcher_story_3_staffing_vs_answer_speed.png'),
 ('Data Outputs/eda_slides/1_weekly_mean_over_time.png',
  'Data Outputs/Graphs/Slides/EDA Slides/eda_1_weekly_mean_calls_over_time.png'),
 ('Data Outputs/eda_slides/2_weekly_extremes_over_time.png',
  'Data Outputs/Graphs/Slides/EDA Slides/eda_2_weekly_extremes_over_time.png'),
 ('Data Outputs/eda_slides/3_variance_by_hour_two_periods.png',
  'Data Outputs/Graphs/Slides/EDA Slides/eda_3_variance_by_hour_two_periods.png'),
 ('Data Outputs/eda_slides/4_seasonality_robustness_overlay.png',
  'Data Outputs/Graphs/Slides/EDA Slides/eda_4_seasonality_robustness_overlay.png'),
 ('Data Outputs/eda_slides/5_trend_component.png', 'Data Outputs/Graphs/Slides/EDA Slides/eda_5_trend_component.png'),
 ('Data Outputs/eda_slides/ci_boxplots.png', 'Data Outputs/Graphs/Slides/EDA Slides/forecast_ci_boxplots.png'),
 ('Data Outputs/eda_slides/ci_fanchart.png', 'Data Outputs/Graphs/Slides/EDA Slides/forecast_ci_fan_chart.png'),
 ('Data Outputs/eda_slides/ci_table.png', 'Data Outputs/Graphs/Slides/EDA Slides/forecast_ci_table_48h.png'),
 ('Data Outputs/eda_slides/ci_table_48.csv', 'Data Outputs/Analysis/Tables/Slide Tables/forecast_ci_table_48h.csv'),
 ('Data Outputs/eda_slides/darkness_effect.png',
  'Data Outputs/Graphs/Slides/EDA Slides/eda_darkness_effect_on_calls.png'),
 ('Data Outputs/eda_slides/darkness_test.csv', 'Data Outputs/Analysis/Tables/Slide Tables/eda_darkness_test.csv'),
 ('Data Outputs/eda_slides/temperature_effect.png',
  'Data Outputs/Graphs/Slides/EDA Slides/eda_temperature_effect_on_calls.png'),
 ('Data Outputs/facility_to_addresses_summary.csv',
  'Data Outputs/Analysis/Tables/Travel Time/facility_to_addresses_summary.csv'),
 ('Data Outputs/facility_to_addresses_times.parquet',
  'Data Outputs/Analysis/Tables/Travel Time/facility_to_addresses_times.parquet'),
 ('Data Outputs/hourly_call_vol_p1.png', 'Data Outputs/Graphs/Call Volume/hourly_call_vol_p1.png'),
 ('Data Outputs/mapbox_vs_cad_sample.parquet',
  'Data Outputs/Analysis/Tables/Travel Time/mapbox_vs_cad_sample.parquet'),
 ('Data Outputs/median_response_time_filtered.png',
  'Data Outputs/Graphs/P1 Response Time/Overview/median_response_time_filtered.png'),
 ('Data Outputs/median_response_time_p1.png',
  'Data Outputs/Graphs/P1 Response Time/Overview/median_response_time_p1.png'),
 ('Data Outputs/oakland_911_forecast.ipynb', 'Data Outputs/Analysis/Notebooks/oakland_911_forecast.ipynb'),
 ('Data Outputs/observed_2026_drive_times_by_beat.png',
  'Data Outputs/Graphs/Travel Time and Maps/observed_2026_drive_times_by_beat.png'),
 ('Data Outputs/observed_2026_drive_times_map.png',
  'Data Outputs/Graphs/Travel Time and Maps/observed_2026_drive_times_map.png'),
 ('Data Outputs/opd_patrol_officers_by_shift_day.csv',
  'Data Outputs/Analysis/Tables/Patrol Staffing/opd_patrol_officers_by_shift_day.csv'),
 ('Data Outputs/opd_patrol_shift_structure.csv',
  'Data Outputs/Analysis/Tables/Patrol Staffing/opd_patrol_shift_structure.csv'),
 ('Data Outputs/opd_patrol_shifts_by_area_2026.png',
  'Data Outputs/Graphs/Patrol Staffing/opd_patrol_shifts_by_area_2026.png'),
 ('Data Outputs/p1_daily_call_volume.png', 'Data Outputs/Graphs/Call Volume/p1_daily_call_volume.png'),
 ('Data Outputs/p1_median_response_time_by_beat.png',
  'Data Outputs/Graphs/P1 Response Time/Overview/p1_median_response_time_by_beat.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_area_2021.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and Year/p1_median_response_time_by_hour_by_area_2021.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_area_2022.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and Year/p1_median_response_time_by_hour_by_area_2022.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_area_2023.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and Year/p1_median_response_time_by_hour_by_area_2023.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_area_2024.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and Year/p1_median_response_time_by_hour_by_area_2024.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_area_2025.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and Year/p1_median_response_time_by_hour_by_area_2025.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_area_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and Year/p1_median_response_time_by_hour_by_area_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area1_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area1_2021_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area1_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area1_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area2_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area2_2021_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area2_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area2_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area3_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area3_2021_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area4_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area4_2021_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area5_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area5_2021_2026.png'),
 ('Data Outputs/p1_median_response_time_by_hour_by_weekday_area6_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/By Area and '
  'Weekday/p1_median_response_time_by_hour_by_weekday_area6_2021_2026.png'),
 ('Data Outputs/p1_median_response_time_filtered.png',
  'Data Outputs/Graphs/P1 Response Time/Overview/p1_median_response_time_filtered.png'),
 ('Data Outputs/p1_response_time_distribution.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution.png'),
 ('Data Outputs/p1_response_time_distribution_1440min_pct.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution_1440min_pct.png'),
 ('Data Outputs/p1_response_time_distribution_24h.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution_24h.png'),
 ('Data Outputs/p1_response_time_distribution_2h.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution_2h.png'),
 ('Data Outputs/p1_response_time_distribution_30min.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution_30min.png'),
 ('Data Outputs/p1_response_time_distribution_30min_pct.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution_30min_pct.png'),
 ('Data Outputs/p1_response_time_distribution_by_hour.png',
  'Data Outputs/Graphs/P1 Response Time/Distributions/p1_response_time_distribution_by_hour.png'),
 ('Data Outputs/p1_response_vs_volume_by_hour_by_weekday_area1_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/Response vs Volume by '
  'Area/p1_response_vs_volume_by_hour_by_weekday_area1_2021_2026.png'),
 ('Data Outputs/p1_response_vs_volume_by_hour_by_weekday_area2_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/Response vs Volume by '
  'Area/p1_response_vs_volume_by_hour_by_weekday_area2_2021_2026.png'),
 ('Data Outputs/p1_response_vs_volume_by_hour_by_weekday_area3_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/Response vs Volume by '
  'Area/p1_response_vs_volume_by_hour_by_weekday_area3_2021_2026.png'),
 ('Data Outputs/p1_response_vs_volume_by_hour_by_weekday_area4_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/Response vs Volume by '
  'Area/p1_response_vs_volume_by_hour_by_weekday_area4_2021_2026.png'),
 ('Data Outputs/p1_response_vs_volume_by_hour_by_weekday_area5_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/Response vs Volume by '
  'Area/p1_response_vs_volume_by_hour_by_weekday_area5_2021_2026.png'),
 ('Data Outputs/p1_response_vs_volume_by_hour_by_weekday_area6_2021_2026.png',
  'Data Outputs/Graphs/P1 Response Time/Response vs Volume by '
  'Area/p1_response_vs_volume_by_hour_by_weekday_area6_2021_2026.png'),
 ('Data Outputs/p1_travel_response_time_filtered.png',
  'Data Outputs/Graphs/P1 Response Time/Overview/p1_travel_response_time_filtered.png'),
 ('Data Outputs/p1_volume_by_beat.png', 'Data Outputs/Graphs/Call Volume/p1_volume_by_beat.png'),
 ('Data Outputs/sched_0_forecast_shape.png',
  'Data Outputs/Graphs/Call-Taker Scheduling/scheduling_1_forecast_daily_call_curve.png'),
 ('Data Outputs/sched_1_required_vs_current.png',
  'Data Outputs/Graphs/Call-Taker Scheduling/scheduling_2_required_vs_current_call_takers.png'),
 ('Data Outputs/sched_2_gap_heatmap.png',
  'Data Outputs/Graphs/Call-Taker Scheduling/scheduling_3_gap_heatmap_by_weekday_hour.png'),
 ('Data Outputs/sched_3_shift_proposal.png',
  'Data Outputs/Graphs/Call-Taker Scheduling/scheduling_4_shift_options_b_and_c.png'),
 ('Data Outputs/sched_4_shift_blocks.png',
  'Data Outputs/Graphs/Call-Taker Scheduling/scheduling_5_option_b_shifts_over_call_curve.png'),
 ('Data Outputs/slides_forecast/1_forecast_calculation_3_thursdays.png',
  'Data Outputs/Graphs/Slides/Forecast Slides/1_forecast_calculation_3_thursdays.png'),
 ('Data Outputs/slides_forecast/2a_distribution_16h.png',
  'Data Outputs/Graphs/Slides/Forecast Slides/2a_distribution_16h.png'),
 ('Data Outputs/slides_forecast/2b_distribution_03h.png',
  'Data Outputs/Graphs/Slides/Forecast Slides/2b_distribution_03h.png'),
 ('Data Outputs/slides_forecast/3_hours_above_P90.png',
  'Data Outputs/Graphs/Slides/Forecast Slides/3_hours_above_P90.png'),
 ('Data Outputs/slides_forecast/4_unused_buffer_P90.png',
  'Data Outputs/Graphs/Slides/Forecast Slides/4_unused_buffer_P90.png'),
 ('Data Outputs/story_1_phone_demand_vs_staffing_2024.png',
  'Data Outputs/Graphs/Dispatcher Story/dispatcher_story_1_phone_demand_vs_staffing_2024.png'),
 ('Data Outputs/story_2_answer_time_by_month_hour_2024.png',
  'Data Outputs/Graphs/Dispatcher Story/dispatcher_story_2_answer_time_by_month_hour_2024.png'),
 ('Data Outputs/story_5_calls_per_officer_by_area_2025.png',
  'Data Outputs/Graphs/Dispatcher Story/dispatcher_story_5_calls_per_officer_by_area_2025.png'),
 ('Data Outputs/v2_hour_of_day_bias.png',
  'Data Outputs/Graphs/Forecast Models/forecast_v2_holidays_hour_of_day_bias.png'),
 ('Data Outputs/v2_long_horizon_eval.png',
  'Data Outputs/Graphs/Forecast Models/forecast_v2_holidays_long_horizon_eval.png'),
 ('Data Outputs/v3_hour_of_day_bias.png',
  'Data Outputs/Graphs/Forecast Models/forecast_v3_trend_hour_of_day_bias.png'),
 ('Data Outputs/v4_hour_of_day_bias.png',
  'Data Outputs/Graphs/Forecast Models/forecast_v4_weather_hour_of_day_bias.png'),
 ('Data Outputs/volume_by_month.png', 'Data Outputs/Graphs/Call Volume/volume_by_month.png'),
 ('Data Outputs/volume_by_priority.png', 'Data Outputs/Graphs/Call Volume/volume_by_priority.png'),
 ('Data Outputs/volume_over_week.png', 'Data Outputs/Graphs/Call Volume/volume_over_week.png')]

WORKSPACE = "OPD & TAN - Core Workspace"
OPD_FOLDER_NAMES = ("OPD - Oakland Police Dept", "02 Oakland Police Dept (OPD)")
_PO, _DI, _DO = "Data Collection (Police Officer)", "Data Collection (Dispatcher)", "Data Outputs"
_OLD_DIRS = (f"{_PO}/Our Data", _DO, "Data/Our Data", "Outputs", f"{_DI}/Our Data")   # older layouts, searched last
_DIR_ALIASES = {"OPD Reports": f"{_PO}/Our Data/Patrol Staffing/Raw"}
_IMAGES = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}
# New output files that are not in the table above are filed by name prefix (so a 2027 chart lands next to the 2026 one):
# (prefix, folder for images, folder for tables/data files), relative to the OPD folder.
_G, _T = f"{_DO}/Graphs", f"{_DO}/Analysis/Tables"
_OUT_RULES = (
    ("p1_median_response_time_by_hour_by_weekday_area", f"{_G}/P1 Response Time/By Area and Weekday", _T),
    ("p1_median_response_time_by_hour_by_area_", f"{_G}/P1 Response Time/By Area and Year", _T),
    ("p1_response_vs_volume_by_hour_by_weekday_area", f"{_G}/P1 Response Time/Response vs Volume by Area", _T),
    ("p1_response_time_distribution", f"{_G}/P1 Response Time/Distributions", _T),
    ("daily_call_volume", f"{_G}/Call Volume", _T),
    ("cad_", _G, f"{_T}/CAD Demand and Response Stages"),
    ("beat_center_to_", f"{_G}/Travel Time and Maps", f"{_T}/Travel Time"),
    ("facility_to_", f"{_G}/Travel Time and Maps", f"{_T}/Travel Time"),
)

def _find_box_root() -> Path:
    env = os.environ.get("BOX_ROOT")
    if env and Path(env).expanduser().is_dir():
        return Path(env).expanduser()
    home = Path.home()
    for c in glob.glob(str(home / "Library/CloudStorage/Box-*")) + [str(home / "Box"), str(home / "Box Sync")]:
        if os.path.isdir(c):
            return Path(c)
    raise FileNotFoundError("Couldn't find the Box Drive folder. Install/sign in to Box Drive or set BOX_ROOT.")


def _find_root() -> Path:
    env = os.environ.get("OPD_ROOT")
    if env and Path(env).expanduser().is_dir():
        return Path(env).expanduser()
    ws = _find_box_root() / WORKSPACE
    for n in OPD_FOLDER_NAMES:
        if (ws / n).is_dir():
            return ws / n
    raise FileNotFoundError(f"No OPD folder found in {ws}. Is the Box folder synced? (looked for {OPD_FOLDER_NAMES})")


ROOT = _find_root()
_BY_NAME = {}
for _old, _new in _MOVES:
    _BY_NAME[os.path.basename(_new)] = (_new, _old)
    _BY_NAME[os.path.basename(_old)] = (_new, _old)


def locate(name, kind="data", create=False) -> Path:
    """Full path for a file by name (old or new). Existing files are found wherever they are.
    A file that does not exist yet (you are about to write it) gets its NEW location; with create=True its folder is created."""
    name = str(name).replace("\\", "/")
    if name in _DIR_ALIASES:
        return ROOT / _DIR_ALIASES[name]
    base = os.path.basename(name)
    hit = _BY_NAME.get(base)
    if hit:
        new, old = hit
        for c in [ROOT / new, ROOT / old] + [ROOT / d / os.path.basename(old) for d in _OLD_DIRS]:
            if c.exists():
                return c
        target = ROOT / new
    else:
        found = [ROOT / d / base for d in _OLD_DIRS if (ROOT / d / base).exists()]
        if found:
            return found[0]
        if kind == "out":
            is_img = Path(base).suffix.lower() in _IMAGES
            rule = next((r for r in _OUT_RULES if base.startswith(r[0])), None)
            folder = (rule[1] if is_img else rule[2]) if rule else (_G if is_img else _T)
            target = ROOT / folder / base
        else:
            target = ROOT / _PO / "Our Data" / base
    if create:
        target.parent.mkdir(parents=True, exist_ok=True)
    return target


class _Folder:
    """`DATA / "file.csv"` and `OUT / "chart.png"` resolve through locate(); everything else behaves like a folder path."""

    def __init__(self, kind, default):
        self.kind, self.default = kind, default

    def __truediv__(self, name):
        return locate(name, self.kind, create=(self.kind == "out"))

    def __fspath__(self):
        return str(ROOT / self.default)

    __str__ = __fspath__

    def mkdir(self, *a, **k):
        pass


DATA = _Folder("data", f"{_PO}/Our Data")
OUT = _Folder("out", f"{_DO}/Graphs")


def check():
    """Print every known file and where it is found."""
    miss = 0
    for name in sorted(_BY_NAME):
        if name.endswith(".gdoc"):
            continue
        p = locate(name, create=False)
        ok = p.exists()
        miss += not ok
        if not ok:
            print("MISSING", name, "->", p)
    print(f"OPD folder: {ROOT}\n{len(_BY_NAME)} known names, {miss} missing")
    return miss == 0


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
