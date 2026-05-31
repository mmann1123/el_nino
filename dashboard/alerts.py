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
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from .. import config
from ..etl import storage, triggers


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


def _spi3_reading(threshold: float) -> CurrentReading:
    v = _country_mean_latest("chirps", "spi_3")
    return _make_reading(
        label="Rainfall (last 3 months)",
        value=v,
        threshold=threshold,
        wet_text="Wetter than usual",
        normal_text="Near normal",
        approaching_text="Drier than usual",
        triggered_text="Very dry — at or past alert level",
        unit_suffix="",
        threshold_text=f"Activates if below {threshold:+.1f}",
        sign_format=lambda x: f"{x:+.2f}",
    )


def _rzsm_reading(threshold: float) -> CurrentReading:
    v = _country_mean_latest("smap", "value_anom_z")
    return _make_reading(
        label="Soil moisture (root-zone)",
        value=v,
        threshold=threshold,
        wet_text="Wetter than usual",
        normal_text="Near normal",
        approaching_text="Drier than usual",
        triggered_text="Very dry — at or past alert level",
        unit_suffix="σ",
        threshold_text=f"Activates if below {threshold:+.1f}σ",
        sign_format=lambda x: f"{x:+.2f}σ",
    )


def _make_reading(*, label, value, threshold,
                  wet_text, normal_text, approaching_text, triggered_text,
                  unit_suffix, threshold_text, sign_format) -> CurrentReading:
    if value is None:
        return CurrentReading(label, "No data yet", "—", NEUTRAL, threshold_text)
    if value < threshold:
        # at or past the trigger threshold (drier than required for alert)
        return CurrentReading(label, triggered_text, sign_format(value), RED, threshold_text)
    # Define a "watching" zone within ~0.5 of threshold
    if value < threshold + 0.5:
        return CurrentReading(label, approaching_text, sign_format(value), AMBER, threshold_text)
    if value < 0:
        return CurrentReading(label, "Slightly drier than usual", sign_format(value), NEUTRAL, threshold_text)
    return CurrentReading(label, wet_text, sign_format(value), GREEN, threshold_text)


# ---------- main banner ----------

def banner() -> None:
    """Render the drought-alert summary. Designed for non-technical readers."""
    status = triggers.current_status()
    if status is None:
        st.info(
            "Drought alert thresholds are not yet calibrated for this country. "
            "Run `COUNTRY=<key> python -m el_nino.experiments.trigger_calibration` "
            "and bake the recommended config into `etl/triggers.py`."
        )
        return
    trig = status["trigger"]
    today = status["today"]
    triggered_this_year = status["fires_this_year"]
    past_triggered = status["fires_history"]

    window_start_label = _doy_to_label(trig.window_doy[0], today.year)
    window_end_label = _doy_to_label(trig.window_doy[1], today.year)

    # Section header
    st.markdown("### Drought alert")

    # ---- status pill ----
    n_fired = len({f['departamento'] for f in triggered_this_year})
    dep_word = "department" + ("s" if n_fired != 1 else "")
    if triggered_this_year:
        pill_bg, pill_label, pill_sub = RED, "ALERT — drought conditions met", \
            f"Triggered in {n_fired} {dep_word} so far this year"
    elif status["window_active"]:
        pill_bg, pill_label, pill_sub = AMBER, "Watching closely", \
            f"Critical growth weeks are happening now ({window_start_label}–{window_end_label})"
    elif status["window_passed"]:
        pill_bg, pill_label, pill_sub = GREEN, "All clear for this year's growing season", \
            f"The {today.year} critical window passed without the alert triggering."
    else:
        days_until = trig.window_doy[0] - today.timetuple().tm_yday
        pill_bg, pill_label, pill_sub = NEUTRAL, "Pre-season — quiet for now", \
            f"Critical growth weeks start in {days_until} days ({window_start_label})."

    st.markdown(
        f"<div style='background-color:{pill_bg};color:white;"
        "padding:14px 18px;border-radius:8px;margin-bottom:12px;'>"
        f"<div style='font-size:0.85em;opacity:0.85;text-transform:uppercase;letter-spacing:0.5px;'>"
        "Current status</div>"
        f"<div style='font-weight:700;font-size:1.25em;margin-top:2px;'>{pill_label}</div>"
        f"<div style='font-size:0.95em;margin-top:4px;opacity:0.92;'>{pill_sub}</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- current readings ----
    spi3 = _spi3_reading(trig.spi3_threshold)
    rzsm = _rzsm_reading(trig.rzsm_threshold)

    st.markdown("**Right now (country-wide):**")
    c1, c2 = st.columns(2)
    for col, r in zip((c1, c2), (spi3, rzsm)):
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
        f"**What sets off this alert.** When rainfall has been **very dry for "
        f"the last 3 months** *and* **soil moisture is below normal**, all at "
        f"the same time during the critical growth window "
        f"(**{window_start_label} to {window_end_label}**). This is when "
        f"rainfed crops in {config.CC['display_name']} are most vulnerable to "
        f"drought — water stress during this window translates directly into "
        f"yield loss in the {config.CC['priority_label'].lower()} "
        f"({config.CC['priority_display_names']})."
    )

    # ---- triggered-this-year details ----
    if triggered_this_year:
        with st.expander("Show triggered departments", expanded=True):
            for f in sorted(triggered_this_year, key=lambda r: r["departamento"]):
                st.markdown(
                    f"- **{f['departamento']}** — rainfall index `{f['spi3_min']:.2f}`, "
                    f"soil moisture `{f['rzsm_min_z']:.2f}σ`, on {f['fire_date']}"
                )

    # ---- confidence expander (now also contains the past-triggered history) ----
    if trig.stats is not None or past_triggered:
        if trig.stats is not None:
            s = trig.stats
            heading = f"How confident is this alert? (based on {s.n_years} years of data)"
        else:
            heading = "Past years this alert triggered"

        with st.expander(heading):
            if trig.stats is not None:
                # Pull the severe anchor years from the country's labeled
                # events so the descriptive copy stays in sync with config.
                severe_yrs = sorted(
                    y for y, (sev, _) in config.CC.get("labeled_events", {}).items()
                    if sev.startswith("severe")
                )
                if severe_yrs:
                    severe_anchor = "(e.g., " + ", ".join(str(y) for y in severe_yrs) + ")"
                else:
                    severe_anchor = ""
                st.markdown(
                    f"""
                    | Metric | Estimate | 95% range |
                    |---|---:|---:|
                    | When triggered, how often there was a real drought event | {s.precision:.0%} | {s.precision_ci[0]:.0%} – {s.precision_ci[1]:.0%} |
                    | Fraction of drought years the alert catches | {s.recall:.0%} | {s.recall_ci[0]:.0%} – {s.recall_ci[1]:.0%} |
                    | Fraction of *severe* drought years caught {severe_anchor} | {s.severe_recall:.0%} | {s.severe_recall_ci[0]:.0%} – {s.severe_recall_ci[1]:.0%} |
                    | False alarms per decade | {s.fp_per_decade:.1f} | {s.fp_per_decade_ci[0]:.1f} – {s.fp_per_decade_ci[1]:.1f} |

                    Thresholds were chosen by checking which would have flagged
                    the documented El Niño drought years for
                    {config.CC['display_name']} {severe_anchor} without firing
                    in normal years. The fire test runs **per department** —
                    if any one of the {config.CC['priority_label'].lower()}
                    ({config.CC['priority_display_names']}) crosses both
                    thresholds, the alert is raised. With only {s.n_years}
                    years of soil-moisture data, the margin of error is still
                    wide. Re-run `COUNTRY={config.COUNTRY} python -m
                    el_nino.experiments.trigger_calibration` annually as more
                    data accumulates.
                    """
                )

            # Past triggered-years history (moved here from its own expander
            # so users get one consolidated "track record" section).
            if past_triggered:
                by_year: dict[int, list[str]] = defaultdict(list)
                for f in past_triggered:
                    by_year[f["year"]].append(f["departamento"])
                years_summary = ", ".join(str(y) for y in sorted(by_year, reverse=True))
                st.markdown(
                    f"**📜 Past years this alert triggered: {len(by_year)} "
                    f"({years_summary})**"
                )
                for y in sorted(by_year, reverse=True):
                    deps = sorted(by_year[y])
                    dep_word = "department" + ("s" if len(deps) != 1 else "")
                    st.markdown(
                        f"- **{y}** — {len(deps)} {dep_word}: "
                        f"{', '.join(deps)}"
                    )


def _doy_to_label(doy: int, year: int) -> str:
    d = datetime(year, 1, 1) + timedelta(days=int(doy) - 1)
    return d.strftime("%b %d")
