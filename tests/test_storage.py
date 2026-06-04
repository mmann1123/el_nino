"""Raw-parquet path sanitization and the upsert/dedup contract."""

from __future__ import annotations

from datetime import date

import pandas as pd

from el_nino.etl import storage


class TestRawPath:
    def test_spaces_become_underscores(self, tmp_storage):
        p = storage.raw_path("chirps", "San Miguel")
        assert p.name == "San_Miguel.parquet"
        assert p.parent.name == "chirps"

    def test_accents_stripped(self, tmp_storage):
        # Accented Spanish names must map to ASCII filenames deterministically.
        assert storage.raw_path("smap", "Usulután").name == "Usulutan.parquet"
        assert storage.raw_path("smap", "Morazán").name == "Morazan.parquet"
        assert storage.raw_path("smap", "La Unión").name == "La_Union.parquet"

    def test_under_configured_raw_dir(self, tmp_storage):
        p = storage.raw_path("imerg", "Sud")
        assert tmp_storage in p.parents


class TestUpsertRaw:
    def _rows(self, dates, values):
        return pd.DataFrame({
            "date": list(dates),
            "departamento": ["Morazan"] * len(dates),
            "value": list(values),
        })

    def test_round_trip(self, tmp_storage):
        df = self._rows([date(2020, 1, 1), date(2020, 1, 6)], [1.0, 2.0])
        storage.upsert_raw("chirps", "Morazan", df)
        back = storage.read_parquet(storage.raw_path("chirps", "Morazan"))
        assert len(back) == 2
        assert list(back["value"]) == [1.0, 2.0]

    def test_appends_new_dates(self, tmp_storage):
        storage.upsert_raw("chirps", "Morazan",
                           self._rows([date(2020, 1, 1)], [1.0]))
        storage.upsert_raw("chirps", "Morazan",
                           self._rows([date(2020, 1, 6)], [2.0]))
        back = storage.read_parquet(storage.raw_path("chirps", "Morazan"))
        assert len(back) == 2

    def test_duplicate_date_keeps_last_write(self, tmp_storage):
        storage.upsert_raw("chirps", "Morazan",
                           self._rows([date(2020, 1, 1)], [1.0]))
        storage.upsert_raw("chirps", "Morazan",
                           self._rows([date(2020, 1, 1)], [99.0]))
        back = storage.read_parquet(storage.raw_path("chirps", "Morazan"))
        assert len(back) == 1
        assert back.iloc[0]["value"] == 99.0

    def test_result_is_sorted_by_date(self, tmp_storage):
        out = storage.upsert_raw("chirps", "Morazan",
                                 self._rows([date(2020, 3, 1), date(2020, 1, 1),
                                             date(2020, 2, 1)], [3.0, 1.0, 2.0]))
        assert list(out["value"]) == [1.0, 2.0, 3.0]


class TestReadParquet:
    def test_missing_file_returns_empty_frame(self, tmp_storage):
        df = storage.read_parquet(tmp_storage / "does_not_exist.parquet")
        assert isinstance(df, pd.DataFrame)
        assert df.empty
