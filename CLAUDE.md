# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit dashboard + ETL pipeline that tracks rainfall, soil moisture,
evapotranspiration, and a calibrated drought-alert trigger at the ADM1
(department) level. One codebase serves two countries — **El Salvador** and
**Haiti** — selected at startup via the `COUNTRY` env var. See [README.md](README.md)
for the full data-source table and live-deployment URLs.

## Critical: run as a package from the *parent* directory

This repo is the Python package `el_nino`. Nothing runs from the repo root —
everything runs from the parent (`/home/mmann1123/Documents/github/`) so that
`el_nino.*` imports resolve:

```bash
python -m el_nino.etl.run_etl <subcommand>      # ETL CLI
streamlit run el_nino/dashboard/app.py          # dashboard
```

[dashboard/app.py](dashboard/app.py) self-inserts the parent into `sys.path`
because Streamlit invokes it as a script, not a package member. There is no
`setup.py`/`pyproject.toml` and the package is not pip-installed; `PYTHONPATH`
(set to `/app` in the Dockerfile) is what makes the imports work in production.

## Common commands

```bash
pip install -r requirements.txt            # or: conda activate haiti

# Fastest path to a working UI — no GEE, no auth (~30yr of plausible series):
python -m el_nino.etl.run_etl synth --start 1995-01-01
streamlit run el_nino/dashboard/app.py

# Haiti instead of the default El Salvador — prefix every command:
COUNTRY=haiti python -m el_nino.etl.run_etl synth --start 1995-01-01
COUNTRY=haiti streamlit run el_nino/dashboard/app.py

# Real data (requires `earthengine authenticate` + GEE_PROJECT in .env):
python -m el_nino.etl.aoi.fetch_aoi                                   # one-time AOI bootstrap
python -m el_nino.etl.run_etl backfill --indicator chirps --start 1981-01-01
python -m el_nino.etl.run_etl prelim                                 # UCSB CHIRPS-Prelim gap fill
python -m el_nino.etl.run_etl forecast                               # NOAA GFS 15-day
python -m el_nino.etl.run_etl finalize                               # SPI + climatology + anomaly + freshness

# Re-run trigger calibration after a data refresh:
python -m el_nino.experiments.trigger_calibration                    # ES
COUNTRY=haiti python -m el_nino.experiments.trigger_calibration      # HT
```

### Tests

```bash
# From the repo root (pytest.ini lives here):
python -m pytest                         # whole suite
python -m pytest tests/test_triggers.py  # one module
python -m pytest -k window               # one pattern
# Or from the parent dir, like the rest of the project:
python -m pytest el_nino
```

Tests live in [tests/](tests/) and cover pure logic only — no GEE, network, or
real `data/` access. The `tmp_storage` fixture in [tests/conftest.py](tests/conftest.py)
monkeypatches `config`'s storage paths to a temp dir, so a test run never
touches the developer's `./data`. Use it for anything that reads/writes
parquets. There is no linter config or build step.

## ETL subcommands ([etl/run_etl.py](etl/run_etl.py))

`synth` (local fake data) · `fetch` (one small GEE window) · `backfill`
(chunked historical pull) · `prelim` (CHIRPS-Prelim gap fill) · `forecast`
(GFS) · `climatology` · `enso` (NOAA ONI) · `finalize` (SPI recompute →
climatology → anomaly z-scores → freshness). `synth` ends by calling `finalize`.

## Architecture

**Data flow:** GEE (or `synth`) → per-indicator/per-department raw parquets →
climatology (per-day-of-year percentile fences) → anomaly z-scores attached
back onto raw → `freshness.json`. The dashboard reads those parquets at request
time, filtered to the active country.

**Layers:**
- [config.py](config.py) — the single source of country differences. The
  `COUNTRIES` registry holds AOI filename, map center, ADM1 term, priority
  departments, silking window, and labeled historical drought events per
  country; the active entry is exposed as `config.CC`. **Add a country** by
  appending one entry and running `COUNTRY=<key> python -m el_nino.etl.aoi.fetch_aoi`.
- [etl/storage.py](etl/storage.py) — all reads/writes go through `STORAGE_ROOT`,
  which is a local path by default and a gcsfuse mount (`/mnt/gcs`) in Cloud
  Run. Same code, no branching. `upsert_raw` dedups on `(date, departamento)`.
- [etl/indicators/base.py](etl/indicators/base.py) — `Indicator` ABC. Each
  indicator (chirps/smap/wapor/imerg) declares `name`, `value_columns`,
  `primary_column`, a `FreshnessSpec` derived from its cadence, and chunk
  sizes tuned to stay under GEE's ~5000-feature `getInfo()` ceiling. `backfill`
  retries by halving the chunk on `EEException`. Register new ones in
  `etl/indicators/__init__.py`'s `INDICATORS` dict.
- [etl/triggers.py](etl/triggers.py) — `CalibratedTrigger` fires when SPI-3 AND
  SMAP root-zone anomaly are both below per-country thresholds during the
  silking window. Operating points live in `TRIGGERS_BY_COUNTRY`, calibrated by
  [experiments/trigger_calibration.py](experiments/trigger_calibration.py)
  against `config.CC['labeled_events']`.
- [etl/refresh_check.py](etl/refresh_check.py) — backs the dashboard's "Check
  for new data" button. One cheap `aggregate_max` getInfo per indicator to
  decide whether a heavier fetch is needed; rate-limited to once per 12h across
  all users via [dashboard/refresh_lock.py](dashboard/refresh_lock.py).
- [dashboard/](dashboard/) — Streamlit app (Overview / Indicator Detail / Year
  Compare). `data.py` is the country-filtered parquet read layer; `auth.py` is
  an OIDC gate disabled by default (public deploys).

**Country data co-mingling:** ES and HT can share one local `STORAGE_ROOT`.
Cross-pollution is prevented at *read* time via `config.country_departments()`
(derived from the AOI geojson's `ADM1_NAME`s), not by separate directories.
Department names must match GAUL `ADM1_NAME` exactly (spaces, not hyphens).

**Deployment:** one Docker image, two Cloud Run services (one per country),
each with its own GCS bucket and six Cloud Scheduler ETL jobs. The image's
default `CMD` is the dashboard; the Cloud Run Job overrides it with
`python -m el_nino.etl.run_etl ...`. See [deploy/README.md](deploy/README.md).

## GEE auth

Locally: `earthengine authenticate` once, then `GEE_PROJECT=...` in `.env`. In
Cloud Run: a service-account JSON via Secret Manager in
`GEE_SERVICE_ACCOUNT_JSON`. The `synth` path needs neither — `earthengine-api`
is imported lazily inside indicator methods so it can be absent locally.
