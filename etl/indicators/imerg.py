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
    freshness = FreshnessSpec(fresh_days=2, aging_days=4, expected_cadence_days=1)
    has_forecast = False
    default_chunk_months = 6  # daily × 14 deps → keep getInfo() feature count under ~5000
    min_chunk_months = 1

    ASSET = "NASA/GPM_L3/IMERG_V07"

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        import ee
        coll = (
            ee.ImageCollection(self.ASSET)
            .filterDate(start.isoformat(), end.isoformat())
            .select("precipitation")
        )
        # IMERG is half-hourly; aggregate to daily before reducing.
        def to_daily(d):
            d = ee.Date(d)
            day = coll.filterDate(d, d.advance(1, "day")).sum()
            return day.set("system:time_start", d.millis())

        n_days = (end - start).days
        day_list = ee.List.sequence(0, n_days - 1).map(
            lambda i: ee.Date(start.isoformat()).advance(i, "day").millis()
        )
        daily_coll = ee.ImageCollection(day_list.map(to_daily))

        df = self.reduce_imagecollection_by_departamento(daily_coll, band="precipitation")
        if df.empty:
            return df
        df = df.rename(columns={"value": "imerg_precip_mm"})
        df["is_forecast"] = False
        return df
