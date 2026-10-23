"""The "This season" record: the Confirmed rule, season bounds, and how Alert
and Confirmed fires merge into one per-department entry that stays listed
until the season ends."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from el_nino import config
from el_nino.etl import season, storage, triggers

RULE = {"indicator": "wapor", "window_doy": (182, 243), "z_threshold": -1.25, "consecutive": 2}
SEASON = {"key": "primera", "doy": (110, 243)}


def _dekads(year, zs, start_month=7):
    """Dekadal rows from Jul 1 (or start_month) with the given z values."""
    dates = [date(year, start_month + i // 3, 1 + 10 * (i % 3)) for i in range(len(zs))]
    return pd.DataFrame({"date": dates, "value_anom_z": zs, "is_forecast": False})


class TestFirstConfirmedDate:
    def first(self, df, year=2026):
        return season.first_confirmed_date(df, year, RULE["window_doy"], RULE["z_threshold"], RULE["consecutive"])

    def test_fires_on_the_dekad_completing_the_run(self):
        assert self.first(_dekads(2026, [-0.5, -1.4, -1.6, -2.0])) == date(2026, 7, 21)

    def test_a_single_dip_does_not_fire(self):
        assert self.first(_dekads(2026, [-2.0, 0.1, -2.0, 0.3])) is None

    def test_missing_value_breaks_the_run(self):
        assert self.first(_dekads(2026, [-2.0, float("nan"), -2.0])) is None

    def test_threshold_is_inclusive(self):
        assert self.first(_dekads(2026, [-1.25, -1.25])) == date(2026, 7, 11)

    def test_outside_window_is_ignored(self):
        june = _dekads(2026, [-3.0, -3.0, -3.0], start_month=6)
        assert self.first(june) is None

    def test_other_years_are_ignored(self):
        assert self.first(_dekads(2025, [-2.0, -2.0])) is None

    def test_forecast_rows_do_not_count(self):
        df = _dekads(2026, [-2.0, -2.0])
        df["is_forecast"] = [False, True]
        assert self.first(df) is None


@pytest.mark.parametrize("d, end", [
    (date(2026, 7, 1), date(2026, 7, 10)),
    (date(2026, 7, 11), date(2026, 7, 20)),
    (date(2026, 7, 21), date(2026, 7, 31)),
    (date(2026, 2, 21), date(2026, 2, 28)),
    (date(2028, 2, 21), date(2028, 2, 29)),
])
def test_dekad_end(d, end):
    assert season.dekad_end(d) == end


def _fire(dep, year, first):
    return triggers.FireRecord("t", "high", year, dep, first, -2.0, -1.0, first_date=first)


@pytest.fixture
def es_season(monkeypatch, tmp_storage):
    monkeypatch.setitem(config.CC, "season", SEASON)
    monkeypatch.setitem(config.CC, "confirm_rule", RULE)
    monkeypatch.setattr(config, "country_departments", lambda: frozenset())
    return tmp_storage


def _wapor(dep, df):
    df = df.assign(departamento=dep)
    storage.write_parquet(df, storage.raw_path("wapor", dep))


class TestSeasonRecord:
    def test_merges_alert_and_confirmed_per_department(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history",
                            lambda: [_fire("Morazan", 2026, date(2026, 7, 24))])
        _wapor("Morazan", _dekads(2026, [-1.5, -1.6]))
        _wapor("San Vicente", _dekads(2026, [-1.3, -2.0]))
        rec = season.season_record(date(2026, 8, 15))
        assert rec.active and rec.year == 2026
        by_dep = {e.departamento: e for e in rec.entries}
        assert by_dep["Morazan"].alert_date == date(2026, 7, 24)
        assert by_dep["Morazan"].confirmed_date == date(2026, 7, 11)
        assert by_dep["San Vicente"].alert_date is None
        # Ordered by first fire date.
        assert [e.departamento for e in rec.entries] == ["Morazan", "San Vicente"]

    def test_confirmed_waits_for_its_dekad_to_end(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
        _wapor("Morazan", _dekads(2026, [-1.5, -1.6]))  # completes on the Jul 11-20 dekad
        assert season.season_record(date(2026, 7, 15)).entries == []
        (entry,) = season.season_record(date(2026, 7, 20)).entries
        assert entry.confirmed_date == date(2026, 7, 11)
        assert entry.confirmed_end == date(2026, 7, 20)

    def test_department_stays_listed_after_conditions_recover(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
        _wapor("La Union", _dekads(2026, [-2.0, -2.0, 1.5, 1.5, 1.5]))
        rec = season.season_record(date(2026, 8, 30))
        assert [e.departamento for e in rec.entries] == ["La Union"]

    def test_other_years_fires_are_excluded(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history",
                            lambda: [_fire("Morazan", 2025, date(2025, 7, 24))])
        assert season.season_record(date(2026, 8, 1)).entries == []

    def test_after_season_end_is_a_recap_of_it(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history",
                            lambda: [_fire("Morazan", 2026, date(2026, 7, 24))])
        rec = season.season_record(date(2026, 10, 23))
        assert not rec.active and rec.year == 2026
        assert [e.departamento for e in rec.entries] == ["Morazan"]

    def test_before_season_start_recaps_last_year(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history",
                            lambda: [_fire("Morazan", 2026, date(2026, 7, 24))])
        rec = season.season_record(date(2027, 3, 1))
        assert not rec.active and rec.year == 2026
        assert rec.start == date(2026, 4, 20) and rec.end == date(2026, 8, 31)

    def test_no_confirm_rule_lists_alerts_only(self, es_season, monkeypatch):
        monkeypatch.setitem(config.CC, "confirm_rule", None)
        monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
        _wapor("Morazan", _dekads(2026, [-2.0, -2.0]))
        assert season.season_record(date(2026, 8, 1)).entries == []

    def test_no_season_configured(self, monkeypatch):
        monkeypatch.setitem(config.CC, "season", None)
        assert season.season_record(date(2026, 8, 1)) is None


@pytest.mark.parametrize("country", sorted(config.COUNTRIES))
def test_every_country_defines_a_season(country):
    cc = config.COUNTRIES[country]
    start, end = cc["season"]["doy"]
    assert 1 <= start < end <= 366
    assert "confirm_rule" in cc
