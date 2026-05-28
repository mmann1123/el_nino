"""SMAP L4 root-zone soil moisture. NASA/SMAP/SPL4SMGP/008.

Root-zone (0-100 cm) is what matters at silking; surface alone misses canícula
desiccation of the deeper store.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .base import FreshnessSpec, Indicator


class SMAP(Indicator):
    name = "smap"
    primary_column = "rzsm_m3m3"
    value_columns = ["rzsm_m3m3"]
    freshness = FreshnessSpec(fresh_days=4, aging_days=8, expected_cadence_days=3)
    has_forecast = False

    ASSET = "NASA/SMAP/SPL4SMGP/008"

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        import ee
        coll = (
            ee.ImageCollection(self.ASSET)
            .filterDate(start.isoformat(), end.isoformat())
            .select("sm_rootzone")
        )
        df = self.reduce_imagecollection_by_departamento(coll, band="sm_rootzone")
        if df.empty:
            return df
        df = df.rename(columns={"value": "rzsm_m3m3"})
        df["is_forecast"] = False
        return df
