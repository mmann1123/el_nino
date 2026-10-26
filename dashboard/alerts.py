"""Drought-alert summary panel.

Written for a non-technical audience. The panel sits at the bottom of the
Overview tab and shows:

  1. A current status pill (color-coded: green/amber/red).
  2. Plain-language explanation of when the alert activates.
  3. The two indicators it watches, with current readings and color cues.
  4. Two expanders: past triggered years, and a confidence read-out.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from .. import config
from ..etl import season, season_history, storage, triggers
from . import freshness, i18n


# ---------- color helpers ----------

GREEN  = "#2e7d32"   # clear
AMBER  = "#f9a825"   # watching / approaching
RED    = "#c62828"   # triggered / dry side of threshold
NEUTRAL = "#546e7a"  # pre-season / N/A


@dataclass
class CurrentReading:
    label: str           # "Rainfall (last 3 months)"
    plain_status: str    # "Wetter than usual" / "Slightly dry" / "Drought"
    value_text: str      # "+1.8" or "−1.7σ"
    color: str           # hex
    threshold_text: str  # "Triggered if below −1.5"


def _country_mean_latest(indicator: str, value_col: str) -> float | None:
    """Latest observed (non-forecast) country-mean of one column."""
    d = config.RAW_DIR / indicator
    if not d.exists():
        return None
    frames = []
    for f in d.glob("*.parquet"):
        df = storage.read_parquet(f)
        if df.empty or value_col not in df.columns:
            continue
        if "is_forecast" in df.columns:
            df = df[~df["is_forecast"].fillna(False)]
        if df.empty:
            continue
        frames.append(df[["date", value_col]])
    if not frames:
        return None
    pooled = pd.concat(frames, ignore_index=True)
    pooled["date"] = pd.to_datetime(pooled["date"])
    grouped = pooled.groupby("date")[value_col].mean().dropna()
    if grouped.empty:
        return None
    return float(grouped.iloc[-1])


def _stale_reading(label: str, threshold_text: str) -> CurrentReading:
    return CurrentReading(label, i18n.t("cat_stale_label"), "—", NEUTRAL, threshold_text)


def _spi_reading(threshold: float, column: str = "spi_3") -> CurrentReading:
    """Country-mean SPI on the same scale the trigger uses."""
    label = i18n.t("reading_rain_label" if column == "spi_3" else f"reading_rain_label_{column}")
    if freshness.is_stale("chirps", config.today()):
        return _stale_reading(label, i18n.t("reading_activates_below", thr=f"{threshold:+.1f}"))
    v = _country_mean_latest("chirps", column)
    return _make_reading(
        label=label,
        value=v,
        threshold=threshold,
        wet_text=i18n.t("reading_wet"),
        normal_text=i18n.t("reading_normal"),
        approaching_text=i18n.t("reading_approaching"),
        triggered_text=i18n.t("reading_triggered"),
        unit_suffix="",
        threshold_text=i18n.t("reading_activates_below", thr=f"{threshold:+.1f}"),
        sign_format=lambda x: f"{x:+.2f}",
    )


def _rzsm_reading(threshold: float) -> CurrentReading:
    if freshness.is_stale("smap", config.today()):
        return _stale_reading(i18n.t("reading_soil_label"),
                              i18n.t("reading_activates_below", thr=f"{threshold:+.1f}σ"))
    v = _country_mean_latest("smap", "value_anom_z")
    return _make_reading(
        label=i18n.t("reading_soil_label"),
        value=v,
        threshold=threshold,
        wet_text=i18n.t("reading_wet"),
        normal_text=i18n.t("reading_normal"),
        approaching_text=i18n.t("reading_approaching"),
        triggered_text=i18n.t("reading_triggered"),
        unit_suffix="σ",
        threshold_text=i18n.t("reading_activates_below", thr=f"{threshold:+.1f}σ"),
        sign_format=lambda x: f"{x:+.2f}σ",
    )


def _make_reading(*, label, value, threshold,
                  wet_text, normal_text, approaching_text, triggered_text,
                  unit_suffix, threshold_text, sign_format) -> CurrentReading:
    if value is None:
        return CurrentReading(label, i18n.t("reading_no_data"), "—", NEUTRAL, threshold_text)
    if value < threshold:
        # at or past the trigger threshold (drier than required for alert)
        return CurrentReading(label, triggered_text, sign_format(value), RED, threshold_text)
    # Define a "watching" zone within ~0.5 of threshold
    if value < threshold + 0.5:
        return CurrentReading(label, approaching_text, sign_format(value), AMBER, threshold_text)
    if value < 0:
        return CurrentReading(label, i18n.t("reading_slightly_dry"), sign_format(value), NEUTRAL, threshold_text)
    return CurrentReading(label, wet_text, sign_format(value), GREEN, threshold_text)


# ---------- main banner ----------

@st.cache_data(ttl=300)
def _status(today_: date) -> tuple[dict | None, season.SeasonSpan | None]:
    """Trigger state for the season on screen, so the banner resets on the
    same day as the season panel instead of on Jan 1."""
    span = season.current_span(today_)
    status = triggers.current_status(today_, span=span)
    if status is not None and span is not None and not span.active:
        # A closed, frozen season shows what the season panel shows.
        frozen = season_history.frozen_entries(span)
        if frozen is not None:
            status["fires_this_year"] = [
                {"departamento": e.departamento, "first_date": e.alert_date.isoformat(), "frozen": True}
                for e in frozen[0] if e.alert_date is not None
            ]
    return status, span


def rule_text(trig: triggers.CalibratedTrigger | None) -> str:
    """Short description of what fires a trigger, for captions."""
    if trig is None:
        return i18n.t("rule_short_rain_soil", rain=i18n.t("rain_short_spi_3"))
    rain = i18n.t(f"rain_short_{trig.spi_column}")
    key = "rule_short_rain" if trig.rzsm_threshold is None else "rule_short_rain_soil"
    return i18n.t(key, rain=rain)


def _condition_text(trig: triggers.CalibratedTrigger) -> str:
    rain = i18n.t(f"rain_{trig.spi_column}")
    key = "alert_cond_rain" if trig.rzsm_threshold is None else "alert_cond_rain_soil"
    return i18n.t(key, rain=rain)


def _provisional_text(trig: triggers.CalibratedTrigger) -> str:
    labels = config.season_cfg(trig.season)["labeled_events"]
    years = sorted(y for y, (sev, _) in labels.items() if sev not in ("normal", "excluded"))
    return i18n.t("alert_provisional", season=i18n.t(f"season_{trig.season}"),
                  n=len(years), years=", ".join(map(str, years)))


def banner() -> None:
    """Render the drought-alert summary. Designed for non-technical readers."""
    status, span = _status(config.today())
    if status is None:
        if span is not None and triggers.CALIBRATED_TRIGGERS:
            # Another season has an alert; this one isn't calibrated yet.
            st.markdown(i18n.t("alert_header"))
            st.info(i18n.t("alert_not_calibrated_season",
                           season=i18n.t(f"season_{span.key}"), year=span.year))
        else:
            st.info(i18n.t("alert_not_calibrated"))
        return
    trig = status["trigger"]
    today = status["today"]
    triggered_this_year = status["fires_this_year"]
    past_triggered = status["fires_history"]

    window_start_label = i18n.fmt_mon_day(status["window_start"])
    window_end_label = i18n.fmt_mon_day(status["window_end"])

    # Section header
    st.markdown(i18n.t("alert_header"))

    # ---- status pill ----
    n_fired = len({f['departamento'] for f in triggered_this_year})
    dep_word = i18n.dept_term(plural=True) if n_fired != 1 else i18n.dept_term()
    season_over = span is not None and not span.active
    if triggered_this_year and not season_over:
        pill_bg, pill_label, pill_sub = RED, i18n.t("alert_pill_alert"), \
            i18n.t("alert_pill_alert_sub", n=n_fired, dep_word=dep_word)
    elif triggered_this_year:
        # The season it fired in is over: a recap, not a live alert.
        pill_bg, pill_label, pill_sub = NEUTRAL, i18n.t("alert_pill_ended"), \
            i18n.t("alert_pill_ended_sub", n=n_fired, dep_word=dep_word,
                   season=i18n.t(f"season_{span.key}"), year=span.year)
    elif status["window_active"]:
        pill_bg, pill_label, pill_sub = AMBER, i18n.t("alert_pill_watching"), \
            i18n.t("alert_pill_watching_sub", start=window_start_label, end=window_end_label)
    elif status["window_passed"]:
        pill_bg, pill_label, pill_sub = GREEN, i18n.t("alert_pill_clear"), \
            i18n.t("alert_pill_clear_sub", year=span.year if span else today.year)
    else:
        days_until = (status["window_start"] - today).days
        pill_bg, pill_label, pill_sub = NEUTRAL, i18n.t("alert_pill_pre"), \
            i18n.t("alert_pill_pre_sub", days=days_until, start=window_start_label)

    st.markdown(
        f"<div style='background-color:{pill_bg};color:white;"
        "padding:14px 18px;border-radius:8px;margin-bottom:12px;'>"
        f"<div style='font-size:0.85em;opacity:0.85;text-transform:uppercase;letter-spacing:0.5px;'>"
        f"{i18n.t('current_status')}</div>"
        f"<div style='font-weight:700;font-size:1.25em;margin-top:2px;'>{pill_label}</div>"
        f"<div style='font-size:0.95em;margin-top:4px;opacity:0.92;'>{pill_sub}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if trig.provisional:
        st.caption(_provisional_text(trig))

    # ---- current readings: the indicators this trigger actually uses ----
    readings = [_spi_reading(trig.spi3_threshold, trig.spi_column)]
    if trig.rzsm_threshold is not None:
        readings.append(_rzsm_reading(trig.rzsm_threshold))

    st.markdown(i18n.t("alert_right_now"))
    for col, r in zip(st.columns(2), readings):
        with col:
            st.markdown(
                f"<div style='border-left:6px solid {r.color};"
                "padding:8px 14px;background-color:#fafafa;border-radius:4px;margin-bottom:6px;'>"
                f"<div style='font-size:0.8em;color:#546e7a;'>{r.label}</div>"
                f"<div style='font-size:1.3em;font-weight:700;color:{r.color};margin-top:2px;'>{r.value_text}</div>"
                f"<div style='font-size:0.9em;color:#37474f;margin-top:2px;'>{r.plain_status}</div>"
                f"<div style='font-size:0.75em;color:#90a4ae;margin-top:4px;'>{r.threshold_text}</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    # ---- plain-language explanation ----
    st.markdown(
        i18n.t(
            "alert_explain",
            condition=_condition_text(trig),
            start=window_start_label,
            end=window_end_label,
            country=config.CC["display_name"],
            priority=i18n.priority_label().lower(),
            names=config.CC["priority_display_names"],
        )
    )

    # ---- triggered-this-year details ----
    if triggered_this_year:
        with st.expander(
            i18n.t("alert_show_triggered", depts=i18n.dept_term(plural=True)),
            expanded=not season_over,
        ):
            if not any(f.get("frozen") for f in triggered_this_year):
                st.caption(i18n.t("alert_scores_note"))
            for f in sorted(triggered_this_year, key=lambda r: r["departamento"]):
                st.markdown(_fire_row(f))

    # ---- confidence expander (now also contains the past-triggered history) ----
    if trig.stats is not None or past_triggered:
        if trig.stats is not None:
            s = trig.stats
            heading = i18n.t("alert_confidence_heading", n=s.n_years)
        else:
            heading = i18n.t("alert_history_heading")

        with st.expander(heading):
            if trig.stats is not None:
                # Pull the severe anchor years from the country's labeled
                # events so the descriptive copy stays in sync with config.
                severe_yrs = sorted(
                    y for y, (sev, _) in config.season_cfg(trig.season)["labeled_events"].items()
                    if sev.startswith("severe")
                )
                if severe_yrs:
                    severe_anchor = i18n.t("alert_eg", years=", ".join(str(y) for y in severe_yrs))
                else:
                    severe_anchor = ""
                st.markdown(
                    i18n.t(
                        "alert_confidence_body",
                        precision=f"{s.precision:.0%}",
                        precision_lo=f"{s.precision_ci[0]:.0%}",
                        precision_hi=f"{s.precision_ci[1]:.0%}",
                        recall=f"{s.recall:.0%}",
                        recall_lo=f"{s.recall_ci[0]:.0%}",
                        recall_hi=f"{s.recall_ci[1]:.0%}",
                        severe=_pct(s.severe_recall),
                        severe_lo=_pct(s.severe_recall_ci[0]),
                        severe_hi=_pct(s.severe_recall_ci[1]),
                        fp=f"{s.fp_per_decade:.1f}",
                        fp_lo=f"{s.fp_per_decade_ci[0]:.1f}",
                        fp_hi=f"{s.fp_per_decade_ci[1]:.1f}",
                        anchor=severe_anchor,
                        country=config.CC["display_name"],
                        dept=i18n.dept_term(),
                        n_years=s.n_years,
                        country_key=config.COUNTRY,
                    )
                )

            # Past triggered-years history (moved here from its own expander
            # so users get one consolidated "track record" section).
            if past_triggered:
                by_year: dict[int, list[str]] = defaultdict(list)
                for f in past_triggered:
                    by_year[f["year"]].append(f["departamento"])
                years_summary = ", ".join(str(y) for y in sorted(by_year, reverse=True))
                st.markdown(
                    i18n.t("alert_past_years", n=len(by_year), years=years_summary)
                )
                for y in sorted(by_year, reverse=True):
                    deps = sorted(by_year[y])
                    dep_word = i18n.dept_term(plural=True) if len(deps) != 1 else i18n.dept_term()
                    st.markdown(
                        i18n.t(
                            "alert_past_row",
                            year=y, n=len(deps), dep_word=dep_word, deps=", ".join(deps),
                        )
                    )


def _pct(x: float) -> str:
    """A proportion as a percentage; "—" when undefined (no severe label)."""
    return "—" if x != x else f"{x:.0%}"


def _fire_row(f: dict) -> str:
    """One triggered department, with the values that apply to it."""
    date_ = i18n.fmt_day_mon_year(f.get("first_date") or f.get("fire_date"))
    if f.get("frozen"):
        return i18n.t("alert_triggered_row_frozen", dep=f["departamento"], date=date_)
    rzsm = f.get("rzsm_min_z")
    if rzsm is None:
        return i18n.t("alert_triggered_row_rain", dep=f["departamento"],
                      spi=f"{f['spi3_min']:.2f}", date=date_)
    return i18n.t("alert_triggered_row", dep=f["departamento"], spi=f"{f['spi3_min']:.2f}",
                  rzsm=f"{rzsm:.2f}", date=date_)
