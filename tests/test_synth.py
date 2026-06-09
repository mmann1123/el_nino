"""Anomaly z-score attachment — joins per-DOY climatology mu/sigma onto the raw
parquets and standardizes the primary column into value_anom_z.

This backs the drought-status badge and the map: status.py drops rows with NaN
value_anom_z, so attach_anomaly_z must run after every fetch/prelim/forecast for
the badge and map to reflect the newest observations.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from el_nino.etl import climatology, storage, synth

PRIMARY = "rzsm_m3m3"   # smap's primary column
DEP = "Morazan"


def _save_climatology(mu=0.30, sigma=0.10):
    clim = pd.DataFrame({
        "departamento": [DEP] * 3,
        "value_column": [PRIMARY] * 3,
        "doy": [1, 2, 3],
        "mu": [mu] * 3,
        "sigma": [sigma] * 3,
    })
    climatology.save("smap", clim)


def _save_raw(values=(0.30, 0.40, 0.20)):
    raw = pd.DataFrame({
        "date": [date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3)],
        "departamento": [DEP] * 3,
        PRIMARY: list(values),
        "is_forecast": [False] * 3,
    })
    storage.write_parquet(raw, storage.raw_path("smap", DEP))


class TestAttachAnomalyZ:
    def test_standardizes_primary_against_climatology(self, tmp_storage):
        _save_climatology(mu=0.30, sigma=0.10)
        _save_raw(values=(0.30, 0.40, 0.20))  # -> z = 0, +1, -1
        synth.attach_anomaly_z("smap")
        out = storage.read_parquet(storage.raw_path("smap", DEP)).sort_values("date")
        assert "value_anom_z" in out.columns
        assert np.allclose(out["value_anom_z"].to_numpy(), [0.0, 1.0, -1.0])

    def test_zero_sigma_yields_nan(self, tmp_storage):
        _save_climatology(mu=0.30, sigma=0.0)
        _save_raw()
        synth.attach_anomaly_z("smap")
        out = storage.read_parquet(storage.raw_path("smap", DEP))
        assert out["value_anom_z"].isna().all()

    def test_preserves_existing_columns(self, tmp_storage):
        _save_climatology()
        _save_raw()
        synth.attach_anomaly_z("smap")
        out = storage.read_parquet(storage.raw_path("smap", DEP))
        assert {"date", "departamento", PRIMARY, "is_forecast"} <= set(out.columns)
        # The merge helper columns must not leak into the written parquet.
        assert not {"doy", "mu", "sigma"} & set(out.columns)

    def test_missing_climatology_is_noop(self, tmp_storage):
        _save_raw()  # no climatology saved
        synth.attach_anomaly_z("smap")
        out = storage.read_parquet(storage.raw_path("smap", DEP))
        assert "value_anom_z" not in out.columns  # untouched
