"""FAO WAPOR v3 L1 Actual Evapotranspiration & Interception (dekadal, ~300m).

User's pick (no MODIS). Dekadal cadence aligns with the role originally
planned for SSEBop in the design — confirmation indicator that crop-water
stress is translating into reduced ET. Coverage starts 2018-01-01.

Asset: FAO/WAPOR/3/L1_AETI_D — Africa + Near East + Latin America. Band
`L1-AETI-D` is in DN; multiply by SCALE (0.1) to get mm/dekad.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .base import FreshnessSpec, Indicator


class WAPOR(Indicator):
    name = "wapor"
    primary_column = "eta_mm"
    value_columns = ["eta_mm"]
    freshness = FreshnessSpec(fresh_days=12, aging_days=22, expected_cadence_days=10)
    has_forecast = False
    status_window_days = 10  # one dekad — WAPOR is already a 10-day mean
    climatology_doy_window = 30  # only 8 years of record — widen to ±30 days for stable fences
    default_chunk_months = 60  # dekadal × 14 deps is tiny; large chunks fine

    ASSET = "FAO/WAPOR/3/L1_AETI_D"
    BAND = "L1-AETI-D"
    # FAO WAPOR v3 L1 AETI dekadal: values are reported directly in mm/dekad.
    # Verified empirically against El Salvador (typical mean dekad ~30, max ~112
    # = ~3 mm/day mean, ~11 mm/day peak — matches local ET climatology).
    SCALE = 1.0

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        import ee
        from .. import gee
        gee.init()

        coll = (
            ee.ImageCollection(self.ASSET)
            .filterDate(start.isoformat(), end.isoformat())
        )
        df = self.reduce_imagecollection_by_departamento(coll, band=self.BAND)
        if df.empty:
            return df
        df["value"] = df["value"] * self.SCALE
        df = df.rename(columns={"value": "eta_mm"})
        df["is_forecast"] = False
        return df
        df = self.reduce_imagecollection_by_departamento(coll, band=self.BAND)
        if df.empty:
            return df
        df = df.rename(columns={"value": "eta_mm"})
        df["is_forecast"] = False
        return df
