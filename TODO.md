# TODO

## Before the `season-watch` changes go live

- [ ] **Re-backfill WAPOR as cropland-weighted, then `finalize`**, for both
      countries. `WAPOR.crop_weighted = True` changes the whole series; until
      the history is re-pulled, new dekads are compared against a
      whole-department baseline, and the "Confirmed" tier (calibrated on
      cropland ETa) is not meaningful.
      `python -m el_nino.etl.run_etl backfill --indicator wapor --start 2018-01-01`
      then `python -m el_nino.etl.run_etl finalize` (as the Cloud Run job, against
      the country's bucket).

## Postrera

- [ ] **Validate the provisional ES postrera alert** (`postrera_drought_v1` in
      `etl/triggers.py`: SPI-1 < −1.0 AND SMAP root-zone < −1.5σ, Sep 2–Oct 2).
      It is calibrated on only two documented postrera droughts (2023, 2025),
      with the thresholds picked on those same years, and false-alarms in 2015.
      In 2026 it fired in all 14 departments on Sep 2 (window start), before
      any harvest report. To validate:
      1. When FEWS NET / GIEWS publish the 2026/27 postrera outcome (Dec–Feb),
         add the evidence to `experiments/evidence/labels.csv`, rebuild with
         `python -m el_nino.experiments.build_evidence`, and label 2026 in the
         postrera `labeled_events`.
      2. Re-run `python -m el_nino.experiments.trigger_calibration --season postrera`
         against the deployed data (copy the bucket's `raw/` locally and set
         `STORAGE_ROOT`).
      3. If 2026 was a documented drought and the rule still holds, drop
         `provisional=True` (removes the dashboard caveat) and update its
         stats; otherwise recalibrate or remove the trigger.
      Also check whether the early-window fire is just primera soil carrying
      over (try a later window start), and why WaPOR z-scores look clipped
      (identical −2.27 in 2018/2020/2022; −4.75 matching SMAP in 2026) before
      adding an ETa condition.

## Haiti automne

- [ ] **Fill the evidence gaps behind the provisional HT automne alert**
      (`automne_drought_v1`: SPI-1 < −1.3, rainfall only, Sep 15–Nov 1). It
      catches 5 of 6 documented autumn droughts with 1 false alarm in 4
      documented normal years, but fires in 29 of 45 years since 1981, and
      most of those years have no autumn evidence either way. Since 2009 it
      fired in 2014 and 2020, which have no autumn evidence, and in 2012
      (Tropical Storm Sandy).
      1. Search FEWS NET / GIEWS / CNSA / WFP for Haiti autumn outcomes in
         2014 and 2020, and confirm the hurricane years 2012 (Sandy), 2016
         (Matthew), 2017 (Irma) and 2025 (Melissa) so they can be labeled
         `excluded`. Extend back before 2009 where reports exist.
      2. Add verbatim quotes to `experiments/evidence/labels.csv`, rebuild
         with `python -m el_nino.experiments.build_evidence`, and update the
         automne `labeled_events`.
      3. Re-run `COUNTRY=haiti python -m el_nino.experiments.trigger_calibration
         --season automne` on the deployed data. Tighter variants already
         tested (deeper SPI-1, SPI-3, ≥2–3 departments) bring the all-years
         fire rate to ~30% but lose a documented drought; revisit once more
         years are labeled, and drop `provisional=True` if the rule holds.

## Early "Watch" tier (not shipped)

- [ ] **Find an early warning that clears an absolute threshold.** The
      cropland blend of NDVI + daytime LST + SMAP surface soil moisture ranks
      the right departments within a year (2015 vs MAG survey: Spearman 0.85;
      2018 and 2026 east ranked top), but on the dashboard's own anomaly scale
      it did not cross a usable threshold:
      - Apr 20–Jun 15 mean, z ≤ −0.6: fires 2015 (6 depts, matching MAG's
        worst six), 2016 (3), 2023 (4); misses 2018 and 2026.
      - Jun 15–Jul 10 mean, z ≤ −0.5: 2026 La Union + Morazan and 2018
        Usulutan, La Paz, San Vicente — but also 7 depts in 2016 and in 2019.
      Ideas: a within-year rank tier ("most stressed this season") shown as
      context rather than an alert; check 2016/2019 against MAG data before
      calling them false alarms. Analysis: `experiments/leading_indicators.py`,
      `experiments/leading_indicators_report.md`.

## Calibration data

- [ ] Ask MAG (DGEA) for maize area lost / yield by department and year. The
      2015 damage survey (CAC presentation, MAG/DGEA/DEA, Jun/Jul 2015) is the
      only official department-level table found; 2018 and 2023 rely on CAMPO
      estimates.
- [ ] Add the 2015/2018/2023/2026 department-level damage to
      `config.CC["labeled_events"]` once there is a format for per-department
      labels (today it is per year).
