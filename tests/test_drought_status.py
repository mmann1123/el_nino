"""USDM-style classification of standardized anomalies."""

from __future__ import annotations

from el_nino.dashboard import drought_status as ds


class TestClassify:
    def test_none_is_pending(self):
        assert ds.classify(None).is_pending

    def test_nan_is_pending(self):
        assert ds.classify(float("nan")).is_pending

    def test_normal_band_is_symmetric_around_zero(self):
        # (-1.0, 1.0) exclusive maps to Normal.
        assert ds.classify(0.0).short == "N"
        assert ds.classify(0.9).short == "N"
        assert ds.classify(-0.99).short == "N"

    def test_dry_tiers(self):
        assert ds.classify(-1.0).short == "D0"   # boundary: not > -1.0
        assert ds.classify(-1.3).short == "D1"
        assert ds.classify(-1.6).short == "D2"
        assert ds.classify(-2.0).short == "D3"
        assert ds.classify(-2.5).short == "D4"
        assert ds.classify(-5.0).short == "D4"   # saturates at the bottom

    def test_wet_tiers(self):
        assert ds.classify(1.0).short == "W1"
        assert ds.classify(2.0).short == "W2"
        assert ds.classify(2.5).short == "W3"
        assert ds.classify(10.0).short == "W3"   # saturates at the top

    def test_every_category_carries_color_and_description(self):
        for z in (None, 0.0, 1.0, 2.0, 2.5, -1.0, -1.3, -1.6, -2.0, -2.5):
            cat = ds.classify(z)
            assert cat.color.startswith("#")
            assert cat.description
            assert cat.short


class TestPlainLanguage:
    def test_none_message(self):
        assert "Not enough data" in ds.plain_language(None)

    def test_wet_phrasing_at_zero(self):
        # z=0 -> 50th percentile, "wetter than 50%".
        msg = ds.plain_language(0.0)
        assert "wetter than 50%" in msg

    def test_dry_phrasing(self):
        msg = ds.plain_language(-2.0)
        assert "driest" in msg
        # norm.cdf(-2) ~ 2.3% -> rounds to 2%
        assert "2%" in msg
