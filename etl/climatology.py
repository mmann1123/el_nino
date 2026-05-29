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


def compute_for_indicator(
    indicator_name: str,
    value_columns: list[str],
    doy_window: int = 0,
) -> pd.DataFrame:
    """Walk every per-departamento parquet, compute per-DOY percentiles, and
    return a tidy frame: (departamento, value_column, doy, mu, sigma, p05...p95,
    n_samples).

    `doy_window` is the half-width of a circular day-of-year window. For each
    target DOY, the percentile fences are computed over the pool of values
    whose DOY falls within ±doy_window days of the target (wrapping at
    year-end). This is the standard fix for short-record climatologies (e.g.
    WAPOR's 8-year record): with only N years per DOY, the p05/p95 fences are
    noisy; pooling adjacent DOYs gives N×(2W+1)/cadence effective samples.

    `doy_window=0` (default) reproduces the original behaviour: per-DOY only.
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
        dep = baseline["departamento"].iloc[0]

        for col in value_columns:
            if col not in baseline.columns:
                continue
            stats = _windowed_doy_stats(
                baseline[["doy", col]].dropna(),
                value_col=col,
                doy_window=doy_window,
            )
            stats["departamento"] = dep
            stats["value_column"] = col
            rows.append(stats)

    if not rows:
        return pd.DataFrame()

    return pd.concat(rows, ignore_index=True)[
        ["departamento", "value_column", "doy"] + CLIMATOLOGY_COLUMNS + ["n_samples"]
    ]


def _windowed_doy_stats(df: pd.DataFrame, value_col: str, doy_window: int) -> pd.DataFrame:
    """For every observed DOY, compute percentile fences over the pool of
    rows whose DOY falls within ±doy_window of it (circular, year-wrap)."""
    target_doys = sorted(df["doy"].unique())
    out_rows = []
    vals_by_doy = df.groupby("doy")[value_col].apply(list).to_dict()
    for target in target_doys:
        if doy_window <= 0:
            pool = vals_by_doy.get(target, [])
        else:
            window_doys = _circular_doy_window(target, doy_window)
            pool = [v for d in window_doys for v in vals_by_doy.get(d, [])]
        if not pool:
            continue
        arr = np.asarray(pool, dtype=float)
        out_rows.append({
            "doy": target,
            "mu": float(np.nanmean(arr)),
            "sigma": float(np.nanstd(arr, ddof=1)) if len(arr) > 1 else float("nan"),
            "p05": float(np.nanpercentile(arr, 5)),
            "p10": float(np.nanpercentile(arr, 10)),
            "p25": float(np.nanpercentile(arr, 25)),
            "p50": float(np.nanpercentile(arr, 50)),
            "p75": float(np.nanpercentile(arr, 75)),
            "p90": float(np.nanpercentile(arr, 90)),
            "p95": float(np.nanpercentile(arr, 95)),
            "n_samples": int(len(arr)),
        })
    return pd.DataFrame(out_rows)


def _circular_doy_window(target: int, window: int) -> list[int]:
    """All DOYs within ±window of `target`, wrapping at 365/366."""
    return [((target - 1 + d) % 365) + 1 for d in range(-window, window + 1)]


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
