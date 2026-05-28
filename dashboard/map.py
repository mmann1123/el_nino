"""Departamento choropleth on a CARTO base map.

Two layers:
  1. CARTO Positron base (free, no Mapbox token) — ocean, coastline, roads,
     and city labels for geographic context.
  2. Departamento polygons colored by the latest value_anom_z, using a
     continuous diverging colormap (red = dry, blue = wet). Continuous rather
     than the discrete drought-monitor tiers because within-country variation
     is often subtle — a continuous gradient surfaces those differences while
     the hover tooltip still gives the USDM tier name.

The selected departamento gets a thick outline overlay.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .. import config
from ..etl import storage
from . import drought_status

# El Salvador rough center + zoom for the mini-map.
ES_CENTER = {"lat": 13.794, "lon": -88.917}
ES_ZOOM = 6.7


def _latest_anom_per_departamento(indicator_name: str) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    indicator_dir = config.RAW_DIR / indicator_name
    if not indicator_dir.exists():
        return out
    for parquet in indicator_dir.glob("*.parquet"):
        df = storage.read_parquet(parquet)
        if df.empty:
            continue
        dep = df["departamento"].iloc[0]
        if "value_anom_z" not in df.columns:
            out[dep] = None
            continue
        # Use the most recent OBSERVED row (skip forecasts) so the map reflects
        # the current state, not a 15-day forward projection.
        obs = df
        if "is_forecast" in df.columns:
            obs = df[~df["is_forecast"].fillna(False)]
        z = obs["value_anom_z"].dropna()
        out[dep] = float(z.iloc[-1]) if not z.empty else None
    return out


def _load_geojson() -> dict | None:
    p = Path(config.AOI_PATH)
    if not p.exists():
        return None
    with p.open() as f:
        return json.load(f)


def departamento_status_figure(
    indicator_name: str,
    selected_departamento: str | None = None,
) -> go.Figure | None:
    gj = _load_geojson()
    if gj is None:
        return None

    latest_anom = _latest_anom_per_departamento(indicator_name)

    rows = []
    for feat in gj["features"]:
        dep = feat["properties"].get("ADM1_NAME", "")
        z = latest_anom.get(dep)
        cat = drought_status.classify(z)
        rows.append({
            "departamento": dep,
            "z": z if (z is not None and not pd.isna(z)) else 0.0,
            "z_display": f"{z:.2f}" if z is not None and not pd.isna(z) else "—",
            "status_label": cat.label,
        })
    df = pd.DataFrame(rows)

    # Continuous diverging colormap on z-score, anchored at 0 so blue=wet and
    # red=dry are symmetric. Bounded ±2.5 (USDM D3/W3 cutoff) so the gradient
    # uses the same scale across indicators.
    fig = px.choropleth_map(
        df,
        geojson=gj,
        locations="departamento",
        featureidkey="properties.ADM1_NAME",
        color="z",
        color_continuous_scale="RdBu",  # negative red, positive blue
        range_color=(-2.5, 2.5),
        center=ES_CENTER,
        zoom=ES_ZOOM,
        map_style="carto-positron",
        opacity=0.78,
        hover_data={
            "departamento": True,
            "status_label": True,
            "z_display": True,
            "z": False,
        },
        labels={
            "z": "Anomaly (σ)",
            "status_label": "Drought status",
            "z_display": "Anomaly z-score",
        },
    )

    # Outline the currently-selected departamento with a thicker stroke.
    if selected_departamento:
        sel_features = [
            f for f in gj["features"]
            if f["properties"].get("ADM1_NAME") == selected_departamento
        ]
        if sel_features:
            sel_gj = {"type": "FeatureCollection", "features": sel_features}
            outline = go.Choroplethmap(
                geojson=sel_gj,
                locations=[selected_departamento],
                featureidkey="properties.ADM1_NAME",
                z=[1],
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker=dict(line=dict(color="#263238", width=3)),
                hoverinfo="skip",
            )
            fig.add_trace(outline)

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=360,
        coloraxis_colorbar=dict(
            title="Anomaly (σ)",
            thickness=10, len=0.7,
            tickvals=[-2.5, -1.5, -1, 0, 1, 1.5, 2.5],
            ticktext=["−2.5", "−1.5", "−1", "0", "+1", "+1.5", "+2.5"],
            ticks="outside",
            tickfont=dict(size=10),
        ),
    )
    return fig
