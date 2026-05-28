# Trigger Calibration Report

Generated from `el_nino/experiments/trigger_calibration.py`.

**Region:** eastern Dry Corridor (mean of Morazán, San Miguel, La Unión, Usulután).
**Labels:** drawn from `el_nino/el_nino_agricultural_risks.md`.

**Severe positive:** 2015 (60% maize / 80% beans loss in Dry Corridor).
**Moderate positives:** 2002, 2009, 2014, 2018, 2023.
**Negatives:** all other years with available data.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI-3 only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-0.8 in DOY 196-227 | 4 | 8 | 3 | 30 | 0.33 [0.14–0.61] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.78 [0.91–4.15] |
| SPI3<-0.8 in DOY 181-243 | 4 | 15 | 3 | 23 | 0.21 [0.09–0.43] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 3.33 [2.21–6.51] |
| SPI3<-0.8 in DOY 213-273 | 6 | 12 | 1 | 26 | 0.33 [0.16–0.56] | 0.86 [0.49–0.97] | 1.00 [0.34–1.00] | 2.67 [1.63–5.52] |
| SPI3<-1.0 in DOY 196-227 | 4 | 7 | 3 | 31 | 0.36 [0.15–0.65] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 1.56 [0.74–3.80] |
| SPI3<-1.0 in DOY 181-243 | 4 | 11 | 3 | 27 | 0.27 [0.11–0.52] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 2.44 [1.45–5.18] |
| SPI3<-1.0 in DOY 213-273 | 4 | 9 | 3 | 29 | 0.31 [0.13–0.58] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 2.00 [1.08–4.50] |
| SPI3<-1.3 in DOY 196-227 | 3 | 3 | 4 | 35 | 0.50 [0.19–0.81] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |
| SPI3<-1.3 in DOY 181-243 | 3 | 6 | 4 | 32 | 0.33 [0.12–0.65] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 1.33 [0.58–3.44] |
| SPI3<-1.3 in DOY 213-273 | 4 | 4 | 3 | 34 | 0.50 [0.22–0.78] | 0.57 [0.25–0.84] | 0.50 [0.09–0.91] | 0.89 [0.29–2.70] |
| SPI3<-1.5 in DOY 196-227 | 3 | 2 | 4 | 36 | 0.60 [0.23–0.88] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.5 in DOY 181-243 | 3 | 3 | 4 | 35 | 0.50 [0.19–0.81] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |
| SPI3<-1.5 in DOY 213-273 | 3 | 2 | 4 | 36 | 0.60 [0.23–0.88] | 0.43 [0.16–0.75] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.7 in DOY 196-227 | 1 | 2 | 6 | 36 | 0.33 [0.06–0.79] | 0.14 [0.03–0.51] | 0.50 [0.09–0.91] | 0.44 [0.06–1.90] |
| SPI3<-1.7 in DOY 181-243 | 2 | 3 | 5 | 35 | 0.40 [0.12–0.77] | 0.29 [0.08–0.64] | 0.50 [0.09–0.91] | 0.67 [0.16–2.31] |
| SPI3<-1.7 in DOY 213-273 | 2 | 1 | 5 | 37 | 0.67 [0.21–0.94] | 0.29 [0.08–0.64] | 0.50 [0.09–0.91] | 0.22 [0.01–1.47] |

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

**Recommended SPI-only trigger:** `SPI3<-0.8 in DOY 213-273`
- Precision: 0.33 [0.16–0.56] | Recall: 0.86 [0.49–0.97] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 2.67 [1.63–5.52]

| Year | Label | Min SPI-3 | Fired? | Notes |
|---|---|---:|:---:|---|
| 1981 | negative | 0.39 | — |  |
| 1982 | negative | -1.20 | ✓ |  |
| 1983 | negative | -1.02 | ✓ |  |
| 1984 | negative | 0.51 | — |  |
| 1985 | negative | -0.10 | — |  |
| 1986 | negative | -0.95 | ✓ |  |
| 1987 | negative | 0.59 | — |  |
| 1988 | negative | 0.85 | — |  |
| 1989 | negative | 0.06 | — |  |
| 1990 | negative | -0.17 | — |  |
| 1991 | negative | -1.35 | ✓ |  |
| 1992 | negative | 0.03 | — |  |
| 1993 | negative | 0.12 | — |  |
| 1994 | negative | -1.56 | ✓ |  |
| 1995 | negative | 0.34 | — |  |
| 1996 | negative | 0.21 | — |  |
| 1997 | severe-moderate | -0.93 | ✓ | Super El Niño; FAO 'considerably below-average' 2nd-season maize |
| 1998 | negative | -0.03 | — |  |
| 1999 | negative | 0.36 | — |  |
| 2000 | negative | -1.11 | ✓ |  |
| 2001 | negative | -1.22 | ✓ |  |
| 2002 | moderate | -0.31 | — | Moderate El Niño |
| 2003 | negative | 0.09 | — |  |
| 2004 | negative | -0.94 | ✓ |  |
| 2005 | negative | 0.13 | — |  |
| 2006 | negative | 0.49 | — |  |
| 2007 | negative | -1.33 | ✓ |  |
| 2008 | negative | 0.42 | — |  |
| 2009 | moderate | -0.97 | ✓ | Moderate El Niño |
| 2010 | negative | 1.62 | — |  |
| 2011 | negative | 0.82 | — |  |
| 2012 | negative | -0.46 | — |  |
| 2013 | negative | -0.76 | — |  |
| 2014 | moderate | -1.58 | ✓ | Weak El Niño precursor; CHIRPS deficits documented late summer |
| 2015 | severe | -3.06 | ✓ | Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor |
| 2016 | negative | -1.18 | ✓ |  |
| 2017 | negative | -0.97 | ✓ |  |
| 2018 | moderate | -2.65 | ✓ | Weak El Niño; postrera impact even at weak strength (FAO 2018) |
| 2019 | negative | -2.03 | ✓ |  |
| 2020 | negative | 0.36 | — |  |
| 2021 | negative | -0.51 | — |  |
| 2022 | negative | -0.76 | — |  |
| 2023 | moderate | -1.32 | ✓ | Strong El Niño; one-month delay to postrera; 25%+ subsistence yield reduction |
| 2024 | negative | 0.31 | — |  |
| 2025 | negative | 0.10 | — |  |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI3<-1.5 ∧ RZSM<-0.5σ`** in DOY 196-227
- Precision: 1.00 [0.34–1.00] | Recall: 0.67 [0.21–0.94] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.00 [0.00–4.61]

| Year | Label | SPI-3 min | RZSM min (σ) | ETa min (σ) | Fired? |
|---|---|---:|---:|---:|:---:|
| 2015 | severe | -2.83 | -1.72 | — | ✓ |
| 2016 | negative | -1.12 | -0.85 | — | — |
| 2017 | negative | -0.91 | 0.06 | — | — |
| 2018 | moderate | -1.56 | -1.22 | — | ✓ |
| 2019 | negative | -1.32 | -1.10 | — | — |
| 2020 | negative | 1.62 | -0.09 | — | — |
| 2021 | negative | -1.03 | -0.18 | — | — |
| 2022 | negative | -0.76 | -0.13 | — | — |
| 2023 | moderate | -1.05 | -0.64 | — | — |
| 2024 | negative | 1.12 | 1.70 | — | — |
| 2025 | negative | 0.32 | -0.32 | — | — |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.