"""IMERG-Late V07 daily precipitation — event-scale rainfall verification.

CHIRPS is weak at the daily event scale in El Salvador's orographic chain;
IMERG preserves the convective texture better. Used as a verifier alongside
CHIRPS rather than as a climatology baseline.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .base import FreshnessSpec, Indicator


class IMERG(Indicator):
    name = "imerg"
    primary_column = "imerg_precip_mm"
    value_columns = ["imerg_precip_mm"]
    freshness = FreshnessSpec.from_cadence(1)
    has_forecast = False
    status_window_days = 7  # daily IMERG is very noisy; average a week
    default_chunk_months = 6  # daily × 14 deps → keep getInfo() feature count under ~5000
    min_chunk_months = 1

    ASSET = "NASA/GPM_L3/IMERG_V07"

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        import ee
        from .. import gee
        gee.init()
        coll = (
            ee.ImageCollection(self.ASSET)
            .filterDate(start.isoformat(), end.isoformat())
            .select("precipitation")
        )
        if (end - start).days <= 0:
            return pd.DataFrame()

        # IMERG is half-hourly; sum to daily over days that actually have data
        # (skip the unpublished latency tail, which would otherwise produce
        # band-less images that crash the reduce). See Indicator.daily_aggregate.
        daily_coll = self.daily_aggregate(coll, lambda ic: ic.sum(), "precipitation")

        df = self.reduce_imagecollection_by_departamento(daily_coll, band="precipitation")
        if df.empty:
            return df
        df = df.rename(columns={"value": "imerg_precip_mm"})
        df["is_forecast"] = False
        return df
