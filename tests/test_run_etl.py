"""Cron-triggered ETL commands must leave anomaly z-scores (value_anom_z)
attached, so the drought-status badge and map reflect the freshly fetched rows.

The GEE/UCSB fetches are stubbed so the suite stays offline — the point is to
guard the post-fetch wiring (recompute SPI where needed, then attach_anomaly_z),
not the network calls.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import numpy as np
import pandas as pd

from el_nino.etl import refresh_check, run_etl, storage, synth
from el_nino.etl.indicators import INDICATORS
from el_nino.etl.indicators import chirps as chirps_mod

DEP = "Morazan"


def _seed_smap_baseline():
    """25 baseline-year DOY-1 observations (median 0.30) so the nonparametric
    index has a pool to rank a freshly-fetched row against."""
    rows = [{"date": date(2000 + i, 1, 1), "departamento": DEP,
             "rzsm_m3m3": v, "is_forecast": False}
            for i, v in enumerate(np.round(np.linspace(0.10, 0.50, 25), 4))]
    storage.write_parquet(pd.DataFrame(rows), storage.raw_path("smap", DEP))


class TestCmdFetchAttachesZ:
    """Full cron-fetch path with a stubbed GEE pull: the fetched row must come
    out with value_anom_z computed (nonparametrically) against the baseline."""

    def test_new_rows_get_z(self, tmp_storage, monkeypatch):
        _seed_smap_baseline()
        fake = pd.DataFrame({
            "date": [date(2026, 1, 1)],
            "departamento": [DEP],
            "rzsm_m3m3": [0.30],   # median of the baseline -> z ~ 0
            "is_forecast": [False],
        })
        monkeypatch.setattr(INDICATORS["smap"], "fetch", lambda self, s, e: fake)
        run_etl.cmd_fetch(SimpleNamespace(
            indicator="smap", start=date(2026, 1, 1), end=date(2026, 1, 1)))
        out = storage.read_parquet(storage.raw_path("smap", DEP))
        out["date"] = pd.to_datetime(out["date"])
        cur = out.sort_values("date").iloc[-1]
        assert not np.isnan(cur["value_anom_z"])
        assert abs(cur["value_anom_z"]) < 0.2   # median fetched value -> ~0

    def test_empty_fetch_skips_without_error(self, tmp_storage, monkeypatch):
        monkeypatch.setattr(INDICATORS["smap"], "fetch", lambda self, s, e: pd.DataFrame())
        # Should return early (no rows) and not raise.
        run_etl.cmd_fetch(SimpleNamespace(
            indicator="smap", start=date(2020, 1, 1), end=date(2020, 1, 3)))
        assert not storage.raw_path("smap", DEP).exists()


class TestCmdPrelimAttachesZ:
    def test_attaches_z_for_chirps(self, tmp_storage, monkeypatch):
        calls = []
        monkeypatch.setattr("el_nino.etl.chirps_prelim.run", lambda **k: 0)
        monkeypatch.setattr(synth, "attach_anomaly_z", lambda name: calls.append(name))
        monkeypatch.setattr(refresh_check, "_update_freshness", lambda: None)
        run_etl.cmd_prelim(SimpleNamespace(start=None, end=None))
        assert calls == ["chirps"]


class TestCmdForecastAttachesZ:
    def test_attaches_z_after_spi_recompute(self, tmp_storage, monkeypatch):
        order = []
        # Empty forecast -> purge-only branch, which still recomputes SPI + z.
        monkeypatch.setattr(chirps_mod.CHIRPS, "fetch_forecast",
                            lambda self, issuance=None: pd.DataFrame())
        monkeypatch.setattr(chirps_mod, "recompute_spi_for_all_parquets",
                            lambda: order.append("spi"))
        monkeypatch.setattr(synth, "attach_anomaly_z",
                            lambda name: order.append(("z", name)))
        monkeypatch.setattr(refresh_check, "_update_freshness", lambda: None)
        run_etl.cmd_forecast(SimpleNamespace(issuance=None))
        assert ("z", "chirps") in order
        # z-scores depend on SPI, so SPI must be recomputed first.
        assert order.index("spi") < order.index(("z", "chirps"))
