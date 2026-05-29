# Google Cloud deployment plan — El Niño dashboard + ETL

> Run all commands from the repo root, whatever that path becomes after the
> move. Nothing here hard-codes the host path.

## Target architecture

```
                ┌──────────────────────────────────────────────────────────┐
                │  Cloud Scheduler (6 cron entries)                        │
                │  ── es-prelim, es-forecast, es-fetch-{chirps,smap,...}   │
                └────────────────────┬─────────────────────────────────────┘
                                     │ HTTP POST  /jobs/es-drought-etl:run
                                     ▼
                ┌──────────────────────────────────────────────────────────┐
                │  Cloud Run JOB  es-drought-etl                           │
                │  (same image, command = python -m el_nino.etl.run_etl)   │
                └────────────────────┬─────────────────────────────────────┘
                                     │  reads/writes
                                     ▼
                ┌──────────────────────────────────────────────────────────┐
                │  GCS bucket  haiti-fews-mmann1123-es-drought-dash        │
                │  mounted at /mnt/gcs (gcsfuse volume)                    │
                │  ── raw/, climatology/, enso/, freshness.json,           │
                │     cache/chirps_prelim/  (pruned to 3 newest tifs)      │
                └────────────────────▲─────────────────────────────────────┘
                                     │ reads
                ┌────────────────────┴─────────────────────────────────────┐
                │  Cloud Run SERVICE  es-drought-dashboard  (NEW)          │
                │  (same image, default CMD = streamlit run ...)           │
                │  Public URL, --allow-unauthenticated                     │
                └──────────────────────────────────────────────────────────┘
```

Both the Job and the Service run the **same Docker image** from Artifact
Registry. The Job overrides the CMD to launch the ETL CLI; the Service uses the
Dockerfile's default Streamlit CMD.

## Decisions captured

- **Access:** Dashboard is fully public (`--allow-unauthenticated`). No
  app-level OIDC, no IAP. `AUTH_MODE=disabled` overrides the Dockerfile default.
- **GCP project:** `haiti-fews-mmann1123`
- **Region:** `us-central1`
- **Bucket:** `haiti-fews-mmann1123-es-drought-dash`
- **Service account:** `es-drought-etl@haiti-fews-mmann1123.iam.gserviceaccount.com`
  (reused by both Job and Service)
- **Image registry:** `us-central1-docker.pkg.dev/haiti-fews-mmann1123/el-nino/es-drought-dash`

---

## Phase 0 — Pre-flight (local, ~5 min)

1. Commit pending working-tree changes so the Cloud Build `$SHORT_SHA` tag is
   meaningful. As of this writing, untracked/uncommitted files include:
   - `el_nino/dashboard/app.py` (freshness strip → sidebar caption)
   - `el_nino/dashboard/alerts.py` (paragraph + expander reorder)
   - `el_nino/dashboard/freshness.py` (sidebar_refresh_caption)
   - `el_nino/dashboard/status.py` (new file — untracked)
   - `el_nino/etl/chirps_prelim.py` (TIF prune-to-3)
   - `el_nino/etl/indicators/{base,chirps,imerg,smap,wapor}.py`

2. (Optional) Sanity-check the Dockerfile builds locally:
   ```bash
   docker build -f el_nino/Dockerfile -t es-drought:test .
   ```

3. Confirm GCP auth: `gcloud auth list`, `gcloud config get-value project`.

---

## Phase 1 — Infrastructure (one-time, ~3 min)

```bash
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/setup_infra.sh
```

[setup_infra.sh](setup_infra.sh) is idempotent and:

- Enables APIs: Run, Cloud Build, Scheduler, Artifact Registry, Earth Engine,
  Secret Manager, IAM Credentials
- Creates GCS bucket `gs://haiti-fews-mmann1123-es-drought-dash`
- Creates service account `es-drought-etl@…`
- Grants roles: `storage.objectUser`, `run.invoker`,
  `secretmanager.secretAccessor`, `earthengine.viewer`
- Registers the SA with Earth Engine
- Creates Artifact Registry repo `el-nino`

**Verification:**
```bash
gcloud storage buckets list | grep es-drought-dash
gcloud artifacts repositories list --location=us-central1 | grep el-nino
```

---

## Phase 2 — Build & push the image (~3–5 min)

```bash
gcloud builds submit --config el_nino/deploy/cloudbuild.yaml \
  --substitutions=_REGION=us-central1 .
```

Produces two tags in Artifact Registry: `:$SHORT_SHA` and `:latest`. Both the
Job and Service pull `:latest`.

**Verification:**
```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/haiti-fews-mmann1123/el-nino
```

---

## Phase 3 — Deploy the ETL Cloud Run **Job** (~1 min)

```bash
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/deploy_job.sh
```

[deploy_job.sh](deploy_job.sh) wires up `es-drought-etl` with: 2 vCPU, 2 Gi
RAM, 30 min timeout, GCS volume at `/mnt/gcs`, `STORAGE_ROOT=/mnt/gcs`,
`GEE_PROJECT=haiti-fews-mmann1123`.

**Verification — run one ETL command end-to-end** before scheduling:
```bash
gcloud run jobs execute es-drought-etl --region=us-central1 \
  --args="-m,el_nino.etl.run_etl,prelim" --wait
gcloud beta run jobs logs read --job=es-drought-etl --region=us-central1 --limit=200
```

---

## Phase 4 — Deploy the dashboard Cloud Run **Service** (NEW — script TBD)

Not yet scripted. Will add `el_nino/deploy/deploy_service.sh` that runs:

```bash
gcloud run deploy es-drought-dashboard \
  --image=us-central1-docker.pkg.dev/haiti-fews-mmann1123/el-nino/es-drought-dash:latest \
  --region=us-central1 \
  --service-account=es-drought-etl@haiti-fews-mmann1123.iam.gserviceaccount.com \
  --cpu=1 --memory=1Gi \
  --min-instances=0 --max-instances=2 \
  --port=8080 \
  --allow-unauthenticated \
  --set-env-vars="STORAGE_ROOT=/mnt/gcs,GEE_PROJECT=haiti-fews-mmann1123,AUTH_MODE=disabled" \
  --add-volume="name=gcs,type=cloud-storage,bucket=haiti-fews-mmann1123-es-drought-dash" \
  --add-volume-mount="volume=gcs,mount-path=/mnt/gcs" \
  --timeout=300
```

Notes:
- `--allow-unauthenticated` per decision above.
- `AUTH_MODE=disabled` overrides the Dockerfile's `oidc` default since we're
  not gating in-app.
- `min-instances=0` keeps idle cost near zero; first request after idle has a
  cold start (~10 s for Streamlit).
- 1 vCPU / 1 Gi is plenty for the dashboard's read-only loads.

**Verification:**
```bash
gcloud run services describe es-drought-dashboard --region=us-central1 \
  --format='value(status.url)'
```
…then hit the URL.

---

## Phase 5 — Cloud Scheduler entries (~1 min)

```bash
PROJECT=haiti-fews-mmann1123 bash el_nino/deploy/schedule.sh
```

Creates the 6 cron entries listed in [README.md](README.md), spaced 15 min apart.

**Verification — trigger one manually and tail logs:**
```bash
gcloud scheduler jobs run es-prelim --location=us-central1
gcloud beta run jobs logs read --job=es-drought-etl --region=us-central1 --limit=200
```

---

## Phase 6 — Smoke tests & monitoring (~10 min)

1. Hit the dashboard URL, confirm all four indicator tabs render and the
   freshness sidebar shows non-stale data.
2. Manually trigger `es-prelim` and verify the TIF cache in GCS contains ≤ 3
   files (new prune behavior in `chirps_prelim._prune_cache`).
3. Verify scheduler entries fire — leave it for 24 h and re-check
   `gcloud scheduler jobs list` for `LAST_SUCCESS_TIME`.
4. Confirm cost is in the $2–3/mo ballpark in the billing console after a week.

---

## Risk register

| Risk | Mitigation |
|---|---|
| GEE auth fails inside Cloud Run (no service-account JSON env var) | SA is registered with EE via `setup_infra.sh`; Cloud Run uses ADC. If `ee.Initialize()` fails, fall back to setting `GEE_SERVICE_ACCOUNT_JSON` via Secret Manager. |
| Dashboard cold starts are slow | Acceptable for an internal tool. Bump `min-instances=1` (~$5/mo extra) if it becomes painful. |
| Public dashboard exposes data | Per decision above. Easy to revert: rerun `deploy_service.sh` with `--no-allow-unauthenticated`. |
| gcsfuse latency on Parquet reads | DuckDB at `/mnt/gcs/dashboard.duckdb` reads through gcsfuse — known to be slow. If the dashboard feels sluggish, consider switching to GCS-native reads via `read_parquet('gs://...')`. |

---

## Outstanding work before "deploy" can mean "press the button"

- [ ] Phase 0: commit pending edits.
- [ ] Phase 4: write `deploy_service.sh` and add a step to
      [README.md](README.md).
- [ ] Phase 1–3, 5: handed off to a human to run — these incur real GCP
      charges and create live infrastructure.

---

## Path-portability note (since the project directory is moving)

Nothing in this plan depends on the host filesystem path of the repo. The
build context (`.` in `gcloud builds submit ... .`) is whatever directory you
`cd` into before running the command. The only place an old absolute path
might survive is in `el_nino/deploy/README.md`'s example block — after the
move, just `cd` to the new repo root and re-run the same commands.
