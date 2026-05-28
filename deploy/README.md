# Deployment

Three scripts, run in order. Each is idempotent — safe to re-run.

```bash
cd /home/mmann1123/Documents/github/gwu_haiti_project

# 1. One-time: enable APIs, create bucket, service account, Artifact Registry repo
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/setup_infra.sh

# 2. Build & push the container image (~3-5 min)
gcloud builds submit --config el_nino/deploy/cloudbuild.yaml \
  --substitutions=_REGION=us-central1 .

# 3. Deploy / update the Cloud Run Job
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_job.sh

# 4. Create the Cloud Scheduler entries
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/schedule.sh
```

## Scheduled jobs

| Job name | Cron (UTC) | Local time | What it does |
|---|---|---|---|
| `es-prelim` | `0 9 * * *` | 03:00 SV | UCSB CHIRPS-Prelim fill (3-day-latency rainfall) |
| `es-forecast` | `15 9 * * *` | 03:15 SV | NOAA GFS 15-day rainfall forecast |
| `es-fetch-chirps` | `30 9 */3 * *` | 03:30 SV / every 3 days | CHIRPS from GEE (whatever's caught up) |
| `es-fetch-smap` | `45 9 */3 * *` | 03:45 SV / every 3 days | SMAP L4 root-zone soil moisture |
| `es-fetch-wapor` | `0 10 */3 * *` | 04:00 SV / every 3 days | FAO WAPOR v3 L1 AETI evapotranspiration |
| `es-fetch-imerg` | `15 10 * * *` | 04:15 SV | NASA IMERG-Late daily rainfall |

All times are 15 min apart so the Cloud Run Job concurrency stays at 1.

## Run a scheduler entry manually (for testing)

```bash
gcloud scheduler jobs run es-prelim --location=us-central1
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

## Cost (rough, USD/month)

- Cloud Run Job: ~6 jobs/day × ~3 min × 2 vCPU ≈ ~18 vCPU-hours/mo = **$1.50**
- Cloud Build (only on image rebuilds): trivial unless you build daily
- Cloud Scheduler: 6 jobs × $0.10/mo = **$0.60**
- Artifact Registry: a few GB of layers = **<$0.50**
- GCS: a few hundred MB total = **<$0.10**
- Earth Engine: free for non-commercial / research

**Total: ~$2–3/mo** for the scheduled ETL. Add a Cloud Run dashboard service (next step) for the front end.

## To stop / pause everything

```bash
# Pause all scheduler entries (still exist but won't fire)
for j in es-prelim es-forecast es-fetch-chirps es-fetch-smap es-fetch-wapor es-fetch-imerg; do
  gcloud scheduler jobs pause "$j" --location=us-central1
done

# Or hard-delete
for j in es-prelim es-forecast es-fetch-chirps es-fetch-smap es-fetch-wapor es-fetch-imerg; do
  gcloud scheduler jobs delete "$j" --location=us-central1 --quiet
done
```
