"""This season's record per department, for the Overview's "This season" table.

Two tiers, each dated by the first day it fired:

  Alert      the calibrated trigger (etl/triggers.py): SPI-3 and SMAP root-zone
             both past their thresholds in the silking window. Priority
             departments only, as calibrated.
  Confirmed  crop water use well below normal: the indicator named in
             ``config.CC['confirm_rule']`` (cropland WAPOR ETa) at or below its
             z threshold for N observations in a row inside the rule's window.

Once a department fires it stays listed until the season ends, so the table
answers "where has this season gone wrong so far", while the map and panels
show today's conditions. Between seasons the table recaps the last one.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from .. import config
from . import storage, triggers


@dataclass
class SeasonEntry:
    departamento: str
    alert_date: date | None = None
    confirmed_date: date | None = None  # start of the dekad that completed the run

    @property
    def confirmed_end(self) -> date | None:
        return dekad_end(self.confirmed_date) if self.confirmed_date else None

    @property
    def first_date(self) -> date:
        return min(d for d in (self.alert_date, self.confirmed_date) if d is not None)


@dataclass
class SeasonRecord:
    key: str            # i18n stem: season_<key>
    year: int
    start: date
    end: date
    active: bool        # False → the season has ended and this is a recap
    entries: list[SeasonEntry]


def dekad_end(d: date) -> date:
    """Last day of the dekad (1-10, 11-20, 21-end of month) that starts on or contains `d`."""
    if d.day <= 10:
        return d.replace(day=10)
    if d.day <= 20:
        return d.replace(day=20)
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def _doy_to_date(year: int, doy: int) -> date:
    return date(year, 1, 1) + timedelta(days=doy - 1)


def season_bounds(year: int, season: dict) -> tuple[date, date]:
    start_doy, end_doy = season["doy"]
    return _doy_to_date(year, start_doy), _doy_to_date(year, end_doy)


def first_confirmed_date(
    df: pd.DataFrame,
    year: int,
    window_doy: tuple[int, int],
    z_threshold: float,
    consecutive: int,
) -> date | None:
    """Date of the observation that completes the first run of `consecutive`
    observed values at or below `z_threshold` inside the window. A missing
    value breaks the run. For dekadal data this is the dekad's start date."""
    if df.empty or "value_anom_z" not in df.columns:
        return None
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    if "is_forecast" in d.columns:
        d = d[~d["is_forecast"].fillna(False).astype(bool)]
    doy = d["date"].dt.dayofyear
    d = d[(d["date"].dt.year == year) & (doy >= window_doy[0]) & (doy <= window_doy[1])]
    run = 0
    for row in d.sort_values("date").itertuples():
        z = row.value_anom_z
        run = run + 1 if pd.notna(z) and z <= z_threshold else 0
        if run >= consecutive:
            return row.date.date()
    return None


def confirmed_fires(year: int, rule: dict) -> dict[str, date]:
    out: dict[str, date] = {}
    indicator_dir = config.RAW_DIR / rule["indicator"]
    if not indicator_dir.exists():
        return out
    country = config.country_departments()
    for parquet in indicator_dir.glob("*.parquet"):
        df = storage.read_parquet(parquet)
        if df.empty:
            continue
        dep = df["departamento"].iloc[0]
        if country and dep not in country:
            continue
        fired = first_confirmed_date(
            df, year, tuple(rule["window_doy"]), rule["z_threshold"], rule["consecutive"]
        )
        if fired is not None:
            out[dep] = fired
    return out


def season_record(today: date | None = None) -> SeasonRecord | None:
    """The current season if it has started this year, otherwise last year's
    as a recap. None if the active country defines no season."""
    season = config.CC.get("season")
    if not season:
        return None
    today = today or config.today()
    start, end = season_bounds(today.year, season)
    year = today.year if today >= start else today.year - 1
    if year != today.year:
        start, end = season_bounds(year, season)
    active = start <= today <= end

    entries: dict[str, SeasonEntry] = {}
    for fire in triggers.evaluate_history():
        if fire.year == year and fire.first_date is not None and fire.first_date <= today:
            entries.setdefault(fire.departamento, SeasonEntry(fire.departamento)).alert_date = fire.first_date
    rule = config.CC.get("confirm_rule")
    if rule:
        for dep, fired in confirmed_fires(year, rule).items():
            # Not confirmed until the dekad that completes the run is over.
            if dekad_end(fired) <= today:
                entries.setdefault(dep, SeasonEntry(dep)).confirmed_date = fired

    ordered = sorted(entries.values(), key=lambda e: (e.first_date, e.departamento))
    return SeasonRecord(season["key"], year, start, end, active, ordered)
