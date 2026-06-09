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

from el_nino.etl import climatology, refresh_check, run_etl, storage, synth
from el_nino.etl.indicators import INDICATORS
from el_nino.etl.indicators import chirps as chirps_mod

DEP = "Morazan"


def _smap_climatology():
    climatology.save("smap", pd.DataFrame({
        "departamento": [DEP] * 3,
        "value_column": ["rzsm_m3m3"] * 3,
        "doy": [1, 2, 3],
        "mu": [0.30] * 3,
        "sigma": [0.10] * 3,
    }))


class TestCmdFetchAttachesZ:
    """Full cron-fetch path with a stubbed GEE pull: the written rows must come
    out with value_anom_z computed from the climatology."""

    def test_new_rows_get_z(self, tmp_storage, monkeypatch):
        _smap_climatology()
        fake = pd.DataFrame({
            "date": [date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3)],
            "departamento": [DEP] * 3,
            "rzsm_m3m3": [0.30, 0.40, 0.20],   # -> z = 0, +1, -1
            "is_forecast": [False] * 3,
        })
        monkeypatch.setattr(INDICATORS["smap"], "fetch", lambda self, s, e: fake)
        run_etl.cmd_fetch(SimpleNamespace(
            indicator="smap", start=date(2020, 1, 1), end=date(2020, 1, 3)))
        out = storage.read_parquet(storage.raw_path("smap", DEP)).sort_values("date")
        assert "value_anom_z" in out.columns
        assert np.allclose(out["value_anom_z"].to_numpy(), [0.0, 1.0, -1.0])

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
