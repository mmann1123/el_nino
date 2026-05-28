"""CHIRPS v3 daily precipitation + SPI-1/3/6.

CHIRPS3 daily 'sat' product (UCSB-CHC/CHIRPS/V3/DAILY_SAT) is preliminary.
For climatology backfill from 1981, fall back to UCSB-CHG/CHIRPS/DAILY (v2),
which the dashboard treats as historically equivalent for SPI fitting.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import gamma, norm

from .base import FreshnessSpec, Indicator


class CHIRPS(Indicator):
    name = "chirps"
    primary_column = "spi_3"
    value_columns = ["precip_pentad_mm", "spi_1", "spi_3", "spi_6"]
    freshness = FreshnessSpec(fresh_days=3, aging_days=7, expected_cadence_days=3)
    has_forecast = True
    # Pentad aggregation keeps feature count low (14 × 73 ≈ 1022/yr), so big chunks work.
    default_chunk_months = 24
    min_chunk_months = 3

    DAILY_V3 = "UCSB-CHC/CHIRPS/V3/DAILY_SAT"
    DAILY_V2 = "UCSB-CHG/CHIRPS/DAILY"

    def fetch(self, start: date, end: date) -> pd.DataFrame:
        """Return CHIRPS pentad-summed precip per departamento, aggregated server-side."""
        import ee
        from .. import gee
        gee.init()
        asset = self._daily_collection_for(start)
        daily = ee.ImageCollection(asset).select("precipitation")

        # Clamp the request to the asset's actual coverage, otherwise empty
        # date ranges produce no-band images and break .rename().
        try:
            last_avail_ms = daily.aggregate_max("system:time_start").getInfo()
            if last_avail_ms is not None:
                last_avail = date.fromtimestamp(last_avail_ms / 1000)
                if end > last_avail:
                    end = last_avail
        except Exception:
            pass
        if end < start:
            return pd.DataFrame()

        # Build pentad image list server-side. Pentads N=1..73 end at DOY 5N
        # (pentad 73 captures DOY 361-365 plus the leap-year remainder).
        from datetime import timedelta as _td
        pentad_imgs = []
        cur = start
        while cur <= end:
            # Snap to the pentad-of-year boundary: pentads start at DOY 1, 6, 11, ...
            doy = cur.timetuple().tm_yday
            pent_idx = (doy - 1) // 5  # 0..72
            pent_start_doy = pent_idx * 5 + 1
            pent_end_doy = min(pent_start_doy + 4, 366 if _is_leap(cur.year) else 365)
            pent_start = date(cur.year, 1, 1) + _td(days=pent_start_doy - 1)
            pent_end = date(cur.year, 1, 1) + _td(days=pent_end_doy - 1)

            window_end = min(pent_end, end)
            ee_start = ee.Date(pent_start.isoformat())
            ee_end = ee.Date(window_end.isoformat()).advance(1, "day")
            summed = daily.filterDate(ee_start, ee_end).sum().rename("precip_pentad_mm")
            summed = summed.set("system:time_start", ee.Date(window_end.isoformat()).millis())
            summed = summed.set("pentad_start", pent_start.isoformat())
            summed = summed.set("pentad_end", window_end.isoformat())
            pentad_imgs.append(summed)

            cur = pent_end + _td(days=1)

        if not pentad_imgs:
            return pd.DataFrame()

        coll = ee.ImageCollection.fromImages(pentad_imgs)
        df = self.reduce_imagecollection_by_departamento(coll, band="precip_pentad_mm")
        if df.empty:
            return df
        df = df.rename(columns={"value": "precip_pentad_mm"})
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["pentad"] = ((df["date"].dt.dayofyear - 1) // 5) + 1
        df.loc[df["pentad"] > 73, "pentad"] = 73
        df["date"] = df["date"].dt.date
        df["is_forecast"] = False
        # SPI columns are populated post-backfill by recompute_spi_for_all_parquets()
        for col in ("spi_1", "spi_3", "spi_6"):
            df[col] = pd.NA
        return df

    def _daily_collection_for(self, start: date) -> str:
        # Use v2 for the climatology baseline; v3 only for the recent (post-2023) window.
        return self.DAILY_V3 if start >= date(2023, 12, 1) else self.DAILY_V2

    # ---- 15-day rainfall forecast (NOAA GFS0P25) ----
    #
    # CHIRPS-GEFS (the CHIRPS-bias-corrected forecast) isn't in the public GEE
    # catalog — it requires Climate Engine asset sharing we don't have. So we
    # use raw NOAA GFS 0.25° precipitation_rate instead. GFS over Central
    # America is documented to over-predict by ~40 mm (per el_nino/notes.md),
    # so values shown here are "uncalibrated forecast" — caveat displayed in
    # the dashboard.
    GFS_ASSET = "NOAA/GFS0P25"

    def fetch_forecast(self, issuance_date: date | None = None) -> pd.DataFrame:
        """Pull the latest GFS issuance and aggregate to 3 forward pentads (15 days).

        Returns one row per (pentad_end_date, departamento) with
        precip_pentad_mm and is_forecast=True. SPI columns are left null and
        get populated by `recompute_spi_for_all_parquets()` after merge.
        """
        import ee
        from datetime import timedelta as _td
        from .. import gee as _gee
        _gee.init()

        # Pick the most recent issuance that has the full 360-hour horizon.
        target = issuance_date or (date.today() - _td(days=1))
        coll = (
            ee.ImageCollection(self.GFS_ASSET)
            .filterDate(target.isoformat(), (target + _td(days=2)).isoformat())
            .filter(ee.Filter.lte("forecast_hours", 360))
            .filter(ee.Filter.gt("forecast_hours", 0))
        )
        n = coll.size().getInfo()
        if n == 0:
            return pd.DataFrame()

        # Pick the latest issuance (max creation_time) and restrict to it.
        latest_creation = coll.aggregate_max("creation_time").getInfo()
        coll = coll.filter(ee.Filter.eq("creation_time", latest_creation))

        # precipitation_rate is kg/m²/s = mm/s. GFS time-step is 1 h up to
        # forecast_hours=120, then 3 h. Multiply each image's rate by its step
        # length to get mm accumulated over that step.
        def to_mm_per_step(img):
            hours = ee.Number(img.get("forecast_hours"))
            step_seconds = ee.Algorithms.If(hours.lte(120), 3600, 3 * 3600)
            return (
                img.select("precipitation_rate")
                .multiply(ee.Number(step_seconds))
                .rename("precip_mm_step")
                .copyProperties(img, ["system:time_start", "forecast_hours"])
            )

        mm_coll = coll.map(to_mm_per_step)

        # Three forward 5-day windows: [0-120h], [120-240h], [240-360h]
        pentad_imgs = []
        for i in range(3):
            h_start = i * 120
            h_end = (i + 1) * 120
            pent_subset = mm_coll.filter(ee.Filter.And(
                ee.Filter.gt("forecast_hours", h_start),
                ee.Filter.lte("forecast_hours", h_end),
            ))
            pent_total = pent_subset.sum().rename("precip_pentad_mm")
            pent_end = target + _td(days=(i + 1) * 5)
            pent_total = pent_total.set("system:time_start", ee.Date(pent_end.isoformat()).millis())
            pentad_imgs.append(pent_total)

        fc_coll = ee.ImageCollection.fromImages(pentad_imgs)
        df = self.reduce_imagecollection_by_departamento(fc_coll, band="precip_pentad_mm")
        if df.empty:
            return df
        df = df.rename(columns={"value": "precip_pentad_mm"})
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["pentad"] = ((df["date"].dt.dayofyear - 1) // 5) + 1
        df.loc[df["pentad"] > 73, "pentad"] = 73
        df["date"] = df["date"].dt.date
        df["is_forecast"] = True
        for col in ("spi_1", "spi_3", "spi_6"):
            df[col] = pd.NA  # filled in by recompute_spi_for_all_parquets
        return df


def recompute_spi_for_all_parquets() -> None:
    """Read each per-departamento CHIRPS parquet, recompute SPI-1/3/6 across the
    full history, write back. Call after a backfill finishes so SPI uses the
    full record rather than per-chunk windows.
    """
    from .. import storage
    from ... import config
    indicator_dir = config.RAW_DIR / "chirps"
    if not indicator_dir.exists():
        return
    for parquet in sorted(indicator_dir.glob("*.parquet")):
        df = storage.read_parquet(parquet)
        if df.empty or "precip_pentad_mm" not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["pentad"] = ((df["date"].dt.dayofyear - 1) // 5) + 1
        df.loc[df["pentad"] > 73, "pentad"] = 73
        df = df.sort_values("date").reset_index(drop=True)
        with_spi = attach_spi(df)
        with_spi["date"] = with_spi["date"].dt.date
        storage.write_parquet(with_spi, parquet)


def aggregate_to_pentad(daily: pd.DataFrame) -> pd.DataFrame:
    """Sum daily precip into pentads (5-day blocks of the calendar year)."""
    if daily.empty:
        return daily
    d = daily.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["year"] = d["date"].dt.year
    d["doy"] = d["date"].dt.dayofyear
    d["pentad"] = ((d["doy"] - 1) // 5) + 1
    d.loc[d["pentad"] > 73, "pentad"] = 73  # collapse leap-year remainder
    g = d.groupby(["departamento", "year", "pentad"], as_index=False).agg(
        precip_pentad_mm=("precip_mm", "sum"),
    )
    g["date"] = g.apply(_pentad_end_date, axis=1)
    return g[["date", "departamento", "year", "pentad", "precip_pentad_mm"]]


def _pentad_end_date(row) -> date:
    # Pentad N ends on DOY 5*N (clipped at 365 for non-leap, 366 for leap years).
    last_doy = min(int(row["pentad"]) * 5, 366 if _is_leap(int(row["year"])) else 365)
    return pd.Timestamp(year=int(row["year"]), month=1, day=1).to_pydatetime().date() \
        .replace(day=1, month=1).fromordinal(
            pd.Timestamp(year=int(row["year"]), month=1, day=1).toordinal() + last_doy - 1
        )


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def compute_spi(pentads: pd.DataFrame, scale_pentads: int) -> pd.Series:
    """SPI at a given rolling-pentad scale (e.g., 6 pentads ≈ 1 month, 18 ≈ 3 months).

    For each (departamento, pentad-of-year), fit a gamma distribution to the
    rolling-sum historical record, then transform new accumulations through
    gamma CDF → inverse normal CDF.

    Returns a Series aligned to the input DataFrame index. NaN where the
    rolling window is incomplete or the gamma fit failed.
    """
    out = np.full(len(pentads), np.nan)
    if pentads.empty:
        return pd.Series(out, index=pentads.index)

    df = pentads.sort_values(["departamento", "date"]).copy()
    df["rolling_sum"] = (
        df.groupby("departamento")["precip_pentad_mm"]
        .transform(lambda s: s.rolling(scale_pentads, min_periods=scale_pentads).sum())
    )

    for (dep, pent), group in df.groupby(["departamento", "pentad"], sort=False):
        sums = group["rolling_sum"].dropna().values
        if len(sums) < 10:
            continue
        non_zero = sums[sums > 0]
        if len(non_zero) < 8:
            continue
        try:
            shape, loc, scale = gamma.fit(non_zero, floc=0)
        except Exception:
            continue
        zero_prob = (sums == 0).sum() / len(sums)
        for idx, val in zip(group.index, group["rolling_sum"]):
            if np.isnan(val):
                continue
            if val == 0:
                p = zero_prob / 2
            else:
                p = zero_prob + (1 - zero_prob) * gamma.cdf(val, shape, loc=loc, scale=scale)
            p = min(max(p, 1e-6), 1 - 1e-6)
            out[idx] = norm.ppf(p)

    return pd.Series(out, index=df.index).reindex(pentads.index)


def attach_spi(pentads: pd.DataFrame) -> pd.DataFrame:
    """Attach SPI-1 (6 pentads), SPI-3 (18), SPI-6 (36)."""
    p = pentads.copy()
    p["spi_1"] = compute_spi(p, scale_pentads=6)
    p["spi_3"] = compute_spi(p, scale_pentads=18)
    p["spi_6"] = compute_spi(p, scale_pentads=36)
    return p
