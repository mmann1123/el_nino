# Trigger Calibration Report — Haiti, Printemps

Generated from `el_nino/experiments/trigger_calibration.py`.

**Country:** Haiti (HT).
**Region:** all 10 départements; a year fires if any one of them meets the conditions.
**Season:** Printemps. **Windows swept:** DOY 135-212, DOY 154-192, DOY 135-258.
**Labels:** the season's `labeled_events` in `config.CC['seasons']`, traced to highlighted sources in `experiments/evidence/`.

**Severe positive(s):** 2015 (El Niño drought, losses in all parts of the country (FEWS NET Feb 2016)).
**Moderate positives:** 1997, 2011, 2012, 2014, 2018, 2019, 2020, 2022, 2023, 2024, 2025.
**Documented normal seasons:** 2009, 2010, 2013, 2016, 2021.
**Excluded (non-drought losses, e.g. hurricanes):** 2017.
**Negatives:** the documented normal seasons only; unlabeled years are not scored.
**Geo hits:** positive years where the alert fired in at least one department the evidence names, out of positive years that name any. Unnamed departments are not counted against the alert.

## Confidence intervals

All point estimates here come from small samples (the longest series, CHIRPS-only, has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported alongside the point estimate to make the uncertainty visible:

- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).
- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate given exposure = number of negative years / 10.

## SPI only (long baseline, 1981+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |
|---|---:|---:|---:|---:|---|---|---|---|---:|
| SPI-3<-0.8 in DOY 135-212 | 10 | 3 | 2 | 2 | 0.77 [0.50–0.92] | 0.83 [0.55–0.95] | 1.00 [0.21–1.00] | 6.00 [1.24–17.53] | 2/4 |
| SPI-3<-0.8 in DOY 154-192 | 8 | 2 | 4 | 3 | 0.80 [0.49–0.94] | 0.67 [0.39–0.86] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-0.8 in DOY 135-258 | 11 | 4 | 1 | 1 | 0.73 [0.48–0.89] | 0.92 [0.65–0.99] | 1.00 [0.21–1.00] | 8.00 [2.18–20.48] | 3/4 |
| SPI-3<-1.0 in DOY 135-212 | 10 | 2 | 2 | 3 | 0.83 [0.55–0.95] | 0.83 [0.55–0.95] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-1.0 in DOY 154-192 | 8 | 2 | 4 | 3 | 0.80 [0.49–0.94] | 0.67 [0.39–0.86] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-1.0 in DOY 135-258 | 11 | 3 | 1 | 2 | 0.79 [0.52–0.92] | 0.92 [0.65–0.99] | 1.00 [0.21–1.00] | 6.00 [1.24–17.53] | 3/4 |
| SPI-3<-1.3 in DOY 135-212 | 8 | 2 | 4 | 3 | 0.80 [0.49–0.94] | 0.67 [0.39–0.86] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-1.3 in DOY 154-192 | 5 | 2 | 7 | 3 | 0.71 [0.36–0.92] | 0.42 [0.19–0.68] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-1.3 in DOY 135-258 | 9 | 3 | 3 | 2 | 0.75 [0.47–0.91] | 0.75 [0.47–0.91] | 1.00 [0.21–1.00] | 6.00 [1.24–17.53] | 3/4 |
| SPI-3<-1.5 in DOY 135-212 | 7 | 2 | 5 | 3 | 0.78 [0.45–0.94] | 0.58 [0.32–0.81] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-1.5 in DOY 154-192 | 4 | 2 | 8 | 3 | 0.67 [0.30–0.90] | 0.33 [0.14–0.61] | 1.00 [0.21–1.00] | 4.00 [0.48–14.45] | 2/4 |
| SPI-3<-1.5 in DOY 135-258 | 8 | 3 | 4 | 2 | 0.73 [0.43–0.90] | 0.67 [0.39–0.86] | 1.00 [0.21–1.00] | 6.00 [1.24–17.53] | 3/4 |
| SPI-3<-1.7 in DOY 135-212 | 5 | 1 | 7 | 4 | 0.83 [0.44–0.97] | 0.42 [0.19–0.68] | 1.00 [0.21–1.00] | 2.00 [0.05–11.14] | 2/4 |
| SPI-3<-1.7 in DOY 154-192 | 3 | 1 | 9 | 4 | 0.75 [0.30–0.95] | 0.25 [0.09–0.53] | 1.00 [0.21–1.00] | 2.00 [0.05–11.14] | 2/4 |
| SPI-3<-1.7 in DOY 135-258 | 8 | 1 | 4 | 4 | 0.89 [0.57–0.98] | 0.67 [0.39–0.86] | 1.00 [0.21–1.00] | 2.00 [0.05–11.14] | 3/4 |

## Combined SPI ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)

| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |
|---|---:|---:|---:|---:|---|---|---|---|---:|
| SPI-3<-1.0 ∧ RZSM<-0.5σ | 6 | 1 | 2 | 1 | 0.86 [0.49–0.97] | 0.75 [0.41–0.93] | 1.00 [0.21–1.00] | 5.00 [0.13–27.86] | 2/4 |
| SPI-3<-1.0 ∧ RZSM<-0.5σ ∧ ETa<0 | 5 | 1 | 3 | 1 | 0.83 [0.44–0.97] | 0.62 [0.31–0.86] | 0.00 [0.00–0.79] | 5.00 [0.13–27.86] | 1/4 |
| SPI-3<-1.0 ∧ RZSM<-1.0σ | 5 | 0 | 3 | 2 | 1.00 [0.57–1.00] | 0.62 [0.31–0.86] | 1.00 [0.21–1.00] | 0.00 [0.00–18.44] | 2/4 |
| SPI-3<-1.0 ∧ RZSM<-1.0σ ∧ ETa<0 | 4 | 0 | 4 | 2 | 1.00 [0.51–1.00] | 0.50 [0.22–0.78] | 0.00 [0.00–0.79] | 0.00 [0.00–18.44] | 1/4 |
| SPI-3<-1.0 ∧ RZSM<-1.5σ | 3 | 0 | 5 | 2 | 1.00 [0.44–1.00] | 0.38 [0.14–0.69] | 1.00 [0.21–1.00] | 0.00 [0.00–18.44] | 1/4 |
| SPI-3<-1.0 ∧ RZSM<-1.5σ ∧ ETa<0 | 2 | 0 | 6 | 2 | 1.00 [0.34–1.00] | 0.25 [0.07–0.59] | 0.00 [0.00–0.79] | 0.00 [0.00–18.44] | 0/4 |
| SPI-3<-1.3 ∧ RZSM<-0.5σ | 5 | 1 | 3 | 1 | 0.83 [0.44–0.97] | 0.62 [0.31–0.86] | 1.00 [0.21–1.00] | 5.00 [0.13–27.86] | 2/4 |
| SPI-3<-1.3 ∧ RZSM<-0.5σ ∧ ETa<0 | 4 | 1 | 4 | 1 | 0.80 [0.38–0.96] | 0.50 [0.22–0.78] | 0.00 [0.00–0.79] | 5.00 [0.13–27.86] | 1/4 |
| SPI-3<-1.3 ∧ RZSM<-1.0σ | 4 | 0 | 4 | 2 | 1.00 [0.51–1.00] | 0.50 [0.22–0.78] | 1.00 [0.21–1.00] | 0.00 [0.00–18.44] | 2/4 |
| SPI-3<-1.3 ∧ RZSM<-1.0σ ∧ ETa<0 | 3 | 0 | 5 | 2 | 1.00 [0.44–1.00] | 0.38 [0.14–0.69] | 0.00 [0.00–0.79] | 0.00 [0.00–18.44] | 1/4 |
| SPI-3<-1.3 ∧ RZSM<-1.5σ | 2 | 0 | 6 | 2 | 1.00 [0.34–1.00] | 0.25 [0.07–0.59] | 1.00 [0.21–1.00] | 0.00 [0.00–18.44] | 1/4 |
| SPI-3<-1.3 ∧ RZSM<-1.5σ ∧ ETa<0 | 1 | 0 | 7 | 2 | 1.00 [0.21–1.00] | 0.12 [0.02–0.47] | 0.00 [0.00–0.79] | 0.00 [0.00–18.44] | 0/4 |
| SPI-3<-1.5 ∧ RZSM<-0.5σ | 4 | 1 | 4 | 1 | 0.80 [0.38–0.96] | 0.50 [0.22–0.78] | 1.00 [0.21–1.00] | 5.00 [0.13–27.86] | 2/4 |
| SPI-3<-1.5 ∧ RZSM<-0.5σ ∧ ETa<0 | 3 | 1 | 5 | 1 | 0.75 [0.30–0.95] | 0.38 [0.14–0.69] | 0.00 [0.00–0.79] | 5.00 [0.13–27.86] | 1/4 |
| SPI-3<-1.5 ∧ RZSM<-1.0σ | 3 | 0 | 5 | 2 | 1.00 [0.44–1.00] | 0.38 [0.14–0.69] | 1.00 [0.21–1.00] | 0.00 [0.00–18.44] | 2/4 |
| SPI-3<-1.5 ∧ RZSM<-1.0σ ∧ ETa<0 | 2 | 0 | 6 | 2 | 1.00 [0.34–1.00] | 0.25 [0.07–0.59] | 0.00 [0.00–0.79] | 0.00 [0.00–18.44] | 1/4 |
| SPI-3<-1.5 ∧ RZSM<-1.5σ | 2 | 0 | 6 | 2 | 1.00 [0.34–1.00] | 0.25 [0.07–0.59] | 1.00 [0.21–1.00] | 0.00 [0.00–18.44] | 1/4 |
| SPI-3<-1.5 ∧ RZSM<-1.5σ ∧ ETa<0 | 1 | 0 | 7 | 2 | 1.00 [0.21–1.00] | 0.12 [0.02–0.47] | 0.00 [0.00–0.79] | 0.00 [0.00–18.44] | 0/4 |

## Per-year detail (best SPI-only configuration)

**Recommended SPI-only trigger:** `SPI-3<-1.7 in DOY 135-258`
- Precision: 0.89 [0.57–0.98] | Recall: 0.67 [0.39–0.86] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 2.00 [0.05–11.14]

| Year | Label | Worst dep | Min SPI | Deps fired | Fired? | Notes |
|---|---|---|---:|:---:|:---:|---|
| 1997 | moderate | Nippes | -1.82 | 2/10 | ✓ | Prolonged first-half drought affected all crops (GIEWS Dec 1997) |
| 2009 | normal | Nippes | -0.92 | 0/10 | — | Abundant, well-distributed rain; NW mountains only poor harvest (GIEWS 2009-10) |
| 2010 | normal | Nord Est | 0.09 | 0/10 | — | Spring rains abundant and beneficial (GIEWS Aug 2010) |
| 2011 | moderate | Nord | -2.19 | 4/10 | ✓ | Dry spring; North, Northwest, Northeast, High Central Plateau worst (GIEWS Feb 2012) |
| 2012 | moderate | Nippes | -1.16 | 0/10 | — | Dry May–early June cut maize yields (GIEWS Aug 2012) |
| 2013 | normal | Nord Est | -2.17 | 9/10 | ✓ | Maize yields recovered (GIEWS Oct 2013) |
| 2014 | moderate | Sud Est | -1.99 | 3/10 | ✓ | Jun–Aug dryness; Central Plateau, North-West, South-East, West (GIEWS Dec 2014) |
| 2015 | severe | Ouest | -2.56 | 10/10 | ✓ | El Niño drought, losses in all parts of the country (FEWS NET Feb 2016) |
| 2016 | normal | Nord Est | -1.66 | 0/10 | — | Good harvest after El Niño ended (GIEWS Oct 2016) |
| 2018 | moderate | Centre | -1.95 | 3/10 | ✓ | June dryness; maize 13% below 5-yr avg; Artibonite, Centre (GIEWS Dec 2018) |
| 2019 | moderate | Centre | -2.12 | 4/10 | ✓ | Apr–Aug deficit; production ~10% down (GIEWS Jun 2020) |
| 2020 | moderate | Nord Est | -2.83 | 7/10 | ✓ | Apr–Jul deficit hit main maize and paddy (GIEWS Jun 2021) |
| 2021 | normal | Nord Est | -1.60 | 0/10 | — | Abundant Mar–Apr rain (GIEWS Jun 2021) |
| 2022 | moderate | Grande Anse | -1.20 | 0/10 | — | Below-average May–June rain; below-average harvest (GIEWS Aug 2022) |
| 2023 | moderate | Nord Est | -1.46 | 0/10 | — | Apr–Sep rain 50% below average (FEWS NET Oct 2023) |
| 2024 | moderate | Sud Est | 0.00 | 0/10 | — | Mar–May dry spells hurt establishment (GIEWS Oct 2024) |
| 2025 | moderate | Nord Est | -1.87 | 1/10 | ✓ | Main season hit by dry weather (GIEWS Dec 2025) |

## Recommended combined trigger (where SMAP/WAPOR available)

**`SPI-3<-1.0 ∧ RZSM<-1.0σ`** in DOY 135-212
- Precision: 1.00 [0.57–1.00] | Recall: 0.62 [0.31–0.86] | Severe recall: 1.00 [0.21–1.00] | FP/decade: 0.00 [0.00–18.44]

| Year | Label | Worst dep | SPI min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |
|---|---|---|---:|---:|---:|:---:|:---:|
| 2015 | severe | Ouest | -2.56 | -2.94 | — | 10/10 | ✓ |
| 2016 | normal | Sud Est | -0.07 | -0.76 | — | 0/10 | — |
| 2018 | moderate | Ouest | -0.77 | -1.36 | — | 0/10 | — |
| 2019 | moderate | Ouest | -1.53 | -0.98 | — | 0/10 | — |
| 2020 | moderate | Nord Est | -2.83 | -1.96 | — | 7/10 | ✓ |
| 2021 | normal | Nord Est | -1.60 | -0.90 | — | 0/10 | — |
| 2022 | moderate | Nord Ouest | -1.04 | -1.20 | — | 1/10 | ✓ |
| 2023 | moderate | Nord Est | -1.46 | -2.94 | — | 10/10 | ✓ |
| 2024 | moderate | Sud Est | 0.00 | -0.85 | — | 0/10 | — |
| 2025 | moderate | Nord Est | -1.62 | -1.33 | — | 5/10 | ✓ |

## Operational recommendations

1. Use the **SPI-only** trigger for the long-baseline alert (fires whenever SPI falls below threshold inside the window).
2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.
3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.