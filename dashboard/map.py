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
    """Load the AOI GeoJSON and normalize any GeometryCollection to a
    Polygon/MultiPolygon. FAO GAUL ships at least one El Salvador feature
    (San Miguel) as a GeometryCollection mixing a stray LineString with the
    actual Polygon; Plotly's choropleth_map silently drops such features."""
    p = Path(config.AOI_PATH)
    if not p.exists():
        return None
    with p.open() as f:
        gj = json.load(f)

    for feat in gj.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") != "GeometryCollection":
            continue
        polys = [g for g in geom.get("geometries", [])
                 if g.get("type") in ("Polygon", "MultiPolygon")]
        if not polys:
            continue
        if len(polys) == 1 and polys[0]["type"] == "Polygon":
            feat["geometry"] = polys[0]
        else:
            # Flatten any MultiPolygons too, into one MultiPolygon
            coords = []
            for g in polys:
                if g["type"] == "Polygon":
                    coords.append(g["coordinates"])
                else:
                    coords.extend(g["coordinates"])
            feat["geometry"] = {"type": "MultiPolygon", "coordinates": coords}
    return gj


def departamento_status_figure(
    indicator_name: str,
    selected_departamento: str | None = None,
) -> go.Figure | None:
    gj = _load_geojson()
    if gj is None:
        return None

    latest_anom = _latest_anom_per_departamento(indicator_name)

    # Use the SAME discrete U.S. Drought Monitor tiers + colors as the badges
    # in the dashboard panels — this is the only way the map's visual color
    # and the panel's "Severe Drought / Exceptional Drought" labels agree.
    # A continuous diverging colormap would surface within-tier variation
    # but loses alignment with the legend, which surprised users.
    rows = []
    for feat in gj["features"]:
        dep = feat["properties"].get("ADM1_NAME", "")
        z = latest_anom.get(dep)
        cat = drought_status.classify(z)
        rows.append({
            "departamento": dep,
            "status_label": cat.label,
            "z_display": f"{z:+.2f}" if z is not None and not pd.isna(z) else "—",
        })
    df = pd.DataFrame(rows)

    # Build the discrete color map across every tier so plotly applies the
    # exact same hex per category as the panel badges + the legend column.
    all_cats = [
        drought_status.W3, drought_status.W2, drought_status.W1,
        drought_status.NORMAL,
        drought_status.D0, drought_status.D1, drought_status.D2,
        drought_status.D3, drought_status.D4,
        drought_status.PENDING,
    ]
    color_map = {cat.label: cat.color for cat in all_cats}
    # Force the legend order — wet to dry — so the choropleth's internal
    # category ordering matches the dashboard's USDM legend column.
    category_order = [cat.label for cat in all_cats]

    fig = px.choropleth_map(
        df,
        geojson=gj,
        locations="departamento",
        featureidkey="properties.ADM1_NAME",
        color="status_label",
        color_discrete_map=color_map,
        category_orders={"status_label": category_order},
        center=ES_CENTER,
        zoom=ES_ZOOM,
        map_style="carto-positron",
        opacity=0.78,
        hover_data={
            "departamento": True,
            "status_label": True,
            "z_display": True,
        },
        labels={
            "status_label": "Status",
            "departamento": "Departamento",
            "z_display": "Anomaly (σ)",
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
        # No in-figure legend — the dashboard renders its own USDM legend
        # column to the right of the map, sharing the exact same colors.
        showlegend=False,
    )
    return fig
