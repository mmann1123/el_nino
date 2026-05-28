"""Streamlit entry point. Three tabs: Overview / Indicator Detail / Year Compare.

Local run:
    streamlit run el_nino/dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit invokes this as a top-level script, not as a package member, so
# relative imports fail. Add the project root to sys.path so absolute imports
# of `el_nino.*` resolve.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from datetime import date  # noqa: E402

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from el_nino import config  # noqa: E402
from el_nino.etl.indicators import INDICATORS  # noqa: E402
from el_nino.dashboard import auth, charts, data, drought_status, freshness  # noqa: E402

st.set_page_config(
    page_title="El Salvador Drought Monitor",
    page_icon="🌾",
    layout="wide",
)

auth.require_login()

INDICATOR_LABELS = {
    "chirps": "Rainfall (SPI-3)",
    "smap": "Soil moisture (root-zone)",
    "ssebop": "Evapotranspiration anomaly",
    "imerg": "Daily rainfall (event scale)",
}

today_ = config.today()

# ---------- Sidebar ----------
st.sidebar.title("El Salvador Drought Monitor")
deps_available = data.list_departamentos()
if not deps_available:
    st.sidebar.warning("No data found. Run the ETL first:\n\n`python -m el_nino.etl.run_etl synth`")
    st.warning("No indicator data available yet. The ETL needs to populate `data/raw/`. See sidebar.")
    st.stop()

default_dep = "Morazán" if "Morazán" in deps_available else deps_available[0]
departamento = st.sidebar.selectbox("Departamento", deps_available, index=deps_available.index(default_dep))

indicator_name = st.sidebar.selectbox(
    "Indicator",
    list(INDICATORS),
    format_func=lambda k: INDICATOR_LABELS.get(k, k),
)
indicator_cls = INDICATORS[indicator_name]

show_forecast = st.sidebar.toggle("Show 15-day forecast (where available)", value=True)
if st.sidebar.button("Refresh data caches"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(f"Baseline period: {config.CLIMATOLOGY_START_YEAR}–{config.CLIMATOLOGY_END_YEAR}")

# ---------- Freshness strip ----------
freshness.freshness_strip(today_)

tabs = st.tabs(["Overview", "Indicator Detail", "Year Compare"])

# ============= Tab 1 — Overview =============
with tabs[0]:
    st.subheader(f"Overview — {departamento}")
    st.caption("Each panel shows the current year against the historical climatology envelope for the past 12 months.")

    panel_indicators = ["chirps", "smap", "ssebop"]
    cols = st.columns(len(panel_indicators))
    for col, ind_name in zip(cols, panel_indicators):
        ind_cls = INDICATORS[ind_name]
        with col:
            st.markdown(f"**{INDICATOR_LABELS[ind_name]}**")
            st.caption(freshness.indicator_badge(ind_name, today_))
            ind_df = data.load_indicator(ind_name, departamento)
            if ind_df.empty:
                st.info("No data.")
                continue
            primary = ind_cls.primary_column
            clim = data.load_climatology(ind_name, departamento, primary)
            window_start = pd.Timestamp(today_) - pd.Timedelta(days=365)
            current = ind_df[ind_df["date"] >= window_start][["date", primary, "is_forecast"]].dropna(subset=[primary])
            fig = charts.climatology_envelope_figure(
                title="",
                value_label=primary,
                climatology=clim,
                current=current,
                primary_column=primary,
                today_=today_,
                last_observation=freshness.last_observation_date(ind_name),
            )
            fig.update_layout(height=320, showlegend=False)
            st.plotly_chart(fig, width="stretch")

            latest_z = ind_df.dropna(subset=["value_anom_z"]).iloc[-1]["value_anom_z"] if "value_anom_z" in ind_df.columns and not ind_df["value_anom_z"].dropna().empty else None
            cat = drought_status.classify(latest_z)
            st.markdown(
                f"<span style='background-color:{cat.color};color:white;padding:4px 10px;border-radius:6px;font-weight:600'>"
                f"{cat.short} · {cat.label}</span>",
                unsafe_allow_html=True,
            )

# ============= Tab 2 — Indicator Detail =============
with tabs[1]:
    primary = indicator_cls.primary_column
    st.subheader(f"{INDICATOR_LABELS[indicator_name]} — {departamento}")
    st.caption(freshness.indicator_badge(indicator_name, today_))

    ind_df = data.load_indicator(indicator_name, departamento)
    if ind_df.empty:
        st.info("No data for this indicator/departamento combination.")
    else:
        clim = data.load_climatology(indicator_name, departamento, primary)
        window_start = pd.Timestamp(today_) - pd.Timedelta(days=365)
        cur = ind_df[ind_df["date"] >= window_start][["date", primary, "is_forecast"]].dropna(subset=[primary])
        if not show_forecast:
            cur = cur[~cur.get("is_forecast", pd.Series([False] * len(cur))).fillna(False)]

        fig = charts.climatology_envelope_figure(
            title="",
            value_label=primary,
            climatology=clim,
            current=cur,
            primary_column=primary,
            today_=today_,
            last_observation=freshness.last_observation_date(indicator_name),
        )
        st.plotly_chart(fig, width="stretch")

        # Plain-language status
        z_series = ind_df["value_anom_z"].dropna() if "value_anom_z" in ind_df.columns else pd.Series(dtype=float)
        latest_z = z_series.iloc[-1] if not z_series.empty else None
        cat = drought_status.classify(latest_z)
        st.markdown("### Current status")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(
                f"<div style='background-color:{cat.color};color:white;padding:16px;border-radius:8px;text-align:center;font-size:1.1em'>"
                f"<div style='font-size:0.85em;opacity:0.9'>{cat.short}</div>"
                f"<div style='font-weight:700;font-size:1.4em'>{cat.label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.write(drought_status.plain_language(latest_z))
            st.caption(cat.description)

        with st.expander("Show technical details"):
            st.write(f"Latest anomaly z-score: {latest_z:.2f}" if latest_z is not None and not pd.isna(latest_z) else "Latest anomaly z-score: —")
            st.write(f"Primary column: `{primary}`")
            st.write(f"Baseline: {config.CLIMATOLOGY_START_YEAR}–{config.CLIMATOLOGY_END_YEAR} per-DOY percentiles")

# ============= Tab 3 — Year Compare =============
with tabs[2]:
    primary = indicator_cls.primary_column
    st.subheader(f"Compare years — {INDICATOR_LABELS[indicator_name]} in {departamento}")

    ind_df = data.load_indicator(indicator_name, departamento)
    if ind_df.empty:
        st.info("No data.")
    else:
        clim = data.load_climatology(indicator_name, departamento, primary)
        available_years = sorted(ind_df["year"].dropna().unique().tolist())

        enso_df = data.load_enso()
        from el_nino.etl import enso as enso_mod
        el_nino_yrs = enso_mod.el_nino_years(enso_df) if not enso_df.empty else [1982, 1997, 2009, 2015, 2023]
        la_nina_yrs = enso_mod.la_nina_years(enso_df) if not enso_df.empty else [1988, 1998, 2007, 2010, 2020]

        c1, c2, c3 = st.columns(3)
        if c1.button("📊 El Niño years"):
            st.session_state["selected_years"] = [y for y in el_nino_yrs if y in available_years]
        if c2.button("❄️ La Niña years"):
            st.session_state["selected_years"] = [y for y in la_nina_yrs if y in available_years]
        if c3.button("Clear"):
            st.session_state["selected_years"] = []

        default_years = st.session_state.get("selected_years", [y for y in [2015, 2023] if y in available_years])
        selected = st.multiselect(
            "Years to overlay on the current year",
            options=available_years,
            default=default_years,
            key="selected_years",
        )

        analogs = {}
        for y in selected:
            yr_df = ind_df[ind_df["year"] == y][["date", primary]].dropna(subset=[primary])
            if not yr_df.empty:
                analogs[y] = yr_df

        window_start = pd.Timestamp(today_) - pd.Timedelta(days=365)
        cur = ind_df[ind_df["date"] >= window_start][["date", primary, "is_forecast"]].dropna(subset=[primary])

        fig = charts.climatology_envelope_figure(
            title="",
            value_label=primary,
            climatology=clim,
            current=cur,
            primary_column=primary,
            analogs=analogs,
            today_=today_,
            last_observation=freshness.last_observation_date(indicator_name),
        )
        fig.update_layout(height=520)
        st.plotly_chart(fig, width="stretch")

# ---------- About this data ----------
with st.expander("About this data"):
    st.markdown(f"""
    **Indicators** (refresh cadence in parentheses):
    - **CHIRPS v3** rainfall + SPI-1/3/6 ({INDICATORS['chirps'].freshness.expected_cadence_days} days)
    - **SMAP L4** root-zone soil moisture ({INDICATORS['smap'].freshness.expected_cadence_days} days)
    - **SSEBop v6** ET anomaly ({INDICATORS['ssebop'].freshness.expected_cadence_days} days, dekadal)
    - **IMERG-Late V07** daily rainfall ({INDICATORS['imerg'].freshness.expected_cadence_days} day)

    **Climatology baseline:** {config.CLIMATOLOGY_START_YEAR}–{config.CLIMATOLOGY_END_YEAR}.

    **Drought classification:** U.S. Drought Monitor SPI bins
    (D0 ≤ −1.0, D1 ≤ −1.3, D2 ≤ −1.6, D3 ≤ −2.0, D4 ≤ −2.5).

    Alert thresholds are pending calibration against historical crop-loss events
    (1997-98, 2015-16, 2023-24) before being turned on — see
    `el_nino/experiments/trigger_calibration.ipynb`.
    """)
