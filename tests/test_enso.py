"""ONI phase classification and El Niño / La Niña year extraction."""

from __future__ import annotations

import pandas as pd

from el_nino.etl import enso


class TestClassify:
    def test_el_nino_at_threshold(self):
        assert enso._classify(0.5) == "El Niño"
        assert enso._classify(2.4) == "El Niño"

    def test_la_nina_at_threshold(self):
        assert enso._classify(-0.5) == "La Niña"
        assert enso._classify(-1.8) == "La Niña"

    def test_neutral_between(self):
        assert enso._classify(0.0) == "Neutral"
        assert enso._classify(0.49) == "Neutral"
        assert enso._classify(-0.49) == "Neutral"


class TestSeasonToCenterMonth:
    def test_known_seasons(self):
        assert enso._season_to_center_month("DJF") == 1
        assert enso._season_to_center_month("JJA") == 7
        assert enso._season_to_center_month("NDJ") == 12

    def test_case_and_whitespace_insensitive(self):
        assert enso._season_to_center_month(" jja ") == 7

    def test_unknown_defaults_to_january(self):
        assert enso._season_to_center_month("ZZZ") == 1


class TestYearExtraction:
    def _df(self):
        return pd.DataFrame({
            "year": [2014, 2015, 2015, 2016, 2017],
            "phase": ["Neutral", "El Niño", "El Niño", "La Niña", "Neutral"],
        })

    def test_el_nino_years_deduped_and_sorted(self):
        assert enso.el_nino_years(self._df()) == [2015]

    def test_la_nina_years(self):
        assert enso.la_nina_years(self._df()) == [2016]

    def test_empty_frame_returns_empty_list(self):
        assert enso.el_nino_years(pd.DataFrame()) == []
        assert enso.la_nina_years(pd.DataFrame()) == []
