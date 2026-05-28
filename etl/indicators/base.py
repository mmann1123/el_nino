"""Base contract for indicators.

Each indicator knows how to:
  - fetch raw timeseries from GEE for a date window over the given AOI
  - emit a tidy DataFrame with columns: date, departamento, value, [extras...], is_forecast
  - declare a refresh cadence (days) and freshness thresholds for the dashboard badges
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Iterator

import pandas as pd

from ... import config


@dataclass
class FreshnessSpec:
    fresh_days: int        # green up to this lag
    aging_days: int        # yellow up to this lag; red beyond
    expected_cadence_days: int


class Indicator(ABC):
    name: str = ""
    value_columns: list[str] = []       # which numeric columns the climatology applies to
    primary_column: str = "value"        # column shown in the dashboard as the "main" series
    freshness: FreshnessSpec = FreshnessSpec(fresh_days=3, aging_days=7, expected_cadence_days=3)
    has_forecast: bool = False

    # GEE returns up to ~5000 features per getInfo(). Chunk sizes below keep
    # each interactive call under that ceiling for 14 departamentos:
    #   CHIRPS pentad: 14 × 73 ≈ 1022/yr → safe at 12 months
    #   SMAP 3-day:    14 × 122 ≈ 1700/yr → safe at 12 months
    #   IMERG daily:   14 × 365 ≈ 5110/yr → use 6 months
    #   WAPOR dekadal: 14 × 36 ≈ 504/yr → safe at 24+ months
    default_chunk_months: int = 12
    min_chunk_months: int = 1

    @abstractmethod
    def fetch(self, start: date, end: date) -> pd.DataFrame:
        """Pull observations for [start, end] across all departamentos in the AOI."""

    # ---- backfill ----

    def backfill(
        self,
        start: date,
        end: date,
        writer: Callable[[str, pd.DataFrame], None],
        chunk_months: int | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> int:
        """Iterate the [start, end] window in chunks, fetch each, write incrementally.

        Retries each chunk by halving its length on EEException up to min_chunk_months.
        Returns the total number of rows written.
        """
        chunk_months = chunk_months or self.default_chunk_months
        total = 0
        for window_start, window_end in _iter_windows(start, end, chunk_months):
            total += self._fetch_window_with_retry(window_start, window_end, chunk_months, writer, on_progress)
        return total

    def _fetch_window_with_retry(
        self,
        window_start: date,
        window_end: date,
        chunk_months: int,
        writer: Callable[[str, pd.DataFrame], None],
        on_progress: Callable[[str], None] | None,
    ) -> int:
        from ee.ee_exception import EEException  # local import; ee may not be installed locally

        attempt_months = chunk_months
        attempt_start = window_start
        rows_written = 0
        while attempt_start <= window_end:
            attempt_end = min(_add_months(attempt_start, attempt_months) - timedelta(days=1), window_end)
            msg = f"  {self.name}: {attempt_start} -> {attempt_end}"
            if on_progress:
                on_progress(msg)
            try:
                df = self.fetch(attempt_start, attempt_end)
                if not df.empty:
                    for dep, group in df.groupby("departamento"):
                        writer(dep, group.copy())
                    rows_written += len(df)
                attempt_start = attempt_end + timedelta(days=1)
            except EEException as e:
                if attempt_months <= self.min_chunk_months:
                    if on_progress:
                        on_progress(f"    skipped (already at min chunk): {e}")
                    attempt_start = attempt_end + timedelta(days=1)
                    continue
                attempt_months = max(self.min_chunk_months, attempt_months // 2)
                if on_progress:
                    on_progress(f"    retrying with chunk_months={attempt_months} after EEException: {e}")
                time.sleep(2)
            except Exception as e:
                if on_progress:
                    on_progress(f"    error: {e}")
                attempt_start = attempt_end + timedelta(days=1)
        return rows_written

    # ---- shared helpers ----

    def aoi(self):
        import ee  # local import: synth path does not need earthengine-api installed
        from .. import gee
        gee.init()
        with open(config.AOI_PATH) as f:
            geojson = json.load(f)
        return ee.FeatureCollection(geojson)

    def reduce_imagecollection_by_departamento(
        self,
        coll,
        band: str,
        reducer=None,
    ) -> pd.DataFrame:
        """Reduce an ImageCollection to a tidy (date, departamento, value) DataFrame.

        Default reducer is mean over the polygon at the asset's native scale.
        """
        import ee
        reducer = reducer or ee.Reducer.mean()
        aoi = self.aoi()

        def per_image(img):
            stats = img.select(band).reduceRegions(
                collection=aoi,
                reducer=reducer,
                scale=img.projection().nominalScale(),
            )
            date_str = img.date().format("YYYY-MM-dd")
            return stats.map(lambda f: f.set({"date": date_str, "indicator_band": band}))

        flat = coll.map(per_image).flatten()
        info = flat.getInfo()
        rows = []
        for feat in info["features"]:
            props = feat["properties"]
            rows.append({
                "date": props["date"],
                "departamento": props.get("ADM1_NAME") or props.get("departamento"),
                "value": props.get("mean") if "mean" in props else props.get(band),
            })
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna(subset=["value"]).sort_values(["departamento", "date"]).reset_index(drop=True)


# ---- date-window helpers ----

def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    # clamp day for short months
    day = min(d.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(y: int, m: int) -> int:
    if m == 12:
        return 31
    return (date(y, m + 1, 1) - date(y, m, 1)).days


def _iter_windows(start: date, end: date, chunk_months: int) -> Iterator[tuple[date, date]]:
    cur = start
    while cur <= end:
        win_end = min(_add_months(cur, chunk_months) - timedelta(days=1), end)
        yield cur, win_end
        cur = win_end + timedelta(days=1)
