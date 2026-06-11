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

# On phones, Plotly's touch handlers grab vertical swipes as pan/select, so the
# page won't scroll past a chart. staticPlot renders a flat, non-interactive
# image — swipes scroll the page every time. The per-chart caption already
# surfaces the key numbers, so losing hover/zoom on mobile costs little.
CHART_CONFIG_MOBILE = {
    "staticPlot": True,
    "displayModeBar": False,
    "responsive": True,
}


def chart_config(mobile: bool = False) -> dict:
    """Plotly `config` for the data charts: static (scroll-friendly) on mobile,
    fully interactive on desktop."""
    return CHART_CONFIG_MOBILE if mobile else CHART_CONFIG


ENVELOPE_OUTER_OBSERVED = "rgba(120, 144, 156, 0.18)"   # p05-p95 (past)
ENVELOPE_INNER_OBSERVED = "rgba(120, 144, 156, 0.32)"   # p25-p75 (past)
ENVELOPE_OUTER_FUTURE   = "rgba(120, 144, 156, 0.07)"   # p05-p95 (future, faded)
ENVELOPE_INNER_FUTURE   = "rgba(120, 144, 156, 0.14)"   # p25-p75 (future, faded)
ENVELOPE_MEDIAN_OBSERVED = "rgba(96, 125, 139, 0.65)"
ENVELOPE_MEDIAN_FUTURE   = "rgba(96, 125, 139, 0.30)"
CURRENT_YEAR = "#d32f2f"
FORECAST_DASH = "dash"
ANALOG_PALETTE = ["#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


ENSO_THRESHOLD = 0.5
ENSO_EL_NINO_BAND = "rgba(211, 47, 47, 0.12)"
ENSO_LA_NINA_BAND = "rgba(25, 118, 210, 0.12)"


def _oni_climatology(df: pd.DataFrame) -> pd.DataFrame:
    """Per-calendar-month *empirical percentiles* of ONI across the whole record,
    interpolated to a daily [doy, p05/p25/p50/p75/p95] climatology so it renders
    through climatology_envelope_figure exactly like the indicator charts — and
    makes no normality assumption (ONI is fat-tailed during strong events).

    Daily (not 12-point monthly) resolution matters: the envelope's past/future
    halves overlap by one sample at Today to avoid a seam, so coarse monthly
    anchors would stack into a visible ~month-wide lighter band there. Anchors
    are at each month's 15th and interpolated circularly so the band is smooth
    and the overlap is a single invisible day."""
    import numpy as np

    d = df.dropna(subset=["oni"]).copy()
    if d.empty:
        return pd.DataFrame()
    d["date"] = pd.to_datetime(d["date"])
    d["month"] = d["date"].dt.month

    probs = {"p05": 0.05, "p25": 0.25, "p50": 0.50, "p75": 0.75, "p95": 0.95}
    q = d.groupby("month")["oni"].quantile(list(probs.values())).unstack()
    q.columns = list(probs.keys())
    q = q.reindex(range(1, 13)).interpolate().bfill().ffill().sort_index()

    anchor_doy = [pd.Timestamp(2001, int(m), 15).dayofyear for m in q.index]
    # Circular padding so January interpolates against December and vice-versa.
    ext_doy = np.array([anchor_doy[-1] - 365] + anchor_doy + [anchor_doy[0] + 365])
    days = np.arange(1, 366)

    out = {"doy": days}
    for name in probs:
        vals = q[name].to_numpy()
        ext = np.concatenate([[vals[-1]], vals, [vals[0]]])
        out[name] = np.interp(days, ext_doy, ext)
    return pd.DataFrame(out)


def enso_year_compare_figure(
    oni: pd.DataFrame,
    today_: date,
    analogs: dict[int, pd.DataFrame] | None = None,
    latest_nino34: dict | None = None,
) -> go.Figure:
    """ENSO twin of the Year Compare chart. Reuses ``climatology_envelope_figure``
    for the exact same visual language — ±6-month window centred on Today, analog
    years re-anchored across calendar years in the ANALOG_PALETTE, red current-year
    line, dotted Today marker — then swaps the percentile envelope for ±0.5 °C
    El Niño / La Niña phase bands and drops the freshest weekly Niño 3.4 reading
    on as an amber star.

    oni: cols [date, year, oni]; analogs: {year: df[date, oni]};
    latest_nino34: {date, nino34_ssta, phase}."""
    if oni is None or oni.empty:
        return go.Figure()

    df = oni.copy()
    df["date"] = pd.to_datetime(df["date"])
    if "year" not in df.columns:
        df["year"] = df["date"].dt.year

    # "Current" line = the recent ONI run at its real dates (it lags ~1 month,
    # so it ends just shy of Today — the weekly star then extends it). Pulling a
    # little over a year keeps the left half of the window populated, matching
    # how the indicator charts plot the last 12 months.
    window_start = pd.Timestamp(today_) - pd.Timedelta(days=400)
    cur = df[df["date"] >= window_start][["date", "oni"]].copy()
    cur["is_forecast"] = False

    analogs = analogs or {}

    # Empirical-percentile envelope, computed per calendar month over the whole
    # ONI record and rendered exactly like the indicator charts' climatology band
    # (same percentile fences, same legend labels) — no normality assumption.
    clim = _oni_climatology(df)

    fig = climatology_envelope_figure(
        title="",
        value_label="SST anomaly (°C) — ONI / Niño 3.4",
        climatology=clim,
        current=cur,
        primary_column="oni",
        analogs=analogs,
        today_=today_,
        last_observation=None,
    )

    # Y-range from everything we draw, so the phase-band shapes can't stretch
    # the axis. Floor at ±2.5 °C so the bands always read.
    yvals = list(cur["oni"].dropna())
    for adf in analogs.values():
        yvals += list(pd.to_numeric(adf["oni"], errors="coerce").dropna())
    if not clim.empty:
        yvals += list(clim["p05"]) + list(clim["p95"])
    if latest_nino34:
        yvals.append(latest_nino34["nino34_ssta"])
    y_lo = min([-2.5] + yvals) - 0.4
    y_hi = max([2.5] + yvals) + 0.4

    # ±0.5 °C phase bands (drawn under the data) + dotted threshold lines.
    fig.add_hrect(y0=ENSO_THRESHOLD, y1=y_hi, fillcolor=ENSO_EL_NINO_BAND,
                  line_width=0, layer="below")
    fig.add_hrect(y0=y_lo, y1=-ENSO_THRESHOLD, fillcolor=ENSO_LA_NINA_BAND,
                  line_width=0, layer="below")
    for thr, txt, col in (
        (ENSO_THRESHOLD, "El Niño ≥ +0.5 °C", "#ef5350"),
        (-ENSO_THRESHOLD, "La Niña ≤ −0.5 °C", "#42a5f5"),
    ):
        fig.add_hline(
            y=thr, line=dict(color=col, width=1, dash="dot"),
            annotation=dict(text=txt, font=dict(size=18, color=col)),
            annotation_position="top right",
        )

    # Freshest weekly Niño 3.4 — the leading edge, ~1 month ahead of ONI. Drawn
    # as a dashed red continuation of the current-year line (same idiom as the
    # 15-day forecast on the indicator charts) rather than a free-floating point.
    if latest_nino34:
        d = pd.to_datetime(latest_nino34["date"])
        lead_x = [d]
        lead_y = [latest_nino34["nino34_ssta"]]
        if not cur.empty:
            last_cur = cur.sort_values("date").iloc[-1]
            lead_x = [pd.to_datetime(last_cur["date"]), d]
            lead_y = [last_cur["oni"], latest_nino34["nino34_ssta"]]
        fig.add_trace(go.Scatter(
            x=lead_x, y=lead_y,
            mode="lines+markers",
            line=dict(color=CURRENT_YEAR, width=3, dash=FORECAST_DASH),
            marker=dict(size=8, color=CURRENT_YEAR),
            name="Latest weekly Niño 3.4",
            hovertemplate=(
                f"Weekly Niño 3.4 · {d.date()}: "
                f"{latest_nino34['nino34_ssta']:+.2f} °C<extra></extra>"
            ),
        ))

    # A touch thicker current-year line than the indicator charts so it reads
    # against the analog overlays, and a larger legend.
    fig.update_traces(line=dict(width=4), selector=dict(name="Current year"))
    fig.update_layout(height=520, legend=dict(font=dict(size=15)))
    fig.update_yaxes(range=[y_lo, y_hi])
    return fig


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
    outer_label: str = "Typical range (5th–95th pct)",
    inner_label: str = "Most common range (25th–75th pct)",
    median_label: str = "Median (typical)",
) -> go.Figure:
    """climatology: cols [doy, p05, p10, p25, p50, p75, p90, p95]
    current: cols [date, primary_column, is_forecast]
    analogs: {year: DataFrame with [date, primary_column]}

    outer_label/inner_label/median_label name the two bands and the centre line —
    defaults describe the percentile envelope the indicator charts use; the ENSO
    chart overrides them with mean ± SD wording.
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
                name=outer_label,
                hoverinfo="skip", showlegend=True,
                legendgroup="env_outer",
            ))
            fig.add_trace(go.Scatter(
                x=past_dates + past_dates[::-1],
                y=p75[past_slice] + p25[past_slice][::-1],
                fill="toself", fillcolor=ENVELOPE_INNER_OBSERVED, line=dict(width=0),
                name=inner_label,
                hoverinfo="skip", showlegend=True,
                legendgroup="env_inner",
            ))
            fig.add_trace(go.Scatter(
                x=past_dates, y=p50[past_slice],
                line=dict(color=ENVELOPE_MEDIAN_OBSERVED, width=1, dash="dot"),
                name=median_label,
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
