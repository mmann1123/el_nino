#!/usr/bin/env bash
# Deploy (or update) the Cloud Run Service that serves the Streamlit dashboard.
# Publicly accessible — anyone with the URL can view the dashboard. Mount the
# country's GCS bucket via gcsfuse so the dashboard reads the same parquets
# the ETL Job writes.
#
# Usage:
#   bash deploy_service.sh                                       # El Salvador (default)
#   COUNTRY=haiti COUNTRY_CODE=ht bash deploy_service.sh         # Haiti

set -euo pipefail

PROJECT="${PROJECT:-haiti-fews-mmann1123}"
REGION="${REGION:-us-central1}"
COUNTRY="${COUNTRY:-el_salvador}"
COUNTRY_CODE="${COUNTRY_CODE:-es}"
BUCKET="${BUCKET:-${PROJECT}-${COUNTRY_CODE}-drought-dash}"
SA_NAME="${SA_NAME:-${COUNTRY_CODE}-drought-etl}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
REPO="${REPO:-el-nino}"
IMAGE_NAME="${IMAGE_NAME:-el-nino-dash}"
SERVICE_NAME="${SERVICE_NAME:-${COUNTRY_CODE}-drought-dash}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${IMAGE_NAME}:latest"
# GA4 measurement ID. Shared by both countries and the landing page — GA4 splits
# them by hostname, and one property keeps a country switch as a single session.
# Not a secret (it ships in the page source of every public deploy). Export
# GA_MEASUREMENT_ID= (empty) to deploy a dashboard untracked.
GA_MEASUREMENT_ID="${GA_MEASUREMENT_ID-G-PW1R91K8VT}"

echo "Deploying Cloud Run Service '$SERVICE_NAME' (country=$COUNTRY) from $IMAGE"

# --allow-unauthenticated makes the dashboard publicly accessible.
# The Service uses the same image and bucket as the ETL Job; STORAGE_ROOT
# points at the gcsfuse mount so the dashboard reads what the ETL writes.
#
# Sizing: measured peak is ~350 MB and ~40% of one vCPU, so 1Gi leaves ~3x
# headroom (gcsfuse caches on top of the Python heap — don't drop to 512Mi).
# CPU must stay >= 1: Cloud Run rejects sub-1 CPU unless concurrency is 1, and
# this service peaks at ~52 concurrent requests on a single instance. Serving
# time is billed per open Streamlit websocket, not per CPU-second, so packing
# high concurrency onto one instance is what keeps the bill small.
gcloud run deploy "$SERVICE_NAME" \
  --project="$PROJECT" \
  --image="$IMAGE" \
  --region="$REGION" \
  --service-account="$SA_EMAIL" \
  --cpu=1 --memory=1Gi \
  --min-instances=0 \
  --max-instances=4 \
  --port=8080 \
  --timeout=300 \
  --allow-unauthenticated \
  --ingress=all \
  --set-env-vars="STORAGE_ROOT=/mnt/gcs,GEE_PROJECT=${PROJECT},COUNTRY=${COUNTRY},AUTH_MODE=disabled,GA_MEASUREMENT_ID=${GA_MEASUREMENT_ID}" \
  --add-volume="name=gcs,type=cloud-storage,bucket=${BUCKET}" \
  --add-volume-mount="volume=gcs,mount-path=/mnt/gcs"

URL=$(gcloud run services describe "$SERVICE_NAME" --project="$PROJECT" --region="$REGION" --format='value(status.url)')
echo
echo "Service deployed: $URL"
echo "Bookmark this URL — it's the country's dashboard entry point."
