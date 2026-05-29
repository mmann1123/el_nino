"""SMAP L4 root-zone soil moisture. NASA/SMAP/SPL4SMGP/008.

Root-zone (0-100 cm) is what matters at silking; surface alone misses canícula
desiccation of the deeper store.

The native L4 collection is 3-hourly (8 images per day), which means a naive
12-month fetch over 14 departamentos returns ~40K features — over the GEE
interactive feature ceiling. We aggregate to daily means server-side before
reducing, dropping the feature count to ~365 × 14 ≈ 5100/year, safe at the
6-month chunk size we set below.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from .base import FreshnessSpec, Indicator


class SMAP(Indicator):
    name = "smap"
    primary_column = "rzsm_m3m3"
    value_columns = ["rzsm_m3m3"]
    freshness = FreshnessSpec(fresh_days=4, aging_days=8, expected_cadence_days=3)
    has_forecast = False
    status_window_days = 7  # average a week of daily reads — soil moisture has multi-day persistence
    climatology_doy_window = 15  # 10 years × ~30 DOYs = ~300 samples per fence
    # 6-month chunks: ~183 daily means × 14 deps ≈ 2562 features per chunk.
    default_chunk_months = 6
    min_chunk_months = 1

    ASSET = "NASA/SMAP/SPL4SMGP/008"

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        import ee
        from .. import gee
        gee.init()

        coll_raw = (
            ee.ImageCollection(self.ASSET)
            .filterDate(start.isoformat(), end.isoformat())
            .select("sm_rootzone")
        )

        # Aggregate to daily means server-side.
        n_days = (end - start).days
        if n_days <= 0:
            return pd.DataFrame()

        def daily_mean(i):
            d = ee.Date(start.isoformat()).advance(ee.Number(i), "day")
            day = coll_raw.filterDate(d, d.advance(1, "day")).mean()
            return day.rename("rzsm_m3m3").set("system:time_start", d.millis())

        day_list = ee.List.sequence(0, n_days - 1).map(daily_mean)
        daily_coll = ee.ImageCollection(day_list)

        df = self.reduce_imagecollection_by_departamento(daily_coll, band="rzsm_m3m3")
        if df.empty:
            return df
        df = df.rename(columns={"value": "rzsm_m3m3"})
        df["is_forecast"] = False
        return df
