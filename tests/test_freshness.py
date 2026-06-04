"""Freshness classification and record round-trip."""

from __future__ import annotations

import json
from datetime import date

from el_nino.etl import freshness


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
