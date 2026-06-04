"""Per-DOY climatology fences and anomaly standardization."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from el_nino.etl import climatology, storage


class TestCircularDoyWindow:
    def test_centered_window(self):
        assert climatology._circular_doy_window(100, 2) == [98, 99, 100, 101, 102]

    def test_wraps_at_year_start(self):
        # DOY 1 with ±1 should wrap to include 365.
        assert climatology._circular_doy_window(1, 1) == [365, 1, 2]

    def test_wraps_at_year_end(self):
        assert climatology._circular_doy_window(365, 1) == [364, 365, 1]


class TestComputeAnomalyZ:
    def test_standardizes_against_climatology(self):
        clim = pd.DataFrame({"doy": [1, 2], "mu": [10.0, 20.0], "sigma": [2.0, 5.0]})
        values = pd.Series([12.0, 10.0])
        doys = pd.Series([1, 2])
        z = climatology.compute_anomaly_z(values, doys, clim)
        # (12-10)/2 = 1.0 ; (10-20)/5 = -2.0
        assert z.tolist() == [1.0, -2.0]

    def test_zero_sigma_yields_nan(self):
        clim = pd.DataFrame({"doy": [1], "mu": [10.0], "sigma": [0.0]})
        z = climatology.compute_anomaly_z(pd.Series([12.0]), pd.Series([1]), clim)
        assert np.isnan(z.iloc[0])

    def test_empty_climatology_is_all_nan(self):
        z = climatology.compute_anomaly_z(pd.Series([1.0, 2.0]), pd.Series([1, 2]),
                                          pd.DataFrame())
        assert z.isna().all()
        assert len(z) == 2


class TestWindowedDoyStats:
    def test_pooling_increases_sample_count(self):
        # Two DOYs, one value each. Window 0 -> 1 sample per DOY; window 1 pools.
        df = pd.DataFrame({"doy": [10, 11], "v": [1.0, 3.0]})
        narrow = climatology._windowed_doy_stats(df, "v", doy_window=0)
        wide = climatology._windowed_doy_stats(df, "v", doy_window=1)
        assert set(narrow["n_samples"]) == {1}
        # DOY 10's window (9,10,11) pools both observed values.
        row10 = wide[wide["doy"] == 10].iloc[0]
        assert row10["n_samples"] == 2
        assert row10["mu"] == 2.0


class TestComputeForIndicator:
    def _write_daily(self, dep, start, days, value):
        rows = [{
            "date": start + timedelta(days=i),
            "departamento": dep,
            "rzsm_m3m3": value + (i % 5) * 0.01,
        } for i in range(days)]
        storage.write_parquet(pd.DataFrame(rows),
                              storage.raw_path("smap", dep))

    def test_produces_fences_for_value_column(self, tmp_storage):
        # Two years of daily data inside the climatology baseline window.
        self._write_daily("Morazan", date(2016, 1, 1), 730, 0.30)
        clim = climatology.compute_for_indicator("smap", ["rzsm_m3m3"], doy_window=5)
        assert not clim.empty
        assert set(["departamento", "value_column", "doy", "mu", "sigma",
                    "p05", "p95", "n_samples"]).issubset(clim.columns)
        assert (clim["value_column"] == "rzsm_m3m3").all()
        assert (clim["departamento"] == "Morazan").all()
        # Percentile ordering must hold per row.
        assert (clim["p05"] <= clim["p95"]).all()

    def test_baseline_window_excludes_out_of_range_years(self, tmp_storage, monkeypatch):
        from el_nino import config
        monkeypatch.setattr(config, "CLIMATOLOGY_START_YEAR", 2016)
        monkeypatch.setattr(config, "CLIMATOLOGY_END_YEAR", 2016)
        # 2015 data only -> outside baseline -> nothing computed.
        self._write_daily("Morazan", date(2015, 1, 1), 60, 0.30)
        clim = climatology.compute_for_indicator("smap", ["rzsm_m3m3"])
        assert clim.empty

    def test_missing_indicator_dir_returns_empty(self, tmp_storage):
        assert climatology.compute_for_indicator("nonexistent", ["v"]).empty
