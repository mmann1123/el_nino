"""Frozen record of each closed season, so later data revisions (CHIRPS-Prelim
replaced by final, a climatology refresh, a recalibration) can't rewrite what
the dashboard showed for a season that has ended.

`freeze_closed()` runs at the end of `run_etl finalize`. It stores every season
that closed between FREEZE_DELAY and FREEZE_LOOKBACK ago and isn't stored yet,
and never overwrites an entry. The delay lets late observations for the end
of the season arrive first (CHIRPS final ~3 weeks, WAPOR dekads up to ~2
months); until then a closed season is recapped live. Older seasons are not
backfilled: those were never shown live, and freezing reconstructions would
block recalibrating them. The open season is always computed live
(etl/season.py).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .. import config
from . import season, triggers

FREEZE_DELAY = timedelta(days=60)
FREEZE_LOOKBACK = timedelta(days=365)


def _path() -> Path:
    return config.STORAGE_ROOT / "season_history.json"


def _key(span: season.SeasonSpan) -> str:
    return f"{config.COUNTRY}/{span.key}/{span.year}"


def load() -> dict[str, dict]:
    path = _path()
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def frozen_entries(span: season.SeasonSpan) -> tuple[list[season.SeasonEntry], bool] | None:
    """The stored entries and has_confirm flag for a closed season, if frozen."""
    rec = load().get(_key(span))
    if rec is None:
        return None
    entries = [
        season.SeasonEntry(
            e["departamento"],
            date.fromisoformat(e["alert_date"]) if e["alert_date"] else None,
            date.fromisoformat(e["confirmed_date"]) if e["confirmed_date"] else None,
        )
        for e in rec["entries"]
    ]
    return entries, rec["has_confirm"]


def freeze_closed(today: date | None = None) -> list[str]:
    """Store each season that closed between FREEZE_DELAY and FREEZE_LOOKBACK
    ago and isn't stored yet. Returns the keys written."""
    today = today or config.today()
    stored = load()
    fires = triggers.evaluate_history()
    written = []
    for span in season.closed_spans(today):
        age = today - span.end
        if age < FREEZE_DELAY or age > FREEZE_LOOKBACK or _key(span) in stored:
            continue
        entries, has_confirm = season.live_entries(span, span.end, fires)
        trig = triggers.trigger_for(span.key)
        stored[_key(span)] = {
            "frozen_on": today.isoformat(),
            "trigger": trig.name if trig else None,
            "has_confirm": has_confirm,
            "entries": [
                {"departamento": e.departamento,
                 "alert_date": e.alert_date.isoformat() if e.alert_date else None,
                 "confirmed_date": e.confirmed_date.isoformat() if e.confirmed_date else None}
                for e in entries
            ],
        }
        written.append(_key(span))
    if written:
        _path().parent.mkdir(parents=True, exist_ok=True)
        with _path().open("w") as f:
            json.dump(stored, f, indent=2)
    return written


def clear() -> None:
    """Drop every frozen season for the active country (synthetic rebuilds)."""
    stored = {k: v for k, v in load().items() if not k.startswith(f"{config.COUNTRY}/")}
    if _path().exists():
        with _path().open("w") as f:
            json.dump(stored, f, indent=2)
