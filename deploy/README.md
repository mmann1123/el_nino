# Deployment

Three scripts, run in order. Each is idempotent — safe to re-run. All three are
parameterized by `COUNTRY` and `COUNTRY_CODE` so the same scripts deploy a
second country (Haiti) without touching the El Salvador stack.

## El Salvador (defaults)

```bash
cd /home/mmann1123/Documents/github/gwu_haiti_project

# 1. One-time: enable APIs, create bucket, service account, Artifact Registry repo
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/setup_infra.sh

# 2. Build & push the shared container image (~3-5 min)
gcloud builds submit --config el_nino/deploy/cloudbuild.yaml \
  --substitutions=_REGION=us-central1 .

# 3. Deploy / update the Cloud Run Job
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_job.sh

# 4. Create the Cloud Scheduler entries
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/schedule.sh
```

## Haiti

Same scripts, two extra env vars per call:

```bash
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/setup_infra.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_job.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/schedule.sh
```

The image is shared across countries; you only need to rebuild it once when the
code changes. The Cloud Run Job is created per-country with `COUNTRY` set as an
env var on the job, so the running container reads the right config.

## Scheduled jobs

Each country gets six entries, named `${COUNTRY_CODE}-*`:

| Job name | Cron (UTC) | What it does |
|---|---|---|
| `${COUNTRY_CODE}-prelim` | `0 9 * * *` | UCSB CHIRPS-Prelim fill (3-day-latency rainfall) |
| `${COUNTRY_CODE}-forecast` | `15 9 * * *` | NOAA GFS 15-day rainfall forecast |
| `${COUNTRY_CODE}-fetch-chirps` | `30 9 */3 * *` | CHIRPS from GEE (every 3 days) |
| `${COUNTRY_CODE}-fetch-smap` | `45 9 */3 * *` | SMAP L4 root-zone soil moisture |
| `${COUNTRY_CODE}-fetch-wapor` | `0 10 */3 * *` | FAO WAPOR v3 L1 AETI evapotranspiration |
| `${COUNTRY_CODE}-fetch-imerg` | `15 10 * * *` | NASA IMERG-Late daily rainfall |

All times are 15 min apart so the Cloud Run Job concurrency stays at 1 per
country. ES local time is UTC-6, HT local time is UTC-5.

## Run a scheduler entry manually (for testing)

```bash
gcloud scheduler jobs run es-prelim --location=us-central1
gcloud scheduler jobs run ht-prelim --location=us-central1
```

Or trigger the Cloud Run Job directly with arbitrary args:

```bash
gcloud run jobs execute es-drought-etl \
  --region=us-central1 \
  --args="-m,el_nino.etl.run_etl,prelim"
```

## Watch logs

```bash
gcloud run jobs executions list --job=es-drought-etl --region=us-central1 --limit=10
gcloud beta run jobs logs read --job=es-drought-etl --region=us-central1 --limit=200
```

Swap `es-drought-etl` for `ht-drought-etl` to watch Haiti.

## Cost (rough, USD/month, per country)

- Cloud Run Job: ~6 jobs/day × ~3 min × 2 vCPU ≈ ~18 vCPU-hours/mo = **$1.50**
- Cloud Build (only on image rebuilds, shared across countries): trivial
- Cloud Scheduler: 6 jobs × $0.10/mo = **$0.60**
- Artifact Registry: a few GB of layers (shared) = **<$0.50**
- GCS: a few hundred MB total = **<$0.10**
- Earth Engine: free for non-commercial / research

**Total: ~$2–3/mo per country** for the scheduled ETL. Add a Cloud Run dashboard service per country for the front end.

## To stop / pause one country

```bash
COUNTRY_CODE=es  # or ht

for j in ${COUNTRY_CODE}-prelim ${COUNTRY_CODE}-forecast \
         ${COUNTRY_CODE}-fetch-chirps ${COUNTRY_CODE}-fetch-smap \
         ${COUNTRY_CODE}-fetch-wapor ${COUNTRY_CODE}-fetch-imerg; do
  gcloud scheduler jobs pause "$j" --location=us-central1
done
```
