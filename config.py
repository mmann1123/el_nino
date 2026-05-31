"""Central configuration. Local-first; env vars override for cloud deployment.

Run locally with defaults. To target a GCS-mounted path on Cloud Run, set
STORAGE_ROOT=/mnt/gcs (the gcsfuse mount point) and the rest of the pipeline
keeps working unchanged.

Multi-country: set COUNTRY=el_salvador (default) or COUNTRY=haiti at startup.
Country-specific assets and constants live in COUNTRIES below; the active
country's entry is exposed as `CC`.
"""

from __future__ import annotations

import functools
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

STORAGE_ROOT = Path(os.environ.get("STORAGE_ROOT", PROJECT_ROOT / "data"))

RAW_DIR = STORAGE_ROOT / "raw"
CLIMATOLOGY_DIR = STORAGE_ROOT / "climatology"
ENSO_DIR = STORAGE_ROOT / "enso"
FRESHNESS_PATH = STORAGE_ROOT / "freshness.json"
DUCKDB_PATH = STORAGE_ROOT / "dashboard.duckdb"

GEE_PROJECT = os.environ.get("GEE_PROJECT", "")
GEE_SERVICE_ACCOUNT_JSON = os.environ.get("GEE_SERVICE_ACCOUNT_JSON", "")

AUTH_MODE = os.environ.get("AUTH_MODE", "disabled")  # disabled | oidc
ALLOWED_EMAILS = [e.strip() for e in os.environ.get("ALLOWED_EMAILS", "").split(",") if e.strip()]

CLIMATOLOGY_START_YEAR = 1981
CLIMATOLOGY_END_YEAR = 2025

INDICATORS = ["chirps", "smap", "wapor", "imerg"]


COUNTRY = os.environ.get("COUNTRY", "el_salvador")

# Country-specific configuration. Each entry owns everything that differs
# between deployments — AOI filename, map center, UI strings, priority regions.
# Add a new country by adding a new entry and bootstrapping its AOI geojson via
# `COUNTRY=<key> python -m el_nino.etl.aoi.fetch_aoi`.
COUNTRIES: dict[str, dict] = {
    "el_salvador": {
        "iso2": "SV",
        "display_name": "El Salvador",
        "short_code": "ES",
        "gaul_adm0_name": "El Salvador",
        "aoi_filename": "departamentos_es.geojson",
        "map_center": {"lat": 13.794, "lon": -88.917},
        "map_zoom": 6.7,
        # Native term for ADM1 in the country's official language.
        # Used for user-facing labels and hover tooltips.
        "dept_term": "departamento",
        "dept_term_plural": "departamentos",
        "priority_departments": ["Morazan", "San Miguel", "La Union", "Usulutan"],
        "priority_label": "Eastern Dry Corridor",
        "priority_display_names": "Morazán, San Miguel, La Unión, Usulután",
        "crop_focus_caption": "maize-season indicators",
        # Calibration anchors — primera maize silking, mid-Jul to mid-Aug.
        "silking_window": (196, 227),
        # year → (severity, note). Drawn from el_nino_agricultural_risks.md.
        "labeled_events": {
            1997: ("severe-moderate", "Super El Niño; FAO 'considerably below-average' 2nd-season maize"),
            2002: ("moderate",        "Moderate El Niño"),
            2009: ("moderate",        "Moderate El Niño"),
            2014: ("moderate",        "Weak El Niño precursor; CHIRPS deficits late summer"),
            2015: ("severe",          "Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor"),
            2018: ("moderate",        "Weak El Niño; postrera impact even at weak strength (FAO 2018)"),
            2023: ("moderate",        "Strong El Niño; one-month delay to postrera; 25%+ subsistence yield reduction"),
        },
    },
    "haiti": {
        "iso2": "HT",
        "display_name": "Haiti",
        "short_code": "HT",
        "gaul_adm0_name": "Haiti",
        "aoi_filename": "departamentos_ht.geojson",
        "map_center": {"lat": 18.85, "lon": -72.80},
        "map_zoom": 6.9,
        # Haiti's ADM1 are départements in French (the country's official lang).
        "dept_term": "département",
        "dept_term_plural": "départements",
        # Priority departments are the rainfed "dry corridor analog" per
        # el_nino_agricultural_risks.md: southern peninsula + Northwest +
        # Central Plateau. Artibonite is excluded — it's irrigated/buffered.
        # Names must match GAUL ADM1_NAME exactly (spaces, not hyphens).
        "priority_departments": ["Sud", "Sud Est", "Grande Anse", "Nippes", "Nord Ouest", "Centre"],
        "priority_label": "Drought-vulnerable departments",
        "priority_display_names": "Sud, Sud-Est, Grand'Anse, Nippes, Nord-Ouest, Centre",
        "crop_focus_caption": "printemps/été drought indicators",
        # Calibration anchors — printemps grain-fill (~Jun) through été silking
        # (~Jul-Aug), spanning the Hispaniola canícula that El Niño intensifies.
        # Curtis & Gamble 2007 place midsummer-drought onset in early June.
        "silking_window": (152, 227),  # Jun 1 → Aug 15
        # year → (severity, note). Doc-anchored events from
        # el_nino_agricultural_risks.md plus moderate analog years (NOAA ONI).
        # 1997/2015/2023 are explicitly documented as Caribbean drought years.
        "labeled_events": {
            1997: ("severe-moderate", "Super El Niño; Caribbean drought; pre-Mitch deficits"),
            2009: ("moderate",        "Moderate El Niño 2009-10"),
            2014: ("moderate",        "Weak El Niño precursor; lead-up to 2015 crisis"),
            2015: ("severe",          "Very Strong El Niño; -39% rainfed maize / -44% beans nationally; national emergency (FEWS NET 2016)"),
            2018: ("moderate",        "Weak El Niño; postrera/automne impact"),
            2023: ("moderate",        "Strong El Niño; FEWS Aug 2023 Northwest + southern peninsula impact"),
        },
    },
}

if COUNTRY not in COUNTRIES:
    raise ValueError(
        f"Unknown COUNTRY={COUNTRY!r}. Valid options: {sorted(COUNTRIES)}"
    )

CC = COUNTRIES[COUNTRY]

AOI_PATH = PROJECT_ROOT / "etl" / "aoi" / CC["aoi_filename"]
PRIORITY_DEPARTMENTS = CC["priority_departments"]


def ensure_dirs() -> None:
    for d in (RAW_DIR, CLIMATOLOGY_DIR, ENSO_DIR):
        d.mkdir(parents=True, exist_ok=True)


def today() -> date:
    """Hook so tests/notebooks can monkey-patch a fixed date."""
    return date.today()


@functools.lru_cache(maxsize=1)
def country_departments() -> frozenset[str]:
    """ADM1 names that belong to the active country, sourced from AOI_PATH.

    Used to filter mixed per-country data when ES and HT share one local
    STORAGE_ROOT. Empty (no filter) if the AOI hasn't been bootstrapped yet."""
    if not AOI_PATH.exists():
        return frozenset()
    try:
        with AOI_PATH.open() as f:
            gj = json.load(f)
    except (OSError, json.JSONDecodeError):
        return frozenset()
    return frozenset(
        feat["properties"]["ADM1_NAME"]
        for feat in gj.get("features", [])
        if feat.get("properties", {}).get("ADM1_NAME")
    )
