"""Storage helpers. Reads/writes work the same against a local path or a
gcsfuse-mounted GCS bucket — STORAGE_ROOT is what swaps between them."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from .. import config


def raw_path(indicator: str, departamento: str) -> Path:
    safe_dep = departamento.replace(" ", "_").replace("ó", "o").replace("ú", "u").replace("á", "a").replace("é", "e").replace("í", "i").replace("ñ", "n")
    return config.RAW_DIR / indicator / f"{safe_dep}.parquet"


def climatology_path(indicator: str) -> Path:
    return config.CLIMATOLOGY_DIR / f"{indicator}.parquet"


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def upsert_raw(indicator: str, departamento: str, new_rows: pd.DataFrame) -> pd.DataFrame:
    """Append new rows by date, drop duplicates on (date, departamento)."""
    path = raw_path(indicator, departamento)
    existing = read_parquet(path)
    combined = pd.concat([existing, new_rows], ignore_index=True)
    combined = (
        combined.drop_duplicates(subset=["date", "departamento"], keep="last")
        .sort_values("date")
        .reset_index(drop=True)
    )
    write_parquet(combined, path)
    return combined


def drop_all_forecasts(indicator: str, departamentos: Iterable[str] | None = None) -> int:
    """Remove every ``is_forecast`` row from an indicator's per-departamento
    parquets and write them back. A fresh forecast issuance fully supersedes the
    prior one, and forecast pentads are dated on a rolling issuance grid that
    doesn't align with the observed pentad-of-year grid — so they are never
    overwritten by ``upsert_raw`` and otherwise accumulate (stale past leftovers
    + stacked future issuances). Call this before writing a new issuance.

    ``departamentos`` restricts the sweep to one country's parquets (filenames
    are derived via ``raw_path``); ``None`` sweeps every parquet in the dir.
    Returns the number of forecast rows removed."""
    indicator_dir = config.RAW_DIR / indicator
    if not indicator_dir.exists():
        return 0
    if departamentos is None:
        paths = sorted(indicator_dir.glob("*.parquet"))
    else:
        paths = [raw_path(indicator, dep) for dep in departamentos]

    removed = 0
    for path in paths:
        df = read_parquet(path)
        if df.empty or "is_forecast" not in df.columns:
            continue
        mask = df["is_forecast"].fillna(False).astype(bool)
        n = int(mask.sum())
        if n == 0:
            continue
        write_parquet(df[~mask].sort_values("date").reset_index(drop=True), path)
        removed += n
    return removed
