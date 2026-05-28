"""Plotly chart helpers. Climatology envelope (dual band) + current-year line
+ optional analog-year overlays + 'Today' marker + 'awaiting new data' band.

The envelope rendering is modeled on the dual-band Prophet chart in
FEWS_Price_data/dashboard/app.py (lines 744-778).
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go

ENVELOPE_OUTER_OBSERVED = "rgba(120, 144, 156, 0.18)"   # p05-p95 (past)
ENVELOPE_INNER_OBSERVED = "rgba(120, 144, 156, 0.32)"   # p25-p75 (past)
ENVELOPE_OUTER_FUTURE   = "rgba(120, 144, 156, 0.07)"   # p05-p95 (future, faded)
ENVELOPE_INNER_FUTURE   = "rgba(120, 144, 156, 0.14)"   # p25-p75 (future, faded)
ENVELOPE_MEDIAN_OBSERVED = "rgba(96, 125, 139, 0.65)"
ENVELOPE_MEDIAN_FUTURE   = "rgba(96, 125, 139, 0.30)"
CURRENT_YEAR = "#d32f2f"
FORECAST_DASH = "dash"
ANALOG_PALETTE = ["#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


def climatology_envelope_figure(
    title: str,
    value_label: str,
    climatology: pd.DataFrame,
    current: pd.DataFrame,
    primary_column: str,
    analogs: dict[int, pd.DataFrame] | None = None,
    today_: date | None = None,
    last_observation: date | None = None,
    is_forecast_col: str = "is_forecast",
) -> go.Figure:
    """climatology: cols [doy, p05, p10, p25, p50, p75, p90, p95]
    current: cols [date, primary_column, is_forecast]
    analogs: {year: DataFrame with [date, primary_column]}
    """
    fig = go.Figure()
    today_ = today_ or date.today()

    if not climatology.empty:
        clim = climatology.sort_values("doy")
        # Anchor climatology to the current year so x axis is the same date scale.
        year = today_.year
        clim_dates = [
            datetime(year, 1, 1) + pd.Timedelta(days=int(d) - 1) for d in clim["doy"]
        ]
        # Split observed (past, up to today) vs future for fading.
        observed_mask = [d.date() <= today_ for d in clim_dates]
        idx_split = sum(observed_mask)
        past_dates = clim_dates[:idx_split]
        future_dates = clim_dates[idx_split:]
        p05 = list(clim["p05"]); p25 = list(clim["p25"])
        p50 = list(clim["p50"])
        p75 = list(clim["p75"]); p95 = list(clim["p95"])

        # PAST (full opacity)
        if past_dates:
            fig.add_trace(go.Scatter(
                x=past_dates + past_dates[::-1],
                y=p95[:idx_split] + p05[:idx_split][::-1],
                fill="toself", fillcolor=ENVELOPE_OUTER_OBSERVED, line=dict(width=0),
                name="Typical range (5th–95th pct)", hoverinfo="skip", showlegend=True,
            ))
            fig.add_trace(go.Scatter(
                x=past_dates + past_dates[::-1],
                y=p75[:idx_split] + p25[:idx_split][::-1],
                fill="toself", fillcolor=ENVELOPE_INNER_OBSERVED, line=dict(width=0),
                name="Most common range (25th–75th pct)", hoverinfo="skip", showlegend=True,
            ))
            fig.add_trace(go.Scatter(
                x=past_dates, y=p50[:idx_split],
                line=dict(color=ENVELOPE_MEDIAN_OBSERVED, width=1, dash="dot"),
                name="Median (typical)", hoverinfo="skip",
            ))

        # FUTURE (faded — "expected typical range")
        if future_dates:
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=p95[idx_split:] + p05[idx_split:][::-1],
                fill="toself", fillcolor=ENVELOPE_OUTER_FUTURE, line=dict(width=0),
                name="Expected typical (forward)", hoverinfo="skip",
                showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=p75[idx_split:] + p25[idx_split:][::-1],
                fill="toself", fillcolor=ENVELOPE_INNER_FUTURE, line=dict(width=0),
                hoverinfo="skip", showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=future_dates, y=p50[idx_split:],
                line=dict(color=ENVELOPE_MEDIAN_FUTURE, width=1, dash="dot"),
                hoverinfo="skip", showlegend=False,
            ))

    if analogs:
        for i, (yr, df) in enumerate(sorted(analogs.items())):
            color = ANALOG_PALETTE[i % len(ANALOG_PALETTE)]
            d = df.copy()
            if d.empty:
                continue
            d["date"] = pd.to_datetime(d["date"])
            # Re-anchor to the current calendar year so the analog overlays
            # on the climatology x-axis.
            year = today_.year
            d["date"] = d["date"].apply(
                lambda ts, yr=year: ts.replace(year=yr) if (ts.month, ts.day) != (2, 29) else ts.replace(year=yr, day=28)
            )
            fig.add_trace(go.Scatter(
                x=d["date"], y=d[primary_column],
                line=dict(color=color, width=1.2),
                name=f"{yr}", opacity=0.85,
            ))

    if not current.empty:
        c = current.copy()
        c["date"] = pd.to_datetime(c["date"])
        observed = c[~c.get(is_forecast_col, pd.Series([False] * len(c))).fillna(False)]
        forecast = c[c.get(is_forecast_col, pd.Series([False] * len(c))).fillna(False)]
        if not observed.empty:
            fig.add_trace(go.Scatter(
                x=observed["date"], y=observed[primary_column],
                line=dict(color=CURRENT_YEAR, width=2.5),
                name="Current year",
            ))
        if not forecast.empty:
            fig.add_trace(go.Scatter(
                x=forecast["date"], y=forecast[primary_column],
                line=dict(color=CURRENT_YEAR, width=2, dash=FORECAST_DASH),
                name="Forecast (next 15 days)",
            ))

    # Today marker. Plotly needs a millisecond timestamp for datetime axes.
    today_ts = pd.Timestamp(today_).timestamp() * 1000
    fig.add_vline(
        x=today_ts,
        line=dict(color="#37474f", width=1, dash="dot"),
        annotation_text=f"Today · {today_.isoformat()}",
        annotation_position="top left",
        annotation=dict(
            yref="paper", y=0.97, xref="x", x=today_ts,
            xanchor="right", yanchor="top",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#37474f", borderwidth=1, borderpad=3,
            font=dict(size=10, color="#263238"),
        ),
    )

    # Awaiting-new-data band: last observation -> today
    if last_observation and last_observation < today_:
        fig.add_vrect(
            x0=pd.Timestamp(last_observation).timestamp() * 1000,
            x1=today_ts,
            fillcolor="rgba(176, 190, 197, 0.25)", line_width=0,
            annotation_text="Awaiting new data", annotation_position="top left",
        )

    fig.update_layout(
        title=title,
        yaxis_title=value_label,
        hovermode="x unified",
        height=420,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
