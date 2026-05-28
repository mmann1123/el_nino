#!/usr/bin/env bash
# Deploy (or update) the Cloud Run Job that runs the ETL CLI.
# Idempotent — uses `deploy` which creates if absent and updates if present.
#
# Usage: PROJECT=haiti-fews-mmann1123 REGION=us-central1 bash deploy_job.sh

set -euo pipefail

PROJECT="${PROJECT:-haiti-fews-mmann1123}"
REGION="${REGION:-us-central1}"
BUCKET="${BUCKET:-${PROJECT}-es-drought-dash}"
SA_NAME="${SA_NAME:-es-drought-etl}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
REPO="${REPO:-el-nino}"
IMAGE_NAME="${IMAGE_NAME:-es-drought-dash}"
JOB_NAME="${JOB_NAME:-es-drought-etl}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${IMAGE_NAME}:latest"

echo "Deploying Cloud Run Job '$JOB_NAME' from $IMAGE"

# The Job runs a single ETL subcommand. Scheduler entries override --args to
# pick which subcommand to run (prelim, forecast, fetch --indicator X, etc.).
gcloud run jobs deploy "$JOB_NAME" \
  --image="$IMAGE" \
  --region="$REGION" \
  --service-account="$SA_EMAIL" \
  --cpu=2 --memory=2Gi \
  --max-retries=2 \
  --task-timeout=30m \
  --set-env-vars="STORAGE_ROOT=/mnt/gcs,GEE_PROJECT=${PROJECT}" \
  --add-volume="name=gcs,type=cloud-storage,bucket=${BUCKET}" \
  --add-volume-mount="volume=gcs,mount-path=/mnt/gcs" \
  --command="python" \
  --args="-m,el_nino.etl.run_etl,--help"

echo
echo "Cloud Run Job '$JOB_NAME' is deployed. The scheduler entries (in schedule.sh)"
echo "override --args at execute-time so this default --help is never used."
