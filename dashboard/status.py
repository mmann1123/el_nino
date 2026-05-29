"""Helpers backing the "Current status" badge.

Two pieces:

  - `current_status_value(df, window_days, today)` — returns the mean
    `value_anom_z` over the most recent N OBSERVED days (skipping forecast
    rows entirely), plus the latest observed date. The mean smooths daily
    noise on SMAP/IMERG while leaving CHIRPS SPI-3 and dekadal WAPOR
    effectively unchanged (their native cadence already exceeds the window).

  - `lag_phrase(last_obs, today)` — renders "today" / "yesterday" /
    "N days ago" for the badge subtitle.
"""

from __future__ import annotations

from datetime import date

import pandas as pd


def current_status_value(
    ind_df: pd.DataFrame,
    window_days: int,
    today: date,
) -> tuple[float | None, date | None]:
    """Mean `value_anom_z` of the last `window_days` of observed rows.

    Returns (z, latest_observed_date). z is None when there's no usable
    observed data, and latest_observed_date is None in that case too.

    Forecast rows (`is_forecast=True`) are excluded — they never count toward
    the "current status" assessment.
    """
    if ind_df is None or ind_df.empty:
        return (None, None)
    if "value_anom_z" not in ind_df.columns:
        return (None, None)

    df = ind_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    if "is_forecast" in df.columns:
        df = df[~df["is_forecast"].fillna(False)]
    df = df.dropna(subset=["value_anom_z"])
    if df.empty:
        return (None, None)

    latest_obs = df["date"].max().date()
    window_start = pd.Timestamp(latest_obs) - pd.Timedelta(days=window_days - 1)
    window = df[df["date"] >= window_start]
    if window.empty:
        return (None, latest_obs)
    return (float(window["value_anom_z"].mean()), latest_obs)


def lag_phrase(last_obs: date | None, today: date) -> str:
    """Subtitle string for the status badge: 'today' / 'yesterday' /
    'N days ago'. Used in [el_nino/dashboard/app.py]."""
    if last_obs is None:
        return "No observations yet"
    lag = (today - last_obs).days
    if lag <= 0:
        return "Based on today's observations"
    if lag == 1:
        return "Based on yesterday's observations"
    return f"Based on observations from {lag} days ago"
