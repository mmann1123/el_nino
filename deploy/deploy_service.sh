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

echo "Deploying Cloud Run Service '$SERVICE_NAME' (country=$COUNTRY) from $IMAGE"

# --allow-unauthenticated makes the dashboard publicly accessible.
# The Service uses the same image and bucket as the ETL Job; STORAGE_ROOT
# points at the gcsfuse mount so the dashboard reads what the ETL writes.
gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE" \
  --region="$REGION" \
  --service-account="$SA_EMAIL" \
  --cpu=1 --memory=2Gi \
  --min-instances=0 \
  --max-instances=4 \
  --port=8080 \
  --timeout=300 \
  --allow-unauthenticated \
  --ingress=all \
  --set-env-vars="STORAGE_ROOT=/mnt/gcs,GEE_PROJECT=${PROJECT},COUNTRY=${COUNTRY},AUTH_MODE=disabled" \
  --add-volume="name=gcs,type=cloud-storage,bucket=${BUCKET}" \
  --add-volume-mount="volume=gcs,mount-path=/mnt/gcs"

URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')
echo
echo "Service deployed: $URL"
echo "Bookmark this URL — it's the country's dashboard entry point."
