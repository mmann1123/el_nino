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
SEASONS = [
    {"key": "primera", "start": (4, 20), "end": (8, 31), "alert_window_doy": (196, 227),
     "confirm_rule": RULE, "labeled_events": {}},
    {"key": "postrera", "start": (9, 1), "end": (1, 31), "alert_window_doy": None,
     "confirm_rule": None, "labeled_events": {}},
]


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


def _fire(dep, year, first, season_key="primera"):
    return triggers.FireRecord("t", "high", year, dep, first, -2.0, -1.0,
                               first_date=first, season=season_key)


@pytest.fixture
def es_season(monkeypatch, tmp_storage):
    monkeypatch.setitem(config.CC, "seasons", SEASONS)
    monkeypatch.setattr(config, "country_departments", lambda: frozenset())
    return tmp_storage


def _wapor(dep, df):
    df = df.assign(departamento=dep)
    storage.write_parquet(df, storage.raw_path("wapor", dep))


class TestSeasonBounds:
    def test_later_season_ends_the_next_year(self):
        assert season.season_bounds(2026, SEASONS[1]) == (date(2026, 9, 1), date(2027, 1, 31))

    @pytest.mark.parametrize("today, key, year, active", [
        (date(2026, 4, 19), "postrera", 2025, False),   # gap: recap of last postrera
        (date(2026, 4, 20), "primera", 2026, True),
        (date(2026, 8, 31), "primera", 2026, True),
        (date(2026, 9, 1), "postrera", 2026, True),
        (date(2027, 1, 15), "postrera", 2026, True),    # planting year, not calendar year
        (date(2027, 2, 1), "postrera", 2026, False),
    ])
    def test_current_span(self, es_season, today, key, year, active):
        span = season.current_span(today)
        assert (span.key, span.year, span.active) == (key, year, active)

    def test_previous_span(self, es_season):
        primera = season.current_span(date(2026, 7, 1))
        assert (season.previous_span(primera).key, season.previous_span(primera).year) == ("postrera", 2025)
        postrera = season.current_span(date(2026, 10, 1))
        assert (season.previous_span(postrera).key, season.previous_span(postrera).year) == ("primera", 2026)


class TestSeasonRecord:
    def test_merges_alert_and_confirmed_per_department(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history",
                            lambda: [_fire("Morazan", 2026, date(2026, 7, 24))])
        _wapor("Morazan", _dekads(2026, [-1.5, -1.6]))
        _wapor("San Vicente", _dekads(2026, [-1.3, -2.0]))
        rec = season.season_record(date(2026, 8, 15))
        assert rec.active and rec.year == 2026 and rec.has_confirm
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

    def test_next_season_starts_clean_with_previous_summary(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history", lambda: [
            _fire("Morazan", 2026, date(2026, 7, 24)),
            _fire("Cabanas", 2026, date(2026, 7, 30)),
        ])
        _wapor("Morazan", _dekads(2026, [-1.5, -1.6]))
        rec = season.season_record(date(2026, 9, 2))
        assert rec.key == "postrera" and rec.active and not rec.has_confirm
        assert rec.entries == []
        assert rec.previous == season.SeasonSummary("primera", 2026, 1, 1)

    def test_later_season_lists_only_its_own_fires(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history", lambda: [
            _fire("Morazan", 2026, date(2026, 7, 24)),
            _fire("La Paz", 2026, date(2026, 9, 20), "postrera"),
        ])
        rec = season.season_record(date(2027, 1, 15))
        assert (rec.key, rec.year) == ("postrera", 2026)
        assert [e.departamento for e in rec.entries] == ["La Paz"]

    def test_gap_recaps_the_last_season(self, es_season, monkeypatch):
        monkeypatch.setattr(triggers, "evaluate_history",
                            lambda: [_fire("La Paz", 2026, date(2026, 9, 20), "postrera")])
        rec = season.season_record(date(2027, 3, 1))
        assert not rec.active and (rec.key, rec.year) == ("postrera", 2026)
        assert rec.start == date(2026, 9, 1) and rec.end == date(2027, 1, 31)
        assert [e.departamento for e in rec.entries] == ["La Paz"]

    def test_no_confirm_rule_lists_alerts_only(self, es_season, monkeypatch):
        seasons = [dict(SEASONS[0], confirm_rule=None), SEASONS[1]]
        monkeypatch.setitem(config.CC, "seasons", seasons)
        monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
        _wapor("Morazan", _dekads(2026, [-2.0, -2.0]))
        assert season.season_record(date(2026, 8, 1)).entries == []

    def test_no_season_configured(self, monkeypatch):
        monkeypatch.setitem(config.CC, "seasons", [])
        assert season.season_record(date(2026, 8, 1)) is None


@pytest.mark.parametrize("country", sorted(config.COUNTRIES))
def test_every_country_has_two_back_to_back_seasons(country):
    seasons = config.COUNTRIES[country]["seasons"]
    assert len(seasons) == 2
    first_end = season.season_bounds(2026, seasons[0])[1]
    second_start = season.season_bounds(2026, seasons[1])[0]
    assert (second_start - first_end).days == 1
