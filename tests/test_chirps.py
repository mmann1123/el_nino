"""Pentad aggregation completeness guard — the fix for CHIRPS-Prelim freezing
partial trailing pentads (which under-sum and push SPI-3 to false drought).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from el_nino.etl.indicators.chirps import aggregate_to_pentad, _pentad_expected_days


def _daily(days_precip, dep="Morazan"):
    return pd.DataFrame({
        "date": [d for d, _ in days_precip],
        "departamento": [dep] * len(days_precip),
        "precip_mm": [p for _, p in days_precip],
    })


class TestAggregateToPentadCompleteness:
    # Pentad 1 = DOY 1-5 (Jan 1-5); pentad 2 = DOY 6-10 (Jan 6-10).
    FULL_P1 = [(date(2026, 1, d), float(d)) for d in range(1, 6)]      # 5 days -> complete
    PARTIAL_P2 = [(date(2026, 1, 6), 10.0), (date(2026, 1, 7), 20.0)]  # 2 of 5 days

    def test_complete_pentad_emitted_with_full_sum(self):
        out = aggregate_to_pentad(_daily(self.FULL_P1))
        assert len(out) == 1
        assert out.iloc[0]["precip_pentad_mm"] == 15.0          # 1+2+3+4+5
        assert out.iloc[0]["date"] == date(2026, 1, 5)          # pentad-end

    def test_partial_trailing_pentad_dropped(self):
        out = aggregate_to_pentad(_daily(self.FULL_P1 + self.PARTIAL_P2))
        # Only the complete pentad survives; the 2-day partial is held back.
        assert list(out["pentad"]) == [1]
        assert date(2026, 1, 10) not in set(out["date"])

    def test_require_complete_false_keeps_partial(self):
        out = aggregate_to_pentad(_daily(self.FULL_P1 + self.PARTIAL_P2), require_complete=False)
        assert set(out["pentad"]) == {1, 2}
        p2 = out[out["pentad"] == 2].iloc[0]
        assert p2["precip_pentad_mm"] == 30.0                   # 10+20 (only days present)

    def test_four_of_five_days_is_incomplete(self):
        four = [(date(2026, 1, d), 1.0) for d in (1, 2, 3, 4)]  # missing Jan 5
        assert aggregate_to_pentad(_daily(four)).empty

    def test_empty_input(self):
        assert aggregate_to_pentad(pd.DataFrame()).empty


class TestPentadExpectedDays:
    def test_normal_pentads_expect_five(self):
        assert _pentad_expected_days(1, 2026) == 5
        assert _pentad_expected_days(40, 2026) == 5

    def test_last_pentad_absorbs_year_end(self):
        assert _pentad_expected_days(73, 2025) == 5   # common year (361-365)
        assert _pentad_expected_days(73, 2024) == 6   # leap year (361-366)
