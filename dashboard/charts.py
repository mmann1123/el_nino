"""Plotly chart helpers. Climatology envelope (dual band) + current-year line
+ optional analog-year overlays + 'Today' marker + 'awaiting new data' band.

The envelope rendering is modeled on the dual-band Prophet chart in
FEWS_Price_data/dashboard/app.py (lines 744-778).
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go

# Shared Plotly modebar config used by every chart. Strips the default ~8-button
# toolbar down to just download (camera) — pan/zoom/reset are still available
# via direct gestures (drag-to-pan, double-click reset).
CHART_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d",
        "zoomOut2d", "autoScale2d", "resetScale2d",
        "hoverClosestCartesian", "hoverCompareCartesian", "toggleSpikelines",
    ],
    "displayModeBar": "hover",  # only appears on hover, hidden by default
}


def smoothing_diagnostic_figure(
    raw_clim: pd.DataFrame,
    smoothed_clim: pd.DataFrame,
    value_label: str,
) -> go.Figure:
    """Side-by-side per-DOY p05/p95 envelope: raw (per-DOY only) vs windowed.
    Used in the 'How smooth is the envelope?' expander so users can see
    exactly what the DOY window buys them.

    Both inputs must have columns (doy, p05, p25, p50, p75, p95)."""
    fig = go.Figure()
    if raw_clim.empty or smoothed_clim.empty:
        return fig

    raw = raw_clim.sort_values("doy")
    smo = smoothed_clim.sort_values("doy")
    raw_doys = list(raw["doy"])
    smo_doys = list(smo["doy"])

    # Raw envelope — jagged
    fig.add_trace(go.Scatter(
        x=raw_doys + raw_doys[::-1],
        y=list(raw["p95"]) + list(raw["p05"])[::-1],
        fill="toself", fillcolor="rgba(229, 115, 115, 0.20)", line=dict(width=0),
        name="Raw 5-95% (per-DOY only)", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=raw_doys, y=raw["p50"],
        line=dict(color="#c62828", width=1, dash="dot"),
        name="Raw median", hoverinfo="skip",
    ))
    # Smoothed envelope — windowed
    fig.add_trace(go.Scatter(
        x=smo_doys + smo_doys[::-1],
        y=list(smo["p95"]) + list(smo["p05"])[::-1],
        fill="toself", fillcolor="rgba(120, 144, 156, 0.30)", line=dict(width=0),
        name="Windowed 5-95%", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=smo_doys, y=smo["p50"],
        line=dict(color="#37474f", width=1.5),
        name="Windowed median", hoverinfo="skip",
    ))

    fig.update_layout(
        xaxis_title="Day of year",
        yaxis_title=value_label,
        height=280,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9)),
    )
    return fig


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
        clim = climatology.sort_values("doy").reset_index(drop=True)
        doys = [int(d) for d in clim["doy"]]
        p05_yr = list(clim["p05"]); p25_yr = list(clim["p25"])
        p50_yr = list(clim["p50"])
        p75_yr = list(clim["p75"]); p95_yr = list(clim["p95"])

        # Build one continuous series spanning last/this/next year by stitching
        # the per-DOY climatology onto consecutive calendar anchors. Plotting
        # the whole strip as a single trace per band avoids the year-boundary
        # white gap that appeared when each year was drawn separately.
        anchor_years = [today_.year - 1, today_.year, today_.year + 1]
        all_dates: list[datetime] = []
        p05: list[float] = []; p25: list[float] = []
        p50: list[float] = []
        p75: list[float] = []; p95: list[float] = []
        for year in anchor_years:
            all_dates.extend(
                datetime(year, 1, 1) + pd.Timedelta(days=d - 1) for d in doys
            )
            p05.extend(p05_yr); p25.extend(p25_yr); p50.extend(p50_yr)
            p75.extend(p75_yr); p95.extend(p95_yr)

        # Split observed (past, up to today) vs future once over the full strip.
        # Overlap one sample so the past and future fills meet at "today" with
        # no visible seam.
        idx_split = sum(1 for d in all_dates if d.date() <= today_)
        past_slice = slice(0, idx_split + 1 if idx_split < len(all_dates) else idx_split)
        future_slice = slice(max(idx_split - 1, 0), len(all_dates))
        past_dates = all_dates[past_slice]
        future_dates = all_dates[future_slice]

        # PAST (full opacity)
        if past_dates:
            fig.add_trace(go.Scatter(
                x=past_dates + past_dates[::-1],
                y=p95[past_slice] + p05[past_slice][::-1],
                fill="toself", fillcolor=ENVELOPE_OUTER_OBSERVED, line=dict(width=0),
                name="Typical range (5th–95th pct)",
                hoverinfo="skip", showlegend=True,
                legendgroup="env_outer",
            ))
            fig.add_trace(go.Scatter(
                x=past_dates + past_dates[::-1],
                y=p75[past_slice] + p25[past_slice][::-1],
                fill="toself", fillcolor=ENVELOPE_INNER_OBSERVED, line=dict(width=0),
                name="Most common range (25th–75th pct)",
                hoverinfo="skip", showlegend=True,
                legendgroup="env_inner",
            ))
            fig.add_trace(go.Scatter(
                x=past_dates, y=p50[past_slice],
                line=dict(color=ENVELOPE_MEDIAN_OBSERVED, width=1, dash="dot"),
                name="Median (typical)",
                hoverinfo="skip", showlegend=True,
                legendgroup="env_median",
            ))

        # FUTURE (faded — "expected typical range")
        if future_dates:
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=p95[future_slice] + p05[future_slice][::-1],
                fill="toself", fillcolor=ENVELOPE_OUTER_FUTURE, line=dict(width=0),
                hoverinfo="skip", showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=p75[future_slice] + p25[future_slice][::-1],
                fill="toself", fillcolor=ENVELOPE_INNER_FUTURE, line=dict(width=0),
                hoverinfo="skip", showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=future_dates, y=p50[future_slice],
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
            # Re-anchor to each visible calendar year so the analog covers
            # the full ±6-month window (which spans last year and next year).
            pieces = []
            for anchor in (today_.year - 1, today_.year, today_.year + 1):
                shifted = d.copy()
                shifted["date"] = shifted["date"].apply(
                    lambda ts, a=anchor: ts.replace(year=a) if (ts.month, ts.day) != (2, 29) else ts.replace(year=a, day=28)
                )
                pieces.append(shifted)
            d = pd.concat(pieces, ignore_index=True).sort_values("date")
            fig.add_trace(go.Scatter(
                x=d["date"], y=d[primary_column],
                line=dict(color=color, width=1.2),
                name=f"{yr}", opacity=0.85,
                legendgroup=f"analog_{yr}",
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
    # Pin the annotation to the bottom of the plotting area so it doesn't
    # collide with the modebar at the top of the chart.
    today_ts = pd.Timestamp(today_).timestamp() * 1000
    fig.add_vline(
        x=today_ts,
        line=dict(color="#37474f", width=1, dash="dot"),
        annotation=dict(
            text=f"Today · {today_.isoformat()}",
            yref="paper", y=0.03, xref="x", x=today_ts,
            xanchor="left", yanchor="bottom",
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#37474f", borderwidth=1, borderpad=3,
            font=dict(size=10, color="#263238"),
            showarrow=False,
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

    # Center "today" in the chart with a symmetric ±6-month window so the
    # forward view is as wide as the historical view regardless of the
    # day-of-year. Extend if the current-data window pokes past either edge.
    half_window = pd.Timedelta(days=183)
    x_min = pd.Timestamp(today_) - half_window
    x_max = pd.Timestamp(today_) + half_window
    if not current.empty:
        c_dates = pd.to_datetime(current["date"])
        x_min = min(x_min, c_dates.min())
        x_max = max(x_max, c_dates.max() + pd.Timedelta(days=7))

    fig.update_layout(
        title=title,
        yaxis_title=value_label,
        hovermode="x unified",
        height=420,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[x_min, x_max]),
    )
    return fig
