"""Storage helpers. Reads/writes work the same against a local path or a
gcsfuse-mounted GCS bucket — STORAGE_ROOT is what swaps between them."""

from __future__ import annotations

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
