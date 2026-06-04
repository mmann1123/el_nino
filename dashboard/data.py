"""DuckDB-backed read layer for the dashboard. Reads parquet files directly
(DuckDB can query parquet without ingesting). One thread-safe connection per
process, cached via @st.cache_resource.

`ALL` is a sentinel for the "All departamentos — country mean" view: the
load_indicator / load_climatology functions average across every per-dep
parquet by date / DOY respectively.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import streamlit as st

from .. import config
from ..etl import climatology, enso
from ..etl.indicators import INDICATORS

ALL = "All (country mean)"


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=":memory:")


@st.cache_data(ttl=3600)
def list_departamentos() -> list[str]:
    deps: set[str] = set()
    country = config.country_departments()  # frozenset; empty = no filter
    for ind in INDICATORS:
        d = config.RAW_DIR / ind
        if not d.exists():
            continue
        for f in d.glob("*.parquet"):
            try:
                df = pd.read_parquet(f, columns=["departamento"])
                if not df.empty:
                    names = df["departamento"].dropna().unique().tolist()
                    if country:
                        names = [n for n in names if n in country]
                    deps.update(names)
            except Exception:
                continue
    return [ALL] + sorted(deps)


@st.cache_data(ttl=3600)
def load_indicator(indicator: str, departamento: str) -> pd.DataFrame:
    if departamento == ALL:
        return _load_indicator_all(indicator)
    safe_dep = _safe(departamento)
    path = config.RAW_DIR / indicator / f"{safe_dep}.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["doy"] = df["date"].dt.dayofyear
    return df.sort_values("date").reset_index(drop=True)


def _load_indicator_all(indicator: str) -> pd.DataFrame:
    """Country mean: pool every per-departamento parquet and average numeric
    columns by date. Preserves is_forecast (any row marked is_forecast on any
    departamento for that date stays True) and departamento label = ALL.

    When ES and HT share one local STORAGE_ROOT, restrict to the active
    country's parquets via the AOI department set."""
    d = config.RAW_DIR / indicator
    if not d.exists():
        return pd.DataFrame()
    country = config.country_departments()
    frames = []
    for f in d.glob("*.parquet"):
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        if df.empty:
            continue
        if country and df["departamento"].iloc[0] not in country:
            continue
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    pooled = pd.concat(frames, ignore_index=True)
    pooled["date"] = pd.to_datetime(pooled["date"])
    numeric_cols = [c for c in pooled.columns
                    if c not in ("date", "departamento", "is_forecast")
                    and pd.api.types.is_numeric_dtype(pooled[c])]
    agg_spec = {c: "mean" for c in numeric_cols}
    if "is_forecast" in pooled.columns:
        # Any row marked is_forecast → keep as forecast in the aggregate.
        agg_spec["is_forecast"] = "any"
    out = pooled.groupby("date", as_index=False).agg(agg_spec)
    out["departamento"] = ALL
    out["year"] = out["date"].dt.year
    out["doy"] = out["date"].dt.dayofyear
    return out.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_climatology(indicator: str, departamento: str, value_column: str) -> pd.DataFrame:
    clim = climatology.load(indicator)
    if clim.empty:
        return clim
    if departamento == ALL:
        # Average per-departamento percentile fences by DOY across the active
        # country's departments — gives a country-mean envelope. Filter against
        # the AOI department set so mixed local data (ES + HT in one
        # STORAGE_ROOT) doesn't cross-pollute.
        sub = clim[clim["value_column"] == value_column]
        country = config.country_departments()
        if country:
            sub = sub[sub["departamento"].isin(country)]
        if sub.empty:
            return sub
        agg_spec = {
            "mu": "mean", "sigma": "mean",
            "p05": "mean", "p10": "mean", "p25": "mean",
            "p50": "mean", "p75": "mean", "p90": "mean", "p95": "mean",
        }
        if "n_samples" in sub.columns:
            # Per-dep n is already pooled samples; mean across deps reflects
            # the typical pool size used to fit each fence.
            agg_spec["n_samples"] = "mean"
        agg = sub.groupby("doy", as_index=False).agg(agg_spec)
        agg["departamento"] = ALL
        agg["value_column"] = value_column
        return agg.sort_values("doy").reset_index(drop=True)
    out = clim[(clim["departamento"] == departamento) & (clim["value_column"] == value_column)]
    return out.sort_values("doy").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_raw_climatology(indicator: str, departamento: str, value_column: str) -> pd.DataFrame:
    """Recompute the per-DOY climatology WITHOUT any DOY window — the raw,
    unsmoothed version. Used only by the 'How smooth is the envelope?'
    diagnostic expander so users can see what the smoothing buys them."""
    from ..etl import climatology as clim_mod
    if departamento == ALL:
        # For the All view, average raw per-dep climatologies. Recompute raw
        # for every dep, then average percentiles by DOY.
        from ..etl.indicators import INDICATORS
        cls = INDICATORS.get(indicator)
        if cls is None:
            return pd.DataFrame()
        raw = clim_mod.compute_for_indicator(indicator, [value_column], doy_window=0)
        if raw.empty:
            return raw
        sub = raw[raw["value_column"] == value_column]
        country = config.country_departments()
        if country:
            sub = sub[sub["departamento"].isin(country)]
        agg_spec = {c: "mean" for c in
                    ["mu", "sigma", "p05", "p10", "p25", "p50", "p75", "p90", "p95"]}
        return sub.groupby("doy", as_index=False).agg(agg_spec).sort_values("doy").reset_index(drop=True)
    raw = clim_mod.compute_for_indicator(indicator, [value_column], doy_window=0)
    if raw.empty:
        return raw
    out = raw[(raw["departamento"] == departamento) & (raw["value_column"] == value_column)]
    return out.sort_values("doy").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_enso() -> pd.DataFrame:
    return enso.load()


@st.cache_data(ttl=3600)
def latest_nino34() -> dict | None:
    """Freshest weekly Niño 3.4 reading, or None if not fetched yet."""
    return enso.latest_nino34()


@st.cache_data(ttl=3600)
def latest_observations() -> pd.DataFrame:
    """One row per (indicator, departamento) at the most recent date."""
    out: list[pd.DataFrame] = []
    for name, cls in INDICATORS.items():
        d = config.RAW_DIR / name
        if not d.exists():
            continue
        for f in d.glob("*.parquet"):
            df = pd.read_parquet(f)
            if df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"])
            obs_df = df[~df.get("is_forecast", pd.Series([False] * len(df))).fillna(False)]
            if obs_df.empty:
                continue
            latest = obs_df.iloc[-1:].copy()
            latest["indicator"] = name
            latest["primary_value"] = latest.get(cls.primary_column)
            out.append(latest)
    if not out:
        return pd.DataFrame()
    return pd.concat(out, ignore_index=True)


def _safe(departamento: str) -> str:
    return (
        departamento
        .replace(" ", "_")
        .replace("ó", "o").replace("ú", "u").replace("á", "a")
        .replace("é", "e").replace("í", "i").replace("ñ", "n")
    )
