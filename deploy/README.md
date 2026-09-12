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
#    Run from the el_nino repo root — the build context is this repo, and
#    .gcloudignore keeps data/ and .git out of the upload (~12 MB context).
cd el_nino
gcloud builds submit --config deploy/cloudbuild.yaml \
  --substitutions=_REGION=us-central1 .

# 3. Deploy / update the Cloud Run Job (ETL)
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_job.sh

# 4. Create the Cloud Scheduler entries
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/schedule.sh

# 5. Deploy the public dashboard Cloud Run Service
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_service.sh
```

The dashboard service is deployed with `--allow-unauthenticated` — public,
no sign-in required. The Cloud Run URL is printed at the end.

## Haiti

Same scripts, two extra env vars per call:

```bash
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/setup_infra.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_job.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/schedule.sh
COUNTRY=haiti COUNTRY_CODE=ht PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_service.sh
```

The image is shared across countries; you only need to rebuild it once when the
code changes. The Cloud Run Job is created per-country with `COUNTRY` set as an
env var on the job, so the running container reads the right config.

## Scheduled jobs

Each country gets seven entries, named `${COUNTRY_CODE}-*`:

| Job name | Cron (UTC) | What it does |
|---|---|---|
| `${COUNTRY_CODE}-prelim` | `0 9 * * *` | UCSB CHIRPS-Prelim fill (3-day-latency rainfall) |
| `${COUNTRY_CODE}-forecast` | `15 9 * * *` | NOAA GFS 15-day rainfall forecast |
| `${COUNTRY_CODE}-fetch-chirps` | `30 9 */3 * *` | CHIRPS from GEE (every 3 days) |
| `${COUNTRY_CODE}-fetch-smap` | `45 9 */3 * *` | SMAP L4 root-zone soil moisture |
| `${COUNTRY_CODE}-fetch-wapor` | `0 10 */3 * *` | FAO WAPOR v3 L1 AETI evapotranspiration |
| `${COUNTRY_CODE}-fetch-imerg` | `15 10 * * *` | NASA IMERG-Late daily rainfall |
| `${COUNTRY_CODE}-enso` | `30 10 * * 2` | NOAA CPC ONI + weekly Niño 3.4 (Tuesdays) |

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

## Google Analytics

All three public surfaces (landing + both dashboards) share **one GA4 property**,
measurement ID **`G-PW1R91K8VT`**. They're subdomains of `pygis.io`, so GA4 keeps
a country switch inside a single session; split them after the fact with the
built-in **Hostname** dimension. The ID is not a secret — it ships in the page
source of every public deploy — so it's committed as the default in
[deploy_service.sh](deploy_service.sh) and [../landing/Dockerfile](../landing/Dockerfile)
rather than passed in by hand. Analytics is off wherever `GA_MEASUREMENT_ID` is
empty, which is every local run and the ETL Job.

**Setting the env var alone does nothing** — the code that reads it
(`inject_ga.py` and the dashboard `CMD`; the `__GA_SNIPPET__` placeholder and
`entrypoint.sh` on the landing page) ships *inside* the images. Any image built
before those existed will happily carry the env var and emit no tag. Both
images must be rebuilt once; after that, changing the ID really is just an env
var.

```bash
# From the el_nino repo root.
# 1. Dashboards — rebuild, then redeploy so Cloud Run picks up the new :latest
gcloud builds submit --config deploy/cloudbuild.yaml --project=haiti-fews-mmann1123 .
bash deploy/deploy_service.sh
COUNTRY=haiti COUNTRY_CODE=ht bash deploy/deploy_service.sh

# 2. Landing page (Cloud Run service name is `drought`, not `drought-landing`)
gcloud builds submit --config deploy/cloudbuild.landing.yaml --project=haiti-fews-mmann1123 .
gcloud run deploy drought --region=us-central1 --project=haiti-fews-mmann1123 \
  --image=us-central1-docker.pkg.dev/haiti-fews-mmann1123/el-nino/drought-landing:latest
```

Verify it actually landed, rather than trusting the env var:

```bash
for u in https://drought.pygis.io https://es.drought.pygis.io https://ht.drought.pygis.io; do
  printf "%-32s " "$u"
  curl -sf "$u" | grep -q G-PW1R91K8VT && echo "tagged" || echo "NO TAG"
done
```

To deploy a surface untracked, pass an explicitly empty value:
`GA_MEASUREMENT_ID= bash deploy/deploy_service.sh`.

**How the tag gets onto the page.** The landing page is plain HTML — the
snippet is substituted into `<head>` by [../landing/entrypoint.sh](../landing/entrypoint.sh)
at container start. The dashboards are not: Streamlit strips `<script>` from
`st.markdown(unsafe_allow_html=True)`, and `st.components.v1.html` renders in a
sandboxed iframe that GA would report instead of the real page. So
[../dashboard/inject_ga.py](../dashboard/inject_ga.py) patches the snippet into
Streamlit's own `static/index.html` from the container's `CMD`, before the
server boots. Confirm it took effect in the deploy logs:

```bash
gcloud beta run services logs read es-drought-dash --region=us-central1 --limit=50 | grep inject_ga
```

Caveat: because the dashboard is a single-page app whose tabs don't change the
URL, GA records **one page_view per visit** per country. Sessions, users,
geography, referrers, and device all work normally; per-tab interaction would
need custom events.

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
