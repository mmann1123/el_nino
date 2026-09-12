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

# Crons below are expressed in each country's LOCAL time, not UTC, so the chain
# always starts at 05:00 local. El Salvador never observes DST (UTC-6 year-round);
# Haiti does (UTC-5 winter, UTC-4 summer), so a UTC-pinned cron drifts an hour
# twice a year for HT.
case "$COUNTRY_CODE" in
  es) TIME_ZONE="${TIME_ZONE:-America/El_Salvador}" ;;
  ht) TIME_ZONE="${TIME_ZONE:-America/Port-au-Prince}" ;;
  *)  TIME_ZONE="${TIME_ZONE:-UTC}" ;;
esac
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

  echo "=> $name  '$cron' ($TIME_ZONE)  args=$args_csv"

  gcloud scheduler jobs delete "$name" --project="$PROJECT" --location="$REGION" --quiet 2>/dev/null || true
  gcloud scheduler jobs create http "$name" \
    --project="$PROJECT" \
    --location="$REGION" \
    --description="$desc" \
    --schedule="$cron" \
    --time-zone="$TIME_ZONE" \
    --uri="$URI" \
    --http-method=POST \
    --oauth-service-account-email="$SA_EMAIL" \
    --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
    --headers="Content-Type=application/json" \
    --message-body="$body"
}

# All times are LOCAL to $TIME_ZONE (see the case block above). The chain starts
# at 05:00 local daily and finishes by ~06:45. Entries are spaced 15 min apart so
# they don't race the same Cloud Run slot — individual runs take 2-9 minutes, and
# they write to the same parquets, so overlapping executions would race on upsert.

create_scheduler "${COUNTRY_CODE}-prelim" \
  "0 5 * * *" \
  "UCSB CHIRPS-Prelim daily (3-day-latency rainfall fill)" \
  "-m,el_nino.etl.run_etl,prelim"

create_scheduler "${COUNTRY_CODE}-forecast" \
  "15 5 * * *" \
  "NOAA GFS 15-day rainfall forecast" \
  "-m,el_nino.etl.run_etl,forecast"

create_scheduler "${COUNTRY_CODE}-fetch-chirps" \
  "30 5 */3 * *" \
  "CHIRPS observed from GEE (every 3 days)" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,chirps"

create_scheduler "${COUNTRY_CODE}-fetch-smap" \
  "45 5 */3 * *" \
  "SMAP L4 root-zone soil moisture (every 3 days)" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,smap"

create_scheduler "${COUNTRY_CODE}-fetch-wapor" \
  "0 6 */3 * *" \
  "FAO WAPOR v3 L1 AETI evapotranspiration (every 3 days)" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,wapor"

create_scheduler "${COUNTRY_CODE}-fetch-imerg" \
  "15 6 * * *" \
  "NASA IMERG-Late daily rainfall" \
  "-m,el_nino.etl.run_etl,fetch,--indicator,imerg"

# ENSO state for the El Niño / La Niña tracker: NOAA CPC ONI (monthly) + the
# weekly Niño 3.4 SST anomaly (updated Mondays). Weekly Tuesday refresh covers
# both; no GEE involved, so it's cheap.
create_scheduler "${COUNTRY_CODE}-enso" \
  "30 6 * * 2" \
  "NOAA CPC ONI + weekly Niño 3.4 SST anomaly" \
  "-m,el_nino.etl.run_etl,enso"

# Must run LAST — it recomputes SPI, climatology, anomaly z-scores and
# freshness.json from whatever the fetch entries above just landed. Without it
# the raw parquets update but the dashboard's trigger evaluation goes stale.
create_scheduler "${COUNTRY_CODE}-finalize" \
  "45 6 * * *" \
  "Recompute SPI + climatology + anomaly z + freshness" \
  "-m,el_nino.etl.run_etl,finalize"

# Executing a Cloud Run *Job* needs the `run.jobs.run` permission, which lives
# in roles/run.developer — NOT roles/run.invoker (that only invokes *services*).
# Granting run.invoker here was a bug: the scheduler fired but every run failed
# with PERMISSION_DENIED (code 7). Idempotent — repeat calls are no-op.
echo
echo "=> Granting scheduler SA run.developer on the Cloud Run Job"
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.developer" \
  --condition=None \
  --quiet >/dev/null

echo
echo "All scheduler entries for ${COUNTRY_CODE}:"
gcloud scheduler jobs list --project="$PROJECT" --location="$REGION" --filter="name~${COUNTRY_CODE}-" \
  --format='table(name.basename(),schedule,state,description)'
