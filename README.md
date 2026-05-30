# Central America & Caribbean Drought & Plant-Stress Dashboard

Sign-in-gated Streamlit dashboard tracking CHIRPS rainfall (with SPI-1/3/6),
SMAP L4 root-zone soil moisture, FAO WAPOR v3 L1 AETI evapotranspiration, and
IMERG-Late rainfall, broken out by ADM1 department. One codebase, currently
deployed for El Salvador (14 departamentos) and Haiti (10 départements); see
[Multi-country deployment](#multi-country-deployment) below.
Same envelope-rendering pattern as the existing FEWS dashboard.
Design plan: `~/.claude/plans/i-need-to-design-parsed-hare.md`.

## Run locally (no GEE, no auth needed)

```bash
pip install -r el_nino/requirements.txt

# Generate a synthetic dataset so the dashboard has something to render.
# Produces ~30 years of plausible per-departamento series with El Niño dips
# baked in for the historical analog years.
python -m el_nino.etl.run_etl synth --start 1995-01-01

# Launch the dashboard
streamlit run el_nino/dashboard/app.py
```

Open http://localhost:8501.

## Real data (Earth Engine)

```bash
# One-time per country: fetch the ADM1 polygons from FAO/GAUL via GEE.
# COUNTRY defaults to el_salvador; set COUNTRY=haiti to bootstrap Haiti.
python -m el_nino.etl.aoi.fetch_aoi
COUNTRY=haiti python -m el_nino.etl.aoi.fetch_aoi

# Pull a window for an indicator
python -m el_nino.etl.run_etl fetch --indicator chirps --start 2026-04-01

# Recompute climatology + anomaly + freshness
python -m el_nino.etl.run_etl finalize
```

GEE auth: `earthengine authenticate` once interactively, then set `GEE_PROJECT`
in `.env`. In Cloud Run, mount a service-account JSON via Secret Manager and set
`GEE_SERVICE_ACCOUNT_JSON`.

## Multi-country deployment

Country selection happens at startup via the `COUNTRY` env var (`el_salvador`
default, `haiti` supported). The same image is deployed twice — once per
country — with `COUNTRY` set as a Cloud Run env var. Each deployment writes to
its own GCS bucket (`${PROJECT}-${COUNTRY_CODE}-drought-dash`) so the two
countries are fully isolated at the data layer.

Country-specific assets and constants live in `el_nino/config.py` under the
`COUNTRIES` registry — AOI filename, map center/zoom, priority departments, UI
labels. Adding a third country is: append an entry, run
`COUNTRY=<key> python -m el_nino.etl.aoi.fetch_aoi` to bootstrap its geojson,
and deploy with the matching `COUNTRY` / `COUNTRY_CODE` env vars. See
[deploy/README.md](deploy/README.md) for the exact commands.

Trigger windows and synthetic-data phenology in `etl/triggers.py`,
`etl/synth.py`, and `experiments/trigger_calibration.py` are currently
El Salvador-tuned; grep for `TODO(haiti-calibration)` to find the spots that
need country-specific values in the follow-up calibration PR.

## Deploy to Google Cloud

See [deploy/README.md](deploy/README.md) for the full, scripted, idempotent
deployment (per-country). Four steps per country: `setup_infra.sh`,
`cloudbuild.yaml`, `deploy_job.sh`, `schedule.sh` — each driven by `COUNTRY`
and `COUNTRY_CODE` env vars so the same scripts deploy ES (defaults) and HT.

**Auth** — in `secrets.toml` (mounted from Secret Manager), configure the
`[auth.google]` OIDC client per Streamlit's docs; set `ALLOWED_EMAILS` env var.

## Layout

```
el_nino/
├── config.py                  # paths, env vars, baseline period
├── etl/
│   ├── run_etl.py             # CLI orchestrator
│   ├── gee.py                 # EE init
│   ├── storage.py             # parquet upsert helpers
│   ├── climatology.py         # per-DOY fences
│   ├── enso.py                # NOAA ONI fetcher
│   ├── freshness.py           # writes data/freshness.json
│   ├── triggers.py            # placeholder; pending calibration
│   ├── synth.py               # synthetic data for local dev
│   ├── aoi/
│   │   ├── fetch_aoi.py       # one-time GEE FAO/GAUL fetch (per country)
│   │   ├── departamentos_es.geojson  # El Salvador ADM1 polygons
│   │   └── departamentos_ht.geojson  # Haiti ADM1 polygons (bootstrap with COUNTRY=haiti)
│   └── indicators/
│       ├── base.py
│       ├── chirps.py          # CHIRPS v3 + SPI
│       ├── smap.py            # SMAP L4 RZSM
│       ├── wapor.py           # FAO WAPOR v3 L1 AETI (dekadal ET)
│       └── imerg.py           # IMERG-Late
├── dashboard/
│   ├── app.py                 # Streamlit entry (3 tabs)
│   ├── auth.py                # Streamlit native OIDC gate (no-op locally)
│   ├── data.py                # DuckDB / parquet read layer
│   ├── charts.py              # climatology envelope helpers
│   ├── drought_status.py      # U.S. Drought Monitor classification
│   └── freshness.py           # badges + Today marker + awaiting-data band
├── experiments/               # trigger calibration notebook (TBD)
├── deploy/                    # Cloud Build / Cloud Run wiring (TBD)
├── data/                      # local-only, gitignored
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Status

- Local synthetic-data flow works end-to-end without GEE or auth configured.
- Real GEE fetchers wired but require `earthengine authenticate` + AOI fetch.
- Alert dispatch intentionally disabled until the trigger-calibration experiment
  picks operating thresholds against historical El Niño events
  (see [el_nino_agricultural_risks.md](el_nino_agricultural_risks.md)).
