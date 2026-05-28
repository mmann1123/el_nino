"""Central configuration. Local-first; env vars override for cloud deployment.

Run locally with defaults. To target a GCS-mounted path on Cloud Run, set
STORAGE_ROOT=/mnt/gcs (the gcsfuse mount point) and the rest of the pipeline
keeps working unchanged.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # picks up el_nino/.env if present

PROJECT_ROOT = Path(__file__).resolve().parent
STORAGE_ROOT = Path(os.environ.get("STORAGE_ROOT", PROJECT_ROOT / "data"))

RAW_DIR = STORAGE_ROOT / "raw"
CLIMATOLOGY_DIR = STORAGE_ROOT / "climatology"
ENSO_DIR = STORAGE_ROOT / "enso"
FRESHNESS_PATH = STORAGE_ROOT / "freshness.json"
DUCKDB_PATH = STORAGE_ROOT / "dashboard.duckdb"
AOI_PATH = PROJECT_ROOT / "etl" / "aoi" / "departamentos.geojson"

GEE_PROJECT = os.environ.get("GEE_PROJECT", "")
GEE_SERVICE_ACCOUNT_JSON = os.environ.get("GEE_SERVICE_ACCOUNT_JSON", "")

AUTH_MODE = os.environ.get("AUTH_MODE", "disabled")  # disabled | oidc
ALLOWED_EMAILS = [e.strip() for e in os.environ.get("ALLOWED_EMAILS", "").split(",") if e.strip()]

CLIMATOLOGY_START_YEAR = 1981
CLIMATOLOGY_END_YEAR = 2025

# Eastern Dry Corridor — the operational focus from el_nino/notes.md.
DRY_CORRIDOR_DEPARTAMENTOS = ["Morazán", "San Miguel", "La Unión", "Usulután"]

INDICATORS = ["chirps", "smap", "ssebop", "imerg"]


def ensure_dirs() -> None:
    for d in (RAW_DIR, CLIMATOLOGY_DIR, ENSO_DIR):
        d.mkdir(parents=True, exist_ok=True)


def today() -> date:
    """Hook so tests/notebooks can monkey-patch a fixed date."""
    return date.today()
