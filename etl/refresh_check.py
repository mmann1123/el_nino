"""Smart refresh: query GEE for each asset's latest-available date, compare to
local parquet's last observation, fetch the gap if behind.

Backs the dashboard's '🔄 Check for new data' button. Designed for cheap,
interactive use — uses one `aggregate_max` call per indicator (single-feature
getInfo) before deciding whether to do any heavy fetching.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

import pandas as pd

from .. import config
from . import freshness, gee, storage
from .indicators import INDICATORS
from .indicators.chirps import recompute_spi_for_all_parquets


@dataclass
class IndicatorRefreshResult:
    indicator: str
    asset_latest: date | None
    local_latest: date | None
    behind_days: int
    fetched_rows: int


def _asset_latest(indicator_name: str) -> date | None:
    """One cheap getInfo per indicator to discover the asset's latest frame."""
    import ee

    asset_paths = {
        "chirps": "UCSB-CHC/CHIRPS/V3/DAILY_SAT",
        "smap":   "NASA/SMAP/SPL4SMGP/008",
        "wapor":  "FAO/WAPOR/3/L1_AETI_D",
        "imerg":  "NASA/GPM_L3/IMERG_V07",
    }
    asset = asset_paths.get(indicator_name)
    if not asset:
        return None
    coll = ee.ImageCollection(asset)
    last_ms = coll.aggregate_max("system:time_start").getInfo()
    if not last_ms:
        return None
    return date.fromtimestamp(last_ms / 1000)


def _local_latest(indicator_name: str) -> date | None:
    """Latest *observed* (non-forecast) date across the active country's
    per-dep parquets. Filters out other countries' parquets when ES and HT
    share one local STORAGE_ROOT — otherwise a wetter/fresher ES record
    would mask an HT gap (or vice versa)."""
    d = config.RAW_DIR / indicator_name
    if not d.exists():
        return None
    country = config.country_departments()  # frozenset; empty = no filter
    latest: date | None = None
    for f in d.glob("*.parquet"):
        try:
            df = pd.read_parquet(f, columns=["date", "departamento", "is_forecast"])
        except Exception:
            try:
                df = pd.read_parquet(f, columns=["date", "departamento"])
                df["is_forecast"] = False
            except Exception:
                continue
        if df.empty:
            continue
        if country and df["departamento"].iloc[0] not in country:
            continue
        observed = df[~df["is_forecast"].fillna(False)]
        if observed.empty:
            continue
        d_max = pd.to_datetime(observed["date"]).max().date()
        if latest is None or d_max > latest:
            latest = d_max
    return latest


def run(verbose_logger: Callable[[str], None] = print) -> list[dict]:
    """Check + (optionally) fetch the gap for each indicator. Returns a list
    of result dicts so the caller can render a summary."""
    gee.init()
    results: list[dict] = []

    for name, cls in INDICATORS.items():
        try:
            asset_latest = _asset_latest(name)
        except Exception as e:
            verbose_logger(f"❌ {name}: could not query asset: {e}")
            results.append({
                "indicator": name, "asset_latest": None, "local_latest": None,
                "behind_days": -1, "fetched_rows": 0, "error": str(e),
            })
            continue

        local_latest = _local_latest(name)
        if asset_latest is None:
            verbose_logger(f"⚠️  {name}: asset reports no data")
            results.append({
                "indicator": name, "asset_latest": None, "local_latest": local_latest,
                "behind_days": 0, "fetched_rows": 0,
            })
            continue

        if local_latest is None:
            verbose_logger(f"📭 {name}: no local data — run a full backfill")
            results.append({
                "indicator": name, "asset_latest": asset_latest, "local_latest": None,
                "behind_days": (date.today() - asset_latest).days, "fetched_rows": 0,
            })
            continue

        behind = (asset_latest - local_latest).days
        if behind <= 0:
            verbose_logger(f"✅ {name}: up to date (local {local_latest}, asset {asset_latest})")
            results.append({
                "indicator": name, "asset_latest": asset_latest, "local_latest": local_latest,
                "behind_days": 0, "fetched_rows": 0,
            })
            continue

        # Fetch the gap. Pull a small overlap window so anything that arrived
        # late in the local store gets updated too.
        fetch_start = local_latest - timedelta(days=7)
        fetch_end = asset_latest
        verbose_logger(f"⏬ {name}: {behind} days behind — fetching {fetch_start} → {fetch_end}")
        try:
            ind = cls()
            df = ind.fetch(fetch_start, fetch_end)
            if df.empty:
                rows = 0
            else:
                for dep, group in df.groupby("departamento"):
                    storage.upsert_raw(name, dep, group.copy())
                rows = len(df)
            verbose_logger(f"   wrote {rows} rows")
            results.append({
                "indicator": name, "asset_latest": asset_latest, "local_latest": local_latest,
                "behind_days": behind, "fetched_rows": rows,
            })
        except Exception as e:
            verbose_logger(f"❌ {name}: fetch failed: {e}")
            results.append({
                "indicator": name, "asset_latest": asset_latest, "local_latest": local_latest,
                "behind_days": behind, "fetched_rows": 0, "error": str(e),
            })

    # Fill the CHIRPS V3 → today gap with UCSB CHIRPS-Prelim daily TIFFs.
    # GEE's V3 'sat' product runs ~28 days behind; without this step the
    # dashboard chart shows a multi-week dead zone before the GFS forecast.
    from . import chirps_prelim
    try:
        prelim_rows = chirps_prelim.run(verbose_logger=verbose_logger)
    except Exception as e:
        verbose_logger(f"❌ prelim: failed — {e}")
        prelim_rows = 0
    results.append({
        "indicator": "chirps-prelim",
        "asset_latest": None, "local_latest": None,
        "behind_days": 0, "fetched_rows": prelim_rows,
    })

    # Refresh the 15-day GFS rainfall forecast. New issuance every day, so
    # the button should always pull it — cheap enough (one GFS pull, ~30 rows).
    forecast_rows = _refresh_forecast(verbose_logger)
    results.append({
        "indicator": "chirps-forecast",
        "asset_latest": None, "local_latest": None,
        "behind_days": 0, "fetched_rows": forecast_rows,
    })

    # CHIRPS SPI needs a recompute whenever new observed OR forecast pentads
    # landed. prelim.run() already recomputes internally, so we only need to
    # re-trigger here if the GEE catch-up or the GFS forecast added rows.
    chirps_changed = any(
        r["indicator"] in ("chirps", "chirps-forecast") and r["fetched_rows"] > 0
        for r in results
    )
    if chirps_changed:
        verbose_logger("🔁 Recomputing CHIRPS SPI…")
        recompute_spi_for_all_parquets()

    # Update freshness.json from whatever's now on disk.
    _update_freshness()
    return results


def _refresh_forecast(verbose_logger: Callable[[str], None]) -> int:
    """Pull the latest GFS 15-day forecast and merge into CHIRPS parquets.
    Mirrors run_etl.cmd_forecast: a fresh issuance fully supersedes the prior
    one, so purge existing forecast rows before writing (they sit on a rolling
    date grid that upsert_raw never overwrites, otherwise they accumulate), and
    keep only future-dated pentads. Returns rows written (0 on failure)."""
    from .indicators.chirps import CHIRPS
    issuance = date.today() - timedelta(days=1)
    verbose_logger(f"🌧️  forecast: pulling GFS 15-day (issuance {issuance})")
    try:
        df = CHIRPS().fetch_forecast(issuance)
    except Exception as e:
        verbose_logger(f"❌ forecast: fetch failed: {e}")
        return 0

    country = config.country_departments() or None
    purged = storage.drop_all_forecasts("chirps", country)
    if purged:
        verbose_logger(f"   purged {purged} prior forecast row(s)")

    if df.empty:
        verbose_logger("   (no forecast data returned — stale forecasts cleared)")
        return 0
    today = config.today()
    df = df[pd.to_datetime(df["date"]).dt.date > today]
    for dep, group in df.groupby("departamento"):
        storage.upsert_raw("chirps", dep, group.copy())
    verbose_logger(f"   wrote {len(df)} forecast pentads across "
                   f"{df['departamento'].nunique()} departamentos")
    return int(len(df))


def _update_freshness() -> None:
    """Mirror the synth/finalize freshness writer using the post-refresh state."""
    today_ = config.today()
    records = []
    for name, cls in INDICATORS.items():
        last = _local_latest(name)
        records.append(freshness.make_record(
            indicator=name,
            last_obs=last,
            fresh_days=cls.freshness.fresh_days,
            aging_days=cls.freshness.aging_days,
            cadence_days=cls.freshness.expected_cadence_days,
            today_=today_,
        ))
    freshness.write_all(records)
