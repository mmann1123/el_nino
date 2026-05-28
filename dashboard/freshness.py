"""Render freshness UI: persistent strip + per-indicator badge."""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from ..etl import freshness as freshness_io

BADGE_COLOR = {
    "fresh": ("🟢", "#2e7d32"),
    "aging": ("🟡", "#f9a825"),
    "stale": ("🔴", "#c62828"),
    "no_data": ("⚪", "#616161"),
}


def freshness_strip(today_: date) -> None:
    records = freshness_io.read_all()
    if not records:
        st.info("No refresh has run yet. Run `python -m el_nino.etl.run_etl synth` for a synthetic dataset, or `... fetch --indicator chirps` for real data.")
        return

    refreshed_at = max(
        (r.get("last_refresh_at", "") for r in records.values()),
        default="",
    )
    next_refresh = min(
        (r.get("expected_next_refresh", "") for r in records.values()),
        default="",
    )
    refreshed_human = refreshed_at[:16].replace("T", " ") if refreshed_at else "—"
    c1, c2, c3 = st.columns(3)
    c1.metric("Today", today_.isoformat())
    c2.metric("Data refreshed", refreshed_human)
    c3.metric("Next refresh", next_refresh or "—")


def indicator_badge(indicator: str, today_: date) -> str:
    records = freshness_io.read_all()
    rec = records.get(indicator)
    if not rec:
        emoji, _ = BADGE_COLOR["no_data"]
        return f"{emoji} No data"

    status = rec.get("status", "no_data")
    emoji, _ = BADGE_COLOR[status]
    last_obs = rec.get("last_observation_date")
    if not last_obs:
        return f"{emoji} No observations"
    lag = (today_ - date.fromisoformat(last_obs)).days
    suffix = "today" if lag == 0 else f"{lag} day{'s' if lag != 1 else ''} ago"
    return f"{emoji} Last observation: {last_obs} ({suffix})"


def last_observation_date(indicator: str) -> date | None:
    records = freshness_io.read_all()
    rec = records.get(indicator)
    if not rec or not rec.get("last_observation_date"):
        return None
    return date.fromisoformat(rec["last_observation_date"])
