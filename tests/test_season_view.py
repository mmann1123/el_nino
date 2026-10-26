"""Layout of the Overview's "This season" panel: confirmed departments in
their own box, alert-only ones collapsed into one line."""

from __future__ import annotations

from datetime import date

import pytest

from el_nino import config
from el_nino.dashboard import i18n, season_view
from el_nino.etl.season import SeasonEntry, SeasonRecord


@pytest.fixture(autouse=True)
def _english():
    i18n.set_offline_lang("en")
    yield
    i18n.set_offline_lang("en")


def _rec(entries):
    return SeasonRecord("primera", 2026, date(2026, 4, 20), date(2026, 8, 31), False, entries)


ALERT = date(2026, 7, 19)
ENTRIES = [
    SeasonEntry("Ahuachapan", ALERT),
    SeasonEntry("San Miguel", ALERT, date(2026, 8, 1)),
    SeasonEntry("La Union", ALERT, date(2026, 7, 11)),
    SeasonEntry("Cabanas", ALERT),
]


def test_split_orders_confirmed_by_dekad():
    confirmed, alert_only = season_view._split(ENTRIES)
    assert [e.departamento for e in confirmed] == ["La Union", "San Miguel"]
    assert [e.departamento for e in alert_only] == ["Ahuachapan", "Cabanas"]


def test_confirmed_box_comes_before_alert_line(monkeypatch):
    monkeypatch.setitem(config.CC, "confirm_rule", {"indicator": "wapor"})
    html = season_view._layout(_rec(ENTRIES))
    assert "Confirmed — crop stress (2)" in html
    assert html.index("La Union") < html.index("Ahuachapan")
    assert "Jul 11–20" in html


def test_shared_alert_date_is_printed_once(monkeypatch):
    monkeypatch.setitem(config.CC, "confirm_rule", {"indicator": "wapor"})
    line = season_view._alert_line(season_view._split(ENTRIES)[1], has_confirm=True)
    assert "Alert only since Jul 19 (2):" in line
    assert line.count("Jul 19") == 1


def test_differing_alert_dates_go_on_each_name():
    entries = [SeasonEntry("Ahuachapan", ALERT), SeasonEntry("Cabanas", date(2026, 7, 29))]
    line = season_view._alert_line(entries, has_confirm=True)
    assert "Alert only (2):" in line
    assert "Jul 19" in line and "Jul 29" in line


def test_alert_only_country_has_no_confirmed_box(monkeypatch):
    monkeypatch.setitem(config.CC, "confirm_rule", None)
    html = season_view._layout(_rec([SeasonEntry("Nord", ALERT)]))
    assert "Confirmed" not in html
    assert "Alert since Jul 19 (1):" in html
