"""CHIRPS-Prelim daily download from UCSB Climate Hazards Center direct.

The GEE-hosted CHIRPS assets lag by ~28 days. UCSB's `data.chc.ucsb.edu`
publishes the same Prelim product with ~3-day latency. This module bridges
the gap: for any date in the [last GEE date + 1, today] window, it downloads
the daily GeoTIFF, runs zonal stats over the departamento polygons, and
returns a DataFrame that slots into the same `chirps/<dep>.parquet` schema
as the GEE-sourced data.

Endpoint:
  https://data.chc.ucsb.edu/products/CHIRPS-2.0/prelim/global_daily/tifs/p05/{year}/chirps-v2.0.{year}.{mm}.{dd}.tif.gz

Caching:
  Files are downloaded to ${STORAGE_ROOT}/cache/chirps_prelim/ so repeated
  runs don't re-fetch. ~2 MB compressed per day for the global 0.05° image;
  manageable even for a full month's gap.
"""

from __future__ import annotations

import gzip
import io
import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

import pandas as pd
import requests

from .. import config

BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/prelim/global_daily/tifs/p05"
CACHE_DIR = config.STORAGE_ROOT / "cache" / "chirps_prelim"
REQUEST_TIMEOUT = 60  # seconds per file


def _url_for(d: date) -> str:
    return f"{BASE_URL}/{d.year}/chirps-v2.0.{d.year}.{d.month:02d}.{d.day:02d}.tif.gz"


def _cache_path(d: date) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"chirps-v2.0.{d.year}.{d.month:02d}.{d.day:02d}.tif"


def fetch_daily_tif(d: date, force: bool = False) -> Path | None:
    """Download (and decompress) one day's CHIRPS-Prelim GeoTIFF to cache.
    Returns the cached path, or None if the file isn't available upstream."""
    cached = _cache_path(d)
    if cached.exists() and cached.stat().st_size > 0 and not force:
        return cached

    url = _url_for(d)
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None

    raw = resp.content  # ~2 MB per day; fine to materialize
    try:
        decompressed = gzip.decompress(raw)
    except (OSError, gzip.BadGzipFile):
        return None

    cached.write_bytes(decompressed)
    return cached


def list_available(start: date, end: date) -> list[date]:
    """HEAD each day in the range, return only those UCSB actually has."""
    out: list[date] = []
    for d in _daterange(start, end):
        url = _url_for(d)
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                out.append(d)
        except requests.RequestException:
            continue
    return out


def _daterange(start: date, end: date) -> Iterator[date]:
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def fetch_window(start: date, end: date,
                 on_progress=lambda s: None) -> pd.DataFrame:
    """Pull every available CHIRPS-Prelim day in [start, end] and run zonal
    stats over the El Salvador departamentos.

    Returns columns: date, departamento, precip_mm. is_forecast=False is
    added by the caller.
    """
    import geopandas as gpd
    import rasterstats

    if not config.AOI_PATH.exists():
        raise FileNotFoundError(
            f"AOI polygons not found at {config.AOI_PATH}. "
            "Run `python -m el_nino.etl.aoi.fetch_aoi` first."
        )

    aoi = gpd.read_file(config.AOI_PATH)
    if "ADM1_NAME" not in aoi.columns:
        # GAUL feature collection uses ADM1_NAME at top level after GeoJSON conversion
        raise ValueError("AOI GeoJSON missing ADM1_NAME column")

    rows: list[dict] = []
    available = list_available(start, end)
    on_progress(f"UCSB CHIRPS-Prelim: {len(available)} day(s) available in {start}..{end}")

    for d in available:
        tif = fetch_daily_tif(d)
        if tif is None:
            on_progress(f"  {d}: download failed")
            continue

        # Zonal stats: mean per departamento polygon. CHIRPS no-data is -9999.
        stats = rasterstats.zonal_stats(
            aoi, str(tif),
            stats=["mean"],
            nodata=-9999,
            all_touched=False,
        )
        for feature, stat in zip(aoi.itertuples(index=False), stats):
            dep = getattr(feature, "ADM1_NAME")
            mean = stat["mean"]
            if mean is None:
                continue
            rows.append({
                "date": d,
                "departamento": dep,
                "precip_mm": float(mean),
            })
        on_progress(f"  {d}: zonal stats OK ({len([r for r in rows if r['date']==d])} deps)")

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["departamento", "date"]).reset_index(drop=True)


def clear_cache() -> int:
    """Remove all cached TIFFs. Returns count deleted."""
    if not CACHE_DIR.exists():
        return 0
    n = 0
    for f in CACHE_DIR.glob("*.tif"):
        f.unlink()
        n += 1
    return n
