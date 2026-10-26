"""Banner text that depends on the season's trigger: rule descriptions, the
provisional caveat, and triggered-department rows."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from el_nino import config
from el_nino.dashboard import alerts, i18n
from el_nino.etl import triggers

BASE = triggers.CalibratedTrigger("t", "", (245, 275), -1.0, -1.5, "high", season="postrera",
                                  spi_column="spi_1")


@pytest.fixture(autouse=True)
def _english():
    i18n.set_offline_lang("en")
    yield
    i18n.set_offline_lang("en")


def test_rule_text_follows_the_trigger():
    assert alerts.rule_text(BASE) == "rainfall over the last month and soil moisture both very low during the alert period"
    rain_only = dataclasses.replace(BASE, rzsm_threshold=None)
    assert alerts.rule_text(rain_only) == "rainfall over the last month very low during the alert period"


def test_rainfall_only_row_has_no_soil_value():
    fire = triggers.FireRecord("t", "high", 2026, "Sud", date(2026, 9, 20), -1.52, float("nan"),
                               first_date=date(2026, 9, 17), season="automne").to_dict()
    assert fire["rzsm_min_z"] is None
    row = alerts._fire_row(fire)
    assert "soil" not in row and "nan" not in row
    assert "`-1.52`" in row


def test_frozen_row_shows_only_the_date():
    row = alerts._fire_row({"departamento": "Morazan", "first_date": "2026-07-24", "frozen": True})
    assert row == "- **Morazan** — first fired on 24 Jul 2026"


def test_provisional_text_cites_the_seasons_labels(monkeypatch):
    seasons = [dict(s) for s in config.CC["seasons"]]
    for s in seasons:
        if s["key"] == "postrera":
            s["labeled_events"] = {2023: ("moderate", ""), 2025: ("moderate", ""), 2015: ("normal", "")}
    monkeypatch.setitem(config.CC, "seasons", seasons)
    text = alerts._provisional_text(BASE)
    assert "set using 2 past droughts with written reports (2023, 2025)" in text
