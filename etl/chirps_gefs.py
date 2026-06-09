"""CHIRPS-GEFS v3 — 15-day rainfall forecast, bias-corrected to CHIRPS.

UCSB's Climate Hazards Center publishes GEFSv12 forecasts quantile-matched
to the CHIRPS historical distribution at 0.05°. Files appear daily on
data.chc.ucsb.edu around 08:30 UTC for that day's 00 UTC issuance. We pull
the rolling 5/10/15-day totals, difference them into three forward 5-day
pentads (matching the schema the rest of the pipeline already uses), and
run zonal stats over the active country's departments.

Streaming — no permanent files:
  CHC ships ~66 MB global stripped TIFFs (PackBits, not COG). We open each
  file via `/vsicurl/` and read only the row-strips that intersect the
  country bbox — typically 1-2 MB of HTTP range fetches per file instead of
  the full 66 MB. Nothing is written to disk.

Endpoints:
  https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3/{5,10,15}_day/global/data/{year}/c3g_{YYYY.MM.DD}.tif
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Callable

import pandas as pd
import requests

from .. import config

BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3"
LEADS_DAYS = (5, 10, 15)  # cumulative rolling totals published by CHC
REQUEST_TIMEOUT = 30  # seconds for HEAD checks
NODATA = -9999.0

# Strips are 1-row × 7200-col PackBits, so GDAL needs to fetch full strips
# anyway — small chunks are wasteful. Larger chunks amortize HTTP overhead.
_VSI_ENV = {
    "GDAL_HTTP_TIMEOUT": "60",
    "CPL_VSIL_CURL_USE_HEAD": "YES",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "VSI_CACHE": "TRUE",
    "VSI_CACHE_SIZE": "10000000",  # 10 MB per file
    "CPL_VSIL_CURL_CHUNK_SIZE": "524288",  # 512 KB range reads
}


def _url_for(lead_days: int, issuance: date) -> str:
    # CHC zero-pads the 5-day path (`05_day/`) but not 10/15. Match exactly.
    lead_seg = f"{lead_days:02d}_day" if lead_days < 10 else f"{lead_days}_day"
    return (
        f"{BASE_URL}/{lead_seg}/global/data/{issuance.year}/"
        f"c3g_{issuance.year}.{issuance.month:02d}.{issuance.day:02d}.tif"
    )


def _vsicurl(url: str) -> str:
    return f"/vsicurl/{url}"


def issuance_available(issuance: date) -> bool:
    """Check whether all three lead-day totals are published for this issuance.
    A HEAD on each — fast (<1s total) and cheap (no body)."""
    for lead in LEADS_DAYS:
        try:
            r = requests.head(_url_for(lead, issuance), timeout=REQUEST_TIMEOUT)
        except requests.RequestException:
            return False
        if r.status_code != 200:
            return False
    return True


def latest_available_issuance(today_: date | None = None, max_lookback: int = 3) -> date | None:
    """Walk back from yesterday until a fully-published issuance is found.
    Caps at `max_lookback` days so a prolonged CHC outage surfaces as None
    rather than spinning."""
    today_ = today_ or config.today()
    for back in range(1, max_lookback + 1):
        d = today_ - timedelta(days=back)
        if issuance_available(d):
            return d
    return None


def _read_window_mean(url: str, geometries) -> dict[str, float]:
    """Open `url` via /vsicurl/, read only the AOI-bbox window, compute
    mean precip per polygon. Returns {ADM1_NAME: mean_mm}."""
    import rasterio
    from rasterio.windows import from_bounds, Window
    import rasterstats

    with rasterio.Env(**_VSI_ENV):
        with rasterio.open(_vsicurl(url)) as src:
            minx, miny, maxx, maxy = geometries.total_bounds
            # Pad by one pixel each side so polygons clipping the edge aren't truncated.
            px = src.res[0]
            win = from_bounds(
                minx - px, miny - px, maxx + px, maxy + px,
                transform=src.transform,
            ).round_offsets().round_lengths()
            # Clamp to dataset extent.
            win = Window(
                col_off=max(0, win.col_off),
                row_off=max(0, win.row_off),
                width=min(src.width - max(0, win.col_off), win.width),
                height=min(src.height - max(0, win.row_off), win.height),
            )
            arr = src.read(1, window=win)
            transform = src.window_transform(win)
            src_nodata = src.nodata if src.nodata is not None else NODATA

    stats = rasterstats.zonal_stats(
        geometries, arr,
        affine=transform,
        nodata=src_nodata,
        stats=["mean"],
        all_touched=False,
    )
    out: dict[str, float] = {}
    for feature, stat in zip(geometries.itertuples(index=False), stats):
        m = stat["mean"]
        if m is None:
            continue
        out[getattr(feature, "ADM1_NAME")] = float(m)
    return out


def fetch_pentad_totals(
    issuance: date,
    on_progress: Callable[[str], None] = lambda s: None,
) -> pd.DataFrame:
    """Pull the 5/10/15-day rolling totals for `issuance`, difference into three
    forward 5-day pentads (days 0-5, 5-10, 10-15 from issuance), aggregate by
    departamento. Returns rows: date, departamento, precip_pentad_mm, year, pentad.

    Caller is responsible for adding is_forecast=True / SPI null columns and
    upserting into the chirps parquets.
    """
    import geopandas as gpd

    if not config.AOI_PATH.exists():
        raise FileNotFoundError(
            f"AOI polygons not found at {config.AOI_PATH}. "
            "Run `python -m el_nino.etl.aoi.fetch_aoi` first."
        )

    aoi = gpd.read_file(config.AOI_PATH)
    if "ADM1_NAME" not in aoi.columns:
        raise ValueError("AOI GeoJSON missing ADM1_NAME column")

    # Pull each lead-day cumulative total. Each fetch is ~1-2 MB of strips
    # over a country-sized bbox via /vsicurl/.
    cum: dict[int, dict[str, float]] = {}
    for lead in LEADS_DAYS:
        url = _url_for(lead, issuance)
        on_progress(f"  {lead}-day total: {url.rsplit('/', 1)[-1]}")
        cum[lead] = _read_window_mean(url, aoi)

    # Difference cumulatives into forward 5-day pentads.
    # pentad_i covers days (5*(i-1), 5*i] from issuance, with pentad_end = issuance + 5*i.
    rows: list[dict] = []
    deps = set().union(*cum.values())
    for i, lead in enumerate(LEADS_DAYS, start=1):
        prev = LEADS_DAYS[i - 2] if i > 1 else 0
        pent_end = issuance + timedelta(days=lead)
        for dep in deps:
            v_lead = cum[lead].get(dep)
            v_prev = cum[prev].get(dep, 0.0) if i > 1 else 0.0
            if v_lead is None:
                continue
            pent = v_lead - v_prev
            # Numerical noise from float subtraction can yield tiny negatives.
            if pent < 0:
                pent = 0.0
            rows.append({"date": pent_end, "departamento": dep, "precip_pentad_mm": pent})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    df["pentad"] = ((pd.to_datetime(df["date"]).dt.dayofyear - 1) // 5) + 1
    df.loc[df["pentad"] > 73, "pentad"] = 73
    return df.sort_values(["departamento", "date"]).reset_index(drop=True)
