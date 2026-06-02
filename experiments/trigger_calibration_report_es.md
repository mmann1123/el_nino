# Trigger Calibration Report — El Salvador

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** El Salvador (ES).
**Region:** Eastern Dry Corridor (mean of Morazán, San Miguel, La Unión, Usulután).
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
| SPI3<-0.8 in DOY 196-227 | 4 | 14 | 3 | 24 | 0.22 [0.09–0.45] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 3.11 [2.01–6.18] |
| SPI3<-0.8 in DOY 204-218 | 4 | 11 | 3 | 27 | 0.27 [0.11–0.52] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 2.44 [1.45–5.18] |
| SPI3<-0.8 in DOY 196-273 | 6 | 17 | 1 | 21 | 0.26 [0.13–0.46] | 0.86 [0.49–0.97] | 1.00 [0.34–1.00] | 3.78 [2.61–7.16] |
| SPI3<-1.0 in DOY 196-227 | 4 | 11 | 3 | 27 | 0.27 [0.11–0.52] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 2.44 [1.45–5.18] |
| SPI3<-1.0 in DOY 204-218 | 4 | 8 | 3 | 30 | 0.33 [0.14–0.61] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.78 [0.91–4.15] |
| SPI3<-1.0 in DOY 196-273 | 5 | 15 | 2 | 23 | 0.25 [0.11–0.47] | 0.71 [0.36–0.92] | 0.50 [0.09–0.91] | 3.33 [2.21–6.51] |
| SPI3<-1.3 in DOY 196-227 | 3 | 3 | 4 | 35 | 0.50 [0.19–0.81] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |
| SPI3<-1.3 in DOY 204-218 | 3 | 2 | 4 | 36 | 0.60 [0.23–0.88] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.3 in DOY 196-273 | 5 | 7 | 2 | 31 | 0.42 [0.19–0.68] | 0.71 [0.36–0.92] | 0.50 [0.09–0.91] | 1.56 [0.74–3.80] |
| SPI3<-1.5 in DOY 196-227 | 3 | 2 | 4 | 36 | 0.60 [0.23–0.88] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.5 in DOY 204-218 | 1 | 2 | 6 | 36 | 0.33 [0.06–0.79] | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.5 in DOY 196-273 | 3 | 4 | 4 | 34 | 0.43 [0.16–0.75] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.89 [0.29–2.70] |
| SPI3<-1.7 in DOY 196-227 | 2 | 2 | 5 | 36 | 0.50 [0.15–0.85] | 0.29 [0.08–0.64] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.7 in DOY 204-218 | 1 | 1 | 6 | 37 | 0.50 [0.09–0.91] | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | 0.22 [0.01–1.47] |
| SPI3<-1.7 in DOY 196-273 | 3 | 3 | 4 | 35 | 0.50 [0.19–0.81] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |

## Combined SPI-3 ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-1.0 ∧ RZSM<-0.5σ | 3 | 2 | 0 | 6 | 0.60 [0.23–0.88] | 1.00 [0.44–1.00] | 1.00 [0.21–1.00] | 1.82 [0.30–9.03] |
| SPI3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.0σ | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-1.0σ | 2 | 1 | 1 | 7 | 0.67 [0.21–0.94] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-0.5σ | 2 | 0 | 1 | 8 | 1.00 [0.34–1.00] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 0 | 2 | 8 | 1.00 [0.21–1.00] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.0σ | 2 | 0 | 1 | 8 | 1.00 [0.34–1.00] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 0.00 [0.00–4.61] |
| SPI3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 0 | 2 | 8 | 1.00 [0.21–1.00] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 0.00 [0.00–4.61] |

## Per-year detail (best SPI-3 single-indicator configuration)

**Recommended SPI-only trigger:** `SPI3<-0.8 in DOY 196-273`
- Precision: 0.26 [0.13–0.46] | Recall: 0.86 [0.49–0.97] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 3.78 [2.61–7.16]

| Year | Label | Worst dep | Min SPI-3 | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1981 | negative | San Miguel | 0.33 | 0/4 | — |  |
| 1982 | negative | La Union | -1.41 | 4/4 | ✓ |  |
| 1983 | negative | La Union | -1.20 | 4/4 | ✓ |  |
| 1984 | negative | La Union | -0.10 | 0/4 | — |  |
| 1985 | negative | La Union | -1.00 | 1/4 | ✓ |  |
| 1986 | negative | La Union | -1.28 | 4/4 | ✓ |  |
| 1987 | negative | La Union | -0.01 | 0/4 | — |  |
| 1988 | negative | La Union | 0.16 | 0/4 | — |  |
| 1989 | negative | La Union | -0.66 | 0/4 | — |  |
| 1990 | negative | La Union | -0.50 | 0/4 | — |  |
| 1991 | negative | San Miguel | -1.46 | 4/4 | ✓ |  |
| 1992 | negative | San Miguel | -0.37 | 0/4 | — |  |
| 1993 | negative | San Miguel | -0.07 | 0/4 | — |  |
| 1994 | negative | Morazan | -1.78 | 4/4 | ✓ |  |
| 1995 | negative | San Miguel | -0.19 | 0/4 | — |  |
| 1996 | negative | San Miguel | 0.11 | 0/4 | — |  |
| 1997 | severe-moderate | La Union | -0.99 | 4/4 | ✓ | Super El Niño; FAO 'considerably below-average' 2nd-season maize |
| 1998 | negative | San Miguel | -0.81 | 2/4 | ✓ |  |
| 1999 | negative | La Union | 0.25 | 0/4 | — |  |
| 2000 | negative | La Union | -1.54 | 4/4 | ✓ |  |
| 2001 | negative | La Union | -1.27 | 4/4 | ✓ |  |
| 2002 | moderate | La Union | -0.64 | 0/4 | — | Moderate El Niño |
| 2003 | negative | La Union | -0.23 | 0/4 | — |  |
| 2004 | negative | La Union | -1.19 | 4/4 | ✓ |  |
| 2005 | negative | San Miguel | 0.06 | 0/4 | — |  |
| 2006 | negative | La Union | -0.16 | 0/4 | — |  |
| 2007 | negative | San Miguel | -1.93 | 4/4 | ✓ |  |
| 2008 | negative | La Union | 0.01 | 0/4 | — |  |
| 2009 | moderate | La Union | -1.40 | 4/4 | ✓ | Moderate El Niño |
| 2010 | negative | La Union | 1.59 | 0/4 | — |  |
| 2011 | negative | San Miguel | 0.70 | 0/4 | — |  |
| 2012 | negative | La Union | -0.65 | 0/4 | — |  |
| 2013 | negative | La Union | -1.10 | 1/4 | ✓ |  |
| 2014 | moderate | La Union | -1.90 | 4/4 | ✓ | Weak El Niño precursor; CHIRPS deficits late summer |
| 2015 | severe | San Miguel | -3.19 | 4/4 | ✓ | Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor |
| 2016 | negative | San Miguel | -1.40 | 4/4 | ✓ |  |
| 2017 | negative | San Miguel | -1.14 | 3/4 | ✓ |  |
| 2018 | moderate | San Miguel | -2.79 | 4/4 | ✓ | Weak El Niño; postrera impact even at weak strength (FAO 2018) |
| 2019 | negative | Morazan | -2.04 | 4/4 | ✓ |  |
| 2020 | negative | San Miguel | 0.24 | 0/4 | — |  |
| 2021 | negative | San Miguel | -1.17 | 3/4 | ✓ |  |
| 2022 | negative | San Miguel | -0.97 | 3/4 | ✓ |  |
| 2023 | moderate | San Miguel | -1.36 | 4/4 | ✓ | Strong El Niño; one-month delay to postrera; 25%+ subsistence yield reduction |
| 2024 | negative | San Miguel | 0.17 | 0/4 | — |  |
| 2025 | negative | San Miguel | 0.01 | 0/4 | — |  |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI3<-1.5 ∧ RZSM<-0.5σ`** in DOY 196-227
- Precision: 1.00 [0.34–1.00] | Recall: 0.67 [0.21–0.94] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.00 [0.00–4.61]

| Year | Label | Worst dep | SPI-3 min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | severe | San Miguel | -2.99 | -1.85 | — | 4/4 | ✓ |
| 2016 | negative | San Miguel | -1.25 | -0.95 | — | 0/4 | — |
| 2017 | negative | San Miguel | -1.05 | -0.09 | — | 0/4 | — |
| 2018 | moderate | San Miguel | -1.68 | -1.54 | — | 3/4 | ✓ |
| 2019 | negative | Morazan | -1.35 | -1.27 | — | 0/4 | — |
| 2020 | negative | San Miguel | 1.18 | -0.38 | — | 0/4 | — |
| 2021 | negative | San Miguel | -1.17 | -0.49 | — | 0/4 | — |
| 2022 | negative | San Miguel | -0.97 | -0.08 | — | 0/4 | — |
| 2023 | moderate | San Miguel | -1.18 | -0.84 | — | 0/4 | — |
| 2024 | negative | San Miguel | 0.97 | 1.61 | — | 0/4 | — |
| 2025 | negative | La Union | 0.07 | -0.71 | — | 0/4 | — |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.