"""Frozen season records: closed seasons are stored once, never rewritten,
and read back instead of being recomputed from revised data."""

from __future__ import annotations

from datetime import date

import pytest

from el_nino import config
from el_nino.etl import season, season_history, triggers

SEASONS = [
    {"key": "primera", "start": (4, 20), "end": (8, 31), "alert_window_doy": (196, 227),
     "confirm_rule": None, "labeled_events": {}},
    {"key": "postrera", "start": (9, 1), "end": (1, 31), "alert_window_doy": None,
     "confirm_rule": None, "labeled_events": {}},
]


def _fire(dep, first):
    return triggers.FireRecord("t", "high", first.year, dep, first, -2.0, -1.0,
                               first_date=first, season="primera")


@pytest.fixture
def es_seasons(monkeypatch, tmp_storage):
    monkeypatch.setitem(config.CC, "seasons", SEASONS)
    monkeypatch.setattr(config, "country_departments", lambda: frozenset())


def test_freezes_a_closed_season_once(es_seasons, monkeypatch):
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [_fire("Morazan", date(2026, 7, 24))])
    written = season_history.freeze_closed(date(2026, 11, 1))
    # Postrera 2025 also closed within the past year.
    assert written == [f"{config.COUNTRY}/postrera/2025", f"{config.COUNTRY}/primera/2026"]
    assert season_history.freeze_closed(date(2026, 11, 2)) == []


def test_waits_for_late_data_before_freezing(es_seasons, monkeypatch):
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
    # Primera ended Aug 31; late observations can still arrive in September.
    assert f"{config.COUNTRY}/primera/2026" not in season_history.freeze_closed(date(2026, 9, 2))


def test_frozen_record_survives_data_revision(es_seasons, monkeypatch):
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [_fire("Morazan", date(2026, 7, 24))])
    season_history.freeze_closed(date(2026, 11, 1))
    # Revised data no longer fires; the closed season keeps what was shown.
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
    rec = season.season_record(date(2026, 11, 2))
    assert [e.departamento for e in rec.previous.entries] == ["Morazan"]
    assert season_history.freeze_closed(date(2026, 11, 2)) == []


def test_open_season_is_never_frozen(es_seasons, monkeypatch):
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [_fire("Morazan", date(2026, 7, 24))])
    written = season_history.freeze_closed(date(2026, 8, 1))
    assert f"{config.COUNTRY}/primera/2026" not in written


def test_old_seasons_are_not_backfilled(es_seasons, monkeypatch):
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
    # On Apr 1 2027, postrera 2026 (ended Jan 31) is recent; primera 2025 is not.
    written = season_history.freeze_closed(date(2027, 4, 1))
    assert f"{config.COUNTRY}/postrera/2026" in written
    assert f"{config.COUNTRY}/primera/2025" not in written


def test_clear_drops_only_the_active_country(es_seasons, monkeypatch):
    monkeypatch.setattr(triggers, "evaluate_history", lambda: [])
    season_history.freeze_closed(date(2026, 11, 1))
    path = config.STORAGE_ROOT / "season_history.json"
    path.write_text(path.read_text().replace("{", '{"other/x/2026": {}, ', 1))
    season_history.clear()
    assert list(season_history.load()) == ["other/x/2026"]
