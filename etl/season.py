"""This season's record per department, for the Overview's "This season" panel.

Each country has back-to-back growing seasons (``config.CC['seasons']``).
Two tiers, each dated by the first day it fired:

  Alert      the season's calibrated trigger (etl/triggers.py): SPI and SMAP
             root-zone past their thresholds in the season's alert window, in
             any department, as calibrated.
  Confirmed  crop water use well below normal: the indicator named in the
             season's ``confirm_rule`` (cropland WAPOR ETa) at or below its z
             threshold for N observations in a row inside the rule's window.

Once a department fires it stays listed until its season ends, so the panel
answers "where has this season gone wrong so far", while the map and panels
show today's conditions. The next season starts clean; between seasons the
panel recaps the last one.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

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
    year: int           # planting year
    start: date
    end: date
    active: bool        # False → the season has ended and this is a recap
    entries: list[SeasonEntry]
    has_confirm: bool = False
    previous: SeasonRecord | None = None    # the season before, shown below; never merged


def dekad_end(d: date) -> date:
    """Last day of the dekad (1-10, 11-20, 21-end of month) that starts on or contains `d`."""
    if d.day <= 10:
        return d.replace(day=10)
    if d.day <= 20:
        return d.replace(day=20)
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def season_bounds(year: int, season: dict) -> tuple[date, date]:
    """Start and end of the season planted in `year`; an `end` that falls
    before `start` in the calendar is in the next year."""
    start = date(year, *season["start"])
    end = date(year, *season["end"])
    if end < start:
        end = date(year + 1, *season["end"])
    return start, end


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


@dataclass
class SeasonSpan:
    key: str
    year: int           # planting year
    start: date
    end: date
    active: bool        # False → the season has ended and this is a recap


def _spans(today: date) -> list[SeasonSpan]:
    """Every season instance planted last year or this year, oldest first."""
    out = []
    for year in (today.year - 1, today.year):
        for s in config.CC.get("seasons") or []:
            start, end = season_bounds(year, s)
            out.append(SeasonSpan(s["key"], year, start, end, start <= today <= end))
    return sorted(out, key=lambda sp: sp.start)


def current_span(today: date | None = None) -> SeasonSpan | None:
    """The season on screen: the one running today, otherwise the most recent
    one to end (a recap until the next starts). None if the active country
    defines no seasons. The alert banner and the season panel both key on
    this, so they reset on the same day."""
    today = today or config.today()
    spans = _spans(today)
    active = [sp for sp in spans if sp.active]
    if active:
        return active[0]
    ended = [sp for sp in spans if sp.end < today]
    return ended[-1] if ended else None


def closed_spans(today: date) -> list[SeasonSpan]:
    """Season instances planted last year or this year that ended before today."""
    return [sp for sp in _spans(today) if sp.end < today]


def previous_span(span: SeasonSpan) -> SeasonSpan | None:
    """The season instance that ended most recently before `span` started."""
    ended = [sp for sp in _spans(span.start) if sp.end < span.start]
    if not ended:
        return None
    prev = ended[-1]
    prev.active = False
    return prev


def live_entries(span: SeasonSpan, today: date, fires: list) -> tuple[list[SeasonEntry], bool]:
    """Departments that fired in `span` by `today`, computed from the data,
    and whether the season has a Confirmed tier."""
    entries: dict[str, SeasonEntry] = {}
    for fire in fires:
        if (fire.season == span.key and fire.year == span.year
                and fire.first_date is not None and fire.first_date <= today):
            entries.setdefault(fire.departamento, SeasonEntry(fire.departamento)).alert_date = fire.first_date
    rule = config.season_cfg(span.key).get("confirm_rule")
    if rule:
        for dep, fired in confirmed_fires(span.year, rule).items():
            # Not confirmed until the dekad that completes the run is over.
            if dekad_end(fired) <= today:
                entries.setdefault(dep, SeasonEntry(dep)).confirmed_date = fired
    ordered = sorted(entries.values(), key=lambda e: (e.first_date, e.departamento))
    return ordered, bool(rule)


def _entries(span: SeasonSpan, today: date, fires: list) -> tuple[list[SeasonEntry], bool]:
    """A closed season's frozen record if it has one, otherwise live."""
    from . import season_history  # imports this module
    if span.end < today and (frozen := season_history.frozen_entries(span)) is not None:
        return frozen
    return live_entries(span, today, fires)


def season_record(today: date | None = None) -> SeasonRecord | None:
    """The season on screen (see current_span) with every department that
    fired in it, plus the season before it as its own record. None if the
    active country defines no seasons."""
    today = today or config.today()
    span = current_span(today)
    if span is None:
        return None
    fires = triggers.evaluate_history()
    entries, has_confirm = _entries(span, today, fires)
    previous = None
    if (prev := previous_span(span)) is not None:
        prev_entries, prev_confirm = _entries(prev, today, fires)
        previous = SeasonRecord(prev.key, prev.year, prev.start, prev.end, False,
                                prev_entries, prev_confirm)
    return SeasonRecord(span.key, span.year, span.start, span.end, span.active,
                        entries, has_confirm, previous)
