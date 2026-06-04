"""Calibrated drought-trigger evaluation over historical per-department series.

Builds synthetic CHIRPS (spi_3) and SMAP (value_anom_z) parquets, then asserts
the trigger fires exactly when both indicators cross their thresholds *inside*
the silking window, for priority departments only.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from el_nino import config
from el_nino.etl import storage, triggers


TRIGGER = triggers.CalibratedTrigger(
    name="test_trigger",
    description="test",
    window_doy=(196, 227),      # mid-Jul to mid-Aug
    spi3_threshold=-1.5,
    rzsm_threshold=-0.5,
    severity="high",
)


def _write(indicator, dep, col, rows):
    """rows: list of (date, value)."""
    df = pd.DataFrame({
        "date": [d for d, _ in rows],
        "departamento": [dep] * len(rows),
        col: [v for _, v in rows],
    })
    storage.write_parquet(df, storage.raw_path(indicator, dep))


@pytest.fixture
def priority_only_morazan(monkeypatch):
    monkeypatch.setattr(config, "PRIORITY_DEPARTMENTS", ["Morazan"])


def _seed_morazan(spi_rows, rzsm_rows):
    _write("chirps", "Morazan", "spi_3", spi_rows)
    _write("smap", "Morazan", "value_anom_z", rzsm_rows)


class TestEvaluateHistory:
    def test_fires_when_both_cross_in_window(self, tmp_storage, priority_only_morazan):
        _seed_morazan(
            spi_rows=[(date(2015, 7, 20), -2.0)],     # doy 201, below -1.5
            rzsm_rows=[(date(2015, 7, 20), -1.0)],    # below -0.5
        )
        fires = triggers.evaluate_history(TRIGGER)
        assert len(fires) == 1
        assert fires[0].year == 2015
        assert fires[0].departamento == "Morazan"
        assert fires[0].spi3_min == -2.0
        assert fires[0].rzsm_min_z == -1.0

    def test_no_fire_when_only_one_crosses(self, tmp_storage, priority_only_morazan):
        _seed_morazan(
            spi_rows=[(date(2016, 7, 20), -2.0)],     # crosses
            rzsm_rows=[(date(2016, 7, 20), 0.1)],     # does NOT cross
        )
        assert triggers.evaluate_history(TRIGGER) == []

    def test_out_of_window_extremes_are_ignored(self, tmp_storage, priority_only_morazan):
        # Severe deficits in January must not trigger a silking-window alert.
        _seed_morazan(
            spi_rows=[(date(2017, 1, 15), -3.0), (date(2017, 7, 20), -0.1)],
            rzsm_rows=[(date(2017, 1, 15), -3.0), (date(2017, 7, 20), 0.0)],
        )
        assert triggers.evaluate_history(TRIGGER) == []

    def test_non_priority_department_excluded(self, tmp_storage, priority_only_morazan):
        _write("chirps", "Cabanas", "spi_3", [(date(2015, 7, 20), -2.0)])
        _write("smap", "Cabanas", "value_anom_z", [(date(2015, 7, 20), -1.0)])
        assert triggers.evaluate_history(TRIGGER) == []

    def test_requires_both_indicators_present(self, tmp_storage, priority_only_morazan):
        # CHIRPS only, no SMAP overlap -> cannot evaluate -> no fire.
        _write("chirps", "Morazan", "spi_3", [(date(2015, 7, 20), -2.0)])
        assert triggers.evaluate_history(TRIGGER) == []


class TestCurrentStatus:
    def test_window_active_flag(self, tmp_storage, priority_only_morazan):
        _seed_morazan([(date(2015, 7, 20), -2.0)], [(date(2015, 7, 20), -1.0)])
        status = triggers.current_status(today=date(2015, 7, 20), trigger=TRIGGER)
        assert status["window_active"] is True
        assert status["window_passed"] is False
        assert len(status["fires_this_year"]) == 1

    def test_window_passed_flag(self, tmp_storage, priority_only_morazan):
        _seed_morazan([(date(2015, 7, 20), -2.0)], [(date(2015, 7, 20), -1.0)])
        status = triggers.current_status(today=date(2015, 9, 1), trigger=TRIGGER)
        assert status["window_active"] is False
        assert status["window_passed"] is True

    def test_history_excludes_current_year(self, tmp_storage, priority_only_morazan):
        _seed_morazan(
            [(date(2015, 7, 20), -2.0), (date(2018, 7, 20), -2.0)],
            [(date(2015, 7, 20), -1.0), (date(2018, 7, 20), -1.0)],
        )
        status = triggers.current_status(today=date(2018, 8, 1), trigger=TRIGGER)
        years_this = {f["year"] for f in status["fires_this_year"]}
        years_hist = {f["year"] for f in status["fires_history"]}
        assert years_this == {2018}
        assert years_hist == {2015}
