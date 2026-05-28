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
from el_nino.dashboard import alerts, auth, charts, data, drought_status, freshness, map as map_view  # noqa: E402

st.set_page_config(
    page_title="El Salvador Drought Monitor",
    page_icon="🌾",
    layout="wide",
)

auth.require_login()

INDICATOR_LABELS = {
    "chirps": "Rainfall (SPI-3)",
    "smap": "Soil moisture (root-zone)",
    "wapor": "Evapotranspiration (WAPOR ETa)",
    "imerg": "Daily rainfall (event scale)",
}

INDICATOR_HELP = {
    "chirps": (
        "**SPI-3** (Standardized Precipitation Index, 3-month) — how unusual the "
        "last 3 months of rainfall have been compared to 1981–present at this "
        "location and time of year. **0 = typical**, **−1 = moderate drought**, "
        "**−1.5 = severe drought**. Source: CHIRPS v3. "
        "**15-day forecast** is from NOAA GFS 0.25° (raw, not bias-corrected to "
        "CHIRPS — GFS tends to over-predict in Central America)."
    ),
    "smap": (
        "**Root-zone soil moisture (0–100 cm)** — water available to maize roots. "
        "Even when surface looks moist, what kills yield at silking is depletion "
        "of the deeper store, which this captures. Source: NASA SMAP L4."
    ),
    "wapor": (
        "**Actual evapotranspiration (ETa)** — water actually leaving the soil "
        "and crop canopy. Low ETa during the growing season confirms crop stress. "
        "Lags rainfall/soil moisture by ~10 days. Source: FAO WAPOR v3."
    ),
    "imerg": (
        "**Daily rainfall** at finer temporal/spatial resolution than CHIRPS. "
        "Use for verifying individual rain events. Source: NASA IMERG-Late V07."
    ),
}

# Per-indicator baseline window — different products start at different years.
INDICATOR_BASELINE = {
    "chirps": "1981–present",
    "smap":   "2015–present",
    "wapor":  "2018–present",
    "imerg":  "2000–present",
}

# Human-readable y-axis labels — used everywhere the primary_column would
# otherwise be shown verbatim ("spi_3", "eta_mm", "rzsm_m3m3", ...).
YAXIS_LABELS = {
    "spi_3": "SPI-3 (standardized rainfall, last 3 months)",
    "spi_1": "SPI-1 (standardized rainfall, last month)",
    "spi_6": "SPI-6 (standardized rainfall, last 6 months)",
    "precip_pentad_mm": "Rainfall (mm per 5-day pentad)",
    "rzsm_m3m3": "Root-zone soil moisture (m³/m³)",
    "eta_mm": "Evapotranspiration (mm per dekad)",
    "imerg_precip_mm": "Rainfall (mm per day)",
}


def yaxis_label_for(col: str) -> str:
    return YAXIS_LABELS.get(col, col)


# Historically significant El Niño analog years for El Salvador maize, drawn
# from el_nino_agricultural_risks.md. Keeps the Year Compare overlay readable
# instead of throwing 18+ years at the chart.
NOTABLE_EL_NINO_YEARS = [1997, 2002, 2009, 2015, 2018, 2023]
NOTABLE_LA_NINA_YEARS = [1988, 1999, 2007, 2010, 2020]

today_ = config.today()

# ---------- Sidebar ----------
st.sidebar.markdown(
    "<h2 style='margin-top:0;margin-bottom:0.6em;white-space:nowrap;font-size:1.25em;'>"
    "🌾 ES Drought Monitor</h2>",
    unsafe_allow_html=True,
)
st.sidebar.caption("El Salvador maize-season indicators")

deps_available = data.list_departamentos()
if not deps_available:
    st.sidebar.warning("No data found. Run the ETL first:\n\n`python -m el_nino.etl.run_etl synth`")
    st.warning("No indicator data available yet. The ETL needs to populate `data/raw/`. See sidebar.")
    st.stop()

default_dep = "Morazan" if "Morazan" in deps_available else deps_available[0]
departamento = st.sidebar.selectbox(
    "Departamento", deps_available,
    index=deps_available.index(default_dep),
    help="Pick an El Salvador departamento. Eastern Dry Corridor: Morazán, San Miguel, La Unión, Usulután.",
)

indicator_name = st.sidebar.selectbox(
    "Indicator",
    list(INDICATORS),
    format_func=lambda k: INDICATOR_LABELS.get(k, k),
    help="Pick which indicator to feature in Indicator Detail and Year Compare.",
)
indicator_cls = INDICATORS[indicator_name]
st.sidebar.caption(INDICATOR_HELP.get(indicator_name, ""))

show_forecast = st.sidebar.toggle(
    "Show 15-day forecast (where available)", value=True,
    help="Append the CHIRPS3-GEFS 15-day rainfall forecast as a dashed segment.",
)

# Smart reload: checks the source assets for new data and reports up-to-date status.
reload_clicked = st.sidebar.button("🔄 Check for new data", help="Queries Earth Engine for the latest available date of each indicator, compares to local data, and fetches any gap.")
if reload_clicked:
    with st.sidebar.status("Checking source assets…", expanded=True) as status:
        try:
            from el_nino.etl import refresh_check
            results = refresh_check.run(verbose_logger=lambda m: status.write(m))
            any_behind = any(r["behind_days"] > 0 for r in results)
            if any_behind:
                status.update(label="Found new data — fetched and merged.", state="complete")
            else:
                status.update(label="Already up to date.", state="complete")
            st.cache_data.clear()
        except Exception as e:
            status.update(label=f"Failed: {e}", state="error")
    if reload_clicked:
        st.rerun()

# ---------- Freshness strip ----------
freshness.freshness_strip(today_)

tabs = st.tabs(["Overview", "Indicator Detail", "Year Compare"])

# ============= Tab 1 — Overview =============
with tabs[0]:
    st.subheader(f"Overview — {departamento}")
    st.caption("Each panel shows the current year against the historical climatology envelope for the past 12 months.")

    # Calibrated drought-trigger alert banner
    alerts.banner()

    # Country-wide status mini-map
    map_col, legend_col = st.columns([3, 1])
    with map_col:
        map_fig = map_view.departamento_status_figure(indicator_name, selected_departamento=departamento)
        if map_fig is not None:
            st.markdown(
                f"**Current {INDICATOR_LABELS[indicator_name].split('(')[0].strip()} status — all 14 departamentos**"
            )
            st.plotly_chart(map_fig, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Map unavailable — run `python -m el_nino.etl.aoi.fetch_aoi` to fetch the AOI polygons.")
    with legend_col:
        st.markdown("**Legend**")
        for cat in [
            drought_status.W3, drought_status.W2, drought_status.W1,
            drought_status.NORMAL,
            drought_status.D0, drought_status.D1, drought_status.D2,
            drought_status.D3, drought_status.D4,
        ]:
            st.markdown(
                f"<div style='display:flex;align-items:center;margin:2px 0;'>"
                f"<span style='display:inline-block;width:14px;height:14px;"
                f"background-color:{cat.color};border-radius:3px;margin-right:6px;'></span>"
                f"<span style='font-size:0.85em;'>{cat.label}</span></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    panel_indicators = ["chirps", "smap", "wapor"]
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
                value_label=yaxis_label_for(primary),
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
            badge_text_color = "#37474f" if cat.is_pending else "white"
            st.markdown(
                f"<span style='background-color:{cat.color};color:{badge_text_color};"
                "padding:4px 12px;border-radius:6px;font-weight:600;'>"
                f"{cat.label}</span>",
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
            value_label=yaxis_label_for(primary),
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
        badge_text_color = "#37474f" if cat.is_pending else "white"
        with c1:
            st.markdown(
                f"<div style='background-color:{cat.color};color:{badge_text_color};"
                "padding:18px;border-radius:8px;text-align:center;"
                f"font-weight:700;font-size:1.3em;'>"
                f"{cat.label}</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.write(drought_status.plain_language(latest_z))
            st.caption(cat.description)

        with st.expander("Show technical details"):
            st.write(f"Latest anomaly z-score: {latest_z:.2f}" if latest_z is not None and not pd.isna(latest_z) else "Latest anomaly z-score: —")
            st.write(f"Primary column: `{primary}`")
            st.write(f"Baseline period for {INDICATOR_LABELS[indicator_name]}: {INDICATOR_BASELINE[indicator_name]} (per-DOY percentiles)")
        st.caption(
            f"_Baseline for this indicator: {INDICATOR_BASELINE[indicator_name]}. "
            f"Note: SMAP starts 2015, WAPOR starts 2018 — shorter records make percentile fences wider._"
        )

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

        # Limit auto-selections to the notable analog years (instead of the ~20
        # years that strict ONI classification flags) so the chart stays legible.
        el_nino_yrs = [y for y in NOTABLE_EL_NINO_YEARS if y in available_years]
        la_nina_yrs = [y for y in NOTABLE_LA_NINA_YEARS if y in available_years]

        c1, c2, c3 = st.columns(3)
        if c1.button("📊 Notable El Niño years"):
            st.session_state["selected_years"] = el_nino_yrs
        if c2.button("❄️ Notable La Niña years"):
            st.session_state["selected_years"] = la_nina_yrs
        if c3.button("Clear"):
            st.session_state["selected_years"] = []
        st.caption(
            "El Niño analogs (1997-98, 2009-10, 2015-16, 2018-19, 2023-24) and "
            "La Niña analogs are pre-selected from "
            "[el_nino_agricultural_risks.md](https://github.com/) historical record."
        )

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
            value_label=yaxis_label_for(primary),
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
    - **NOAA GFS0P25** 15-day rainfall forecast (daily refresh, uncalibrated — GFS over-predicts in Central America)
    - **SMAP L4** root-zone soil moisture ({INDICATORS['smap'].freshness.expected_cadence_days} days)
    - **FAO WAPOR v3** L1 AETI (dekadal, ~300 m) ({INDICATORS['wapor'].freshness.expected_cadence_days} days)
    - **IMERG-Late V07** daily rainfall ({INDICATORS['imerg'].freshness.expected_cadence_days} day)

    **Climatology baseline:** {config.CLIMATOLOGY_START_YEAR}–{config.CLIMATOLOGY_END_YEAR}.

    **Drought classification:** U.S. Drought Monitor SPI bins
    (D0 ≤ −1.0, D1 ≤ −1.3, D2 ≤ −1.6, D3 ≤ −2.0, D4 ≤ −2.5).

    Alert thresholds are pending calibration against historical crop-loss events
    (1997-98, 2015-16, 2023-24) before being turned on — see
    `el_nino/experiments/trigger_calibration.ipynb`.
    """)
