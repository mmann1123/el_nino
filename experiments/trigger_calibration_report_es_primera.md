# Trigger Calibration Report — El Salvador, Primera

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** El Salvador (ES).
**Region:** all 14 departamentos; a year fires if any one of them meets the conditions.
**Season:** Primera. **Windows swept:** DOY 196-227, DOY 204-218, DOY 196-273.
**Labels:** the season's `labeled_events` in `config.CC['seasons']`, traced to highlighted sources in `experiments/evidence/`.

**Severe positive(s):** 1997 (El Niño dry weather; ~125 000 t white maize lost (GIEWS Dec 1997)), 2015 (El Niño drought; 64% of maize and 82% of bean area lost (FEWS NET Aug 2015)).
**Moderate positives:** 2000, 2001, 2009, 2012, 2013, 2014, 2018, 2023, 2026.
**Documented normal seasons:** 1998, 1999, 2002, 2003, 2004, 2011, 2016, 2017, 2019, 2021, 2022, 2025.
**Excluded (non-drought losses, e.g. hurricanes):** 2010, 2020, 2024.
**Negatives:** the documented normal seasons only; unlabeled years are not scored.
**Geo hits:** positive years where the alert fired in at least one department the evidence names, out of positive years that name any. Unnamed departments are not counted against the alert.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |
|---|---:|---:|---:|---:|---|---|---|---|---:|
| SPI-3<-0.8 in DOY 196-227 | 8 | 6 | 3 | 6 | 0.57 [0.33–0.79] | 0.73 [0.43–0.90] | 0.50 [0.09–0.91] | 5.00 [1.83–10.88] | 1/3 |
| SPI-3<-0.8 in DOY 204-218 | 7 | 6 | 4 | 6 | 0.54 [0.29–0.77] | 0.64 [0.35–0.85] | 0.50 [0.09–0.91] | 5.00 [1.83–10.88] | 0/3 |
| SPI-3<-0.8 in DOY 196-273 | 10 | 7 | 1 | 5 | 0.59 [0.36–0.78] | 0.91 [0.62–0.98] | 1.00 [0.34–1.00] | 5.83 [2.35–12.02] | 2/3 |
| SPI-3<-1.0 in DOY 196-227 | 7 | 3 | 4 | 9 | 0.70 [0.40–0.89] | 0.64 [0.35–0.85] | 0.50 [0.09–0.91] | 2.50 [0.52–7.31] | 0/3 |
| SPI-3<-1.0 in DOY 204-218 | 5 | 3 | 6 | 9 | 0.62 [0.31–0.86] | 0.45 [0.21–0.72] | 0.50 [0.09–0.91] | 2.50 [0.52–7.31] | 0/3 |
| SPI-3<-1.0 in DOY 196-273 | 9 | 3 | 2 | 9 | 0.75 [0.47–0.91] | 0.82 [0.52–0.95] | 1.00 [0.34–1.00] | 2.50 [0.52–7.31] | 1/3 |
| SPI-3<-1.3 in DOY 196-227 | 5 | 2 | 6 | 10 | 0.71 [0.36–0.92] | 0.45 [0.21–0.72] | 0.50 [0.09–0.91] | 1.67 [0.20–6.02] | 0/3 |
| SPI-3<-1.3 in DOY 204-218 | 4 | 1 | 7 | 11 | 0.80 [0.38–0.96] | 0.36 [0.15–0.65] | 0.50 [0.09–0.91] | 0.83 [0.02–4.64] | 0/3 |
| SPI-3<-1.3 in DOY 196-273 | 6 | 3 | 5 | 9 | 0.67 [0.35–0.88] | 0.55 [0.28–0.79] | 0.50 [0.09–0.91] | 2.50 [0.52–7.31] | 0/3 |
| SPI-3<-1.5 in DOY 196-227 | 5 | 1 | 6 | 11 | 0.83 [0.44–0.97] | 0.45 [0.21–0.72] | 0.50 [0.09–0.91] | 0.83 [0.02–4.64] | 0/3 |
| SPI-3<-1.5 in DOY 204-218 | 3 | 1 | 8 | 11 | 0.75 [0.30–0.95] | 0.27 [0.10–0.57] | 0.50 [0.09–0.91] | 0.83 [0.02–4.64] | 0/3 |
| SPI-3<-1.5 in DOY 196-273 | 5 | 2 | 6 | 10 | 0.71 [0.36–0.92] | 0.45 [0.21–0.72] | 0.50 [0.09–0.91] | 1.67 [0.20–6.02] | 0/3 |
| SPI-3<-1.7 in DOY 196-227 | 4 | 0 | 7 | 12 | 1.00 [0.51–1.00] | 0.36 [0.15–0.65] | 0.50 [0.09–0.91] | 0.00 [0.00–3.07] | 0/3 |
| SPI-3<-1.7 in DOY 204-218 | 3 | 0 | 8 | 12 | 1.00 [0.44–1.00] | 0.27 [0.10–0.57] | 0.50 [0.09–0.91] | 0.00 [0.00–3.07] | 0/3 |
| SPI-3<-1.7 in DOY 196-273 | 5 | 1 | 6 | 11 | 0.83 [0.44–0.97] | 0.45 [0.21–0.72] | 0.50 [0.09–0.91] | 0.83 [0.02–4.64] | 0/3 |

## Combined SPI ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |
|---|---:|---:|---:|---:|---|---|---|---|---:|
| SPI-3<-1.0 ∧ RZSM<-0.5σ | 4 | 3 | 0 | 3 | 0.57 [0.25–0.84] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 5.00 [1.03–14.61] | 0/0 |
| SPI-3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 3 | 2 | 1 | 4 | 0.60 [0.23–0.88] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 3.33 [0.40–12.04] | 0/0 |
| SPI-3<-1.0 ∧ RZSM<-1.0σ | 4 | 2 | 0 | 4 | 0.67 [0.30–0.90] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 3.33 [0.40–12.04] | 0/0 |
| SPI-3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 3 | 1 | 1 | 5 | 0.75 [0.30–0.95] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.0 ∧ RZSM<-1.5σ | 4 | 1 | 0 | 5 | 0.80 [0.38–0.96] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 3 | 1 | 1 | 5 | 0.75 [0.30–0.95] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.3 ∧ RZSM<-0.5σ | 4 | 1 | 0 | 5 | 0.80 [0.38–0.96] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 3 | 1 | 1 | 5 | 0.75 [0.30–0.95] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.3 ∧ RZSM<-1.0σ | 4 | 0 | 0 | 6 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 3 | 0 | 1 | 6 | 1.00 [0.44–1.00] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.3 ∧ RZSM<-1.5σ | 4 | 0 | 0 | 6 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 3 | 0 | 1 | 6 | 1.00 [0.44–1.00] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.5 ∧ RZSM<-0.5σ | 4 | 1 | 0 | 5 | 0.80 [0.38–0.96] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 2 | 5 | 0.67 [0.21–0.94] | 0.50 [0.15–0.85] | 0.00 [0.00–0.79] | 1.67 [0.04–9.29] | 0/0 |
| SPI-3<-1.5 ∧ RZSM<-1.0σ | 4 | 0 | 0 | 6 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 0 | 2 | 6 | 1.00 [0.34–1.00] | 0.50 [0.15–0.85] | 0.00 [0.00–0.79] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.5 ∧ RZSM<-1.5σ | 4 | 0 | 0 | 6 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–6.15] | 0/0 |
| SPI-3<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 2 | 6 | 1.00 [0.34–1.00] | 0.50 [0.15–0.85] | 0.00 [0.00–0.79] | 0.00 [0.00–6.15] | 0/0 |

## Per-year detail (best SPI-only configuration)

**Recommended SPI-only trigger:** `SPI-3<-1.0 in DOY 196-273`
- Precision: 0.75 [0.47–0.91] | Recall: 0.82 [0.52–0.95] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 2.50 [0.52–7.31]

| Year | Label | Worst dep | Min SPI | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1997 | severe-moderate | Chalatenango | -1.15 | 1/14 | ✓ | El Niño dry weather; ~125 000 t white maize lost (GIEWS Dec 1997) |
| 1998 | normal | Chalatenango | -0.79 | 0/14 | — | Significant recovery; Mitch struck after harvest (GIEWS Sep 1998) |
| 1999 | normal | San Salvador | -0.05 | 0/14 | — | Normal to heavy rains benefited first-season crops (GIEWS Sep 1999) |
| 2000 | moderate | La Union | -1.38 | 4/14 | ✓ | Long July canícula severely hit crops in the west, Chalatenango and east (GIEWS Oct 2000) |
| 2001 | moderate | La Union | -1.16 | 1/14 | ✓ | First-season output 18% below average from drought (GIEWS Nov 2001) |
| 2002 | normal | Chalatenango | -0.98 | 0/14 | — | Normal late-July/August rain; isolated damage in San Vicente, La Paz (GIEWS Sep 2002) |
| 2003 | normal | Chalatenango | -0.25 | 0/14 | — | Good first-season maize output (GIEWS Oct 2003) |
| 2004 | normal | La Union | -0.90 | 0/14 | — | Above-average prospects despite August dry-spell losses in the east (GIEWS Oct 2004) |
| 2009 | moderate | La Union | -1.26 | 1/14 | ✓ | MAG: 10% losses east, 25% west, 13.7% national; GIEWS later called the harvest good (GIEWS Sep 2009, CPC Oct 2009) |
| 2011 | normal | Sonsonate | 0.33 | 0/14 | — | Early-sown maize losses, then re-sowing and a good main harvest (GIEWS Feb 2012) |
| 2012 | moderate | La Union | -0.57 | 0/14 | — | National harvest above average, but the East at 70% of average (FEWS NET Oct 2012) |
| 2013 | moderate | La Union | -0.99 | 0/14 | — | July canícula; San Miguel, Usulután, La Unión; main maize −4% (GIEWS Oct 2013) |
| 2014 | moderate | La Union | -1.75 | 7/14 | ✓ | Maize losses 14%; eastern and western regions (FEWS NET Aug 2014) |
| 2015 | severe | Cabanas | -2.74 | 14/14 | ✓ | El Niño drought; 64% of maize and 82% of bean area lost (FEWS NET Aug 2015) |
| 2016 | normal | San Salvador | -1.41 | 13/14 | ✓ | Good primera outcome (GIEWS Dec 2016) |
| 2017 | normal | Cabanas | -1.00 | 0/14 | — | Good rain even in the Dry Corridor (GIEWS Jun 2017) |
| 2018 | moderate | San Vicente | -2.43 | 14/14 | ✓ | June–August dry spells, 45 000 t maize lost, 10 departments (GIEWS Nov 2018) |
| 2019 | normal | La Union | -1.76 | 14/14 | ✓ | Near-average maize; eastern deficits offset (GIEWS Oct 2019) |
| 2021 | normal | San Salvador | -1.60 | 7/14 | ✓ | Well above-average production (GIEWS Oct 2021) |
| 2022 | normal | Cabanas | -0.84 | 0/14 | — | Main maize conditions generally favourable (GIEWS Aug 2022) |
| 2023 | moderate | Ahuachapan | -1.86 | 14/14 | ✓ | Prolonged primera dry spells, below-average cereal output (GIEWS Apr 2024) |
| 2025 | normal | Chalatenango | -0.67 | 0/14 | — | Adequate June–July rain; near-average output (GIEWS Jan 2026) |
| 2026 | moderate | Santa Ana | -4.66 | 14/14 | ✓ | Severe El Niño drought, prolonged August canícula; eastern Dry Corridor worst (GIEWS Oct 2026) |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI-3<-1.3 ∧ RZSM<-1.0σ`** in DOY 196-227
- Precision: 1.00 [0.51–1.00] | Recall: 1.00 [0.51–1.00] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.00 [0.00–6.15]

| Year | Label | Worst dep | SPI min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | severe | Cabanas | -2.74 | -2.94 | — | 14/14 | ✓ |
| 2016 | normal | San Salvador | -1.29 | -1.10 | — | 0/14 | — |
| 2017 | normal | Cabanas | -0.92 | -0.46 | — | 0/14 | — |
| 2018 | moderate | Cabanas | -1.51 | -2.94 | — | 10/14 | ✓ |
| 2019 | normal | San Salvador | -1.36 | -1.53 | — | 0/14 | — |
| 2021 | normal | San Salvador | -1.60 | -0.73 | — | 0/14 | — |
| 2022 | normal | Cabanas | -0.84 | -0.34 | — | 0/14 | — |
| 2023 | moderate | Ahuachapan | -1.86 | -2.94 | — | 7/14 | ✓ |
| 2025 | normal | Chalatenango | -0.67 | -0.94 | — | 0/14 | — |
| 2026 | moderate | Ahuachapan | -3.70 | -4.75 | — | 14/14 | ✓ |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (fires whenever SPI falls below threshold inside the window).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.