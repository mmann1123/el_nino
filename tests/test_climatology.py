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


class TestStandardizedAnomaly:
    """Nonparametric standardized index: empirical Gringorten plotting position
    over the DOY-pooled baseline, then inverse normal. Distribution-free, on a
    standard-normal scale."""

    def _baseline(self, vals, doy=1):
        s = pd.Series(vals, dtype=float)
        return s, pd.Series([doy] * len(vals))

    def test_median_maps_near_zero(self):
        bvals, bdoys = self._baseline(list(range(100)))
        z = climatology.standardized_anomaly(
            pd.Series([49.5]), pd.Series([1]), bvals, bdoys, doy_window=0)
        assert abs(z.iloc[0]) < 0.05

    def test_monotonic_increasing_in_value(self):
        bvals, bdoys = self._baseline(list(range(100)))
        z = climatology.standardized_anomaly(
            pd.Series([10.0, 50.0, 90.0]), pd.Series([1, 1, 1]), bvals, bdoys, doy_window=0)
        assert z.iloc[0] < z.iloc[1] < z.iloc[2]
        assert z.iloc[0] < 0 < z.iloc[2]

    def test_robust_to_skew(self):
        # Heavy right tail pulls the *mean* up, but the median still maps to ~0 —
        # the whole point of going nonparametric vs (x-mean)/sd.
        bvals, bdoys = self._baseline(list(range(90)) + [1000.0] * 10)
        z = climatology.standardized_anomaly(
            pd.Series([49.5]), pd.Series([1]), bvals, bdoys, doy_window=0)
        assert abs(z.iloc[0]) < 0.1

    def test_small_pool_is_nan(self):
        bvals, bdoys = self._baseline([1.0, 2.0, 3.0])  # < ANOMALY_MIN_SAMPLES
        z = climatology.standardized_anomaly(
            pd.Series([2.0]), pd.Series([1]), bvals, bdoys, doy_window=0)
        assert np.isnan(z.iloc[0])

    def test_empty_baseline_is_all_nan(self):
        z = climatology.standardized_anomaly(
            pd.Series([1.0, 2.0]), pd.Series([1, 2]),
            pd.Series([], dtype=float), pd.Series([], dtype=float), doy_window=0)
        assert z.isna().all() and len(z) == 2

    def test_doy_window_pools_neighbours(self):
        # 30 values across doys 1-3; with window=1 the pool for doy 2 is all of
        # them, so a mid value scores near 0.
        vals = list(range(30))
        doys = [1] * 10 + [2] * 10 + [3] * 10
        z = climatology.standardized_anomaly(
            pd.Series([14.5]), pd.Series([2]),
            pd.Series(vals, dtype=float), pd.Series(doys), doy_window=1)
        assert abs(z.iloc[0]) < 0.1


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
