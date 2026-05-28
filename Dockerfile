# Single image with two entry points (dashboard service and ETL job).
# Cloud Run Service:  uvicorn/streamlit entry
# Cloud Run Job:      python -m el_nino.etl.run_etl ...
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

COPY el_nino/requirements.txt /app/el_nino/requirements.txt
RUN pip install --no-cache-dir -r /app/el_nino/requirements.txt

COPY el_nino /app/el_nino

ENV PYTHONPATH=/app
ENV STORAGE_ROOT=/mnt/gcs
ENV AUTH_MODE=oidc
ENV PORT=8080

# Default to the dashboard. The Cloud Run Job overrides with a `python -m ...` command.
CMD ["streamlit", "run", "el_nino/dashboard/app.py", \
     "--server.port=8080", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
