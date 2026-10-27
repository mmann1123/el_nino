"""Calibrated drought-trigger evaluation over historical per-department series.

Builds synthetic CHIRPS (spi_3) and SMAP (value_anom_z) parquets, then asserts
the trigger fires exactly when both indicators cross their thresholds *inside*
the silking window, in any of the active country's departments.
"""

from __future__ import annotations

import dataclasses

from datetime import date

import pandas as pd
import pytest

from el_nino import config
from el_nino.etl import season, storage, triggers


TRIGGER = triggers.CalibratedTrigger(
    name="test_trigger",
    description="test",
    window_doy=(196, 227),      # mid-Jul to mid-Aug
    spi3_threshold=-1.5,
    rzsm_threshold=-0.5,
    severity="high",
    season="primera",
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
def es_departments(monkeypatch):
    monkeypatch.setattr(config, "PRIORITY_DEPARTMENTS", ["Morazan"])
    monkeypatch.setattr(config, "country_departments", lambda: frozenset({"Morazan", "Cabanas"}))


def _seed_morazan(spi_rows, rzsm_rows):
    _write("chirps", "Morazan", "spi_3", spi_rows)
    _write("smap", "Morazan", "value_anom_z", rzsm_rows)


class TestEvaluateHistory:
    def test_fires_when_both_cross_in_window(self, tmp_storage, es_departments):
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

    def test_no_fire_when_only_one_crosses(self, tmp_storage, es_departments):
        _seed_morazan(
            spi_rows=[(date(2016, 7, 20), -2.0)],     # crosses
            rzsm_rows=[(date(2016, 7, 20), 0.1)],     # does NOT cross
        )
        assert triggers.evaluate_history(TRIGGER) == []

    def test_out_of_window_extremes_are_ignored(self, tmp_storage, es_departments):
        # Severe deficits in January must not trigger a silking-window alert.
        _seed_morazan(
            spi_rows=[(date(2017, 1, 15), -3.0), (date(2017, 7, 20), -0.1)],
            rzsm_rows=[(date(2017, 1, 15), -3.0), (date(2017, 7, 20), 0.0)],
        )
        assert triggers.evaluate_history(TRIGGER) == []

    def test_non_priority_department_fires(self, tmp_storage, es_departments):
        _write("chirps", "Cabanas", "spi_3", [(date(2015, 7, 20), -2.0)])
        _write("smap", "Cabanas", "value_anom_z", [(date(2015, 7, 20), -1.0)])
        assert [f.departamento for f in triggers.evaluate_history(TRIGGER)] == ["Cabanas"]

    def test_other_country_department_excluded(self, tmp_storage, es_departments):
        # ES and HT can share one STORAGE_ROOT.
        _write("chirps", "Sud", "spi_3", [(date(2015, 7, 20), -2.0)])
        _write("smap", "Sud", "value_anom_z", [(date(2015, 7, 20), -1.0)])
        assert triggers.evaluate_history(TRIGGER) == []

    def test_first_date_is_when_both_have_crossed(self, tmp_storage, es_departments):
        # SPI crosses Jul 20, soil Jul 25, SPI bottoms out Aug 5: the alert
        # first shows Jul 25 — not on the SPI minimum.
        _seed_morazan(
            spi_rows=[(date(2015, 7, 15), -1.0), (date(2015, 7, 20), -1.6), (date(2015, 8, 5), -2.5)],
            rzsm_rows=[(date(2015, 7, 20), -0.2), (date(2015, 7, 25), -0.8)],
        )
        fire = triggers.evaluate_history(TRIGGER)[0]
        assert fire.first_date == date(2015, 7, 25)
        assert fire.fire_date == date(2015, 8, 5)

    def test_requires_both_indicators_present(self, tmp_storage, es_departments):
        # CHIRPS only, no SMAP overlap -> cannot evaluate -> no fire.
        _write("chirps", "Morazan", "spi_3", [(date(2015, 7, 20), -2.0)])
        assert triggers.evaluate_history(TRIGGER) == []

    def test_forecast_rows_cannot_fire(self, tmp_storage, es_departments):
        # GFS forecast pentads get SPI too; only observations may fire.
        df = pd.DataFrame({
            "date": [date(2015, 7, 20)], "departamento": ["Morazan"],
            "spi_3": [-2.0], "is_forecast": [True],
        })
        storage.write_parquet(df, storage.raw_path("chirps", "Morazan"))
        _write("smap", "Morazan", "value_anom_z", [(date(2015, 7, 20), -1.0)])
        assert triggers.evaluate_history(TRIGGER) == []


class TestCurrentStatus:
    def test_window_active_flag(self, tmp_storage, es_departments):
        _seed_morazan([(date(2015, 7, 20), -2.0)], [(date(2015, 7, 20), -1.0)])
        status = triggers.current_status(today=date(2015, 7, 20), trigger=TRIGGER)
        assert status["window_active"] is True
        assert status["window_passed"] is False
        assert len(status["fires_this_year"]) == 1

    def test_window_passed_flag(self, tmp_storage, es_departments):
        _seed_morazan([(date(2015, 7, 20), -2.0)], [(date(2015, 7, 20), -1.0)])
        status = triggers.current_status(today=date(2015, 9, 1), trigger=TRIGGER)
        assert status["window_active"] is False
        assert status["window_passed"] is True

    def test_history_excludes_current_year(self, tmp_storage, es_departments):
        _seed_morazan(
            [(date(2015, 7, 20), -2.0), (date(2018, 7, 20), -2.0)],
            [(date(2015, 7, 20), -1.0), (date(2018, 7, 20), -1.0)],
        )
        status = triggers.current_status(today=date(2018, 8, 1), trigger=TRIGGER)
        years_this = {f["year"] for f in status["fires_this_year"]}
        years_hist = {f["year"] for f in status["fires_history"]}
        assert years_this == {2018}
        assert years_hist == {2015}

    def test_span_sets_the_season_year(self, tmp_storage, es_departments):
        # Mar 2016 is between seasons; the span on screen is primera 2015.
        _seed_morazan([(date(2015, 7, 20), -2.0)], [(date(2015, 7, 20), -1.0)])
        span = season.SeasonSpan("primera", 2015, date(2015, 4, 20), date(2015, 8, 31), False)
        status = triggers.current_status(today=date(2016, 3, 1), trigger=TRIGGER, span=span)
        assert {f["year"] for f in status["fires_this_year"]} == {2015}
        assert status["fires_history"] == []
        assert status["window_passed"] is True

    def test_season_without_trigger_has_no_status(self, tmp_storage, es_departments, monkeypatch):
        monkeypatch.setattr(triggers, "CALIBRATED_TRIGGERS", [TRIGGER])  # primera only
        span = season.SeasonSpan("postrera", 2026, date(2026, 9, 1), date(2027, 1, 31), True)
        assert triggers.current_status(today=date(2026, 10, 1), span=span) is None


class TestTriggerVariants:
    def test_rainfall_only_trigger_ignores_soil_moisture(self, tmp_storage, es_departments):
        _write("chirps", "Morazan", "spi_3", [(date(2015, 7, 20), -2.0)])
        trig = dataclasses.replace(TRIGGER, rzsm_threshold=None)
        (fire,) = triggers.evaluate_history(trig)
        assert fire.first_date == date(2015, 7, 20)
        assert fire.season == "primera"

    def test_spi_column_selects_the_scale(self, tmp_storage, es_departments):
        _write("chirps", "Morazan", "spi_1", [(date(2015, 9, 20), -2.0)])
        _write("smap", "Morazan", "value_anom_z", [(date(2015, 9, 20), -1.0)])
        trig = dataclasses.replace(TRIGGER, spi_column="spi_1", window_doy=(250, 300))
        assert [f.year for f in triggers.evaluate_history(trig)] == [2015]
        assert triggers.evaluate_history(dataclasses.replace(trig, spi_column="spi_3")) == []


@pytest.mark.parametrize("country", sorted(triggers.TRIGGERS_BY_COUNTRY))
def test_trigger_window_is_its_seasons_alert_window(country):
    seasons = {s["key"]: s for s in config.COUNTRIES[country]["seasons"]}
    for trig in triggers.TRIGGERS_BY_COUNTRY[country]:
        assert trig.window_doy == seasons[trig.season]["alert_window_doy"]
