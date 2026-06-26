"""Freshness classification and record round-trip."""

from __future__ import annotations

import json
from datetime import date

import pandas as pd

from el_nino.etl import freshness, synth


class TestClassify:
    TODAY = date(2020, 1, 31)

    def test_no_data(self):
        assert freshness.classify(None, 5, 9, self.TODAY) == "no_data"

    def test_fresh_within_threshold(self):
        assert freshness.classify(date(2020, 1, 30), 5, 9, self.TODAY) == "fresh"

    def test_fresh_at_exact_boundary(self):
        # lag == fresh_days is still fresh (<=)
        assert freshness.classify(date(2020, 1, 26), 5, 9, self.TODAY) == "fresh"

    def test_aging_between_thresholds(self):
        # lag 7 -> aging
        assert freshness.classify(date(2020, 1, 24), 5, 9, self.TODAY) == "aging"

    def test_aging_at_exact_boundary(self):
        # lag == aging_days is still aging (<=)
        assert freshness.classify(date(2020, 1, 22), 5, 9, self.TODAY) == "aging"

    def test_stale_beyond_aging(self):
        # lag 10 -> stale
        assert freshness.classify(date(2020, 1, 21), 5, 9, self.TODAY) == "stale"


class TestMakeRecord:
    def test_fields_and_status(self):
        rec = freshness.make_record(
            indicator="chirps",
            last_obs=date(2020, 1, 30),
            fresh_days=5, aging_days=9, cadence_days=3,
            today_=date(2020, 1, 31),
        )
        assert rec.indicator == "chirps"
        assert rec.last_observation_date == "2020-01-30"
        assert rec.status == "fresh"
        # expected_next_refresh = today + cadence
        assert rec.expected_next_refresh == "2020-02-03"

    def test_no_data_record(self):
        rec = freshness.make_record("smap", None, 5, 9, 3, today_=date(2020, 1, 1))
        assert rec.last_observation_date is None
        assert rec.status == "no_data"


class TestWriteReadAll:
    def test_round_trip(self, tmp_storage):
        recs = [
            freshness.make_record("chirps", date(2020, 1, 30), 5, 9, 3,
                                  today_=date(2020, 1, 31)),
            freshness.make_record("smap", None, 5, 9, 3, today_=date(2020, 1, 31)),
        ]
        freshness.write_all(recs)
        out = freshness.read_all()
        assert set(out) == {"chirps", "smap"}
        assert out["chirps"]["status"] == "fresh"
        # On-disk payload is keyed by indicator name.
        assert json.loads(tmp_storage.joinpath("freshness.json").read_text())["smap"]["status"] == "no_data"

    def test_read_all_missing_file_is_empty(self, tmp_storage):
        assert freshness.read_all() == {}


class TestPublishedChirpsFreshness:
    """End-to-end on the production writer the online dashboard reads.

    `synth.update_freshness` (run by the `finalize` ETL job, run_etl.py) is what
    writes each bucket's freshness.json. The GFS 15-day forecast tail must never
    leak into CHIRPS `last_observation_date` — otherwise the published date
    lands ~2 weeks in the future and the badge is permanently 'fresh', hiding a
    stalled feed. We assert the on-disk freshness.json, not the helper.
    """

    TODAY = date(2026, 6, 26)  # 22 days after the real last observation -> stale

    def _write_chirps(self, tmp_storage, rows):
        d = tmp_storage / "raw" / "chirps"
        d.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(d / "Testdep.parquet")

    def _published(self, tmp_storage):
        synth.update_freshness(self.TODAY)
        return json.loads(tmp_storage.joinpath("freshness.json").read_text())["chirps"]

    def test_forecast_tail_excluded_and_staleness_surfaced(self, tmp_storage):
        self._write_chirps(tmp_storage, [
            {"date": date(2026, 6, 4), "departamento": "Testdep", "is_forecast": False},
            {"date": date(2026, 6, 12), "departamento": "Testdep", "is_forecast": True},
            {"date": date(2026, 7, 10), "departamento": "Testdep", "is_forecast": True},
        ])
        chirps = self._published(tmp_storage)
        # The published date is the real observation, never the Jul-10 forecast.
        assert chirps["last_observation_date"] == "2026-06-04"
        # And with the tail gone, a 22-day-old feed correctly reads as stale
        # instead of being pinned to 'fresh' by the forecast.
        assert chirps["status"] == "stale"

    def test_all_forecast_publishes_no_data(self, tmp_storage):
        self._write_chirps(tmp_storage, [
            {"date": date(2026, 7, 10), "departamento": "Testdep", "is_forecast": True},
        ])
        chirps = self._published(tmp_storage)
        assert chirps["last_observation_date"] is None
        assert chirps["status"] == "no_data"
