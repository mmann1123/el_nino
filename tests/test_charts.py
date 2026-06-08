"""ENSO mean ± SD climatology shaping and the per-device Plotly config.

charts.py is pure pandas/plotly/numpy (no Streamlit at import time), so these
exercise the logic directly without standing up the dashboard.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from el_nino.dashboard import charts


def _oni(years=range(2000, 2012)):
    """Synthetic monthly ONI with cross-year spread inside each month so the
    per-month standard deviation is non-zero."""
    rows = []
    for y in years:
        for m in range(1, 13):
            rows.append({"date": date(y, m, 1), "oni": (y % 4) * 0.3 + m * 0.05, "year": y})
    return pd.DataFrame(rows)


class TestOniClimatology:
    def test_daily_resolution_not_monthly(self):
        # Regression guard for the "lighter box" artifact: the envelope must be
        # interpolated to 365 daily rows, not 12 coarse monthly anchors (whose
        # past/future overlap stacked into a visible ~month-wide band at Today).
        clim = charts._oni_climatology(_oni())
        assert len(clim) == 365
        assert list(clim["doy"]) == list(range(1, 366))

    def test_fences_are_ordered(self):
        clim = charts._oni_climatology(_oni())
        assert (clim["p05"] <= clim["p25"]).all()
        assert (clim["p25"] <= clim["p50"]).all()
        assert (clim["p50"] <= clim["p75"]).all()
        assert (clim["p75"] <= clim["p95"]).all()

    def test_bands_are_mean_plus_minus_sd(self):
        # p50 is the mean; inner band is ±1 SD, outer is ±2 SD — so both bands
        # are symmetric about the centre line.
        clim = charts._oni_climatology(_oni())
        assert np.allclose((clim["p25"] + clim["p75"]) / 2, clim["p50"])
        assert np.allclose((clim["p05"] + clim["p95"]) / 2, clim["p50"])
        # Outer half-width is exactly twice the inner half-width (2 SD vs 1 SD).
        inner = clim["p75"] - clim["p50"]
        outer = clim["p95"] - clim["p50"]
        assert np.allclose(outer, 2 * inner)

    def test_no_nans(self):
        clim = charts._oni_climatology(_oni())
        assert not clim.isna().any().any()

    def test_single_year_zero_sd_collapses_bands(self):
        # One sample per month -> std NaN -> filled 0 -> all fences equal the mean.
        clim = charts._oni_climatology(_oni(years=[2005]))
        assert len(clim) == 365
        assert np.allclose(clim["p05"], clim["p50"])
        assert np.allclose(clim["p95"], clim["p50"])

    def test_empty_input_returns_empty(self):
        assert charts._oni_climatology(pd.DataFrame({"date": [], "oni": []})).empty


class TestChartConfig:
    def test_desktop_is_interactive(self):
        cfg = charts.chart_config(mobile=False)
        assert not cfg.get("staticPlot", False)
        assert cfg is charts.CHART_CONFIG

    def test_mobile_is_static(self):
        cfg = charts.chart_config(mobile=True)
        assert cfg["staticPlot"] is True
        assert cfg["displayModeBar"] is False
