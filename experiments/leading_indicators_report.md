# Leading indicators of primera crop stress — 2026 check + 2001-2025 track record

Lead windows end before silking; outcome is cropland NDVI z, Jul 15-Sep 10. Rank 1 = most stressed of 14 in 2026. `rho_2026` and `r_panel` > 0 mean early stress went with poor later crop condition; `auc_panel` is skill at flagging department-years with outcome z < -1.0 (0.5 = chance).

| metric         | rainfall   | window        | mask   |   rank_La Union |   rank_Morazan |   rank_Santa Ana | field_2026   |   rho_2026 |   r_panel |   auc_panel |   n_panel | years     |
|:---------------|:-----------|:--------------|:-------|----------------:|---------------:|-----------------:|:-------------|-----------:|----------:|------------:|----------:|:----------|
| ndvi           | False      | pre_canicula  | all    |               1 |              2 |                7 | True         |       0.55 |      0.29 |        0.65 |       350 | 2001-2025 |
| ndvi           | False      | pre_canicula  | crop   |               2 |              1 |               11 | True         |       0.63 |      0.19 |        0.6  |       350 | 2001-2025 |
| dry_spell_days | True       | pre_canicula  | all    |               1 |              3 |                5 | True         |       0.63 |      0.06 |        0.51 |       350 | 2001-2025 |
| lst_day_c      | False      | pre_canicula  | crop   |               2 |              1 |               12 | True         |       0.72 |      0.18 |        0.5  |       350 | 2001-2025 |
| ssm_smap       | False      | establishment | crop   |               2 |              1 |                5 | True         |       0.36 |     -0.09 |        0.5  |       154 | 2015-2025 |
| ssm_smap       | False      | establishment | all    |               4 |              2 |                8 | True         |       0.36 |     -0.1  |        0.49 |       154 | 2015-2025 |
| aeti_mm        | False      | pre_canicula  | crop   |               1 |              2 |                7 | True         |       0.2  |     -0.05 |        0.48 |       112 | 2018-2025 |
| lst_day_c      | False      | establishment | all    |               2 |              1 |               14 | True         |       0.65 |     -0.01 |        0.46 |       350 | 2001-2025 |
| lst_day_c      | False      | establishment | crop   |               4 |              1 |               14 | True         |       0.5  |     -0.03 |        0.45 |       350 | 2001-2025 |
| dry_spell_days | True       | establishment | all    |               2 |              3 |               13 | True         |       0.61 |     -0.12 |        0.4  |       350 | 2001-2025 |
| rain_mm        | True       | establishment | all    |               1 |              2 |               13 | True         |       0.59 |     -0.26 |        0.39 |       350 | 2001-2025 |
| rain_mm        | True       | establishment | crop   |               1 |              3 |               14 | True         |       0.67 |     -0.26 |        0.39 |       350 | 2001-2025 |
| dry_spell_days | True       | establishment | crop   |               4 |              1 |               12 | True         |       0.65 |     -0.2  |        0.38 |       350 | 2001-2025 |
| aeti_mm        | False      | establishment | all    |               1 |              4 |               11 | True         |       0.49 |     -0.04 |        0.38 |       112 | 2018-2025 |
| ndvi           | False      | establishment | crop   |               3 |              2 |                9 | True         |       0.33 |     -0.12 |        0.37 |       350 | 2001-2025 |
| aeti_mm        | False      | establishment | crop   |               4 |              2 |               11 | True         |       0.45 |     -0.17 |        0.33 |       112 | 2018-2025 |
| ssm_smap       | False      | pre_canicula  | crop   |              10 |             13 |                2 | False        |      -0.76 |      0.45 |        0.86 |       154 | 2015-2025 |
| ssm_smap       | False      | pre_canicula  | all    |              10 |             12 |                2 | False        |      -0.67 |      0.42 |        0.85 |       154 | 2015-2025 |
| rzsm_smap      | False      | pre_canicula  | crop   |              10 |             13 |                1 | False        |      -0.77 |      0.38 |        0.84 |       154 | 2015-2025 |
| rzsm_smap      | False      | pre_canicula  | all    |              11 |             10 |                1 | False        |      -0.65 |      0.36 |        0.83 |       154 | 2015-2025 |
| rain_mm        | True       | pre_canicula  | all    |              14 |              9 |                1 | False        |      -0.71 |      0.13 |        0.57 |       350 | 2001-2025 |
| rain_mm        | True       | pre_canicula  | crop   |              14 |             11 |                3 | False        |      -0.73 |      0.13 |        0.56 |       350 | 2001-2025 |
| vpd_kpa        | False      | pre_canicula  | all    |              11 |             14 |               12 | False        |      -0.4  |      0.11 |        0.54 |       350 | 2001-2025 |
| lst_day_c      | False      | pre_canicula  | all    |               1 |              6 |               13 | False        |       0.63 |      0.23 |        0.54 |       350 | 2001-2025 |
| vpd_kpa        | False      | pre_canicula  | crop   |               9 |             11 |               12 | False        |      -0.02 |      0.11 |        0.53 |       350 | 2001-2025 |
| dry_spell_days | True       | pre_canicula  | crop   |               1 |              6 |                3 | False        |       0.56 |      0.09 |        0.53 |       350 | 2001-2025 |
| sm_era5        | False      | pre_canicula  | all    |              13 |              7 |                9 | False        |      -0.49 |      0.04 |        0.52 |       350 | 2001-2025 |
| rzsm_smap      | False      | establishment | crop   |               3 |              5 |                4 | False        |      -0.16 |     -0.07 |        0.5  |       154 | 2015-2025 |
| sm_era5        | False      | pre_canicula  | crop   |              12 |             11 |                9 | False        |      -0.31 |      0.02 |        0.5  |       350 | 2001-2025 |
| rzsm_smap      | False      | establishment | all    |               5 |              4 |                3 | False        |       0.08 |     -0.08 |        0.5  |       154 | 2015-2025 |
| vpd_kpa        | False      | establishment | crop   |              13 |             11 |                2 | False        |      -0.51 |     -0.19 |        0.43 |       350 | 2001-2025 |
| vpd_kpa        | False      | establishment | all    |              13 |              8 |                2 | False        |      -0.26 |     -0.17 |        0.43 |       350 | 2001-2025 |
| ndvi           | False      | establishment | all    |               2 |              7 |                8 | False        |       0.48 |     -0.09 |        0.4  |       350 | 2001-2025 |
| aeti_mm        | False      | pre_canicula  | all    |               1 |              9 |                3 | False        |       0.09 |     -0.07 |        0.38 |       112 | 2018-2025 |
| sm_era5        | False      | establishment | all    |              11 |              4 |               12 | False        |      -0.2  |     -0.34 |        0.33 |       350 | 2001-2025 |
| sm_era5        | False      | establishment | crop   |              10 |              7 |                8 | False        |      -0.26 |     -0.34 |        0.33 |       350 | 2001-2025 |
