#!/usr/bin/env bash
# Create or update Cloud Scheduler entries that invoke the Cloud Run Job.
# Idempotent: deletes-then-creates each entry so the script is declarative.
#
# Usage:
#   bash schedule.sh                                       # El Salvador (default)
#   COUNTRY=haiti COUNTRY_CODE=ht bash schedule.sh         # Haiti

set -euo pipefail

PROJECT="${PROJECT:-haiti-fews-mmann1123}"
REGION="${REGION:-us-central1}"
COUNTRY="${COUNTRY:-el_salvador}"
COUNTRY_CODE="${COUNTRY_CODE:-es}"
SA_NAME="${SA_NAME:-${COUNTRY_CODE}-drought-etl}"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
JOB_NAME="${JOB_NAME:-${COUNTRY_CODE}-drought-etl}"

URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/${JOB_NAME}:run"

# ---- helper: create/replace one scheduler entry ----
# Args: <name> <cron> <description> <comma-separated-args>
create_scheduler() {
  local name="$1"
  local cron="$2"
  local desc="$3"
  local args_csv="$4"

  # Build the JSON body that overrides the Cloud Run Job's container args.
  # Convert "a,b,c" to a JSON list ["a","b","c"].
  local args_json
  args_json=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1].split(',')))" "$args_csv")
  local body
  body=$(printf '{"overrides":{"containerOverrides":[{"args":%s}]}}' "$args_json")

  echo "=> $name  '$cron'  args=$args_csv"

  gcloud scheduler jobs delete "$name" --location="$REGION" --quiet 2>/dev/null || true
  gcloud scheduler jobs create http "$name" \
    --location="$REGION" \
    --description="$desc" \
    --schedule="$cron" \
    --time-zone="UTC" \
    --uri="$URI" \
    --http-method=POST \
    --oauth-service-account-email="$SA_EMAIL" \
    --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
    --headers="Content-Type=application/json" \
    --message-body="$body"
}

# All times in UTC. ES is UTC-6 year-round (09:00 UTC = 03:00 local); HT is
# UTC-5 (09:00 UTC = 04:00 local). Entries are spaced 15 min apart so they
# don't race the same Cloud Run slot.

create_scheduler "${COUNTRY_CODE}-prelim" \
  "0 9 * * *" \
  "UCSB CHIRPS-Prelim daily (3-day-latency rainfall fill)" \
  "-m,el_nino.etl.run_etl,prelim"

create_scheduler "${COUNTRY_CODE}-forecast" \
  "15 9 * * *" \
  "NOAA GFS 15-day rainfall forecast" \
  "-m,el_nino.etl.run_etl,forecast"

create_scheduler "${COUNTRY_CODE}-fetch-chirps" \
  "30 9 */3 * *" \
  "CHIRPS observed from GEE (every 3 days)" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,chirps"

create_scheduler "${COUNTRY_CODE}-fetch-smap" \
  "45 9 */3 * *" \
  "SMAP L4 root-zone soil moisture (every 3 days)" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,smap"

create_scheduler "${COUNTRY_CODE}-fetch-wapor" \
  "0 10 */3 * *" \
  "FAO WAPOR v3 L1 AETI evapotranspiration (every 3 days)" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,wapor"

create_scheduler "${COUNTRY_CODE}-fetch-imerg" \
  "15 10 * * *" \
  "NASA IMERG-Late daily rainfall" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,imerg"

# ENSO state for the El Niño / La Niña tracker: NOAA CPC ONI (monthly) + the
# weekly Niño 3.4 SST anomaly (updated Mondays). Weekly Tuesday refresh covers
# both; no GEE involved, so it's cheap.
create_scheduler "${COUNTRY_CODE}-enso" \
  "30 10 * * 2" \
  "NOAA CPC ONI + weekly Niño 3.4 SST anomaly" \
  "-m,el_nino.etl.run_etl,enso"

# The scheduler-invoking service account needs run.invoker on the job. Grant
# it (idempotent — repeat calls are no-op).
echo
echo "=> Granting scheduler SA run.invoker on the Cloud Run Job"
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" \
  --condition=None \
  --quiet >/dev/null

echo
echo "All scheduler entries for ${COUNTRY_CODE}:"
gcloud scheduler jobs list --location="$REGION" --filter="name~${COUNTRY_CODE}-" \
  --format='table(name.basename(),schedule,state,description)'
