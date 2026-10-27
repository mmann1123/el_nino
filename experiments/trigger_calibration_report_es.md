# Trigger Calibration Report — El Salvador

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** El Salvador (ES).
**Region:** all 14 departamentos; a year fires if any one of them meets the conditions.
**Silking window:** DOY 196-227.
**Labels:** drawn from `el_nino/el_nino_agricultural_risks.md` via `config.CC['labeled_events']`.

**Severe positive(s):** 1997 (Super El Niño; FAO 'considerably below-average' 2nd-season maize), 2015 (Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor).
**Moderate positives:** 2002, 2009, 2014, 2018, 2023, 2026.
**Negatives:** all other years with available data.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI-3 only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-0.8 in DOY 196-227 | 6 | 14 | 2 | 24 | 0.30 [0.15–0.52] | 0.75 [0.41–0.93] | 0.50 [0.09–0.91] | 3.04 [2.01–6.18] |
| SPI3<-0.8 in DOY 204-218 | 6 | 13 | 2 | 25 | 0.32 [0.15–0.54] | 0.75 [0.41–0.93] | 0.50 [0.09–0.91] | 2.83 [1.82–5.85] |
| SPI3<-0.8 in DOY 196-273 | 8 | 16 | 0 | 22 | 0.33 [0.18–0.53] | 1.00 [0.68–1.00] | 1.00 [0.34–1.00] | 3.48 [2.41–6.84] |
| SPI3<-1.0 in DOY 196-227 | 5 | 9 | 3 | 29 | 0.36 [0.16–0.61] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 1.96 [1.08–4.50] |
| SPI3<-1.0 in DOY 204-218 | 5 | 6 | 3 | 32 | 0.45 [0.21–0.72] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 1.30 [0.58–3.44] |
| SPI3<-1.0 in DOY 196-273 | 7 | 11 | 1 | 27 | 0.39 [0.20–0.61] | 0.88 [0.53–0.98] | 1.00 [0.34–1.00] | 2.39 [1.45–5.18] |
| SPI3<-1.3 in DOY 196-227 | 5 | 5 | 3 | 33 | 0.50 [0.24–0.76] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 1.09 [0.43–3.07] |
| SPI3<-1.3 in DOY 204-218 | 4 | 3 | 4 | 35 | 0.57 [0.25–0.84] | 0.50 [0.22–0.78] | 0.50 [0.09–0.91] | 0.65 [0.16–2.31] |
| SPI3<-1.3 in DOY 196-273 | 5 | 7 | 3 | 31 | 0.42 [0.19–0.68] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 1.52 [0.74–3.80] |
| SPI3<-1.5 in DOY 196-227 | 5 | 4 | 3 | 34 | 0.56 [0.27–0.81] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 0.87 [0.29–2.70] |
| SPI3<-1.5 in DOY 204-218 | 3 | 2 | 5 | 36 | 0.60 [0.23–0.88] | 0.38 [0.14–0.69] | 0.50 [0.09–0.91] | 0.43 [0.06–1.90] |
| SPI3<-1.5 in DOY 196-273 | 5 | 5 | 3 | 33 | 0.50 [0.24–0.76] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 1.09 [0.43–3.07] |
| SPI3<-1.7 in DOY 196-227 | 4 | 1 | 4 | 37 | 0.80 [0.38–0.96] | 0.50 [0.22–0.78] | 0.50 [0.09–0.91] | 0.22 [0.01–1.47] |
| SPI3<-1.7 in DOY 204-218 | 3 | 0 | 5 | 38 | 1.00 [0.44–1.00] | 0.38 [0.14–0.69] | 0.50 [0.09–0.91] | 0.00 [0.00–0.97] |
| SPI3<-1.7 in DOY 196-273 | 5 | 3 | 3 | 35 | 0.62 [0.31–0.86] | 0.62 [0.31–0.86] | 0.50 [0.09–0.91] | 0.65 [0.16–2.31] |

## Combined SPI-3 ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-1.0 ∧ RZSM<-0.5σ | 4 | 3 | 0 | 5 | 0.57 [0.25–0.84] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 2.50 [0.77–10.96] |
| SPI3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 3 | 2 | 1 | 6 | 0.60 [0.23–0.88] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 1.67 [0.30–9.03] |
| SPI3<-1.0 ∧ RZSM<-1.0σ | 4 | 2 | 0 | 6 | 0.67 [0.30–0.90] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 1.67 [0.30–9.03] |
| SPI3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 3 | 1 | 1 | 7 | 0.75 [0.30–0.95] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.83 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.5σ | 4 | 1 | 0 | 7 | 0.80 [0.38–0.96] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.83 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 3 | 1 | 1 | 7 | 0.75 [0.30–0.95] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.83 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ | 4 | 1 | 0 | 7 | 0.80 [0.38–0.96] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.83 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 3 | 1 | 1 | 7 | 0.75 [0.30–0.95] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.83 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-1.0σ | 4 | 0 | 0 | 8 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 3 | 0 | 1 | 8 | 1.00 [0.44–1.00] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.3 ∧ RZSM<-1.5σ | 4 | 0 | 0 | 8 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 3 | 0 | 1 | 8 | 1.00 [0.44–1.00] | 0.75 [0.30–0.95] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-0.5σ | 4 | 1 | 0 | 7 | 0.80 [0.38–0.96] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.83 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 2 | 7 | 0.67 [0.21–0.94] | 0.50 [0.15–0.85] | 0.00 [0.00–0.79] | 0.83 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-1.0σ | 4 | 0 | 0 | 8 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 0 | 2 | 8 | 1.00 [0.34–1.00] | 0.50 [0.15–0.85] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.5σ | 4 | 0 | 0 | 8 | 1.00 [0.51–1.00] | 1.00 [0.51–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 2 | 8 | 1.00 [0.34–1.00] | 0.50 [0.15–0.85] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |

## Per-year detail (best SPI-3 single-indicator configuration)

**Recommended SPI-only trigger:** `SPI3<-1.0 in DOY 196-273`
- Precision: 0.39 [0.20–0.61] | Recall: 0.88 [0.53–0.98] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 2.39 [1.45–5.18]

| Year | Label | Worst dep | Min SPI-3 | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1981 | negative | Cabanas | 0.37 | 0/14 | — |  |
| 1982 | negative | Chalatenango | -1.28 | 3/14 | ✓ |  |
| 1983 | negative | La Union | -1.09 | 3/14 | ✓ |  |
| 1984 | negative | Ahuachapan | -0.07 | 0/14 | — |  |
| 1985 | negative | La Union | -0.90 | 0/14 | — |  |
| 1986 | negative | La Union | -1.14 | 1/14 | ✓ |  |
| 1987 | negative | La Union | 0.04 | 0/14 | — |  |
| 1988 | negative | Ahuachapan | 0.15 | 0/14 | — |  |
| 1989 | negative | La Union | -0.57 | 0/14 | — |  |
| 1990 | negative | La Union | -0.42 | 0/14 | — |  |
| 1991 | negative | Chalatenango | -1.71 | 13/14 | ✓ |  |
| 1992 | negative | Cabanas | -0.27 | 0/14 | — |  |
| 1993 | negative | Chalatenango | -0.34 | 0/14 | — |  |
| 1994 | negative | Cabanas | -1.58 | 9/14 | ✓ |  |
| 1995 | negative | Chalatenango | -0.54 | 0/14 | — |  |
| 1996 | negative | San Vicente | 0.17 | 0/14 | — |  |
| 1997 | severe-moderate | Chalatenango | -1.15 | 1/14 | ✓ | Super El Niño; FAO 'considerably below-average' 2nd-season maize |
| 1998 | negative | Chalatenango | -0.79 | 0/14 | — |  |
| 1999 | negative | San Salvador | -0.05 | 0/14 | — |  |
| 2000 | negative | La Union | -1.38 | 4/14 | ✓ |  |
| 2001 | negative | La Union | -1.16 | 1/14 | ✓ |  |
| 2002 | moderate | Chalatenango | -0.98 | 0/14 | — | Moderate El Niño |
| 2003 | negative | Chalatenango | -0.25 | 0/14 | — |  |
| 2004 | negative | La Union | -0.90 | 0/14 | — |  |
| 2005 | negative | Cabanas | 0.11 | 0/14 | — |  |
| 2006 | negative | La Union | -0.10 | 0/14 | — |  |
| 2007 | negative | Cabanas | -1.80 | 12/14 | ✓ |  |
| 2008 | negative | La Union | 0.06 | 0/14 | — |  |
| 2009 | moderate | La Union | -1.26 | 1/14 | ✓ | Moderate El Niño |
| 2010 | negative | Santa Ana | 1.13 | 0/14 | — |  |
| 2011 | negative | Sonsonate | 0.33 | 0/14 | — |  |
| 2012 | negative | La Union | -0.57 | 0/14 | — |  |
| 2013 | negative | La Union | -0.99 | 0/14 | — |  |
| 2014 | moderate | La Union | -1.75 | 7/14 | ✓ | Weak El Niño precursor; CHIRPS deficits late summer |
| 2015 | severe | Cabanas | -2.74 | 14/14 | ✓ | Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor |
| 2016 | negative | San Salvador | -1.41 | 13/14 | ✓ |  |
| 2017 | negative | Cabanas | -1.00 | 0/14 | — |  |
| 2018 | moderate | San Vicente | -2.43 | 14/14 | ✓ | Weak El Niño; postrera impact even at weak strength (FAO 2018) |
| 2019 | negative | La Union | -1.76 | 14/14 | ✓ |  |
| 2020 | negative | San Salvador | -0.64 | 0/14 | — |  |
| 2021 | negative | San Salvador | -1.60 | 7/14 | ✓ |  |
| 2022 | negative | Cabanas | -0.84 | 0/14 | — |  |
| 2023 | moderate | Ahuachapan | -1.86 | 14/14 | ✓ | Strong El Niño; one-month delay to postrera; 25%+ subsistence yield reduction |
| 2024 | negative | Chalatenango | -0.51 | 0/14 | — |  |
| 2025 | negative | Chalatenango | -0.67 | 0/14 | — |  |
| 2026 | moderate | Santa Ana | -4.66 | 14/14 | ✓ | Primera drought; field-confirmed irreversible maize damage in La Union and Morazan, Santa Ana much less affected (experiments/primera_2026_eval_report.md) |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI3<-1.3 ∧ RZSM<-1.0σ`** in DOY 196-227
- Precision: 1.00 [0.51–1.00] | Recall: 1.00 [0.51–1.00] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.00 [0.00–4.61]

| Year | Label | Worst dep | SPI-3 min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | severe | Cabanas | -2.74 | -2.94 | — | 14/14 | ✓ |
| 2016 | negative | San Salvador | -1.29 | -1.10 | — | 0/14 | — |
| 2017 | negative | Cabanas | -0.92 | -0.46 | — | 0/14 | — |
| 2018 | moderate | Cabanas | -1.51 | -2.94 | — | 10/14 | ✓ |
| 2019 | negative | San Salvador | -1.36 | -1.53 | — | 0/14 | — |
| 2020 | negative | Santa Ana | 0.08 | -0.42 | — | 0/14 | — |
| 2021 | negative | San Salvador | -1.60 | -0.73 | — | 0/14 | — |
| 2022 | negative | Cabanas | -0.84 | -0.34 | — | 0/14 | — |
| 2023 | moderate | Ahuachapan | -1.86 | -2.94 | — | 7/14 | ✓ |
| 2024 | negative | Chalatenango | -0.51 | -0.13 | — | 0/14 | — |
| 2025 | negative | Chalatenango | -0.67 | -0.94 | — | 0/14 | — |
| 2026 | moderate | Ahuachapan | -3.70 | -4.75 | — | 14/14 | ✓ |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.