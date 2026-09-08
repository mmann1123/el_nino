"""Completeness + consistency of the dashboard string table, and the
language-resolution helpers that don't need a Streamlit runtime."""

from __future__ import annotations

import re
from datetime import date

import pytest

from el_nino import config
from el_nino.dashboard import drought_status, i18n

_PLACEHOLDER = re.compile(r"{(\w+)}")


@pytest.fixture(autouse=True)
def _reset_lang():
    i18n.set_offline_lang("en")
    yield
    i18n.set_offline_lang("en")


class TestStringTable:
    def test_every_key_has_every_language(self):
        missing = [
            (key, lang)
            for key, entry in i18n.STRINGS.items()
            for lang in i18n.LANGS
            if not entry.get(lang)
        ]
        assert missing == []

    def test_placeholders_match_across_languages(self):
        bad = []
        for key, entry in i18n.STRINGS.items():
            en = set(_PLACEHOLDER.findall(entry["en"]))
            for lang, text in entry.items():
                if set(_PLACEHOLDER.findall(text)) != en:
                    bad.append((key, lang))
        assert bad == []

    def test_unknown_key_raises(self):
        with pytest.raises(KeyError):
            i18n.t("definitely_not_a_key")

    @pytest.mark.parametrize("country", sorted(config.COUNTRIES))
    def test_country_specific_keys_exist(self, country):
        assert f"crop_caption_{country}" in i18n.STRINGS
        assert f"priority_label_{country}" in i18n.STRINGS

    @pytest.mark.parametrize("country", sorted(config.COUNTRIES))
    def test_default_lang_is_known(self, country):
        assert config.COUNTRIES[country]["default_lang"] in i18n.LANGS


class TestLookup:
    def test_formats_placeholders(self):
        assert i18n.t("lag_days_ago", n=3) == "3 days ago"

    def test_switches_language_offline(self):
        i18n.set_offline_lang("es")
        assert i18n.t("lag_days_ago", n=3) == "hace 3 días"
        i18n.set_offline_lang("fr")
        assert i18n.t("tab_overview") == "Vue d'ensemble"

    def test_drought_categories_follow_language(self):
        assert drought_status.D2.label == "Severe Drought"
        i18n.set_offline_lang("es")
        assert drought_status.D2.label == "Sequía severa"
        assert drought_status.classify(-1.7).description

    def test_plain_language_follows_language(self):
        i18n.set_offline_lang("fr")
        assert "plus humide" in drought_status.plain_language(0.0)

    def test_dep_display_translates_only_sentinel(self):
        i18n.set_offline_lang("es")
        assert i18n.dep_display("ALL", "ALL") == "Todos (promedio nacional)"
        assert i18n.dep_display("San Miguel", "ALL") == "San Miguel"

    def test_phase_label(self):
        i18n.set_offline_lang("fr")
        assert i18n.phase_label("Neutral") == "Neutre"
        assert i18n.phase_label("El Niño") == "El Niño"


class TestDates:
    def test_month_day_orders_by_language(self):
        d = date(2026, 7, 15)
        assert i18n.fmt_mon_day(d) == "Jul 15"
        i18n.set_offline_lang("es")
        assert i18n.fmt_mon_day(d) == "15 jul"
        i18n.set_offline_lang("fr")
        assert i18n.fmt_mon_day(d) == "15 juil."

    def test_mon_year_and_day_mon_year(self):
        d = date(2026, 8, 7)
        assert i18n.fmt_mon_year(d) == "Aug 2026"
        assert i18n.fmt_day_mon_year(d) == "07 Aug 2026"
        i18n.set_offline_lang("es")
        assert i18n.fmt_mon_year(d) == "ago 2026"


class TestCountryLangs:
    def test_native_first_then_english(self, monkeypatch):
        monkeypatch.setitem(config.CC, "default_lang", "fr")
        assert i18n.country_langs() == ["fr", "en"]
        monkeypatch.setitem(config.CC, "default_lang", "en")
        assert i18n.country_langs() == ["en"]
