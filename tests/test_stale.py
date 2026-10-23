"""Status displays show "No recent data" once an indicator's latest observation
is more than 3 update cycles old, instead of classifying an old reading."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from el_nino.dashboard import drought_status, freshness
from el_nino.etl.indicators import INDICATORS

TODAY = date(2026, 10, 23)


@pytest.mark.parametrize("name", sorted(INDICATORS))
def test_stale_only_beyond_three_cycles(monkeypatch, name):
    aging = INDICATORS[name].freshness.aging_days  # 3 × cadence
    for lag, expected in [(aging, False), (aging + 1, True)]:
        monkeypatch.setattr(freshness, "_last_obs_from_parquet",
                            lambda _ind, lag=lag: TODAY - timedelta(days=lag))
        assert freshness.is_stale(name, TODAY) is expected


def test_no_data_is_not_stale(monkeypatch):
    # No observations at all is "Computing…"/no-data, handled elsewhere.
    monkeypatch.setattr(freshness, "_last_obs_from_parquet", lambda _ind: None)
    assert freshness.is_stale("wapor", TODAY) is False


def test_live_wapor_case_is_stale(monkeypatch):
    # The live dashboard on 2026-10-23: WAPOR last observed 2026-09-11 (42 days,
    # cadence 10) was still labelled "Normal".
    monkeypatch.setattr(freshness, "_last_obs_from_parquet", lambda _ind: date(2026, 9, 11))
    assert freshness.is_stale("wapor", TODAY) is True


def test_stale_category_is_distinct_from_pending():
    assert drought_status.STALE.label == "No recent data"
    assert not drought_status.STALE.is_pending
