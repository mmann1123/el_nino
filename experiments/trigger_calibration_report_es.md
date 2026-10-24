# Trigger Calibration Report — El Salvador

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** El Salvador (ES).
**Region:** all 14 departamentos; a year fires if any one of them meets the conditions.
**Silking window:** DOY 196-227.
**Labels:** drawn from `el_nino/el_nino_agricultural_risks.md` via `config.CC['labeled_events']`.

**Severe positive(s):** 1997 (Super El Niño; FAO 'considerably below-average' 2nd-season maize), 2015 (Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor).
**Moderate positives:** 2002, 2009, 2014, 2018, 2023.
**Negatives:** all other years with available data.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI-3 only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-0.8 in DOY 196-227 | 5 | 14 | 2 | 24 | 0.26 [0.12–0.49] | 0.71 [0.36–0.92] | 0.50 [0.09–0.91] | 3.11 [2.01–6.18] |
| SPI3<-0.8 in DOY 204-218 | 5 | 13 | 2 | 25 | 0.28 [0.12–0.51] | 0.71 [0.36–0.92] | 0.50 [0.09–0.91] | 2.89 [1.82–5.85] |
| SPI3<-0.8 in DOY 196-273 | 7 | 16 | 0 | 22 | 0.30 [0.16–0.51] | 1.00 [0.65–1.00] | 1.00 [0.34–1.00] | 3.56 [2.41–6.84] |
| SPI3<-1.0 in DOY 196-227 | 4 | 9 | 3 | 29 | 0.31 [0.13–0.58] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 2.00 [1.08–4.50] |
| SPI3<-1.0 in DOY 204-218 | 4 | 6 | 3 | 32 | 0.40 [0.17–0.69] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.33 [0.58–3.44] |
| SPI3<-1.0 in DOY 196-273 | 6 | 11 | 1 | 27 | 0.35 [0.17–0.59] | 0.86 [0.49–0.97] | 1.00 [0.34–1.00] | 2.44 [1.45–5.18] |
| SPI3<-1.3 in DOY 196-227 | 4 | 5 | 3 | 33 | 0.44 [0.19–0.73] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.11 [0.43–3.07] |
| SPI3<-1.3 in DOY 204-218 | 3 | 3 | 4 | 35 | 0.50 [0.19–0.81] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |
| SPI3<-1.3 in DOY 196-273 | 4 | 7 | 3 | 31 | 0.36 [0.15–0.65] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.56 [0.74–3.80] |
| SPI3<-1.5 in DOY 196-227 | 4 | 4 | 3 | 34 | 0.50 [0.22–0.78] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 0.89 [0.29–2.70] |
| SPI3<-1.5 in DOY 204-218 | 2 | 2 | 5 | 36 | 0.50 [0.15–0.85] | 0.29 [0.08–0.64] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.5 in DOY 196-273 | 4 | 5 | 3 | 33 | 0.44 [0.19–0.73] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.11 [0.43–3.07] |
| SPI3<-1.7 in DOY 196-227 | 3 | 1 | 4 | 37 | 0.75 [0.30–0.95] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.22 [0.01–1.47] |
| SPI3<-1.7 in DOY 204-218 | 2 | 0 | 5 | 38 | 1.00 [0.34–1.00] | 0.29 [0.08–0.64] | 0.50 [0.09–0.91] | 0.00 [0.00–0.97] |
| SPI3<-1.7 in DOY 196-273 | 4 | 3 | 3 | 35 | 0.57 [0.25–0.84] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |

## Combined SPI-3 ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-1.0 ∧ RZSM<-0.5σ | 3 | 3 | 0 | 5 | 0.50 [0.19–0.81] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 2 | 1 | 6 | 0.50 [0.15–0.85] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 1.82 [0.30–9.03] |
| SPI3<-1.0 ∧ RZSM<-1.0σ | 3 | 2 | 0 | 6 | 0.60 [0.23–0.88] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 1.82 [0.30–9.03] |
| SPI3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.5σ | 3 | 1 | 0 | 7 | 0.75 [0.30–0.95] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ | 3 | 1 | 0 | 7 | 0.75 [0.30–0.95] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-1.0σ | 3 | 0 | 0 | 8 | 1.00 [0.44–1.00] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 0 | 1 | 8 | 1.00 [0.34–1.00] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.3 ∧ RZSM<-1.5σ | 3 | 0 | 0 | 8 | 1.00 [0.44–1.00] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 1 | 8 | 1.00 [0.34–1.00] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-0.5σ | 3 | 1 | 0 | 7 | 0.75 [0.30–0.95] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-1.0σ | 3 | 0 | 0 | 8 | 1.00 [0.44–1.00] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 0 | 2 | 8 | 1.00 [0.21–1.00] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.5σ | 3 | 0 | 0 | 8 | 1.00 [0.44–1.00] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 1 | 0 | 2 | 8 | 1.00 [0.21–1.00] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |

## Per-year detail (best SPI-3 single-indicator configuration)

**Recommended SPI-only trigger:** `SPI3<-1.0 in DOY 196-273`
- Precision: 0.35 [0.17–0.59] | Recall: 0.86 [0.49–0.97] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 2.44 [1.45–5.18]

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

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI3<-1.3 ∧ RZSM<-1.0σ`** in DOY 196-227
- Precision: 1.00 [0.44–1.00] | Recall: 1.00 [0.44–1.00] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.00 [0.00–4.61]

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

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.