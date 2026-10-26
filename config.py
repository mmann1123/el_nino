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
        # Default dashboard language (dashboard/i18n.py); the UI offers a
        # toggle between this and English.
        "default_lang": "es",
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
        # Growing seasons, back to back. A departamento that fires stays listed
        # from its first fire until its season ends; the next season starts
        # clean. `end` before `start` means the season ends the next year
        # (keyed by planting year). Between seasons the dashboard recaps the
        # last one.
        "seasons": [
            {
                "key": "primera", "start": (4, 20), "end": (8, 31),
                # Alert window: primera maize silking, mid-Jul to mid-Aug (DOY).
                "alert_window_doy": (196, 227),
                # "Confirmed" tier: cropland WAPOR ETa anomaly at or below
                # z_threshold for `consecutive` dekads in a row inside
                # window_doy (Jul 1 → Aug 31). Flagged exactly La Union,
                # Morazan and San Miguel in 2018 and 2026 and nothing in
                # 2019-2025 (experiments/primera_2026_eval.py data, the
                # dashboard's own anomaly). Needs the cropland-weighted WAPOR
                # backfill.
                "confirm_rule": {"indicator": "wapor", "window_doy": (182, 243),
                                 "z_threshold": -1.25, "consecutive": 2},
                # year → (severity, note), each traced to highlighted sources in
                # experiments/evidence/ (labels.csv). "normal" = documented
                # normal season (a negative); "excluded" = mixed or non-drought
                # losses, left out of scoring. A drought year has documented
                # drought losses in at least one department.
                "labeled_events": {
                    1997: ("severe-moderate", "El Niño dry weather; ~125 000 t white maize lost (GIEWS Dec 1997)"),
                    1998: ("normal",   "Significant recovery; Mitch struck after harvest (GIEWS Sep 1998)"),
                    1999: ("normal",   "Normal to heavy rains benefited first-season crops (GIEWS Sep 1999)"),
                    2000: ("moderate", "Long July canícula severely hit crops in the west, Chalatenango and east (GIEWS Oct 2000)"),
                    2001: ("moderate", "First-season output 18% below average from drought (GIEWS Nov 2001)"),
                    2002: ("normal",   "Normal late-July/August rain; isolated damage in San Vicente, La Paz (GIEWS Sep 2002)"),
                    2003: ("normal",   "Good first-season maize output (GIEWS Oct 2003)"),
                    2004: ("normal",   "Above-average prospects despite August dry-spell losses in the east (GIEWS Oct 2004)"),
                    2009: ("moderate", "MAG: 10% losses east, 25% west, 13.7% national; GIEWS later called the harvest good (GIEWS Sep 2009, CPC Oct 2009)"),
                    2010: ("excluded", "Agatha and Matthew; maize good, beans lost to excess water (GIEWS Oct 2010)"),
                    2011: ("normal",   "Early-sown maize losses, then re-sowing and a good main harvest (GIEWS Feb 2012)"),
                    2012: ("moderate", "National harvest above average, but the East at 70% of average (FEWS NET Oct 2012)"),
                    2013: ("moderate", "July canícula; San Miguel, Usulután, La Unión; main maize −4% (GIEWS Oct 2013)"),
                    2014: ("moderate", "Maize losses 14%; eastern and western regions (FEWS NET Aug 2014)"),
                    2015: ("severe",   "El Niño drought; 64% of maize and 82% of bean area lost (FEWS NET Aug 2015)"),
                    2016: ("normal",   "Good primera outcome (GIEWS Dec 2016)"),
                    2017: ("normal",   "Good rain even in the Dry Corridor (GIEWS Jun 2017)"),
                    2018: ("moderate", "June–August dry spells, 45 000 t maize lost, 10 departments (GIEWS Nov 2018)"),
                    2019: ("normal",   "Near-average maize; eastern deficits offset (GIEWS Oct 2019)"),
                    2020: ("excluded", "Tropical Storm Amanda; replanted, normal outcome (GIEWS Aug 2020)"),
                    2021: ("normal",   "Well above-average production (GIEWS Oct 2021)"),
                    2022: ("normal",   "Main maize conditions generally favourable (GIEWS Aug 2022)"),
                    2023: ("moderate", "Prolonged primera dry spells, below-average cereal output (GIEWS Apr 2024)"),
                    2024: ("excluded", "Dry planting stage, then floods (GIEWS Nov 2024)"),
                    2025: ("normal",   "Adequate June–July rain; near-average output (GIEWS Jan 2026)"),
                    2026: ("moderate", "Severe El Niño drought, prolonged August canícula; eastern Dry Corridor worst (GIEWS Oct 2026)"),
                },
            },
            {
                # Beans and sorghum, planted late Aug–Sep, harvested Nov–Jan.
                # Alert window: planting and establishment, Sep 2 → Oct 2.
                # Provisional: only two documented drought seasons (TODO.md).
                "key": "postrera", "start": (9, 1), "end": (1, 31),
                "alert_window_doy": (245, 275),
                "confirm_rule": None,
                # Traced to experiments/evidence/labels.csv, as for Haiti.
                "labeled_events": {
                    1997: ("normal",   "October rain irregular, no relevant effect on second season (GIEWS Dec 1997)"),
                    2000: ("excluded", "Adverse weather, cause unclear (GIEWS Mar 2001)"),
                    2001: ("normal",   "Satisfactory second-season outturns (GIEWS Feb 2002)"),
                    2002: ("normal",   "Satisfactory growing conditions (GIEWS Oct 2002)"),
                    2003: ("normal",   "Second-season harvest completed, normal (GIEWS Feb 2004)"),
                    2009: ("excluded", "Storm Ida (GIEWS Apr 2010)"),
                    2010: ("excluded", "Hurricane rain then October dry spell (GIEWS Dec 2010)"),
                    2011: ("excluded", "Tropical depression 12-E (GIEWS Feb 2012)"),
                    2012: ("normal",   "Average rain, normal cessation (FEWS NET Nov 2012)"),
                    2013: ("normal",   "All three seasons favoured (GIEWS Mar 2014)"),
                    2014: ("normal",   "Forecast early end of rains did not materialize (FEWS NET Nov 2014)"),
                    2015: ("normal",   "Good rain from late September (FEWS NET Dec 2015)"),
                    2016: ("normal",   "Good weather, favourable prospects (GIEWS Dec 2016)"),
                    2017: ("normal",   "Best Dry Corridor harvests in years (FEWS NET Dec 2017)"),
                    2018: ("excluded", "Irregular Sep–Oct rain but torrential October rain and an average harvest (FEWS NET, GIEWS)"),
                    2019: ("excluded", "Torrential October rain (GIEWS May 2020)"),
                    2020: ("excluded", "Hurricanes Eta and Iota (GIEWS Apr 2021)"),
                    2021: ("normal",   "Near-average postrera yields (FEWS NET Feb 2022)"),
                    2022: ("excluded", "Excess moisture, Hurricane Julia (FEWS NET Feb 2023)"),
                    2023: ("moderate", "September rain 40–70% below average in the east; postrera yields cut in the Dry Corridor (FEWS NET Oct 2023, Jan 2024)"),
                    2024: ("excluded", "Tropical Storm Sara (FEWS NET Nov 2025)"),
                    2025: ("moderate", "Erratic rain, dry spells and heat; localized red bean losses in the Dry Corridor (FEWS NET Dec 2025, Jan 2026)"),
                },
            },
        ],
    },
    "haiti": {
        "iso2": "HT",
        "display_name": "Haiti",
        "short_code": "HT",
        "default_lang": "fr",
        "gaul_adm0_name": "Haiti",
        "aoi_filename": "departamentos_ht.geojson",
        "map_center": {"lat": 18.85, "lon": -73.00},
        "map_zoom": 6.2,
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
        "seasons": [
            {
                "key": "printemps", "start": (3, 1), "end": (7, 31),
                # Alert window: May 15 → Jul 31. Documented spring droughts
                # often start in May (2012, 2020, 2022, 2024), before the
                # Hispaniola canícula (Curtis & Gamble 2007: early June).
                "alert_window_doy": (135, 212),
                # No calibrated "Confirmed" rule for Haiti yet — the table
                # shows the Alert tier only.
                "confirm_rule": None,
                # year → (severity, note), each traced to highlighted sources in
                # experiments/evidence/ (labels.csv). "normal" = documented
                # normal season (a negative); "excluded" = losses from something
                # other than drought, left out of scoring.
                "labeled_events": {
                    1997: ("moderate", "Prolonged first-half drought affected all crops (GIEWS Dec 1997)"),
                    2009: ("normal",   "Abundant, well-distributed rain; NW mountains only poor harvest (GIEWS 2009-10)"),
                    2010: ("normal",   "Spring rains abundant and beneficial (GIEWS Aug 2010)"),
                    2011: ("moderate", "Dry spring; North, Northwest, Northeast, High Central Plateau worst (GIEWS Feb 2012)"),
                    2012: ("moderate", "Dry May–early June cut maize yields (GIEWS Aug 2012)"),
                    2013: ("normal",   "Maize yields recovered (GIEWS Oct 2013)"),
                    2014: ("moderate", "Jun–Aug dryness; Central Plateau, North-West, South-East, West (GIEWS Dec 2014)"),
                    2015: ("severe",   "El Niño drought, losses in all parts of the country (FEWS NET Feb 2016)"),
                    2016: ("normal",   "Good harvest after El Niño ended (GIEWS Oct 2016)"),
                    2017: ("excluded", "Excess rain and dry spells mixed (GIEWS Nov 2017)"),
                    2018: ("moderate", "June dryness; maize 13% below 5-yr avg; Artibonite, Centre (GIEWS Dec 2018)"),
                    2019: ("moderate", "Apr–Aug deficit; production ~10% down (GIEWS Jun 2020)"),
                    2020: ("moderate", "Apr–Jul deficit hit main maize and paddy (GIEWS Jun 2021)"),
                    2021: ("normal",   "Abundant Mar–Apr rain (GIEWS Jun 2021)"),
                    2022: ("moderate", "Below-average May–June rain; below-average harvest (GIEWS Aug 2022)"),
                    2023: ("moderate", "Apr–Sep rain 50% below average (FEWS NET Oct 2023)"),
                    2024: ("moderate", "Mar–May dry spells hurt establishment (GIEWS Oct 2024)"),
                    2025: ("moderate", "Main season hit by dry weather (GIEWS Dec 2025)"),
                },
            },
            {
                # Maize, beans, sorghum, planted Aug–Sep, harvested Nov–Jan.
                # Alert window: Sep 15 → Nov 1.
                "key": "automne", "start": (8, 1), "end": (1, 31),
                "alert_window_doy": (258, 305),
                "confirm_rule": None,
                "labeled_events": {
                    1997: ("normal",   "Second-season planting under adequate weather (GIEWS Dec 1997)"),
                    2009: ("normal",   "Second-season planting well advanced (GIEWS Oct 2009)"),
                    2010: ("normal",   "Favourable, well-distributed rain; good output expected (GIEWS Nov 2010)"),
                    2013: ("moderate", "Nov–Mar deficit, 2013/14 autumn losses in the Nord-Ouest (GIEWS Apr 2014)"),
                    2015: ("severe",   "El Niño active in both seasons; poor Jan–Feb harvests (FEWS NET Feb 2016)"),
                    2018: ("normal",   "Oct–Nov rain improved crops in most areas (FEWS NET Nov–Dec 2018)"),
                    2019: ("moderate", "Second-season rain deficit; poor fall and winter harvests (FEWS NET Feb 2020)"),
                    2021: ("moderate", "Aug–Sep deficit, below-average second season (GIEWS Nov 2021)"),
                    2022: ("moderate", "Fall crops below normal; drought since Nov in NW, NE, S, SE, Grand'Anse (FEWS NET Feb 2023)"),
                    2023: ("moderate", "Below-average fall harvests; Aug–Oct deficits in the south (FEWS NET Dec 2023, WFP)"),
                    2026: ("moderate", "70+ day deficit, maize losses in Centre, Ouest, Sud, Sud-Est (FEWS NET Sep 2026)"),
                },
            },
        ],
    },
}

if COUNTRY not in COUNTRIES:
    raise ValueError(
        f"Unknown COUNTRY={COUNTRY!r}. Valid options: {sorted(COUNTRIES)}"
    )

CC = COUNTRIES[COUNTRY]

AOI_PATH = PROJECT_ROOT / "etl" / "aoi" / CC["aoi_filename"]
PRIORITY_DEPARTMENTS = CC["priority_departments"]


def season_cfg(key: str) -> dict:
    """The active country's season entry with this key."""
    return next(s for s in CC["seasons"] if s["key"] == key)


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
