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
from el_nino.dashboard import alerts, auth, charts, data, drought_status, freshness, map as map_view, status as status_view  # noqa: E402

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

def _header_icon_html() -> str:
    """Inline-embed the drought icon from dashboard/assets/drought.png (or .svg)
    as base64 so it ships with the app and doesn't depend on static serving.
    Falls back to a desert emoji if the asset isn't present yet."""
    import base64
    assets = Path(__file__).resolve().parent / "assets"
    for name, mime in (("drought.png", "image/png"),
                       ("drought.svg", "image/svg+xml")):
        p = assets / name
        if p.exists() and p.stat().st_size > 0:
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            return (
                f'<img src="data:{mime};base64,{b64}" alt="" '
                'style="width:26px;height:26px;vertical-align:middle;'
                'margin-right:8px;">'
            )
    # Fallback until the user drops drought.png into the assets folder.
    return '<span style="font-size:1.3em;margin-right:6px;">🏜️</span>'


st.sidebar.markdown(
    "<h2 style='margin-top:0;margin-bottom:0.6em;white-space:nowrap;"
    "font-size:1.25em;display:flex;align-items:center;'>"
    f"{_header_icon_html()}ES Drought Monitor</h2>",
    unsafe_allow_html=True,
)
st.sidebar.caption("El Salvador maize-season indicators")

deps_available = data.list_departamentos()
if not deps_available:
    st.sidebar.warning("No data found. Run the ETL first:\n\n`python -m el_nino.etl.run_etl synth`")
    st.warning("No indicator data available yet. The ETL needs to populate `data/raw/`. See sidebar.")
    st.stop()

default_dep = data.ALL if data.ALL in deps_available else deps_available[0]


def _on_dep_dropdown_changed() -> None:
    """When the user picks a departamento from the dropdown, clear any stale
    map-click selection so the prior click doesn't override the new choice on
    the next rerun."""
    st.session_state.pop("dep_map_select", None)


# Resolve the current departamento from session_state (set either by this
# widget or by a click on the country map below).
default_idx = deps_available.index(st.session_state.get("dep_choice", default_dep))
departamento = st.sidebar.selectbox(
    "Departamento", deps_available,
    index=default_idx,
    on_change=_on_dep_dropdown_changed,
    help=(
        "Pick an El Salvador departamento, or 'All (country mean)' for a "
        "nationwide average. You can also click any departamento on the map. "
        "Eastern Dry Corridor focus: Morazán, San Miguel, La Unión, Usulután."
    ),
)
# Persist the dropdown's current value so the index= computation works on
# next rerun and so map clicks can compare against the active selection.
st.session_state["dep_choice"] = departamento

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

# Refresh timestamps directly under the "Check for new data" button.
freshness.sidebar_refresh_caption()

# Required Flaticon attribution for the sidebar icon (drought.png).
# Rendered at the bottom of the sidebar so it's visible but unobtrusive.
st.sidebar.markdown(
    "<div style='margin-top:1.5em;font-size:0.7em;color:#90a4ae;line-height:1.3;'>"
    'Icon: <a href="https://www.flaticon.com/free-icons/drought" '
    'title="drought icons" style="color:#90a4ae;text-decoration:none;">'
    "Drought icons created by Nualnoi Kinkaeo — Flaticon</a>"
    "</div>",
    unsafe_allow_html=True,
)

tabs = st.tabs(["Overview", "Indicator Detail", "Year Compare"])

# ============= Tab 1 — Overview =============
with tabs[0]:
    st.subheader(f"Overview — {departamento}")
    st.caption("Each panel shows the current year against the historical climatology envelope for the past 12 months.")

    # Country-wide status mini-map. Click events on the polygons re-select the
    # corresponding departamento in the sidebar dropdown.
    map_col, legend_col = st.columns([3, 1])
    with map_col:
        map_fig = map_view.departamento_status_figure(indicator_name, selected_departamento=departamento)
        if map_fig is not None:
            st.markdown(
                f"**Current {INDICATOR_LABELS[indicator_name].split('(')[0].strip()} status — all 14 departamentos**  \n"
                "<span style='font-size:0.85em;color:#546e7a;'>"
                "💡 Click any departamento to focus the dashboard on it.</span>",
                unsafe_allow_html=True,
            )
            map_event = st.plotly_chart(
                map_fig,
                width="stretch",
                config={"displayModeBar": False},
                on_select="rerun",
                selection_mode=("points",),
                key="dep_map_select",
            )

            # "Show country average" button anchored to the bottom-left of the
            # map column, tight against the map frame. Sets the dropdown to
            # "All (country mean)" — the same as picking it from the sidebar.
            btn_col, _ = st.columns([2, 5])
            with btn_col:
                if st.button(
                    "🌐 Select All",
                    key="select_all_btn",
                    help="Switch to the country-mean view across all 14 departamentos.",
                    width="stretch",
                ):
                    if st.session_state.get("dep_choice") != data.ALL:
                        st.session_state["dep_choice"] = data.ALL
                        # Clear any stale map-click so it doesn't override.
                        st.session_state.pop("dep_map_select", None)
                        st.rerun()

            # Translate any click event into a dropdown change.
            clicked_dep = None
            if map_event is not None:
                sel = getattr(map_event, "selection", None)
                pts = getattr(sel, "points", None) or []
                if pts:
                    # Plotly choropleth_map puts the feature's `locations` value
                    # into the "location" key of each point.
                    clicked_dep = pts[0].get("location")
            if (
                clicked_dep
                and clicked_dep in deps_available
                and clicked_dep != departamento
            ):
                st.session_state["dep_choice"] = clicked_dep
                st.rerun()
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
            st.plotly_chart(fig, width="stretch", config=charts.CHART_CONFIG)

            latest_z, latest_obs = status_view.current_status_value(
                ind_df, ind_cls.status_window_days, today_,
            )
            cat = drought_status.classify(latest_z)
            st.markdown(
                f"<span style='background-color:{cat.color};color:{cat.text_color};"
                "padding:4px 12px;border-radius:6px;font-weight:600;'>"
                f"{cat.label}</span>",
                unsafe_allow_html=True,
            )
            # Below the badge: freshness colour-dot + last-observation date +
            # lag. Replaces the previous above-chart placement and the
            # redundant "Based on observations from N days ago" caption.
            st.caption(freshness.indicator_badge(ind_name, today_))

    # Drought-alert summary — at the bottom of Overview, written for a
    # non-technical audience.
    st.divider()
    alerts.banner()

# ============= Tab 2 — Indicator Detail =============
with tabs[1]:
    primary = indicator_cls.primary_column
    st.subheader(f"{INDICATOR_LABELS[indicator_name]} — {departamento}")

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
        st.plotly_chart(fig, width="stretch", config=charts.CHART_CONFIG)

        # Plain-language status — averaged over the indicator's status window
        # of OBSERVED rows only (skips forecasts so the badge never reports a
        # 15-day-ahead projection as the current state).
        latest_z, latest_obs = status_view.current_status_value(
            ind_df, indicator_cls.status_window_days, today_,
        )
        cat = drought_status.classify(latest_z)
        st.markdown("### Current status")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(
                f"<div style='background-color:{cat.color};color:{cat.text_color};"
                "padding:18px;border-radius:8px;text-align:center;"
                f"font-weight:700;font-size:1.3em;'>"
                f"{cat.label}</div>",
                unsafe_allow_html=True,
            )
            # Freshness colour-dot + last-observation date + lag, consolidated
            # under the badge instead of in a separate caption above the chart.
            st.caption(freshness.indicator_badge(indicator_name, today_))
        with c2:
            st.write(drought_status.plain_language(latest_z))
            st.caption(cat.description)

        with st.expander("Show technical details"):
            st.write(f"Latest anomaly z-score: {latest_z:.2f}" if latest_z is not None and not pd.isna(latest_z) else "Latest anomaly z-score: —")
            st.write(f"Primary column: `{primary}`")
            st.write(f"Baseline period for {INDICATOR_LABELS[indicator_name]}: {INDICATOR_BASELINE[indicator_name]} (per-DOY percentiles)")

        # Climatology-smoothing caption + diagnostic mini-chart
        window = getattr(indicator_cls, "climatology_doy_window", 0)
        n_samples_str = ""
        if "n_samples" in clim.columns:
            med_n = int(clim["n_samples"].median())
            n_samples_str = f", median {med_n} samples per percentile fence"
        if window > 0:
            st.caption(
                f"_Baseline: {INDICATOR_BASELINE[indicator_name]}. "
                f"Percentile fences smoothed over ±{window}-day window{n_samples_str} — "
                f"pools nearby days-of-year together so short records (esp. WAPOR's ~8 years) "
                f"produce stable envelopes._"
            )
        else:
            st.caption(
                f"_Baseline: {INDICATOR_BASELINE[indicator_name]} (per-DOY only, no smoothing)._"
            )

        with st.expander("How smooth is the envelope? (raw vs windowed)"):
            st.markdown(
                "With only a few years per day-of-year, the 5th and 95th "
                "percentiles are essentially the min and max of a handful of "
                "values — they jump around as you move through the year, "
                "even though the underlying climate doesn't. We smooth by "
                "pooling each day's history with nearby days-of-year. The "
                "comparison below shows the difference."
            )
            try:
                raw_clim = data.load_raw_climatology(indicator_name, departamento, primary)
                if raw_clim.empty:
                    st.info("Raw climatology unavailable.")
                else:
                    diag_fig = charts.smoothing_diagnostic_figure(
                        raw_clim=raw_clim,
                        smoothed_clim=clim,
                        value_label=yaxis_label_for(primary),
                    )
                    st.plotly_chart(diag_fig, width="stretch", config=charts.CHART_CONFIG)
                    st.caption(
                        f"Indicator: **{INDICATOR_LABELS[indicator_name]}** · "
                        f"Years: {INDICATOR_BASELINE[indicator_name]} · "
                        f"Window: ±{window} days · "
                        f"Raw envelope shown in red, windowed envelope in slate."
                    )
            except Exception as e:
                st.warning(f"Could not load raw climatology: {e}")

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

        # Filter the session-state selection against the currently-available
        # years — when the user switches indicators (e.g., CHIRPS → WAPOR)
        # the prior selection may include years that aren't in the new
        # indicator's history (WAPOR starts 2018, so 2015 from CHIRPS isn't
        # valid). Keep the multiselect's default in sync with the options.
        raw_default = st.session_state.get(
            "selected_years",
            [y for y in [2015, 2023] if y in available_years],
        )
        default_years = [y for y in raw_default if y in available_years]
        if default_years != raw_default:
            st.session_state["selected_years"] = default_years
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
        st.plotly_chart(fig, width="stretch", config=charts.CHART_CONFIG)

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
