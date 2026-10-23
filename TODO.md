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

- [ ] **Handle the postrera season.** Today the "This season" table, the
      calibrated alert (silking window Jul 15–Aug 15) and the Confirmed rule
      (Jul–Aug) all cover primera only. 2023's eastern losses came in August and
      postrera, after every primera window, and the country was in exceptional
      drought in Oct 2026 (SPI-3 −2.96) with nothing in the alert to say so.
      Needs: postrera dates in `config.CC["season"]` (one season becomes a
      list), a postrera alert window and thresholds calibrated in
      `experiments/trigger_calibration.py`, and a postrera Confirmed window.
      Damage labels to calibrate against: 2018 (FAO: postrera impact), 2023
      (CAMPO: 75% of losses in the east, whole 2023-24 cycle), 2026 (CAMPO:
      east ~30–40% down, mostly postrera).

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
