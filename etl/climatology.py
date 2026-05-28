"""Per-DOY climatology fences (μ, σ, p05/p10/p25/p50/p75/p90/p95) for each
indicator × departamento. Baseline period from config.

The dashboard joins current values to this table by (indicator, departamento,
doy) to draw the envelope.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from . import storage

CLIMATOLOGY_COLUMNS = ["mu", "sigma", "p05", "p10", "p25", "p50", "p75", "p90", "p95"]


def compute_for_indicator(indicator_name: str, value_columns: list[str]) -> pd.DataFrame:
    """Walk every per-departamento parquet, compute per-DOY percentiles, and
    return a tidy frame: (departamento, value_column, doy, mu, sigma, p05...p95).
    """
    rows: list[pd.DataFrame] = []
    indicator_dir = config.RAW_DIR / indicator_name
    if not indicator_dir.exists():
        return pd.DataFrame()

    for parquet in sorted(indicator_dir.glob("*.parquet")):
        df = storage.read_parquet(parquet)
        if df.empty:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["doy"] = df["date"].dt.dayofyear
        baseline = df[(df["year"] >= config.CLIMATOLOGY_START_YEAR) & (df["year"] <= config.CLIMATOLOGY_END_YEAR)]
        if baseline.empty:
            continue

        for col in value_columns:
            if col not in baseline.columns:
                continue
            grouped = baseline.groupby("doy")[col].agg(
                mu="mean",
                sigma="std",
                p05=lambda s: np.nanpercentile(s, 5),
                p10=lambda s: np.nanpercentile(s, 10),
                p25=lambda s: np.nanpercentile(s, 25),
                p50=lambda s: np.nanpercentile(s, 50),
                p75=lambda s: np.nanpercentile(s, 75),
                p90=lambda s: np.nanpercentile(s, 90),
                p95=lambda s: np.nanpercentile(s, 95),
            ).reset_index()
            grouped["departamento"] = baseline["departamento"].iloc[0]
            grouped["value_column"] = col
            rows.append(grouped)

    if not rows:
        return pd.DataFrame()

    return pd.concat(rows, ignore_index=True)[
        ["departamento", "value_column", "doy"] + CLIMATOLOGY_COLUMNS
    ]


def compute_anomaly_z(values: pd.Series, doys: pd.Series, climatology: pd.DataFrame) -> pd.Series:
    """Standardize a series against per-DOY climatology. Used post-fetch to
    write the value_anom_z column to the raw parquet."""
    if climatology.empty:
        return pd.Series([np.nan] * len(values), index=values.index)
    lookup = climatology.set_index("doy")[["mu", "sigma"]]
    mu = doys.map(lookup["mu"])
    sigma = doys.map(lookup["sigma"]).replace(0, np.nan)
    return (values - mu) / sigma


def save(indicator_name: str, climatology: pd.DataFrame) -> None:
    if climatology.empty:
        return
    storage.write_parquet(climatology, storage.climatology_path(indicator_name))


def load(indicator_name: str) -> pd.DataFrame:
    return storage.read_parquet(storage.climatology_path(indicator_name))
