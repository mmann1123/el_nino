# Trigger Calibration Report — Haiti

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** Haiti (HT).
**Region:** all 10 départements; a year fires if any one of them meets the conditions.
**Silking window:** DOY 152-227.
**Labels:** drawn from `el_nino/el_nino_agricultural_risks.md` via `config.CC['labeled_events']`.

**Severe positive(s):** 1997 (Super El Niño; Caribbean drought; pre-Mitch deficits), 2015 (Very Strong El Niño; -39% rainfed maize / -44% beans nationally; national emergency (FEWS NET 2016)).
**Moderate positives:** 2009, 2014, 2018, 2023.
**Negatives:** all other years with available data.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI-3 only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-0.8 in DOY 152-227 | 4 | 26 | 2 | 13 | 0.13 [0.05–0.30] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 5.78 [4.35–9.77] |
| SPI3<-0.8 in DOY 171-207 | 3 | 19 | 3 | 20 | 0.14 [0.05–0.33] | 0.50 [0.19–0.81] | 1.00 [0.34–1.00] | 4.22 [2.93–7.61] |
| SPI3<-0.8 in DOY 152-273 | 6 | 31 | 0 | 8 | 0.16 [0.08–0.31] | 1.00 [0.61–1.00] | 1.00 [0.34–1.00] | 6.89 [5.40–11.28] |
| SPI3<-1.0 in DOY 152-227 | 4 | 16 | 2 | 23 | 0.20 [0.08–0.42] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 3.56 [2.34–6.66] |
| SPI3<-1.0 in DOY 171-207 | 3 | 12 | 3 | 27 | 0.20 [0.07–0.45] | 0.50 [0.19–0.81] | 1.00 [0.34–1.00] | 2.67 [1.59–5.37] |
| SPI3<-1.0 in DOY 152-273 | 5 | 24 | 1 | 15 | 0.17 [0.08–0.35] | 0.83 [0.44–0.97] | 1.00 [0.34–1.00] | 5.33 [3.94–9.16] |
| SPI3<-1.3 in DOY 152-227 | 4 | 9 | 2 | 30 | 0.31 [0.13–0.58] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 2.00 [1.06–4.38] |
| SPI3<-1.3 in DOY 171-207 | 2 | 8 | 4 | 31 | 0.20 [0.06–0.51] | 0.33 [0.10–0.70] | 0.50 [0.09–0.91] | 1.78 [0.89–4.04] |
| SPI3<-1.3 in DOY 152-273 | 4 | 14 | 2 | 25 | 0.22 [0.09–0.45] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 3.11 [1.96–6.02] |
| SPI3<-1.5 in DOY 152-227 | 3 | 7 | 3 | 32 | 0.30 [0.11–0.60] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 1.56 [0.72–3.70] |
| SPI3<-1.5 in DOY 171-207 | 2 | 5 | 4 | 34 | 0.29 [0.08–0.64] | 0.33 [0.10–0.70] | 0.50 [0.09–0.91] | 1.11 [0.42–2.99] |
| SPI3<-1.5 in DOY 152-273 | 3 | 11 | 3 | 28 | 0.21 [0.08–0.48] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 2.44 [1.41–5.05] |
| SPI3<-1.7 in DOY 152-227 | 3 | 4 | 3 | 35 | 0.43 [0.16–0.75] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 0.89 [0.28–2.63] |
| SPI3<-1.7 in DOY 171-207 | 2 | 2 | 4 | 37 | 0.50 [0.15–0.85] | 0.33 [0.10–0.70] | 0.50 [0.09–0.91] | 0.44 [0.06–1.85] |
| SPI3<-1.7 in DOY 152-273 | 3 | 7 | 3 | 32 | 0.30 [0.11–0.60] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 1.56 [0.72–3.70] |

## Combined SPI-3 ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-1.0 ∧ RZSM<-0.5σ | 2 | 5 | 1 | 3 | 0.29 [0.08–0.64] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 4.55 [2.03–14.59] |
| SPI3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 4 | 2 | 4 | 0.20 [0.04–0.62] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 3.64 [1.36–12.80] |
| SPI3<-1.0 ∧ RZSM<-1.0σ | 2 | 3 | 1 | 5 | 0.40 [0.12–0.77] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 3 | 2 | 5 | 0.25 [0.05–0.70] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 2.73 [0.77–10.96] |
| SPI3<-1.0 ∧ RZSM<-1.5σ | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 0 | 1 | 3 | 7 | 0.00 [0.00–0.79] | 0.00 [0.00–0.56] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ | 2 | 3 | 1 | 5 | 0.40 [0.12–0.77] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 3 | 2 | 5 | 0.25 [0.05–0.70] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 2.73 [0.77–10.96] |
| SPI3<-1.3 ∧ RZSM<-1.0σ | 2 | 2 | 1 | 6 | 0.50 [0.15–0.85] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 1.82 [0.30–9.03] |
| SPI3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 2 | 2 | 6 | 0.33 [0.06–0.79] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 1.82 [0.30–9.03] |
| SPI3<-1.3 ∧ RZSM<-1.5σ | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 0 | 1 | 3 | 7 | 0.00 [0.00–0.79] | 0.00 [0.00–0.56] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-0.5σ | 2 | 3 | 1 | 5 | 0.40 [0.12–0.77] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 3 | 2 | 5 | 0.25 [0.05–0.70] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 2.73 [0.77–10.96] |
| SPI3<-1.5 ∧ RZSM<-1.0σ | 2 | 2 | 1 | 6 | 0.50 [0.15–0.85] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 1.82 [0.30–9.03] |
| SPI3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 1 | 2 | 2 | 6 | 0.33 [0.06–0.79] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 1.82 [0.30–9.03] |
| SPI3<-1.5 ∧ RZSM<-1.5σ | 1 | 1 | 2 | 7 | 0.50 [0.09–0.91] | 0.33 [0.06–0.79] | 1.00 [0.21–1.00] | 0.91 [0.03–6.96] |
| SPI3<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 0 | 1 | 3 | 7 | 0.00 [0.00–0.79] | 0.00 [0.00–0.56] | 0.00 [0.00–0.79] | 0.91 [0.03–6.96] |

## Per-year detail (best SPI-3 single-indicator configuration)

**Recommended SPI-only trigger:** `SPI3<-1.3 in DOY 152-227`
- Precision: 0.31 [0.13–0.58] | Recall: 0.67 [0.30–0.90] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 2.00 [1.06–4.38]

| Year | Label | Worst dep | Min SPI-3 | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1981 | negative | Grande Anse | -0.87 | 0/10 | — |  |
| 1982 | negative | Ouest | -0.91 | 0/10 | — |  |
| 1983 | negative | Sud | -0.97 | 0/10 | — |  |
| 1984 | negative | Nippes | -0.93 | 0/10 | — |  |
| 1985 | negative | Grande Anse | -0.97 | 0/10 | — |  |
| 1986 | negative | Nord Est | -0.48 | 0/10 | — |  |
| 1987 | negative | Grande Anse | -0.89 | 0/10 | — |  |
| 1988 | negative | Centre | -1.13 | 0/10 | — |  |
| 1989 | negative | Nippes | -1.71 | 9/10 | ✓ |  |
| 1990 | negative | Centre | -1.59 | 10/10 | ✓ |  |
| 1991 | negative | Nord Ouest | -1.31 | 1/10 | ✓ |  |
| 1992 | negative | Nord Ouest | -0.03 | 0/10 | — |  |
| 1993 | negative | Nord | -0.75 | 0/10 | — |  |
| 1994 | negative | Nippes | -0.08 | 0/10 | — |  |
| 1995 | negative | Sud | -0.79 | 0/10 | — |  |
| 1996 | negative | Nippes | -1.00 | 0/10 | — |  |
| 1997 | severe-moderate | Nord | -1.47 | 5/10 | ✓ | Super El Niño; Caribbean drought; pre-Mitch deficits |
| 1998 | negative | Grande Anse | -0.96 | 0/10 | — |  |
| 1999 | negative | Grande Anse | -1.18 | 0/10 | — |  |
| 2000 | negative | Grande Anse | -1.25 | 0/10 | — |  |
| 2001 | negative | Grande Anse | -0.31 | 0/10 | — |  |
| 2002 | negative | Nord Est | -1.03 | 0/10 | — |  |
| 2003 | negative | Nippes | -1.31 | 1/10 | ✓ |  |
| 2004 | negative | Grande Anse | -0.71 | 0/10 | — |  |
| 2005 | negative | Nord Est | 0.19 | 0/10 | — |  |
| 2006 | negative | Nord Est | -0.95 | 0/10 | — |  |
| 2007 | negative | Sud Est | -0.25 | 0/10 | — |  |
| 2008 | negative | Nord | -0.97 | 0/10 | — |  |
| 2009 | moderate | Sud Est | 0.66 | 0/10 | — | Moderate El Niño 2009-10 |
| 2010 | negative | Nord Est | 0.55 | 0/10 | — |  |
| 2011 | negative | Nippes | 0.12 | 0/10 | — |  |
| 2012 | negative | Nippes | -1.16 | 0/10 | — |  |
| 2013 | negative | Nord Ouest | -1.90 | 10/10 | ✓ |  |
| 2014 | moderate | Sud Est | -1.99 | 6/10 | ✓ | Weak El Niño precursor; lead-up to 2015 crisis |
| 2015 | severe | Ouest | -2.56 | 10/10 | ✓ | Very Strong El Niño; -39% rainfed maize / -44% beans nationally; national emergency (FEWS NET 2016) |
| 2016 | negative | Ouest | -1.29 | 0/10 | — |  |
| 2017 | negative | Grande Anse | 0.61 | 0/10 | — |  |
| 2018 | moderate | Centre | -1.95 | 9/10 | ✓ | Weak El Niño; postrera/automne impact |
| 2019 | negative | Ouest | -1.53 | 9/10 | ✓ |  |
| 2020 | negative | Nord Est | -2.83 | 10/10 | ✓ |  |
| 2021 | negative | Nord Est | -1.60 | 5/10 | ✓ |  |
| 2022 | negative | Grande Anse | -1.20 | 0/10 | — |  |
| 2023 | moderate | Sud Est | -0.58 | 0/10 | — | Strong El Niño; FEWS Aug 2023 Northwest + southern peninsula impact |
| 2024 | negative | Nord | 0.40 | 0/10 | — |  |
| 2025 | negative | Nord Est | -1.87 | 2/10 | ✓ |  |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI3<-1.0 ∧ RZSM<-1.5σ`** in DOY 152-227
- Precision: 0.50 [0.09–0.91] | Recall: 0.33 [0.06–0.79] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.91 [0.03–6.96]

| Year | Label | Worst dep | SPI-3 min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | severe | Ouest | -2.56 | -2.94 | — | 10/10 | ✓ |
| 2016 | negative | Ouest | -1.29 | -0.76 | — | 0/10 | — |
| 2017 | negative | Grande Anse | 0.61 | -0.27 | — | 0/10 | — |
| 2018 | moderate | Centre | -1.95 | -1.36 | — | 0/10 | — |
| 2019 | negative | Ouest | -1.53 | -0.88 | — | 0/10 | — |
| 2020 | negative | Nord Est | -2.83 | -1.96 | — | 2/10 | ✓ |
| 2021 | negative | Nord Est | -1.60 | -0.64 | — | 0/10 | — |
| 2022 | negative | Grande Anse | -1.20 | -1.36 | — | 0/10 | — |
| 2023 | moderate | Sud Est | -0.58 | -2.94 | — | 0/10 | — |
| 2024 | negative | Nord | 0.40 | -0.61 | — | 0/10 | — |
| 2025 | negative | Nord Est | -1.87 | -1.36 | — | 0/10 | — |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.