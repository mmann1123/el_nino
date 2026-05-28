"""Single source of truth for per-indicator freshness. ETL writes this on
every run; dashboard reads it and drives all the badges, the 'Today' marker,
and the 'awaiting new data' shaded band off the same file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from .. import config

Status = Literal["fresh", "aging", "stale", "no_data"]


@dataclass
class FreshnessRecord:
    indicator: str
    last_observation_date: str | None  # ISO date or None if no data
    last_refresh_at: str                # ISO timestamp UTC
    expected_next_refresh: str          # ISO date
    fresh_threshold_days: int
    aging_threshold_days: int
    status: Status

    def to_dict(self) -> dict:
        return {
            "indicator": self.indicator,
            "last_observation_date": self.last_observation_date,
            "last_refresh_at": self.last_refresh_at,
            "expected_next_refresh": self.expected_next_refresh,
            "fresh_threshold_days": self.fresh_threshold_days,
            "aging_threshold_days": self.aging_threshold_days,
            "status": self.status,
        }


def classify(last_obs: date | None, fresh_days: int, aging_days: int, today_: date) -> Status:
    if last_obs is None:
        return "no_data"
    lag = (today_ - last_obs).days
    if lag <= fresh_days:
        return "fresh"
    if lag <= aging_days:
        return "aging"
    return "stale"


def make_record(
    indicator: str,
    last_obs: date | None,
    fresh_days: int,
    aging_days: int,
    cadence_days: int,
    today_: date | None = None,
) -> FreshnessRecord:
    today_ = today_ or config.today()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    expected_next = (today_ + timedelta(days=cadence_days)).isoformat()
    return FreshnessRecord(
        indicator=indicator,
        last_observation_date=last_obs.isoformat() if last_obs else None,
        last_refresh_at=now,
        expected_next_refresh=expected_next,
        fresh_threshold_days=fresh_days,
        aging_threshold_days=aging_days,
        status=classify(last_obs, fresh_days, aging_days, today_),
    )


def write_all(records: list[FreshnessRecord]) -> None:
    config.FRESHNESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {r.indicator: r.to_dict() for r in records}
    with config.FRESHNESS_PATH.open("w") as f:
        json.dump(payload, f, indent=2)


def read_all() -> dict[str, dict]:
    if not config.FRESHNESS_PATH.exists():
        return {}
    with config.FRESHNESS_PATH.open() as f:
        return json.load(f)
