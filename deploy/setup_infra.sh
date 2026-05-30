#!/usr/bin/env bash
# One-shot setup: enable APIs, create the GCS bucket, create the service
# account, grant roles, create the Artifact Registry repo. Idempotent — safe
# to re-run.
#
# Per-country deployment is driven by COUNTRY_CODE (es|ht); all resource names
# are templated off it so two deployments don't collide.
#
# Usage:
#   bash setup_infra.sh                                       # El Salvador (default)
#   COUNTRY=haiti COUNTRY_CODE=ht bash setup_infra.sh         # Haiti

set -euo pipefail

PROJECT="${PROJECT:-haiti-fews-mmann1123}"
REGION="${REGION:-us-central1}"
COUNTRY="${COUNTRY:-el_salvador}"
COUNTRY_CODE="${COUNTRY_CODE:-es}"
BUCKET="${BUCKET:-${PROJECT}-${COUNTRY_CODE}-drought-dash}"
SA_NAME="${SA_NAME:-${COUNTRY_CODE}-drought-etl}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
REPO="${REPO:-el-nino}"

echo "Setting up country=$COUNTRY project=$PROJECT region=$REGION bucket=gs://$BUCKET sa=$SA_EMAIL"

gcloud config set project "$PROJECT"

echo "=> Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  artifactregistry.googleapis.com \
  earthengine.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com

echo "=> Ensuring GCS bucket gs://$BUCKET exists..."
if ! gcloud storage buckets describe "gs://$BUCKET" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://$BUCKET" \
    --location="$REGION" \
    --uniform-bucket-level-access
else
  echo "   already exists"
fi

echo "=> Ensuring service account $SA_EMAIL exists..."
if ! gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="${COUNTRY_CODE^^} Drought ETL"
else
  echo "   already exists"
fi

echo "=> Granting roles to service account..."
for role in \
  roles/storage.objectUser \
  roles/run.invoker \
  roles/secretmanager.secretAccessor \
  roles/earthengine.viewer \
; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$role" \
    --condition=None \
    --quiet >/dev/null
done

# Register the SA with Earth Engine (idempotent — repeat calls are no-ops).
echo "=> Registering service account with Earth Engine..."
if ! gcloud earth-engine service-accounts list --project="$PROJECT" 2>/dev/null \
     | grep -q "$SA_EMAIL"; then
  earthengine --project="$PROJECT" \
    set_project --service_account_email="$SA_EMAIL" || true
fi

echo "=> Ensuring Artifact Registry repo '$REPO' exists..."
if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Container images for the el_nino drought dashboard (shared across countries)"
else
  echo "   already exists"
fi

echo
echo "Infra setup complete."
echo "  project: $PROJECT"
echo "  bucket:  gs://$BUCKET"
echo "  sa:      $SA_EMAIL"
echo "  region:  $REGION"
echo "  repo:    $REPO"
