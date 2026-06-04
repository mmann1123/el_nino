"""Shared test fixtures.

This package is imported as `el_nino.*` from the repo's *parent* directory
(see CLAUDE.md). Tests do the same: insert the parent on sys.path so
`import el_nino...` resolves no matter where pytest is invoked from.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PARENT = Path(__file__).resolve().parents[2]  # the dir that contains el_nino/
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))


@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    """Redirect every config storage path to an isolated temp dir.

    config exposes RAW_DIR / CLIMATOLOGY_DIR / ... as module-level Paths that
    the ETL/dashboard code reads at call time, so monkeypatching the attributes
    fully isolates a test from the developer's real ./data directory.

    Returns the temp root (a Path) with raw/, climatology/, enso/ created.
    """
    from el_nino import config

    root = tmp_path / "storage"
    raw = root / "raw"
    clim = root / "climatology"
    enso = root / "enso"
    for d in (raw, clim, enso):
        d.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config, "STORAGE_ROOT", root)
    monkeypatch.setattr(config, "RAW_DIR", raw)
    monkeypatch.setattr(config, "CLIMATOLOGY_DIR", clim)
    monkeypatch.setattr(config, "ENSO_DIR", enso)
    monkeypatch.setattr(config, "FRESHNESS_PATH", root / "freshness.json")
    monkeypatch.setattr(config, "DUCKDB_PATH", root / "dashboard.duckdb")
    return root
