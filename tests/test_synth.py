"""Anomaly z-score attachment — writes value_anom_z onto the raw parquets using
the nonparametric standardized index, ranking each value against the indicator's
baseline-year observed history (DOY-pooled).

This backs the drought-status badge and the map: status.py drops rows with NaN
value_anom_z, so attach_anomaly_z must run after every fetch/prelim/forecast for
the badge and map to reflect the newest observations.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from el_nino.etl import storage, synth

PRIMARY = "rzsm_m3m3"   # smap's primary column (continuous, no SPI needed)
DEP = "Morazan"
BASELINE_VALS = list(np.round(np.linspace(0.10, 0.50, 25), 4))  # 25 baseline years, median 0.30


def _write_smap(current_val, current_year=2026):
    """One DOY-1 observation per baseline year (2000–2024) plus one current-year
    observation to be scored against them."""
    rows = [{"date": date(2000 + i, 1, 1), "departamento": DEP,
             PRIMARY: v, "is_forecast": False}
            for i, v in enumerate(BASELINE_VALS)]
    rows.append({"date": date(current_year, 1, 1), "departamento": DEP,
                 PRIMARY: current_val, "is_forecast": False})
    storage.write_parquet(pd.DataFrame(rows), storage.raw_path("smap", DEP))


def _current_z(current_val, tmp_storage):
    _write_smap(current_val)
    synth.attach_anomaly_z("smap")
    out = storage.read_parquet(storage.raw_path("smap", DEP))
    out["date"] = pd.to_datetime(out["date"])
    return out.sort_values("date").iloc[-1]["value_anom_z"]


class TestAttachAnomalyZ:
    def test_median_value_maps_near_zero(self, tmp_storage):
        assert abs(_current_z(0.30, tmp_storage)) < 0.2

    def test_high_value_is_positive(self, tmp_storage):
        assert _current_z(0.50, tmp_storage) > 1.0

    def test_low_value_is_negative(self, tmp_storage):
        assert _current_z(0.10, tmp_storage) < -1.0

    def test_no_stored_climatology_needed(self, tmp_storage):
        # The index ranks against the raw baseline history, so it works with no
        # climatology parquet on disk.
        assert not (tmp_storage / "climatology" / "smap.parquet").exists()
        _write_smap(0.30)
        synth.attach_anomaly_z("smap")
        out = storage.read_parquet(storage.raw_path("smap", DEP))
        assert "value_anom_z" in out.columns
        assert out["value_anom_z"].notna().any()

    def test_preserves_columns_no_temp_leak(self, tmp_storage):
        _write_smap(0.30)
        synth.attach_anomaly_z("smap")
        out = storage.read_parquet(storage.raw_path("smap", DEP))
        assert {"date", "departamento", PRIMARY, "is_forecast", "value_anom_z"} <= set(out.columns)
        assert not {"doy", "year", "mu", "sigma"} & set(out.columns)

    def test_missing_indicator_dir_is_noop(self, tmp_storage):
        synth.attach_anomaly_z("smap")  # no parquets written → must not raise
