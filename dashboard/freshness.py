"""Render freshness UI: persistent strip + per-indicator badge."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from .. import config
from ..etl import freshness as freshness_io
from ..etl.indicators import INDICATORS

BADGE_COLOR = {
    "fresh": ("🟢", "#2e7d32"),
    "aging": ("🟡", "#f9a825"),
    "stale": ("🔴", "#c62828"),
    "no_data": ("⚪", "#616161"),
}


def freshness_strip(today_: date) -> None:
    """Always renders the Today metric; fills the rest from freshness.json if
    present, otherwise from per-indicator parquet tails as a fallback."""
    records = freshness_io.read_all()

    if records:
        refreshed_at = max(
            (r.get("last_refresh_at", "") for r in records.values()),
            default="",
        )
        next_refresh = min(
            (r.get("expected_next_refresh", "") for r in records.values() if r.get("expected_next_refresh")),
            default="",
        )
        refreshed_human = refreshed_at[:16].replace("T", " ") if refreshed_at else "—"
    else:
        refreshed_human = "—"
        next_refresh = "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("Today", today_.isoformat())
    c2.metric("Data refreshed", refreshed_human)
    c3.metric("Next refresh", next_refresh or "—")

    if not records:
        st.caption(
            "Freshness summary not yet computed. Run "
            "`python -m el_nino.etl.run_etl finalize` once backfills complete."
        )


def indicator_badge(indicator: str, today_: date) -> str:
    """Compact lag indicator next to a chart title.

    Reads freshness.json when present; otherwise reads the parquet directly to
    report a last-observation lag even before `finalize` has run.
    """
    records = freshness_io.read_all()
    rec = records.get(indicator)

    last_obs: date | None = None
    status: str = "no_data"

    if rec:
        status = rec.get("status", "no_data")
        last_obs_str = rec.get("last_observation_date")
        if last_obs_str:
            last_obs = date.fromisoformat(last_obs_str)
    else:
        # Fallback: read the parquets directly.
        last_obs = _last_obs_from_parquet(indicator)
        if last_obs is not None:
            ind_cls = INDICATORS.get(indicator)
            if ind_cls:
                lag = (today_ - last_obs).days
                if lag <= ind_cls.freshness.fresh_days:
                    status = "fresh"
                elif lag <= ind_cls.freshness.aging_days:
                    status = "aging"
                else:
                    status = "stale"

    emoji, _ = BADGE_COLOR.get(status, BADGE_COLOR["no_data"])
    if last_obs is None:
        return f"{emoji} No observations yet"
    lag = (today_ - last_obs).days
    suffix = "today" if lag == 0 else f"{lag} day{'s' if lag != 1 else ''} ago"
    return f"{emoji} Last observation: {last_obs} ({suffix})"


def last_observation_date(indicator: str) -> date | None:
    records = freshness_io.read_all()
    rec = records.get(indicator)
    if rec and rec.get("last_observation_date"):
        return date.fromisoformat(rec["last_observation_date"])
    # Fallback to parquet-derived
    return _last_obs_from_parquet(indicator)


@st.cache_data(ttl=300)
def _last_obs_from_parquet(indicator: str) -> date | None:
    d = config.RAW_DIR / indicator
    if not d.exists():
        return None
    latest: date | None = None
    for f in d.glob("*.parquet"):
        try:
            df = pd.read_parquet(f, columns=["date"])
        except Exception:
            continue
        if df.empty:
            continue
        d_max = pd.to_datetime(df["date"]).max().date()
        if latest is None or d_max > latest:
            latest = d_max
    return latest
