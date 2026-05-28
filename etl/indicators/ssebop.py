"""SSEBop v6 actual ET anomaly — confirmation of crop water stress.

USGS publishes dekadal SSEBop. Not currently in the official EE catalog at v6;
the Climate Engine community catalog hosts it. The path below is the conventional
location used in operational workflows — update it if your tenancy uses a different
location.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .base import FreshnessSpec, Indicator


class SSEBop(Indicator):
    name = "ssebop"
    primary_column = "eta_mm"
    value_columns = ["eta_mm"]
    freshness = FreshnessSpec(fresh_days=12, aging_days=22, expected_cadence_days=10)
    has_forecast = False
    default_chunk_months = 60  # dekadal × 14 deps is tiny; large chunks fine

    ASSET = "projects/climate-engine-pro/assets/ssebop-v6-dekadal"

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        import ee
        coll = (
            ee.ImageCollection(self.ASSET)
            .filterDate(start.isoformat(), end.isoformat())
        )
        df = self.reduce_imagecollection_by_departamento(coll, band="et")
        if df.empty:
            return df
        df = df.rename(columns={"value": "eta_mm"})
        df["is_forecast"] = False
        return df
