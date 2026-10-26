# Trigger Calibration Report — El Salvador, Postrera

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** El Salvador (ES).
**Region:** all 14 departamentos; a year fires if any one of them meets the conditions.
**Season:** Postrera. **Windows swept:** DOY 245-275, DOY 253-267, DOY 245-321.
**Labels:** the season's `labeled_events` in `config.CC['seasons']`, traced to highlighted sources in `experiments/evidence/`.

**Moderate positives:** 2023, 2025.
**Documented normal seasons:** 1997, 2001, 2002, 2003, 2012, 2013, 2014, 2015, 2016, 2017, 2021.
**Excluded (non-drought losses, e.g. hurricanes):** 2000, 2009, 2010, 2011, 2018, 2019, 2020, 2022, 2024.
**Negatives:** the documented normal seasons only; unlabeled years are not scored.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |
|---|---:|---:|---:|---:|---|---|---|---|---:|
| SPI-3<-0.8 in DOY 245-275 | 1 | 6 | 1 | 5 | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | — — | 5.45 [2.00–11.87] | — |
| SPI-3<-0.8 in DOY 253-267 | 1 | 4 | 1 | 7 | 0.20 [0.04–0.62] | 0.50 [0.09–0.91] | — — | 3.64 [0.99–9.31] | — |
| SPI-3<-0.8 in DOY 245-321 | 1 | 8 | 1 | 3 | 0.11 [0.02–0.43] | 0.50 [0.09–0.91] | — — | 7.27 [3.14–14.33] | — |
| SPI-3<-1.0 in DOY 245-275 | 1 | 3 | 1 | 8 | 0.25 [0.05–0.70] | 0.50 [0.09–0.91] | — — | 2.73 [0.56–7.97] | — |
| SPI-3<-1.0 in DOY 253-267 | 1 | 2 | 1 | 9 | 0.33 [0.06–0.79] | 0.50 [0.09–0.91] | — — | 1.82 [0.22–6.57] | — |
| SPI-3<-1.0 in DOY 245-321 | 1 | 6 | 1 | 5 | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | — — | 5.45 [2.00–11.87] | — |
| SPI-3<-1.3 in DOY 245-275 | 0 | 2 | 2 | 9 | 0.00 [0.00–0.66] | 0.00 [0.00–0.66] | — — | 1.82 [0.22–6.57] | — |
| SPI-3<-1.3 in DOY 253-267 | 0 | 1 | 2 | 10 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 0.91 [0.02–5.07] | — |
| SPI-3<-1.3 in DOY 245-321 | 1 | 4 | 1 | 7 | 0.20 [0.04–0.62] | 0.50 [0.09–0.91] | — — | 3.64 [0.99–9.31] | — |
| SPI-3<-1.5 in DOY 245-275 | 0 | 2 | 2 | 9 | 0.00 [0.00–0.66] | 0.00 [0.00–0.66] | — — | 1.82 [0.22–6.57] | — |
| SPI-3<-1.5 in DOY 253-267 | 0 | 1 | 2 | 10 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 0.91 [0.02–5.07] | — |
| SPI-3<-1.5 in DOY 245-321 | 0 | 4 | 2 | 7 | 0.00 [0.00–0.49] | 0.00 [0.00–0.66] | — — | 3.64 [0.99–9.31] | — |
| SPI-3<-1.7 in DOY 245-275 | 0 | 1 | 2 | 10 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 0.91 [0.02–5.07] | — |
| SPI-3<-1.7 in DOY 253-267 | 0 | 1 | 2 | 10 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 0.91 [0.02–5.07] | — |
| SPI-3<-1.7 in DOY 245-321 | 0 | 4 | 2 | 7 | 0.00 [0.00–0.49] | 0.00 [0.00–0.66] | — — | 3.64 [0.99–9.31] | — |
| SPI-1<-0.8 in DOY 245-275 | 2 | 7 | 0 | 4 | 0.22 [0.06–0.55] | 1.00 [0.34–1.00] | — — | 6.36 [2.56–13.11] | — |
| SPI-1<-0.8 in DOY 253-267 | 1 | 6 | 1 | 5 | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | — — | 5.45 [2.00–11.87] | — |
| SPI-1<-0.8 in DOY 245-321 | 2 | 9 | 0 | 2 | 0.18 [0.05–0.48] | 1.00 [0.34–1.00] | — — | 8.18 [3.74–15.53] | — |
| SPI-1<-1.0 in DOY 245-275 | 2 | 7 | 0 | 4 | 0.22 [0.06–0.55] | 1.00 [0.34–1.00] | — — | 6.36 [2.56–13.11] | — |
| SPI-1<-1.0 in DOY 253-267 | 1 | 6 | 1 | 5 | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | — — | 5.45 [2.00–11.87] | — |
| SPI-1<-1.0 in DOY 245-321 | 2 | 8 | 0 | 3 | 0.20 [0.06–0.51] | 1.00 [0.34–1.00] | — — | 7.27 [3.14–14.33] | — |
| SPI-1<-1.3 in DOY 245-275 | 2 | 7 | 0 | 4 | 0.22 [0.06–0.55] | 1.00 [0.34–1.00] | — — | 6.36 [2.56–13.11] | — |
| SPI-1<-1.3 in DOY 253-267 | 1 | 3 | 1 | 8 | 0.25 [0.05–0.70] | 0.50 [0.09–0.91] | — — | 2.73 [0.56–7.97] | — |
| SPI-1<-1.3 in DOY 245-321 | 2 | 7 | 0 | 4 | 0.22 [0.06–0.55] | 1.00 [0.34–1.00] | — — | 6.36 [2.56–13.11] | — |
| SPI-1<-1.5 in DOY 245-275 | 2 | 5 | 0 | 6 | 0.29 [0.08–0.64] | 1.00 [0.34–1.00] | — — | 4.55 [1.48–10.61] | — |
| SPI-1<-1.5 in DOY 253-267 | 1 | 2 | 1 | 9 | 0.33 [0.06–0.79] | 0.50 [0.09–0.91] | — — | 1.82 [0.22–6.57] | — |
| SPI-1<-1.5 in DOY 245-321 | 2 | 5 | 0 | 6 | 0.29 [0.08–0.64] | 1.00 [0.34–1.00] | — — | 4.55 [1.48–10.61] | — |
| SPI-1<-1.7 in DOY 245-275 | 1 | 4 | 1 | 7 | 0.20 [0.04–0.62] | 0.50 [0.09–0.91] | — — | 3.64 [0.99–9.31] | — |
| SPI-1<-1.7 in DOY 253-267 | 1 | 1 | 1 | 10 | 0.50 [0.09–0.91] | 0.50 [0.09–0.91] | — — | 0.91 [0.02–5.07] | — |
| SPI-1<-1.7 in DOY 245-321 | 1 | 5 | 1 | 6 | 0.17 [0.03–0.56] | 0.50 [0.09–0.91] | — — | 4.55 [1.48–10.61] | — |

## Combined SPI ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |
|---|---:|---:|---:|---:|---|---|---|---|---:|
| SPI-3<-1.0 ∧ RZSM<-0.5σ | 1 | 2 | 1 | 2 | 0.33 [0.06–0.79] | 0.50 [0.09–0.91] | — — | 5.00 [0.61–18.06] | — |
| SPI-3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 0 | 1 | 4 | 1.00 [0.21–1.00] | 0.50 [0.09–0.91] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.0 ∧ RZSM<-1.0σ | 1 | 2 | 1 | 2 | 0.33 [0.06–0.79] | 0.50 [0.09–0.91] | — — | 5.00 [0.61–18.06] | — |
| SPI-3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 0 | 1 | 4 | 1.00 [0.21–1.00] | 0.50 [0.09–0.91] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.0 ∧ RZSM<-1.5σ | 1 | 1 | 1 | 3 | 0.50 [0.09–0.91] | 0.50 [0.09–0.91] | — — | 2.50 [0.06–13.93] | — |
| SPI-3<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 1 | 0 | 1 | 4 | 1.00 [0.21–1.00] | 0.50 [0.09–0.91] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.3 ∧ RZSM<-0.5σ | 0 | 2 | 2 | 2 | 0.00 [0.00–0.66] | 0.00 [0.00–0.66] | — — | 5.00 [0.61–18.06] | — |
| SPI-3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 0 | 0 | 2 | 4 | — — | 0.00 [0.00–0.66] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.3 ∧ RZSM<-1.0σ | 0 | 2 | 2 | 2 | 0.00 [0.00–0.66] | 0.00 [0.00–0.66] | — — | 5.00 [0.61–18.06] | — |
| SPI-3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 0 | 0 | 2 | 4 | — — | 0.00 [0.00–0.66] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.3 ∧ RZSM<-1.5σ | 0 | 1 | 2 | 3 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 2.50 [0.06–13.93] | — |
| SPI-3<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 0 | 0 | 2 | 4 | — — | 0.00 [0.00–0.66] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.5 ∧ RZSM<-0.5σ | 0 | 1 | 2 | 3 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 2.50 [0.06–13.93] | — |
| SPI-3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 0 | 0 | 2 | 4 | — — | 0.00 [0.00–0.66] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.5 ∧ RZSM<-1.0σ | 0 | 1 | 2 | 3 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 2.50 [0.06–13.93] | — |
| SPI-3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 0 | 0 | 2 | 4 | — — | 0.00 [0.00–0.66] | — — | 0.00 [0.00–9.22] | — |
| SPI-3<-1.5 ∧ RZSM<-1.5σ | 0 | 1 | 2 | 3 | 0.00 [0.00–0.79] | 0.00 [0.00–0.66] | — — | 2.50 [0.06–13.93] | — |
| SPI-3<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 0 | 0 | 2 | 4 | — — | 0.00 [0.00–0.66] | — — | 0.00 [0.00–9.22] | — |
| SPI-1<-1.0 ∧ RZSM<-0.5σ | 2 | 4 | 0 | 0 | 0.33 [0.10–0.70] | 1.00 [0.34–1.00] | — — | 10.00 [2.72–25.60] | — |
| SPI-1<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.0 ∧ RZSM<-1.0σ | 2 | 3 | 0 | 1 | 0.40 [0.12–0.77] | 1.00 [0.34–1.00] | — — | 7.50 [1.55–21.92] | — |
| SPI-1<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.0 ∧ RZSM<-1.5σ | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 0 | 4 | 1.00 [0.34–1.00] | 1.00 [0.34–1.00] | — — | 0.00 [0.00–9.22] | — |
| SPI-1<-1.3 ∧ RZSM<-0.5σ | 2 | 3 | 0 | 1 | 0.40 [0.12–0.77] | 1.00 [0.34–1.00] | — — | 7.50 [1.55–21.92] | — |
| SPI-1<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.3 ∧ RZSM<-1.0σ | 2 | 2 | 0 | 2 | 0.50 [0.15–0.85] | 1.00 [0.34–1.00] | — — | 5.00 [0.61–18.06] | — |
| SPI-1<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.3 ∧ RZSM<-1.5σ | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 0 | 4 | 1.00 [0.34–1.00] | 1.00 [0.34–1.00] | — — | 0.00 [0.00–9.22] | — |
| SPI-1<-1.5 ∧ RZSM<-0.5σ | 2 | 2 | 0 | 2 | 0.50 [0.15–0.85] | 1.00 [0.34–1.00] | — — | 5.00 [0.61–18.06] | — |
| SPI-1<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.5 ∧ RZSM<-1.0σ | 2 | 2 | 0 | 2 | 0.50 [0.15–0.85] | 1.00 [0.34–1.00] | — — | 5.00 [0.61–18.06] | — |
| SPI-1<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.5 ∧ RZSM<-1.5σ | 2 | 1 | 0 | 3 | 0.67 [0.21–0.94] | 1.00 [0.34–1.00] | — — | 2.50 [0.06–13.93] | — |
| SPI-1<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 0 | 4 | 1.00 [0.34–1.00] | 1.00 [0.34–1.00] | — — | 0.00 [0.00–9.22] | — |

## Per-year detail (best SPI-only configuration)

**Recommended SPI-only trigger:** `SPI-1<-1.5 in DOY 245-275`
- Precision: 0.29 [0.08–0.64] | Recall: 1.00 [0.34–1.00] | Severe recall: — — | FP/decade: 4.55 [1.48–10.61]

| Year | Label | Worst dep | Min SPI | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1997 | normal | Chalatenango | -1.61 | 1/14 | ✓ | October rain irregular, no relevant effect on second season (GIEWS Dec 1997) |
| 2001 | normal | La Paz | -1.91 | 12/14 | ✓ | Satisfactory second-season outturns (GIEWS Feb 2002) |
| 2002 | normal | Chalatenango | -0.69 | 0/14 | — | Satisfactory growing conditions (GIEWS Oct 2002) |
| 2003 | normal | La Union | -0.38 | 0/14 | — | Second-season harvest completed, normal (GIEWS Feb 2004) |
| 2012 | normal | La Union | -1.79 | 1/14 | ✓ | Average rain, normal cessation (FEWS NET Nov 2012) |
| 2013 | normal | Santa Ana | -0.25 | 0/14 | — | All three seasons favoured (GIEWS Mar 2014) |
| 2014 | normal | Sonsonate | -0.12 | 0/14 | — | Forecast early end of rains did not materialize (FEWS NET Nov 2014) |
| 2015 | normal | San Vicente | -1.98 | 9/14 | ✓ | Good rain from late September (FEWS NET Dec 2015) |
| 2016 | normal | Sonsonate | -1.33 | 0/14 | — | Good weather, favourable prospects (GIEWS Dec 2016) |
| 2017 | normal | Ahuachapan | -1.40 | 0/14 | — | Best Dry Corridor harvests in years (FEWS NET Dec 2017) |
| 2021 | normal | San Salvador | -2.29 | 14/14 | ✓ | Near-average postrera yields (FEWS NET Feb 2022) |
| 2023 | moderate | La Union | -2.07 | 11/14 | ✓ | September rain 40–70% below average in the east; postrera yields cut in the Dry Corridor (FEWS NET Oct 2023, Jan 2024) |
| 2025 | moderate | Chalatenango | -1.53 | 1/14 | ✓ | Erratic rain, dry spells and heat; localized red bean losses in the Dry Corridor (FEWS NET Dec 2025, Jan 2026) |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI-1<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0`** in DOY 245-275
- Precision: 1.00 [0.34–1.00] | Recall: 1.00 [0.34–1.00] | Severe recall: — — | FP/decade: 0.00 [0.00–9.22]

| Year | Label | Worst dep | SPI min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | normal | San Vicente | -1.98 | -1.90 | — | 0/14 | — |
| 2016 | normal | Sonsonate | -1.33 | -1.09 | — | 0/14 | — |
| 2017 | normal | Ahuachapan | -1.40 | -0.90 | — | 0/14 | — |
| 2021 | normal | San Salvador | -2.29 | -1.05 | -0.35 | 0/14 | — |
| 2023 | moderate | La Union | -2.07 | -2.30 | -0.52 | 11/14 | ✓ |
| 2025 | moderate | Chalatenango | -1.53 | -2.42 | -1.10 | 1/14 | ✓ |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (fires whenever SPI falls below threshold inside the window).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.