# Drought & El Niño Monitor

A Streamlit dashboard that tracks rainfall, soil moisture, evapotranspiration,
and a calibrated drought-alert trigger at the ADM1 (department / departamento)
level. Two countries are wired up today — **El Salvador** (14 departamentos)
and **Haiti** (10 départements) — from a single codebase with country
selection at startup via the `COUNTRY` env var.

Indicators (refresh cadence in parentheses):

| Source | Variable | Cadence |
|---|---|---|
| [CHIRPS v3](https://www.chc.ucsb.edu/data/chirps) (UCSB) | Pentadal rainfall + SPI-1/3/6 | 3 days (GEE) + UCSB CHIRPS-Prelim fill for the last few weeks |
| [NOAA GFS 0.25°](https://www.nco.ncep.noaa.gov/pmb/products/gfs/) | 15-day rainfall forecast | daily |
| [SMAP L4](https://smap.jpl.nasa.gov/) (NASA) | Root-zone soil moisture (0–100 cm) | 3 days |
| [FAO WAPOR v3](https://wapor.apps.fao.org/) | L1 AETI evapotranspiration (~300 m, dekadal) | 10 days |
| [IMERG-Late V07](https://gpm.nasa.gov/data/imerg) (NASA) | Daily rainfall (event scale) | daily |
| [NOAA ONI](https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php) | ENSO index for analog-year overlay | monthly |

Architecture: **one repo, one Docker image, two Cloud Run services** (one per
country) each backed by its own GCS bucket. A separate static landing page
([landing/](landing/)) lets users pick a country.

Design plan: `~/.claude/plans/i-need-to-design-parsed-hare.md`. Background on
El Niño impacts: [el_nino_agricultural_risks.md](el_nino_agricultural_risks.md).

---

## Local quickstart

### Prerequisites

```bash
pip install -r requirements.txt
# or, in the existing conda env:
conda activate haiti
```

For real data you also need a Google Earth Engine project — see [GEE auth](#gee-auth) below.

### Option A — synthetic data (no GEE, no auth)

Fastest path to see the UI working. Generates ~30 years of plausible
per-departamento series with El Niño dips baked in for historical analog years.

```bash
# (from the repo root: /home/mmann1123/Documents/github/)
python -m el_nino.etl.run_etl synth --start 1995-01-01

# Launch with default country (El Salvador)
streamlit run el_nino/dashboard/app.py

# ...or Haiti
COUNTRY=haiti streamlit run el_nino/dashboard/app.py
```

Open http://localhost:8501.

The synthetic seasonal cycle is ES-tuned (primera/postrera, canícula). Haiti
still renders cleanly with synth but the phenology is approximate; use Option B
for accurate Haiti data.

### Option B — real data via Earth Engine

**El Salvador** (defaults):

```bash
# One-time: bootstrap the AOI polygons from FAO/GAUL
python -m el_nino.etl.aoi.fetch_aoi

# Full historical backfill from 1981 (CHIRPS) — ~15 min
python -m el_nino.etl.run_etl backfill --indicator chirps --start 1981-01-01
python -m el_nino.etl.run_etl backfill --indicator smap   --start 2015-04-01
python -m el_nino.etl.run_etl backfill --indicator wapor  --start 1981-01-01
python -m el_nino.etl.run_etl backfill --indicator imerg  --start 2000-06-01

# Fill the last few weeks (CHIRPS V3 has ~28-day latency; UCSB CHIRPS-Prelim
# is ~3-day latency) and pull the 15-day GFS forecast
python -m el_nino.etl.run_etl prelim
python -m el_nino.etl.run_etl forecast

# Recompute climatology, anomaly z-scores, and freshness
python -m el_nino.etl.run_etl finalize

streamlit run el_nino/dashboard/app.py
```

**Haiti**: same commands, prefix everything with `COUNTRY=haiti`:

```bash
COUNTRY=haiti python -m el_nino.etl.aoi.fetch_aoi
COUNTRY=haiti python -m el_nino.etl.run_etl backfill --indicator chirps --start 1981-01-01
COUNTRY=haiti python -m el_nino.etl.run_etl backfill --indicator smap   --start 2015-04-01
COUNTRY=haiti python -m el_nino.etl.run_etl backfill --indicator wapor  --start 1981-01-01
COUNTRY=haiti python -m el_nino.etl.run_etl backfill --indicator imerg  --start 2000-06-01
COUNTRY=haiti python -m el_nino.etl.run_etl prelim
COUNTRY=haiti python -m el_nino.etl.run_etl forecast
COUNTRY=haiti python -m el_nino.etl.run_etl finalize
COUNTRY=haiti streamlit run el_nino/dashboard/app.py
```

Both countries can share the same local `data/` directory — country filtering
is applied at read time (see [`config.country_departments()`](config.py)) so
the dashboards never cross-pollute.

### GEE auth

```bash
earthengine authenticate     # one-time, interactive
echo "GEE_PROJECT=your-gee-project" >> .env
```

In Cloud Run, mount a service-account JSON via Secret Manager and set
`GEE_SERVICE_ACCOUNT_JSON` instead.

---

## Country switching

Everything country-specific lives in [`config.py`](config.py) under the
`COUNTRIES` registry. The active country's entry is exposed as `config.CC` and
drives:

- AOI geojson filename → `departamentos_es.geojson` / `departamentos_ht.geojson`
- Map center + zoom
- Native ADM1 term (`departamento` / `département`) used in UI labels and tooltips
- Priority departments (the drought-vulnerable focal set for alerts and calibration)
- Silking / growth window for the calibrated trigger
- Labeled historical drought events for calibration scoring

Adding a third country = append one entry, run `COUNTRY=<key> python -m
el_nino.etl.aoi.fetch_aoi`, and the same code paths handle it.

---

## How data refreshes

**In production** (Cloud Run + Cloud Scheduler):

| Job | Cron (UTC) | Purpose |
|---|---|---|
| `${CC}-prelim` | 09:00 daily | Fill the GEE → today gap with UCSB CHIRPS-Prelim |
| `${CC}-forecast` | 09:15 daily | Pull the latest 15-day GFS rainfall forecast |
| `${CC}-fetch-chirps` | 09:30 every 3 days | CHIRPS V3 pentad refresh |
| `${CC}-fetch-smap` | 09:45 every 3 days | SMAP L4 root-zone soil moisture |
| `${CC}-fetch-wapor` | 10:00 every 3 days | FAO WAPOR ETa |
| `${CC}-fetch-imerg` | 10:15 daily | IMERG-Late rainfall |

See [deploy/schedule.sh](deploy/schedule.sh) for the scheduler entries.

**Interactively** (the "🔄 Check for new data" sidebar button):

Triggers the same flow in a single click — GEE catch-up → CHIRPS-Prelim gap
fill → GFS forecast → CHIRPS SPI recompute. Rate-limited to **once per 12
hours across all users** per country via a lock file at
`STORAGE_ROOT/last_refresh.json` (see [dashboard/refresh_lock.py](dashboard/refresh_lock.py)).

---

## Trigger calibration

Alerts fire when **SPI-3 < threshold AND SMAP root-zone anomaly < threshold**
in any one of the country's priority departments during the silking window.
Operating points are calibrated per-country against labeled historical drought
events:

| | El Salvador | Haiti |
|---|---|---|
| Window | DOY 196-227 (mid-Jul to mid-Aug) | DOY 152-227 (Jun 1 to Aug 15) |
| SPI-3 threshold | < −1.5 | < −1.3 |
| SMAP RZSM threshold | < −0.5σ | < −0.5σ |
| Severe recall | 100% (catches 2015) | 100% (catches 2015) |
| Precision | 100% | 40% |
| FP / decade | 0.0 | 2.7 |

Full reports:
- [experiments/trigger_calibration_report_es.md](experiments/trigger_calibration_report_es.md)
- [experiments/trigger_calibration_report_ht.md](experiments/trigger_calibration_report_ht.md)

Re-run after each annual data refresh:

```bash
python -m el_nino.experiments.trigger_calibration                # ES
COUNTRY=haiti python -m el_nino.experiments.trigger_calibration  # HT
```

---

## Deploy to Google Cloud

Three scripted, idempotent steps per country plus a one-time image build. See
[deploy/README.md](deploy/README.md) for the full guide; the short version:

```bash
# El Salvador (defaults)
PROJECT=haiti-fews-mmann1123 bash deploy/setup_infra.sh
gcloud builds submit --config deploy/cloudbuild.yaml .
PROJECT=haiti-fews-mmann1123 bash deploy/deploy_job.sh
PROJECT=haiti-fews-mmann1123 bash deploy/schedule.sh

# Haiti (two extra env vars per call)
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash deploy/setup_infra.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash deploy/deploy_job.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash deploy/schedule.sh
```

Each country gets its own bucket, service account, Cloud Run Job, and six
Scheduler entries. The shared Docker image is built once.

**Landing page**: a static HTML page with a video background lives in
[landing/](landing/) — two country cards that link to each country's Cloud Run
URL. Deploy as a third tiny Cloud Run service (Dockerfile pending, see the
landing folder for the static asset and the design).

---

## Layout

```
el_nino/
├── config.py                 # COUNTRY registry, paths, baselines
├── README.md                 # this file
├── el_nino_agricultural_risks.md   # background on ES/HT El Niño impacts
├── notes.md                  # ES agronomy notes
├── etl/
│   ├── run_etl.py            # CLI: synth | fetch | backfill | prelim | forecast | finalize | climatology | enso
│   ├── refresh_check.py      # "Check for new data" orchestrator (GEE + prelim + forecast)
│   ├── chirps_prelim.py      # UCSB CHIRPS-Prelim daily-TIFF gap fill
│   ├── triggers.py           # CalibratedTrigger runtime evaluator (country-aware)
│   ├── synth.py              # synthetic data for local dev
│   ├── storage.py / climatology.py / enso.py / freshness.py / gee.py
│   ├── aoi/
│   │   ├── fetch_aoi.py      # one-time FAO/GAUL bootstrap per country
│   │   ├── departamentos_es.geojson
│   │   └── departamentos_ht.geojson
│   └── indicators/           # chirps.py / smap.py / wapor.py / imerg.py
├── dashboard/
│   ├── app.py                # Streamlit entry (Overview / Indicator Detail / Year Compare)
│   ├── alerts.py             # drought-alert banner + confidence panel
│   ├── map.py                # departamento choropleth (CARTO Positron)
│   ├── charts.py             # climatology envelope figures
│   ├── data.py               # parquet read layer (country-filtered)
│   ├── drought_status.py     # USDM classification + plain-language labels
│   ├── freshness.py          # data-freshness badges
│   ├── status.py             # current-status helpers
│   ├── auth.py               # Streamlit OIDC gate (disabled by default — public)
│   ├── refresh_lock.py       # 12-hour cross-user rate limit on "Check for new data"
│   └── site_footer.py        # GWU mark + data attribution + disclaimer
├── experiments/
│   ├── trigger_calibration.py
│   ├── trigger_calibration_report_es.md
│   └── trigger_calibration_report_ht.md
├── deploy/                   # Cloud Build + Cloud Run + Cloud Scheduler scripts (see deploy/README.md)
├── landing/
│   └── index.html            # static landing page (video bg, two country cards)
├── static/                   # GW_GE.png logo + landing video
├── data/                     # local-only, gitignored
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Attribution

Created by **Michael Mann, PhD** — George Washington University, Department of
Geography & Environment, Columbian College of Arts & Sciences. Independent
dashboard; not affiliated with or endorsed by the data providers listed above.
Indicators and forecasts are provided without warranty of accuracy or fitness
for any purpose.
