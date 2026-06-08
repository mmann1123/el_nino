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


class TestParseNino34Weekly:
    """CPC weekly Niño 3.4 table parsing. The real file is fixed-width with the
    Niño1+2/3/3.4/4 SST+SSTA columns; the Niño 3.4 anomaly is the 6th float and
    negative anomalies are sign-concatenated to the SST (e.g. '25.5-1.1')."""

    HEADER = (
        " Weekly SST data starts week centered on 2Sept1981\n"
        "\n"
        "                Nino1+2      Nino3        Nino34        Nino4\n"
        " Week          SST SSTA     SST SSTA     SST SSTA     SST SSTA\n"
    )

    def test_extracts_nino34_columns(self):
        text = self.HEADER + " 27MAY2026     26.2 2.2     28.3 1.3     28.8 1.0     29.9 1.1\n"
        df = enso.parse_nino34_weekly(text)
        assert len(df) == 1
        row = df.iloc[0]
        assert str(row["date"]) == "2026-05-27"
        assert row["nino34_sst"] == 28.8   # 5th float
        assert row["nino34_ssta"] == 1.0   # 6th float, NOT the Niño4 value
        assert row["phase"] == "El Niño"

    def test_sign_concatenated_negative_anomaly(self):
        # Old-format rows glue a negative anomaly onto the SST with no space.
        text = self.HEADER + " 06JAN2021     23.1-0.8     24.7-0.8     25.5-1.1     27.1-1.2\n"
        df = enso.parse_nino34_weekly(text)
        assert df.iloc[0]["nino34_sst"] == 25.5
        assert df.iloc[0]["nino34_ssta"] == -1.1
        assert df.iloc[0]["phase"] == "La Niña"

    def test_header_and_blank_lines_skipped(self):
        df = enso.parse_nino34_weekly(self.HEADER)
        assert df.empty

    def test_rows_sorted_oldest_to_newest(self):
        text = self.HEADER + (
            " 27MAY2026     26.2 2.2     28.3 1.3     28.8 1.0     29.9 1.1\n"
            " 13MAY2026     26.4 1.8     28.3 1.1     28.8 0.9     29.8 1.0\n"
        )
        df = enso.parse_nino34_weekly(text)
        assert [str(d) for d in df["date"]] == ["2026-05-13", "2026-05-27"]

    def test_empty_text_returns_empty_frame(self):
        assert enso.parse_nino34_weekly("").empty
