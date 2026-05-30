"""NOAA ONI (Oceanic Niño Index) ingestion. Labels each month
El Niño / Neutral / La Niña using the standard ±0.5°C threshold.
"""

from __future__ import annotations

import io
from datetime import date

import pandas as pd
import requests

from .. import config
from . import storage

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# CPC's "5 overlapping seasons" rule for event classification is approximated
# by labeling each month directly from ONI ≥ 0.5 / ≤ -0.5. Good enough for
# year-compare presets in the dashboard.
EL_NINO_THRESHOLD = 0.5
LA_NINA_THRESHOLD = -0.5

# Canonical "notable" analog years for dashboard overlays, documentation, and
# trigger calibration narratives. Single source of truth — do not redefine
# elsewhere.
#
# El Niño: the four very-strong / strong events with documented agricultural
# impact in El Salvador and Haiti (see el_nino_agricultural_risks.md).
#   1982-83  Very Strong
#   1997-98  Very Strong ("super" El Niño)
#   2015-16  Very Strong (60% maize / 80% beans loss in ES Dry Corridor)
#   2023-24  Strong
# Listed by onset year (boreal-summer development year).
NOTABLE_EL_NINO_YEARS: list[int] = [1982, 1997, 2015, 2023]

# La Niña: strong / multi-year events per NOAA CPC ONI (ggweather.com/enso/oni.htm
# and psl.noaa.gov/enso/climaterisks). Listed by onset year. 1973-76 omitted
# because it predates the CHIRPS record (1981-); 2020 is the onset of the
# 2020-23 "triple-dip" event.
#   1988-89   Strong
#   1998-2001 Strong (multi-year)
#   2007-08   Strong
#   2010-12   Strong (multi-year)
#   2020-23   Moderate, triple-dip (rare)
NOTABLE_LA_NINA_YEARS: list[int] = [1988, 1998, 2007, 2010, 2020]


def fetch() -> pd.DataFrame:
    resp = requests.get(ONI_URL, timeout=30)
    resp.raise_for_status()
    raw = pd.read_csv(io.StringIO(resp.text), sep=r"\s+")
    # Columns: SEAS YR TOTAL ANOM
    raw = raw.rename(columns={"YR": "year", "SEAS": "season", "ANOM": "oni"})
    raw["season_center_month"] = raw["season"].map(_season_to_center_month)
    raw["date"] = pd.to_datetime(dict(year=raw["year"], month=raw["season_center_month"], day=1)).dt.date
    raw["phase"] = raw["oni"].apply(_classify)
    return raw[["date", "year", "season", "oni", "phase"]].sort_values("date").reset_index(drop=True)


def save(df: pd.DataFrame) -> None:
    out = config.ENSO_DIR / "oni.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)


def load() -> pd.DataFrame:
    out = config.ENSO_DIR / "oni.parquet"
    return storage.read_parquet(out)


def el_nino_years(df: pd.DataFrame | None = None) -> list[int]:
    if df is None:
        df = load()
    if df.empty:
        return []
    # A year "is" an El Niño year if any 3-month season centered in it has ONI ≥ 0.5.
    flagged = df[df["phase"] == "El Niño"]
    return sorted(flagged["year"].unique().tolist())


def la_nina_years(df: pd.DataFrame | None = None) -> list[int]:
    if df is None:
        df = load()
    if df.empty:
        return []
    flagged = df[df["phase"] == "La Niña"]
    return sorted(flagged["year"].unique().tolist())


def _season_to_center_month(season: str) -> int:
    mapping = {
        "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
        "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
    }
    return mapping.get(season.strip().upper(), 1)


def _classify(oni: float) -> str:
    if oni >= EL_NINO_THRESHOLD:
        return "El Niño"
    if oni <= LA_NINA_THRESHOLD:
        return "La Niña"
    return "Neutral"
