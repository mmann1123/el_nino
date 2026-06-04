"""Date-window arithmetic and freshness-spec derivation in the Indicator base.

These back the chunked backfill (must tile [start, end] with no gaps or
overlaps) and the dashboard's freshness badges.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from el_nino.etl.indicators.base import (
    FreshnessSpec,
    _add_months,
    _days_in_month,
    _iter_windows,
)


class TestAddMonths:
    def test_simple(self):
        assert _add_months(date(2020, 1, 15), 1) == date(2020, 2, 15)

    def test_year_rollover(self):
        assert _add_months(date(2020, 11, 1), 3) == date(2021, 2, 1)

    def test_zero_months_is_identity(self):
        assert _add_months(date(2020, 6, 30), 0) == date(2020, 6, 30)

    def test_day_clamped_for_short_target_month(self):
        # Jan 31 + 1 month has no Feb 31 — clamp to the last valid day.
        assert _add_months(date(2021, 1, 31), 1) == date(2021, 2, 28)

    def test_day_clamped_into_leap_february(self):
        assert _add_months(date(2020, 1, 31), 1) == date(2020, 2, 29)

    def test_large_span(self):
        assert _add_months(date(2000, 5, 10), 24) == date(2002, 5, 10)


class TestDaysInMonth:
    @pytest.mark.parametrize("year,month,expected", [
        (2021, 1, 31),
        (2021, 2, 28),
        (2020, 2, 29),   # leap year
        (2021, 4, 30),
        (2021, 12, 31),  # December special-cased in the impl
    ])
    def test_lengths(self, year, month, expected):
        assert _days_in_month(year, month) == expected


class TestIterWindows:
    def test_tiles_without_gap_or_overlap(self):
        windows = list(_iter_windows(date(2020, 1, 1), date(2020, 12, 31), 3))
        # Every window's start is the day after the previous window's end.
        for (_, prev_end), (next_start, _) in zip(windows, windows[1:]):
            assert next_start == prev_end + timedelta(days=1)

    def test_covers_full_range(self):
        windows = list(_iter_windows(date(2020, 1, 1), date(2020, 12, 31), 3))
        assert windows[0][0] == date(2020, 1, 1)
        assert windows[-1][1] == date(2020, 12, 31)

    def test_final_window_clamped_to_end(self):
        # 5-month chunks over a 7-month span: second window must not run past end.
        windows = list(_iter_windows(date(2020, 1, 1), date(2020, 7, 15), 5))
        assert all(end <= date(2020, 7, 15) for _, end in windows)
        assert windows[-1][1] == date(2020, 7, 15)

    def test_single_window_when_chunk_exceeds_range(self):
        windows = list(_iter_windows(date(2020, 1, 1), date(2020, 2, 1), 60))
        assert windows == [(date(2020, 1, 1), date(2020, 2, 1))]


class TestFreshnessSpec:
    def test_from_cadence_3(self):
        spec = FreshnessSpec.from_cadence(3)
        assert spec.expected_cadence_days == 3
        assert spec.fresh_days == 5    # ceil(1.5 * 3) = ceil(4.5)
        assert spec.aging_days == 9    # 3 * 3

    def test_from_cadence_daily(self):
        spec = FreshnessSpec.from_cadence(1)
        assert spec.fresh_days == 2    # ceil(1.5)
        assert spec.aging_days == 3

    def test_fresh_never_exceeds_aging(self):
        for cadence in range(1, 31):
            spec = FreshnessSpec.from_cadence(cadence)
            assert spec.fresh_days <= spec.aging_days
