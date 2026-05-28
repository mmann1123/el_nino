# El Salvador Drought & Plant-Stress Dashboard

Sign-in-gated Streamlit dashboard tracking CHIRPS rainfall (with SPI-1/3/6),
SMAP L4 root-zone soil moisture, SSEBop v6 ETa anomaly, and IMERG-Late rainfall
for the 14 departamentos of El Salvador. Same envelope-rendering pattern as the
existing FEWS dashboard. Design plan: `~/.claude/plans/i-need-to-design-parsed-hare.md`.

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
# One-time: fetch the 14 departamento polygons from FAO/GAUL via GEE
python -m el_nino.etl.aoi.fetch_aoi

# Pull a window for an indicator
python -m el_nino.etl.run_etl fetch --indicator chirps --start 2026-04-01

# Recompute climatology + anomaly + freshness
python -m el_nino.etl.run_etl finalize
```

GEE auth: `earthengine authenticate` once interactively, then set `GEE_PROJECT`
in `.env`. In Cloud Run, mount a service-account JSON via Secret Manager and set
`GEE_SERVICE_ACCOUNT_JSON`.

## Deploy to Google Cloud (sketch — see [deploy/](deploy/))

1. Create GCS bucket: `gs://es-drought-dash`.
2. Build & push the image: `gcloud builds submit el_nino --tag gcr.io/$PROJECT/es-drought-dash`.
3. **Dashboard** (Cloud Run Service) — mount the bucket via gcsfuse at `/mnt/gcs`:
   ```bash
   gcloud run deploy es-drought-dash \
       --image gcr.io/$PROJECT/es-drought-dash \
       --add-volume name=gcs,type=cloud-storage,bucket=es-drought-dash \
       --add-volume-mount volume=gcs,mount-path=/mnt/gcs \
       --set-env-vars STORAGE_ROOT=/mnt/gcs,AUTH_MODE=oidc \
       --set-secrets GEE_SERVICE_ACCOUNT_JSON=gee-sa:latest \
       --region us-central1
   ```
4. **ETL** (Cloud Run Job, scheduled every 3 days):
   ```bash
   gcloud run jobs deploy es-drought-etl \
       --image gcr.io/$PROJECT/es-drought-dash \
       --command python --args="-m,el_nino.etl.run_etl,fetch,--indicator,chirps" \
       --add-volume name=gcs,type=cloud-storage,bucket=es-drought-dash \
       --add-volume-mount volume=gcs,mount-path=/mnt/gcs \
       --region us-central1
   gcloud scheduler jobs create http es-drought-etl-cron --schedule="0 9 */3 * *" \
       --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT/jobs/es-drought-etl:run" \
       --oauth-service-account-email=$SA
   ```
5. **Auth** — in `secrets.toml` (mounted from Secret Manager), configure the
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
│   │   ├── fetch_aoi.py       # one-time GEE FAO/GAUL fetch
│   │   └── departamentos.geojson  (gitignored; produced by fetch_aoi)
│   └── indicators/
│       ├── base.py
│       ├── chirps.py          # CHIRPS v3 + SPI
│       ├── smap.py            # SMAP L4 RZSM
│       ├── ssebop.py          # SSEBop v6 ETa
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
