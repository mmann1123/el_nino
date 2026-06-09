"""Pentad-differencing logic for CHIRPS-GEFS.

These tests don't touch the network or disk — `_read_window_mean` is mocked,
and the AOI read is stubbed with an in-memory DataFrame. They guard the
arithmetic that converts CHC's cumulative 5/10/15-day totals into three
forward 5-day pentads matching the chirps parquet schema.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from el_nino.etl import chirps_gefs


def _lead_from_url(url: str) -> int:
    for lead in chirps_gefs.LEADS_DAYS:
        seg = f"{lead:02d}_day" if lead < 10 else f"{lead}_day"
        if f"/{seg}/" in url:
            return lead
    raise ValueError(f"no lead found in {url}")


@pytest.fixture
def stubbed_aoi(tmp_path, monkeypatch):
    """Bypass the geopandas read by returning a stub DataFrame with ADM1_NAME."""
    fake_aoi_path = tmp_path / "aoi.geojson"
    fake_aoi_path.write_text("{}")
    monkeypatch.setattr(chirps_gefs.config, "AOI_PATH", fake_aoi_path)

    import geopandas
    fake_aoi = pd.DataFrame({"ADM1_NAME": ["Morazan", "Sonsonate"]})
    monkeypatch.setattr(geopandas, "read_file", lambda *_a, **_k: fake_aoi)
    return fake_aoi


class TestFetchPentadTotals:
    def _mock_cumulatives(self, monkeypatch, cum_by_lead):
        """cum_by_lead: {5: {dep: mm}, 10: {...}, 15: {...}} — drives mocked HTTP reads."""
        def fake_read(url, _aoi):
            return cum_by_lead[_lead_from_url(url)]
        monkeypatch.setattr(chirps_gefs, "_read_window_mean", fake_read)

    def test_differencing_and_pentad_end_dates(self, stubbed_aoi, monkeypatch):
        # Cumulative totals: day0→5 = 20mm, day0→10 = 35mm, day0→15 = 50mm.
        # Differenced pentads: 20, 15, 15.
        self._mock_cumulatives(monkeypatch, {
            5:  {"Morazan": 20.0, "Sonsonate": 10.0},
            10: {"Morazan": 35.0, "Sonsonate": 18.0},
            15: {"Morazan": 50.0, "Sonsonate": 25.0},
        })

        issuance = date(2026, 6, 1)
        df = chirps_gefs.fetch_pentad_totals(issuance)

        assert set(df["departamento"]) == {"Morazan", "Sonsonate"}
        # Three pentads per department, pentad-end dates are issuance + 5/10/15.
        mor = df[df["departamento"] == "Morazan"].sort_values("date").reset_index(drop=True)
        assert list(mor["date"]) == [date(2026, 6, 6), date(2026, 6, 11), date(2026, 6, 16)]
        assert list(mor["precip_pentad_mm"]) == pytest.approx([20.0, 15.0, 15.0])

        son = df[df["departamento"] == "Sonsonate"].sort_values("date").reset_index(drop=True)
        assert list(son["precip_pentad_mm"]) == pytest.approx([10.0, 8.0, 7.0])

    def test_floating_point_noise_clamped_to_zero(self, stubbed_aoi, monkeypatch):
        # If a later cumulative is microscopically *less* than an earlier one
        # (float subtraction noise), the differenced pentad goes slightly
        # negative — clamp to 0 rather than emit a nonphysical negative rainfall.
        self._mock_cumulatives(monkeypatch, {
            5:  {"Morazan": 10.0, "Sonsonate": 10.0},
            10: {"Morazan": 9.9999999, "Sonsonate": 10.0},  # tiny rounding drop
            15: {"Morazan": 10.0, "Sonsonate": 10.0},
        })

        df = chirps_gefs.fetch_pentad_totals(date(2026, 6, 1))
        mor = df[df["departamento"] == "Morazan"].sort_values("date")
        assert (mor["precip_pentad_mm"] >= 0).all()

    def test_year_and_pentad_columns_attached(self, stubbed_aoi, monkeypatch):
        self._mock_cumulatives(monkeypatch, {
            5:  {"Morazan": 5.0},
            10: {"Morazan": 10.0},
            15: {"Morazan": 15.0},
        })
        df = chirps_gefs.fetch_pentad_totals(date(2026, 6, 1))
        assert set(df.columns) >= {"date", "departamento", "precip_pentad_mm", "year", "pentad"}
        assert df["year"].unique().tolist() == [2026]
        # DOY 157 (June 6 2026) → pentad ((157-1)//5)+1 = 32; DOY 162 → 33; DOY 167 → 34.
        assert df.sort_values("date")["pentad"].tolist() == [32, 33, 34]


class TestUrlConstruction:
    def test_two_digit_lead_unpadded(self):
        assert chirps_gefs._url_for(15, date(2026, 6, 8)) == (
            "https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3/15_day/global/"
            "data/2026/c3g_2026.06.08.tif"
        )

    def test_single_digit_lead_zero_padded(self):
        # CHC's directory tree zero-pads single-digit lead times: 05_day/, not 5_day/.
        assert chirps_gefs._url_for(5, date(2026, 6, 8)) == (
            "https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3/05_day/global/"
            "data/2026/c3g_2026.06.08.tif"
        )
