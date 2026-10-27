"""Country registry invariants and AOI-derived department filtering."""

from __future__ import annotations

import json

import pytest

from el_nino import config


class TestCountriesRegistry:
    def test_active_country_is_registered(self):
        assert config.COUNTRY in config.COUNTRIES
        assert config.CC is config.COUNTRIES[config.COUNTRY]

    @pytest.mark.parametrize("key", list(config.COUNTRIES))
    def test_each_country_has_required_fields(self, key):
        cc = config.COUNTRIES[key]
        for field in ("iso2", "display_name", "aoi_filename", "map_center",
                      "map_zoom", "dept_term", "priority_departments",
                      "seasons"):
            assert field in cc, f"{key} missing {field}"

    @pytest.mark.parametrize("key", list(config.COUNTRIES))
    def test_seasons_are_well_formed(self, key):
        seasons = config.COUNTRIES[key]["seasons"]
        assert len({s["key"] for s in seasons}) == len(seasons)
        for s in seasons:
            assert {"key", "start", "end", "alert_window_doy", "confirm_rule",
                    "labeled_events"} <= set(s)
            if s["alert_window_doy"] is not None:
                lo, hi = s["alert_window_doy"]
                assert 1 <= lo < hi <= 366

    @pytest.mark.parametrize("key", list(config.COUNTRIES))
    def test_priority_departments_nonempty(self, key):
        assert len(config.COUNTRIES[key]["priority_departments"]) > 0

    @pytest.mark.parametrize("key", list(config.COUNTRIES))
    def test_map_center_has_lat_lon(self, key):
        center = config.COUNTRIES[key]["map_center"]
        assert "lat" in center and "lon" in center

    @pytest.mark.parametrize("key", list(config.COUNTRIES))
    def test_labeled_event_keys_are_years(self, key):
        for s in config.COUNTRIES[key]["seasons"]:
            for year in s["labeled_events"]:
                assert isinstance(year, int)
                assert 1980 <= year <= 2100


class TestCountryDepartments:
    def _write_aoi(self, path, names):
        gj = {"features": [
            {"properties": {"ADM1_NAME": n}} for n in names
        ]}
        path.write_text(json.dumps(gj))

    def test_reads_adm1_names_from_aoi(self, tmp_path, monkeypatch):
        aoi = tmp_path / "aoi.geojson"
        self._write_aoi(aoi, ["Morazan", "San Miguel", "La Union"])
        monkeypatch.setattr(config, "AOI_PATH", aoi)
        config.country_departments.cache_clear()
        try:
            result = config.country_departments()
            assert result == frozenset({"Morazan", "San Miguel", "La Union"})
        finally:
            config.country_departments.cache_clear()

    def test_missing_aoi_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "AOI_PATH", tmp_path / "nope.geojson")
        config.country_departments.cache_clear()
        try:
            assert config.country_departments() == frozenset()
        finally:
            config.country_departments.cache_clear()

    def test_malformed_aoi_returns_empty(self, tmp_path, monkeypatch):
        bad = tmp_path / "bad.geojson"
        bad.write_text("{ not valid json")
        monkeypatch.setattr(config, "AOI_PATH", bad)
        config.country_departments.cache_clear()
        try:
            assert config.country_departments() == frozenset()
        finally:
            config.country_departments.cache_clear()


@pytest.mark.parametrize("key", list(config.COUNTRIES))
def test_alert_windows_fall_inside_their_season(key):
    from datetime import date, timedelta
    from el_nino.etl import season as season_mod
    for s in config.COUNTRIES[key]["seasons"]:
        if s["alert_window_doy"] is None:
            continue
        start, end = season_mod.season_bounds(2026, s)
        lo, hi = (date(2026, 1, 1) + timedelta(days=d - 1) for d in s["alert_window_doy"])
        assert start <= lo and hi <= end, s["key"]
