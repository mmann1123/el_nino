"""Per-DOY climatology fences (μ, σ, p05/p10/p25/p50/p75/p90/p95) for each
indicator × departamento. Baseline period from config.

The dashboard joins current values to this table by (indicator, departamento,
doy) to draw the envelope.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from .. import config
from . import storage

CLIMATOLOGY_COLUMNS = ["mu", "sigma", "p05", "p10", "p25", "p50", "p75", "p90", "p95"]

# Minimum DOY-pool size before a nonparametric standardized anomaly is trusted.
ANOMALY_MIN_SAMPLES = 10


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


def standardized_anomaly(
    values: pd.Series,
    doys: pd.Series,
    baseline_values: pd.Series,
    baseline_doys: pd.Series,
    doy_window: int,
) -> pd.Series:
    """Nonparametric standardized index (Farahmand & AghaKouchak 2015).

    For each value, estimate its cumulative probability under the DOY-windowed
    *baseline* distribution via the Gringorten plotting position —
    ``p = (m - 0.44) / (n + 0.12)`` where ``m = #{baseline <= value}`` and ``n``
    is the pool size — then map through the inverse normal CDF. This makes no
    distributional assumption (handles skewed rainfall / bounded soil moisture),
    yet lands on a standard-normal scale so the USDM drought bins still apply.

    The baseline pool is built with the SAME circular ±``doy_window`` pooling the
    percentile fences use, so the badge/map stay consistent with the envelope.
    Returns NaN where the pool is smaller than ANOMALY_MIN_SAMPLES.
    """
    out = pd.Series(np.nan, index=values.index)
    v = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    d = np.asarray(doys, dtype=float)

    bdf = pd.DataFrame({
        "doy": np.asarray(baseline_doys, dtype=float),
        "v": pd.to_numeric(baseline_values, errors="coerce").to_numpy(dtype=float),
    }).dropna()
    if bdf.empty:
        return out
    pool_by_doy = {int(k): g["v"].to_numpy() for k, g in bdf.groupby("doy")}

    for target in np.unique(d[~np.isnan(d)]):
        target = int(target)
        if doy_window <= 0:
            pool = pool_by_doy.get(target, np.empty(0))
        else:
            parts = [pool_by_doy[x] for x in _circular_doy_window(target, doy_window)
                     if x in pool_by_doy]
            pool = np.concatenate(parts) if parts else np.empty(0)
        n = pool.size
        if n < ANOMALY_MIN_SAMPLES:
            continue
        sorted_pool = np.sort(pool)
        mask = d == target
        xv = v[mask]
        m = np.searchsorted(sorted_pool, xv, side="right")  # #{pool <= value}
        p = np.clip((m - 0.44) / (n + 0.12), 1e-6, 1 - 1e-6)
        z = norm.ppf(p)
        z[np.isnan(xv)] = np.nan
        out.iloc[np.where(mask)[0]] = z
    return out


def save(indicator_name: str, climatology: pd.DataFrame) -> None:
    if climatology.empty:
        return
    storage.write_parquet(climatology, storage.climatology_path(indicator_name))


def load(indicator_name: str) -> pd.DataFrame:
    return storage.read_parquet(storage.climatology_path(indicator_name))
