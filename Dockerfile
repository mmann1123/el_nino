# Single image with two entry points (dashboard service and ETL job).
# Cloud Run Service:  uvicorn/streamlit entry
# Cloud Run Job:      python -m el_nino.etl.run_etl ...
FROM python:3.11-slim

WORKDIR /app

# System deps:
#   gcc/g++       — for any sdist that needs to compile (scipy fallback, etc.)
#   libgeos-dev   — geopandas/shapely
#   libgdal-dev   — rasterio (UCSB CHIRPS-Prelim zonal stats)
#   libexpat1     — gdal runtime
#   curl          — for healthchecks / debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libgeos-dev libgdal-dev libexpat1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY el_nino/requirements.txt /app/el_nino/requirements.txt
RUN pip install --no-cache-dir -r /app/el_nino/requirements.txt

COPY el_nino /app/el_nino
# Streamlit reads .streamlit/config.toml from $CWD (=/app here, not /app/el_nino).
COPY el_nino/.streamlit /app/.streamlit

ENV PYTHONPATH=/app
ENV STORAGE_ROOT=/mnt/gcs
# Light theme is also enforced via env var so it survives even if config.toml
# is missing or $CWD changes.
ENV STREAMLIT_THEME_BASE=light
# Public dashboards — no sign-in gate. Set AUTH_MODE=oidc + ALLOWED_EMAILS at
# deploy time to opt back in to the Streamlit OIDC gate (see dashboard/auth.py).
ENV AUTH_MODE=disabled
ENV PORT=8080

# Default to the dashboard. The Cloud Run Job overrides with a `python -m ...` command.
CMD ["streamlit", "run", "el_nino/dashboard/app.py", \
     "--server.port=8080", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
