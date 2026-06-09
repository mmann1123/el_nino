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


class TestDropAllForecasts:
    """Guards the forecast-accumulation fix: forecast pentads sit on a rolling
    issuance-date grid that upsert_raw never overwrites, so they must be purged
    explicitly before a new issuance is written — otherwise stale/past and
    stacked forecasts pile up in the chirps parquets."""

    def _write(self, dep, observed_dates, forecast_dates):
        rows = []
        for d in observed_dates:
            rows.append({"date": d, "departamento": dep, "precip_pentad_mm": 1.0, "is_forecast": False})
        for d in forecast_dates:
            rows.append({"date": d, "departamento": dep, "precip_pentad_mm": 9.0, "is_forecast": True})
        storage.write_parquet(pd.DataFrame(rows), storage.raw_path("chirps", dep))

    def test_removes_forecasts_preserves_observed(self, tmp_storage):
        self._write("Morazan",
                    [date(2020, 1, 5), date(2020, 1, 10)],
                    [date(2020, 1, 13), date(2020, 1, 18), date(2020, 1, 23)])
        removed = storage.drop_all_forecasts("chirps")
        assert removed == 3
        back = storage.read_parquet(storage.raw_path("chirps", "Morazan"))
        assert len(back) == 2
        assert not back["is_forecast"].any()

    def test_returns_zero_when_no_forecasts(self, tmp_storage):
        self._write("Morazan", [date(2020, 1, 5)], [])
        assert storage.drop_all_forecasts("chirps") == 0
        assert len(storage.read_parquet(storage.raw_path("chirps", "Morazan"))) == 1

    def test_result_stays_sorted(self, tmp_storage):
        self._write("Morazan",
                    [date(2020, 3, 1), date(2020, 1, 1), date(2020, 2, 1)],
                    [date(2020, 6, 1)])
        storage.drop_all_forecasts("chirps")
        back = storage.read_parquet(storage.raw_path("chirps", "Morazan"))
        assert list(pd.to_datetime(back["date"])) == sorted(pd.to_datetime(back["date"]))

    def test_scoped_to_named_departamentos(self, tmp_storage):
        # Only the listed departamento is swept; others keep their forecasts.
        self._write("Morazan", [date(2020, 1, 5)], [date(2020, 1, 13)])
        self._write("Sonsonate", [date(2020, 1, 5)], [date(2020, 1, 13)])
        removed = storage.drop_all_forecasts("chirps", ["Morazan"])
        assert removed == 1
        assert not storage.read_parquet(storage.raw_path("chirps", "Morazan"))["is_forecast"].any()
        assert storage.read_parquet(storage.raw_path("chirps", "Sonsonate"))["is_forecast"].any()

    def test_missing_indicator_dir_is_noop(self, tmp_storage):
        assert storage.drop_all_forecasts("nonexistent") == 0

    def test_parquet_without_is_forecast_column_untouched(self, tmp_storage):
        df = pd.DataFrame({"date": [date(2020, 1, 5)], "departamento": ["Morazan"],
                           "precip_pentad_mm": [1.0]})
        storage.write_parquet(df, storage.raw_path("chirps", "Morazan"))
        assert storage.drop_all_forecasts("chirps") == 0
        assert len(storage.read_parquet(storage.raw_path("chirps", "Morazan"))) == 1
