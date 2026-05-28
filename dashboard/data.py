"""DuckDB-backed read layer for the dashboard. Reads parquet files directly
(DuckDB can query parquet without ingesting). One thread-safe connection per
process, cached via @st.cache_resource.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from .. import config
from ..etl import climatology, enso
from ..etl.indicators import INDICATORS


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=":memory:")


@st.cache_data(ttl=3600)
def list_departamentos() -> list[str]:
    deps: set[str] = set()
    for ind in INDICATORS:
        d = config.RAW_DIR / ind
        if not d.exists():
            continue
        for f in d.glob("*.parquet"):
            try:
                df = pd.read_parquet(f, columns=["departamento"])
                if not df.empty:
                    deps.update(df["departamento"].dropna().unique().tolist())
            except Exception:
                continue
    return sorted(deps)


@st.cache_data(ttl=3600)
def load_indicator(indicator: str, departamento: str) -> pd.DataFrame:
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


@st.cache_data(ttl=3600)
def load_climatology(indicator: str, departamento: str, value_column: str) -> pd.DataFrame:
    clim = climatology.load(indicator)
    if clim.empty:
        return clim
    out = clim[(clim["departamento"] == departamento) & (clim["value_column"] == value_column)]
    return out.sort_values("doy").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_enso() -> pd.DataFrame:
    return enso.load()


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
