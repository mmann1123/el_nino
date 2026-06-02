"""Synthetic-data generator. Lets the dashboard render without GEE access
configured. Produces realistic-shaped CHIRPS/SMAP/WAPOR/IMERG timeseries
per department: seasonal cycle + AR(1) noise + a 2015-like dry anomaly in
the canícula window of El Niño years from the NOAA ONI.

The seasonal cycle (primera/postrera, canícula DOY 196-218) is ES-tuned;
under COUNTRY=haiti it still renders plausible-looking traces but the
phenology won't match Haitian printemps/été/automne. Synthetic data is for
local UX work only, so this approximation is OK in practice — real Haiti
data should come from `python -m el_nino.etl.run_etl backfill`.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .. import config
from . import climatology, enso, freshness, storage
from .indicators import INDICATORS

DEPARTAMENTO_FALLBACK = [
    "Ahuachapan", "Cabanas", "Chalatenango", "Cuscatlan", "La Libertad",
    "La Paz", "La Union", "Morazan", "San Miguel", "San Salvador",
    "San Vicente", "Santa Ana", "Sonsonate", "Usulutan",
]

RNG = np.random.default_rng(20260528)


def _departamentos() -> list[str]:
    if not config.AOI_PATH.exists():
        return DEPARTAMENTO_FALLBACK
    with config.AOI_PATH.open() as f:
        gj = json.load(f)
    return sorted(feat["properties"].get("ADM1_NAME", "") for feat in gj.get("features", []))


def _priority_modifier(dep: str) -> float:
    return 1.15 if dep in config.PRIORITY_DEPARTMENTS else 1.0


def _el_nino_year_set() -> set[int]:
    # Light defaults if NOAA ONI hasn't been fetched yet.
    df = enso.load()
    if df.empty:
        return {1982, 1986, 1987, 1991, 1994, 1997, 2002, 2004, 2006, 2009, 2014, 2015, 2018, 2023}
    return set(enso.el_nino_years(df))


def synth_chirps(start: date, end: date) -> None:
    deps = _departamentos()
    nino_years = _el_nino_year_set()
    rows: list[dict] = []
    dates = pd.date_range(start, end, freq="D")

    for dep in deps:
        amp = 8.0 * _priority_modifier(dep)  # daily mean mm
        base = []
        prev = 0.0
        for d in dates:
            # Bimodal seasonal cycle: primera (May-Aug) + postrera (Aug-Nov)
            doy = d.timetuple().tm_yday
            seasonal = 0.0
            if 120 <= doy <= 230:
                seasonal = 12.0 * np.sin(np.pi * (doy - 120) / 110)
            elif 230 < doy <= 320:
                seasonal = 9.0 * np.sin(np.pi * (doy - 230) / 90)
            # Canícula dip
            if 196 <= doy <= 218:
                seasonal *= 0.55
            # El Niño years: extend & deepen the canícula
            if d.year in nino_years and 180 <= doy <= 240:
                seasonal *= 0.45
            noise = max(0.0, RNG.gamma(0.6, amp + seasonal) + 0.3 * prev - 1.5)
            prev = noise
            base.append({"date": d.date(), "departamento": dep, "precip_mm": noise, "is_forecast": False})
        rows.extend(base)

    daily = pd.DataFrame(rows)

    # Aggregate to pentads and attach SPI
    from .indicators.chirps import aggregate_to_pentad, attach_spi
    pentads = aggregate_to_pentad(daily)
    pentads = attach_spi(pentads)

    pentads["is_forecast"] = False
    for dep, group in pentads.groupby("departamento"):
        out = group[["date", "departamento", "precip_pentad_mm", "spi_1", "spi_3", "spi_6", "is_forecast"]]
        storage.upsert_raw("chirps", dep, out)


def synth_smap(start: date, end: date) -> None:
    deps = _departamentos()
    nino_years = _el_nino_year_set()
    smap_start = max(start, date(2015, 4, 1))  # SMAP begins April 2015
    dates = pd.date_range(smap_start, end, freq="3D")

    for dep in deps:
        rows = []
        prev = 0.30
        for d in dates:
            doy = d.timetuple().tm_yday
            seasonal_baseline = 0.32 + 0.10 * np.sin(2 * np.pi * (doy - 90) / 365)
            anomaly = 0.0
            if d.year in nino_years and 180 <= doy <= 240:
                anomaly = -0.08 * _priority_modifier(dep)
            val = 0.7 * prev + 0.3 * (seasonal_baseline + anomaly + RNG.normal(0, 0.015))
            val = float(np.clip(val, 0.05, 0.55))
            prev = val
            rows.append({"date": d.date(), "departamento": dep, "rzsm_m3m3": val, "is_forecast": False})
        df = pd.DataFrame(rows)
        storage.upsert_raw("smap", dep, df)


def synth_wapor(start: date, end: date) -> None:
    deps = _departamentos()
    nino_years = _el_nino_year_set()
    # Dekadal: 3 records per month
    dates = []
    cur = start.replace(day=1) if start.day != 1 else start
    while cur <= end:
        for day in (1, 11, 21):
            d = cur.replace(day=day)
            if start <= d <= end:
                dates.append(d)
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)

    for dep in deps:
        rows = []
        for d in dates:
            doy = d.timetuple().tm_yday
            base_eta = 35 + 25 * np.sin(2 * np.pi * (doy - 60) / 365)
            anomaly = 0.0
            if d.year in nino_years and 196 <= doy <= 240:
                anomaly = -8.0 * _priority_modifier(dep)
            val = base_eta + anomaly + RNG.normal(0, 3.0)
            rows.append({"date": d, "departamento": dep, "eta_mm": float(val), "is_forecast": False})
        df = pd.DataFrame(rows)
        storage.upsert_raw("wapor", dep, df)


def synth_imerg(start: date, end: date) -> None:
    # IMERG is daily, similar shape to CHIRPS daily; skip SPI computation.
    deps = _departamentos()
    nino_years = _el_nino_year_set()
    dates = pd.date_range(start, end, freq="D")

    for dep in deps:
        rows = []
        for d in dates:
            doy = d.timetuple().tm_yday
            seasonal = 0.0
            if 120 <= doy <= 320:
                seasonal = 10.0 * np.sin(np.pi * (doy - 120) / 200)
            if d.year in nino_years and 180 <= doy <= 240:
                seasonal *= 0.5
            val = max(0.0, RNG.gamma(0.7, 8.0 + seasonal) - 1.0)
            rows.append({"date": d.date(), "departamento": dep, "imerg_precip_mm": val, "is_forecast": False})
        df = pd.DataFrame(rows)
        storage.upsert_raw("imerg", dep, df)


def attach_anomaly_z(indicator_name: str) -> None:
    """After climatology is computed, write value_anom_z back into the raw parquet
    for the indicator's primary column."""
    indicator_cls = INDICATORS[indicator_name]
    clim = climatology.load(indicator_name)
    if clim.empty:
        return
    primary = indicator_cls.primary_column
    clim_primary = clim[clim["value_column"] == primary]
    if clim_primary.empty:
        return

    indicator_dir = config.RAW_DIR / indicator_name
    for parquet in sorted(indicator_dir.glob("*.parquet")):
        df = storage.read_parquet(parquet)
        if df.empty or primary not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["doy"] = df["date"].dt.dayofyear
        dep_clim = clim_primary[clim_primary["departamento"] == df["departamento"].iloc[0]]
        df = df.merge(dep_clim[["doy", "mu", "sigma"]], on="doy", how="left")
        df["value_anom_z"] = (df[primary] - df["mu"]) / df["sigma"].replace(0, np.nan)
        df = df.drop(columns=["doy", "mu", "sigma"])
        df["date"] = df["date"].dt.date
        storage.write_parquet(df, parquet)


def update_freshness(today_: date) -> None:
    records = []
    for name, cls in INDICATORS.items():
        last_obs = _last_obs(name)
        records.append(freshness.make_record(
            indicator=name,
            last_obs=last_obs,
            fresh_days=cls.freshness.fresh_days,
            aging_days=cls.freshness.aging_days,
            cadence_days=cls.freshness.expected_cadence_days,
            today_=today_,
        ))
    freshness.write_all(records)


def _last_obs(indicator: str) -> date | None:
    indicator_dir = config.RAW_DIR / indicator
    if not indicator_dir.exists():
        return None
    latest: date | None = None
    for parquet in indicator_dir.glob("*.parquet"):
        df = storage.read_parquet(parquet)
        if df.empty:
            continue
        d = pd.to_datetime(df["date"]).max().date()
        if latest is None or d > latest:
            latest = d
    return latest
