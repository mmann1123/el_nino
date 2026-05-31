"""Cross-user, 12-hour rate limit for the 'Check for new data' button.

State lives in a single JSON file at `STORAGE_ROOT/last_refresh.json`, so all
Streamlit sessions and replicas hitting the same Cloud Run service (which
mounts the same per-country GCS bucket) see the same lock state. Each country
gets its own lock because each deployment has its own STORAGE_ROOT.

Concurrency: gcsfuse doesn't guarantee atomic locking, so two simultaneous
clicks could both pass the check. Worst case is one duplicate refresh per
window — acceptable since the underlying GEE/UCSB pulls are idempotent.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import config

REFRESH_INTERVAL = timedelta(hours=12)
LOCK_FILE: Path = config.STORAGE_ROOT / "last_refresh.json"


def _read_last() -> datetime | None:
    if not LOCK_FILE.exists():
        return None
    try:
        data = json.loads(LOCK_FILE.read_text())
        ts = data.get("timestamp")
        if not ts:
            return None
        return datetime.fromisoformat(ts)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def check_allowed() -> tuple[bool, datetime | None, datetime | None]:
    """Return (allowed, last_refresh_at, next_available_at).

    - allowed: True if no refresh in the last 12h
    - last_refresh_at: timestamp of the previous successful refresh, or None
      if there's never been one
    - next_available_at: when the next refresh is allowed, or None if allowed
      right now
    """
    last = _read_last()
    if last is None:
        return True, None, None
    now = datetime.now(timezone.utc)
    next_at = last + REFRESH_INTERVAL
    return (now >= next_at), last, next_at


def record_refresh() -> None:
    """Persist the current UTC time as the last-refresh marker. Call AFTER a
    successful refresh, not before — so a failed refresh doesn't burn the
    window's slot for everyone."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }))


def format_relative(ts: datetime, now: datetime | None = None) -> str:
    """Compact 'N hours ago' / 'in N hours' helper for the caption."""
    now = now or datetime.now(timezone.utc)
    delta = ts - now
    seconds = int(delta.total_seconds())
    future = seconds > 0
    seconds = abs(seconds)
    if seconds < 60:
        unit = f"{seconds}s"
    elif seconds < 3600:
        unit = f"{seconds // 60}m"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        unit = f"{h}h {m}m" if m else f"{h}h"
    return f"in {unit}" if future else f"{unit} ago"
