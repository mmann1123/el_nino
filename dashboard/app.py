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
from el_nino.etl import enso  # noqa: E402
from el_nino.etl.indicators import INDICATORS  # noqa: E402
from el_nino.dashboard import (
    alerts,
    auth,
    charts,
    data,
    drought_status,
    freshness,
    i18n,
    map as map_view,
    site_footer,
    status as status_view,
)  # noqa: E402

# Resolve the session language before the first translated string.
i18n.init()

st.set_page_config(
    page_title=i18n.t("page_title", name=config.CC["display_name"]),
    page_icon="🌾",
    layout="wide",
)

auth.require_login()

# Indicator labels / help / baselines / axis titles are translated at lookup
# time (dashboard/i18n.py) so they follow the sidebar language toggle.


class _Translated:
    """Mapping-like view that resolves ``prefix + key + suffix`` through i18n
    at access time (so the labels follow the active language)."""

    def __init__(self, prefix: str, keys, suffix: str = ""):
        self._keys = set(keys)
        self._prefix, self._suffix = prefix, suffix

    def __getitem__(self, k: str) -> str:
        if k not in self._keys:
            raise KeyError(k)
        return i18n.t(f"{self._prefix}{k}{self._suffix}")

    def get(self, k: str, default=None):
        return self[k] if k in self._keys else default


INDICATOR_LABELS = _Translated("ind_", INDICATORS)
INDICATOR_HELP = _Translated("ind_", INDICATORS, "_help")


# Per-indicator baseline start year — different products start at different years.
INDICATOR_BASELINE_START = {
    "chirps": 1981,
    "smap": 2015,
    "wapor": 2018,
    "imerg": 2000,
}


def baseline_for(indicator: str) -> str:
    return i18n.t("baseline_fmt", start=INDICATOR_BASELINE_START[indicator])


# Human-readable y-axis labels — used everywhere the primary_column would
# otherwise be shown verbatim ("spi_3", "eta_mm", "rzsm_m3m3", ...).
YAXIS_COLUMNS = (
    "spi_3", "spi_1", "spi_6", "precip_pentad_mm",
    "rzsm_m3m3", "eta_mm", "imerg_precip_mm",
)


def yaxis_label_for(col: str) -> str:
    return i18n.t(f"yaxis_{col}") if col in YAXIS_COLUMNS else col


# Canonical notable analog years are defined in el_nino/etl/enso.py — kept
# centralized so the Year Compare overlay, caption text, and About-this-data
# panel stay in sync.
NOTABLE_EL_NINO_YEARS = enso.NOTABLE_EL_NINO_YEARS
NOTABLE_LA_NINA_YEARS = enso.NOTABLE_LA_NINA_YEARS

today_ = config.today()

# Device detection from the request User-Agent so the data charts can be served
# static (scroll-friendly) on phones and fully interactive on desktop. iPadOS
# reports a desktop UA, so tablets fall through to the interactive path — fine,
# they have the screen room. Detection is best-effort; on any failure we assume
# desktop (the richer experience).
import re  # noqa: E402

_MOBILE_UA_RE = re.compile(
    r"Mobi|Android|iPhone|iPod|IEMobile|BlackBerry|Opera Mini", re.I
)


def _is_mobile() -> bool:
    try:
        ua = st.context.headers.get("User-Agent", "") or ""
    except Exception:
        return False
    return bool(_MOBILE_UA_RE.search(ua))


IS_MOBILE = _is_mobile()
CHART_CFG = charts.chart_config(IS_MOBILE)

# ---------- Sidebar ----------


def _header_icon_html() -> str:
    """Inline-embed the drought icon from dashboard/assets/drought.png (or .svg)
    as base64 so it ships with the app and doesn't depend on static serving.
    Falls back to a desert emoji if the asset isn't present yet."""
    import base64

    assets = Path(__file__).resolve().parent / "assets"
    for name, mime in (("drought.png", "image/png"), ("drought.svg", "image/svg+xml")):
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


# Sidebar header: title, then the ES|EN / FR|EN language toggle on its own
# row directly beneath it (a side-by-side layout clipped the toggle on
# narrower sidebars).
st.sidebar.markdown(
    "<h2 style='margin:0 0 0.35em 0;font-size:1.25em;line-height:1.25;"
    "white-space:nowrap;display:flex;align-items:center;'>"
    f"{_header_icon_html()}<span>"
    f"{i18n.t('sidebar_title', code=config.CC['short_code'])}</span></h2>",
    unsafe_allow_html=True,
)
i18n.language_toggle(st.sidebar)
st.sidebar.caption(f"{config.CC['display_name']} {i18n.crop_caption()}")

deps_available = data.list_departamentos()
if not deps_available:
    st.sidebar.warning(i18n.t("no_data_sidebar"))
    st.warning(i18n.t("no_data_main"))
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
    config.CC["dept_term"].capitalize(),
    deps_available,
    index=default_idx,
    format_func=lambda d: i18n.dep_display(d, data.ALL),
    on_change=_on_dep_dropdown_changed,
    help=i18n.t(
        "dep_select_help",
        country=config.CC["display_name"],
        dept=config.CC["dept_term"],
        all=i18n.t("all_country_mean"),
        priority=i18n.priority_label(),
        names=config.CC["priority_display_names"],
    ),
)
# Display form of the selection (translates the "All (country mean)" sentinel).
departamento_label = i18n.dep_display(departamento, data.ALL)
# Persist the dropdown's current value so the index= computation works on
# next rerun and so map clicks can compare against the active selection.
st.session_state["dep_choice"] = departamento

indicator_name = st.sidebar.selectbox(
    i18n.t("indicator"),
    list(INDICATORS),
    format_func=lambda k: INDICATOR_LABELS.get(k, k),
    help=i18n.t("indicator_help"),
)
indicator_cls = INDICATORS[indicator_name]
st.sidebar.caption(INDICATOR_HELP.get(indicator_name, ""))

show_forecast = st.sidebar.toggle(
    i18n.t("forecast_toggle"),
    value=True,
    help=i18n.t("forecast_toggle_help"),
)

# Data refresh is scheduler-driven only (see deploy/schedule.sh). The dashboard
# never triggers a fetch: running ETL inside the serving process held a Cloud Run
# instance open for the length of a GEE pull, and the same work already runs
# daily. These captions report when the scheduler last landed data.
freshness.sidebar_refresh_caption()

# Required Flaticon attribution for the sidebar icon (drought.png).
# Rendered at the bottom of the sidebar so it's visible but unobtrusive.
st.sidebar.markdown(
    "<div style='margin-top:1.5em;font-size:0.7em;color:#90a4ae;line-height:1.3;'>"
    + i18n.t(
        "icon_attribution",
        link='<a href="https://www.flaticon.com/free-icons/drought" '
             'title="drought icons" style="color:#90a4ae;text-decoration:none;">'
             "Drought icons created by Nualnoi Kinkaeo — Flaticon</a>",
    )
    + "</div>",
    unsafe_allow_html=True,
)

tabs = st.tabs([i18n.t("tab_overview"), i18n.t("tab_detail"), i18n.t("tab_compare")])

# ============= Tab 1 — Overview =============
with tabs[0]:
    st.subheader(i18n.t("overview_header", dep=departamento_label))
    st.caption(i18n.t("overview_caption"))

    # Country-wide status mini-map. Click events on the polygons re-select the
    # corresponding departamento in the sidebar dropdown.
    map_col, legend_col = st.columns([3, 1])
    with map_col:
        map_fig = map_view.departamento_status_figure(
            indicator_name, selected_departamento=departamento
        )
        if map_fig is not None:
            st.markdown(
                i18n.t(
                    "map_title",
                    indicator=INDICATOR_LABELS[indicator_name].split("(")[0].strip(),
                    depts=config.CC["dept_term_plural"],
                )
                + "  \n<span style='font-size:0.85em;color:#546e7a;'>"
                + i18n.t("map_click_hint", dept=config.CC["dept_term"])
                + "</span>",
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
                    i18n.t("select_all_btn"),
                    key="select_all_btn",
                    help=i18n.t("select_all_help", depts=config.CC["dept_term_plural"]),
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
            st.info(i18n.t("map_unavailable"))
    with legend_col:
        st.markdown(i18n.t("legend"))
        for cat in [
            drought_status.W3,
            drought_status.W2,
            drought_status.W1,
            drought_status.NORMAL,
            drought_status.D0,
            drought_status.D1,
            drought_status.D2,
            drought_status.D3,
            drought_status.D4,
        ]:
            st.markdown(
                f"<div style='display:flex;align-items:center;margin:2px 0;'>"
                f"<span style='display:inline-block;width:14px;height:14px;"
                f"background-color:{cat.color};border-radius:3px;margin-right:6px;'></span>"
                f"<span style='font-size:0.85em;'>{cat.label}</span></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ENSO context — current-year ONI vs notable analog years (Year Compare
    # styling) with a mean ± SD envelope and the freshest weekly Niño 3.4 point.
    # ONI is a single global index (not per-departamento), so it sits below the
    # department map as country-wide context.
    oni_df = data.load_enso()
    if not oni_df.empty:
        st.subheader(i18n.t("enso_header"))
        available_enso_years = sorted(oni_df["year"].dropna().unique().tolist())
        el_nino_yrs = [y for y in NOTABLE_EL_NINO_YEARS if y in available_enso_years]
        la_nina_yrs = [y for y in NOTABLE_LA_NINA_YEARS if y in available_enso_years]

        eb1, eb2, eb3 = st.columns(3)
        if eb1.button(i18n.t("enso_btn_elnino"), key="enso_eln_btn"):
            st.session_state["enso_selected_years"] = el_nino_yrs
        if eb2.button(i18n.t("enso_btn_lanina"), key="enso_lan_btn"):
            st.session_state["enso_selected_years"] = la_nina_yrs
        if eb3.button(i18n.t("clear"), key="enso_clear_btn"):
            st.session_state["enso_selected_years"] = []

        # Default to no analog overlay — just the current year, envelope, and the
        # weekly point. Users add notable El Niño / La Niña years via the buttons.
        # The widget is driven entirely by session_state (initialised here and
        # updated by the buttons above), so it takes a `key` but NO `default=` —
        # passing both triggers Streamlit's "created with a default value but
        # also had its value set via the Session State API" warning.
        st.session_state.setdefault("enso_selected_years", [])
        st.session_state["enso_selected_years"] = [
            y
            for y in st.session_state["enso_selected_years"]
            if y in available_enso_years
        ]
        selected_enso = st.multiselect(
            i18n.t("years_overlay_label"),
            options=available_enso_years,
            key="enso_selected_years",
        )

        enso_analogs = {}
        for y in selected_enso:
            yr_df = oni_df[oni_df["year"] == y][["date", "oni"]].dropna(subset=["oni"])
            if not yr_df.empty:
                enso_analogs[y] = yr_df

        latest34 = data.latest_nino34()
        enso_fig = charts.enso_year_compare_figure(
            oni_df,
            today_,
            analogs=enso_analogs,
            latest_nino34=latest34,
        )
        st.plotly_chart(enso_fig, width="stretch", config=CHART_CFG)
        latest_oni = oni_df.sort_values("date").iloc[-1]
        cap = i18n.t(
            "enso_caption_latest",
            oni=f"{latest_oni['oni']:+.2f}",
            phase=i18n.phase_label(latest_oni["phase"]),
            date=i18n.fmt_mon_year(latest_oni["date"]),
        )
        if latest34:
            cap += i18n.t(
                "enso_caption_weekly",
                val=f"{latest34['nino34_ssta']:+.2f}",
                phase=i18n.phase_label(latest34["phase"]),
                date=i18n.fmt_day_mon_year(latest34["date"]),
            )
        cap += i18n.t("enso_caption_note")
        st.caption(cap)
        st.divider()

    panel_indicators = ["chirps", "smap", "wapor"]
    cols = st.columns(len(panel_indicators))
    for col, ind_name in zip(cols, panel_indicators):
        ind_cls = INDICATORS[ind_name]
        with col:
            st.markdown(f"**{INDICATOR_LABELS[ind_name]}**")
            ind_df = data.load_indicator(ind_name, departamento)
            if ind_df.empty:
                st.info(i18n.t("no_data"))
                continue
            primary = ind_cls.primary_column
            clim = data.load_climatology(ind_name, departamento, primary)
            window_start = pd.Timestamp(today_) - pd.Timedelta(days=365)
            current = ind_df[ind_df["date"] >= window_start][
                ["date", primary, "is_forecast"]
            ].dropna(subset=[primary])
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
            st.plotly_chart(fig, width="stretch", config=CHART_CFG)

            latest_z, latest_obs = status_view.current_status_value(
                ind_df,
                ind_cls.status_window_days,
                today_,
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
    st.subheader(
        i18n.t("detail_header", indicator=INDICATOR_LABELS[indicator_name], dep=departamento_label)
    )

    ind_df = data.load_indicator(indicator_name, departamento)
    if ind_df.empty:
        st.info(i18n.t("detail_no_data", dept=config.CC["dept_term"]))
    else:
        clim = data.load_climatology(indicator_name, departamento, primary)
        window_start = pd.Timestamp(today_) - pd.Timedelta(days=365)
        cur = ind_df[ind_df["date"] >= window_start][
            ["date", primary, "is_forecast"]
        ].dropna(subset=[primary])
        if not show_forecast:
            cur = cur[
                ~cur.get("is_forecast", pd.Series([False] * len(cur))).fillna(False)
            ]

        fig = charts.climatology_envelope_figure(
            title="",
            value_label=yaxis_label_for(primary),
            climatology=clim,
            current=cur,
            primary_column=primary,
            today_=today_,
            last_observation=freshness.last_observation_date(indicator_name),
        )
        st.plotly_chart(fig, width="stretch", config=CHART_CFG)

        # Plain-language status — averaged over the indicator's status window
        # of OBSERVED rows only (skips forecasts so the badge never reports a
        # 15-day-ahead projection as the current state).
        latest_z, latest_obs = status_view.current_status_value(
            ind_df,
            indicator_cls.status_window_days,
            today_,
        )
        cat = drought_status.classify(latest_z)
        st.markdown(f"### {i18n.t('current_status')}")
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

        with st.expander(i18n.t("tech_details")):
            st.write(
                i18n.t(
                    "tech_z",
                    z=f"{latest_z:.2f}"
                    if latest_z is not None and not pd.isna(latest_z)
                    else "—",
                )
            )
            st.write(i18n.t("tech_primary_col", col=primary))
            st.write(
                i18n.t(
                    "tech_baseline",
                    indicator=INDICATOR_LABELS[indicator_name],
                    baseline=baseline_for(indicator_name),
                )
            )

        # Climatology-smoothing caption + diagnostic mini-chart
        window = getattr(indicator_cls, "climatology_doy_window", 0)
        n_samples_str = ""
        if "n_samples" in clim.columns:
            med_n = int(clim["n_samples"].median())
            n_samples_str = i18n.t("clim_n_samples", n=med_n)
        if window > 0:
            st.caption(
                i18n.t(
                    "clim_caption_smoothed",
                    baseline=baseline_for(indicator_name),
                    window=window,
                    n_samples=n_samples_str,
                )
            )
        else:
            st.caption(i18n.t("clim_caption_plain", baseline=baseline_for(indicator_name)))


# ============= Tab 3 — Year Compare =============
with tabs[2]:
    primary = indicator_cls.primary_column
    st.subheader(
        i18n.t("compare_header", indicator=INDICATOR_LABELS[indicator_name], dep=departamento_label)
    )

    ind_df = data.load_indicator(indicator_name, departamento)
    if ind_df.empty:
        st.info(i18n.t("no_data"))
    else:
        clim = data.load_climatology(indicator_name, departamento, primary)
        available_years = sorted(ind_df["year"].dropna().unique().tolist())

        # Limit auto-selections to the notable analog years (instead of the ~20
        # years that strict ONI classification flags) so the chart stays legible.
        el_nino_yrs = [y for y in NOTABLE_EL_NINO_YEARS if y in available_years]
        la_nina_yrs = [y for y in NOTABLE_LA_NINA_YEARS if y in available_years]

        c1, c2, c3 = st.columns(3)
        if c1.button(i18n.t("enso_btn_elnino")):
            st.session_state["selected_years"] = el_nino_yrs
        if c2.button(i18n.t("enso_btn_lanina")):
            st.session_state["selected_years"] = la_nina_yrs
        if c3.button(i18n.t("clear")):
            st.session_state["selected_years"] = []
        st.caption(i18n.t("compare_caption"))

        # Filter the session-state selection against the currently-available
        # years — when the user switches indicators (e.g., CHIRPS → WAPOR)
        # the prior selection may include years that aren't in the new
        # indicator's history (WAPOR starts 2018, so 2015 from CHIRPS isn't
        # valid). Keep the multiselect's default in sync with the options.
        raw_default = st.session_state.get(
            "selected_years",
            [y for y in NOTABLE_EL_NINO_YEARS if y in available_years],
        )
        default_years = [y for y in raw_default if y in available_years]
        if default_years != raw_default:
            st.session_state["selected_years"] = default_years
        selected = st.multiselect(
            i18n.t("years_overlay_label"),
            options=available_years,
            default=default_years,
            key="selected_years",
        )

        analogs = {}
        for y in selected:
            yr_df = ind_df[ind_df["year"] == y][["date", primary]].dropna(
                subset=[primary]
            )
            if not yr_df.empty:
                analogs[y] = yr_df

        window_start = pd.Timestamp(today_) - pd.Timedelta(days=365)
        cur = ind_df[ind_df["date"] >= window_start][
            ["date", primary, "is_forecast"]
        ].dropna(subset=[primary])

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
        st.plotly_chart(fig, width="stretch", config=CHART_CFG)

# ---------- About this data ----------
with st.expander(i18n.t("about_title")):
    st.markdown(
        i18n.t(
            "about_body",
            chirps_days=INDICATORS["chirps"].freshness.expected_cadence_days,
            smap_days=INDICATORS["smap"].freshness.expected_cadence_days,
            wapor_days=INDICATORS["wapor"].freshness.expected_cadence_days,
            imerg_days=INDICATORS["imerg"].freshness.expected_cadence_days,
            clim_start=config.CLIMATOLOGY_START_YEAR,
            clim_end=config.CLIMATOLOGY_END_YEAR,
            country=config.CC["display_name"],
            country_key=config.COUNTRY,
        )
    )

# ---------- Site footer (attribution, data sources, GWU mark) ----------
site_footer.render()
