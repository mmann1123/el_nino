# Trigger Calibration Report — Haiti

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** Haiti (HT).
**Region:** Drought-vulnerable departments (mean of Sud, Sud-Est, Grand'Anse, Nippes, Nord-Ouest, Centre).
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
| SPI3<-0.8 in DOY 171-207 | 4 | 19 | 2 | 20 | 0.17 [0.07–0.37] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 4.22 [2.93–7.61] |
| SPI3<-0.8 in DOY 152-273 | 6 | 31 | 0 | 8 | 0.16 [0.08–0.31] | 1.00 [0.61–1.00] | 1.00 [0.34–1.00] | 6.89 [5.40–11.28] |
| SPI3<-1.0 in DOY 152-227 | 4 | 17 | 2 | 22 | 0.19 [0.08–0.40] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 3.78 [2.54–6.98] |
| SPI3<-1.0 in DOY 171-207 | 3 | 12 | 3 | 27 | 0.20 [0.07–0.45] | 0.50 [0.19–0.81] | 1.00 [0.34–1.00] | 2.67 [1.59–5.37] |
| SPI3<-1.0 in DOY 152-273 | 5 | 25 | 1 | 14 | 0.17 [0.07–0.34] | 0.83 [0.44–0.97] | 1.00 [0.34–1.00] | 5.56 [4.15–9.46] |
| SPI3<-1.3 in DOY 152-227 | 4 | 10 | 2 | 29 | 0.29 [0.12–0.55] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 2.22 [1.23–4.72] |
| SPI3<-1.3 in DOY 171-207 | 2 | 8 | 4 | 31 | 0.20 [0.06–0.51] | 0.33 [0.10–0.70] | 0.50 [0.09–0.91] | 1.78 [0.89–4.04] |
| SPI3<-1.3 in DOY 152-273 | 4 | 16 | 2 | 23 | 0.20 [0.08–0.42] | 0.67 [0.30–0.90] | 1.00 [0.34–1.00] | 3.56 [2.34–6.66] |
| SPI3<-1.5 in DOY 152-227 | 3 | 7 | 3 | 32 | 0.30 [0.11–0.60] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 1.56 [0.72–3.70] |
| SPI3<-1.5 in DOY 171-207 | 2 | 5 | 4 | 34 | 0.29 [0.08–0.64] | 0.33 [0.10–0.70] | 0.50 [0.09–0.91] | 1.11 [0.42–2.99] |
| SPI3<-1.5 in DOY 152-273 | 3 | 13 | 3 | 26 | 0.19 [0.07–0.43] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 2.89 [1.77–5.70] |
| SPI3<-1.7 in DOY 152-227 | 3 | 4 | 3 | 35 | 0.43 [0.16–0.75] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 0.89 [0.28–2.63] |
| SPI3<-1.7 in DOY 171-207 | 2 | 3 | 4 | 36 | 0.40 [0.12–0.77] | 0.33 [0.10–0.70] | 0.50 [0.09–0.91] | 0.67 [0.16–2.25] |
| SPI3<-1.7 in DOY 152-273 | 3 | 9 | 3 | 30 | 0.25 [0.09–0.53] | 0.50 [0.19–0.81] | 0.50 [0.09–0.91] | 2.00 [1.06–4.38] |

## Combined SPI-3 ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |
|---|---:|---:|---:|---:|---|---|---|---|
| SPI3<-1.0 ∧ RZSM<-0.5σ | 2 | 5 | 1 | 3 | 0.29 [0.08–0.64] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 4.55 [2.03–14.59] |
| SPI3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 4 | 2 | 4 | 0.20 [0.04–0.62] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 3.64 [1.36–12.80] |
| SPI3<-1.0 ∧ RZSM<-1.0σ | 1 | 3 | 2 | 5 | 0.25 [0.05–0.70] | 0.33 [0.06–0.79] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 0 | 3 | 3 | 5 | 0.00 [0.00–0.56] | 0.00 [0.00–0.56] | 0.00 [0.00–0.79] | 2.73 [0.77–10.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ | 2 | 3 | 1 | 5 | 0.40 [0.12–0.77] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 3 | 2 | 5 | 0.25 [0.05–0.70] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 2.73 [0.77–10.96] |
| SPI3<-1.3 ∧ RZSM<-1.0σ | 1 | 2 | 2 | 6 | 0.33 [0.06–0.79] | 0.33 [0.06–0.79] | 1.00 [0.21–1.00] | 1.82 [0.30–9.03] |
| SPI3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 0 | 2 | 3 | 6 | 0.00 [0.00–0.66] | 0.00 [0.00–0.56] | 0.00 [0.00–0.79] | 1.82 [0.30–9.03] |
| SPI3<-1.5 ∧ RZSM<-0.5σ | 2 | 3 | 1 | 5 | 0.40 [0.12–0.77] | 0.67 [0.21–0.94] | 1.00 [0.21–1.00] | 2.73 [0.77–10.96] |
| SPI3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 1 | 3 | 2 | 5 | 0.25 [0.05–0.70] | 0.33 [0.06–0.79] | 0.00 [0.00–0.79] | 2.73 [0.77–10.96] |
| SPI3<-1.5 ∧ RZSM<-1.0σ | 1 | 2 | 2 | 6 | 0.33 [0.06–0.79] | 0.33 [0.06–0.79] | 1.00 [0.21–1.00] | 1.82 [0.30–9.03] |
| SPI3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 0 | 2 | 3 | 6 | 0.00 [0.00–0.66] | 0.00 [0.00–0.56] | 0.00 [0.00–0.79] | 1.82 [0.30–9.03] |

## Per-year detail (best SPI-3 single-indicator configuration)

**Recommended SPI-only trigger:** `SPI3<-1.3 in DOY 152-227`
- Precision: 0.29 [0.12–0.55] | Recall: 0.67 [0.30–0.90] | Severe recall: 1.00 [0.34–1.00] | FP/decade: 2.22 [1.23–4.72]

| Year | Label | Worst dep | Min SPI-3 | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1981 | negative | Grande Anse | -0.85 | 0/6 | — |  |
| 1982 | negative | Sud Est | -1.05 | 0/6 | — |  |
| 1983 | negative | Sud | -0.96 | 0/6 | — |  |
| 1984 | negative | Nippes | -0.95 | 0/6 | — |  |
| 1985 | negative | Grande Anse | -0.95 | 0/6 | — |  |
| 1986 | negative | Nord Ouest | -0.22 | 0/6 | — |  |
| 1987 | negative | Grande Anse | -0.91 | 0/6 | — |  |
| 1988 | negative | Centre | -1.11 | 0/6 | — |  |
| 1989 | negative | Nippes | -1.81 | 6/6 | ✓ |  |
| 1990 | negative | Centre | -1.57 | 6/6 | ✓ |  |
| 1991 | negative | Nord Ouest | -1.37 | 1/6 | ✓ |  |
| 1992 | negative | Nord Ouest | -0.11 | 0/6 | — |  |
| 1993 | negative | Nord Ouest | -0.66 | 0/6 | — |  |
| 1994 | negative | Nippes | -0.12 | 0/6 | — |  |
| 1995 | negative | Nippes | -0.78 | 0/6 | — |  |
| 1996 | negative | Nippes | -1.01 | 0/6 | — |  |
| 1997 | severe-moderate | Nord Ouest | -1.37 | 3/6 | ✓ | Super El Niño; Caribbean drought; pre-Mitch deficits |
| 1998 | negative | Grande Anse | -0.94 | 0/6 | — |  |
| 1999 | negative | Grande Anse | -1.15 | 0/6 | — |  |
| 2000 | negative | Grande Anse | -1.23 | 0/6 | — |  |
| 2001 | negative | Grande Anse | -0.34 | 0/6 | — |  |
| 2002 | negative | Centre | -0.96 | 0/6 | — |  |
| 2003 | negative | Nippes | -1.34 | 1/6 | ✓ |  |
| 2004 | negative | Grande Anse | -0.68 | 0/6 | — |  |
| 2005 | negative | Centre | 0.51 | 0/6 | — |  |
| 2006 | negative | Centre | -0.98 | 0/6 | — |  |
| 2007 | negative | Sud Est | -0.30 | 0/6 | — |  |
| 2008 | negative | Sud Est | -0.94 | 0/6 | — |  |
| 2009 | moderate | Sud Est | 0.65 | 0/6 | — | Moderate El Niño 2009-10 |
| 2010 | negative | Grande Anse | 0.64 | 0/6 | — |  |
| 2011 | negative | Nippes | 0.11 | 0/6 | — |  |
| 2012 | negative | Nippes | -1.24 | 0/6 | — |  |
| 2013 | negative | Nord Ouest | -1.93 | 6/6 | ✓ |  |
| 2014 | moderate | Sud Est | -2.04 | 3/6 | ✓ | Weak El Niño precursor; lead-up to 2015 crisis |
| 2015 | severe | Sud Est | -2.81 | 6/6 | ✓ | Very Strong El Niño; -39% rainfed maize / -44% beans nationally; national emergency (FEWS NET 2016) |
| 2016 | negative | Sud Est | -1.51 | 1/6 | ✓ |  |
| 2017 | negative | Grande Anse | 0.59 | 0/6 | — |  |
| 2018 | moderate | Sud Est | -2.12 | 6/6 | ✓ | Weak El Niño; postrera/automne impact |
| 2019 | negative | Sud Est | -1.66 | 5/6 | ✓ |  |
| 2020 | negative | Centre | -2.42 | 6/6 | ✓ |  |
| 2021 | negative | Nord Ouest | -1.35 | 2/6 | ✓ |  |
| 2022 | negative | Nord Ouest | -1.25 | 0/6 | — |  |
| 2023 | moderate | Sud Est | -0.59 | 0/6 | — | Strong El Niño; FEWS Aug 2023 Northwest + southern peninsula impact |
| 2024 | negative | Centre | 0.63 | 0/6 | — |  |
| 2025 | negative | Nord Ouest | -1.88 | 1/6 | ✓ |  |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI3<-1.3 ∧ RZSM<-1.0σ`** in DOY 152-227
- Precision: 0.33 [0.06–0.79] | Recall: 0.33 [0.06–0.79] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 1.82 [0.30–9.03]

| Year | Label | Worst dep | SPI-3 min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | severe | Sud Est | -2.81 | -2.93 | — | 6/6 | ✓ |
| 2016 | negative | Sud Est | -1.51 | -0.76 | — | 0/6 | — |
| 2017 | negative | Grande Anse | 0.59 | -0.15 | — | 0/6 | — |
| 2018 | moderate | Sud Est | -2.12 | -0.68 | — | 0/6 | — |
| 2019 | negative | Sud Est | -1.66 | -0.68 | — | 0/6 | — |
| 2020 | negative | Centre | -2.42 | -1.96 | — | 4/6 | ✓ |
| 2021 | negative | Nord Ouest | -1.35 | -0.65 | — | 0/6 | — |
| 2022 | negative | Nord Ouest | -1.25 | -1.36 | — | 0/6 | — |
| 2023 | moderate | Sud Est | -0.59 | -2.93 | — | 0/6 | — |
| 2024 | negative | Centre | 0.63 | -0.62 | — | 0/6 | — |
| 2025 | negative | Nord Ouest | -1.88 | -1.36 | — | 1/6 | ✓ |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.