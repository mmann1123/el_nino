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
                      "silking_window", "labeled_events"):
            assert field in cc, f"{key} missing {field}"

    @pytest.mark.parametrize("key", list(config.COUNTRIES))
    def test_silking_window_is_ordered_doy_pair(self, key):
        lo, hi = config.COUNTRIES[key]["silking_window"]
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
        for year in config.COUNTRIES[key]["labeled_events"]:
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
