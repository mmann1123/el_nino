"""Alert banner for the Overview tab. Reads the calibrated trigger state and
renders an inline summary:

  - This year's fires (if any) — red, prominent
  - Window status (upcoming / active / cleared)
  - Historical fire-year summary
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import streamlit as st

from ..etl import triggers


def banner() -> None:
    status = triggers.current_status()
    trig = status["trigger"]
    today = status["today"]
    window_start_label = _doy_to_label(trig.window_doy[0], today.year)
    window_end_label = _doy_to_label(trig.window_doy[1], today.year)
    fires_this_year = status["fires_this_year"]

    # 1) This-year alert (red) — highest priority.
    if fires_this_year:
        deps = sorted({f["departamento"] for f in fires_this_year})
        with st.container():
            st.markdown(
                f"<div style='background-color:#c62828;color:white;padding:14px 18px;"
                "border-radius:8px;margin-bottom:8px;'>"
                f"<div style='font-weight:700;font-size:1.1em;'>"
                f"🚨 Active drought trigger — {today.year}</div>"
                f"<div style='margin-top:4px;'>{trig.description}</div>"
                f"<div style='margin-top:6px;font-size:0.95em;'>"
                f"Fired in <b>{len(deps)}</b> departamento{'s' if len(deps) != 1 else ''}: {', '.join(deps)}"
                f"</div></div>",
                unsafe_allow_html=True,
            )
            with st.expander("Show fire details"):
                for f in sorted(fires_this_year, key=lambda r: r["departamento"]):
                    st.markdown(
                        f"- **{f['departamento']}** — SPI-3 min `{f['spi3_min']:.2f}`, "
                        f"SMAP RZSM `{f['rzsm_min_z']:.2f}σ` on {f['fire_date']}"
                    )
        return

    # 2) Window status — neutral colors.
    doy = status["doy"]
    if status["window_active"]:
        status_text = (
            f"🟡 Silking window is currently active "
            f"(DOY {trig.window_doy[0]}-{trig.window_doy[1]}, "
            f"{window_start_label}–{window_end_label}). "
            f"No trigger has fired yet for {today.year}."
        )
        bg = "#f9a825"
    elif status["window_passed"]:
        status_text = (
            f"✅ {today.year} silking window cleared without trigger firing. "
            f"Next watch: postrera, then {today.year + 1} silking starting {window_start_label}."
        )
        bg = "#2e7d32"
    else:
        days_until = trig.window_doy[0] - doy
        status_text = (
            f"⏳ Pre-season: trigger watch starts in {days_until} days "
            f"({window_start_label}, DOY {trig.window_doy[0]})."
        )
        bg = "#546e7a"

    st.markdown(
        f"<div style='background-color:{bg};color:white;padding:12px 16px;"
        "border-radius:8px;margin-bottom:8px;font-size:0.95em;'>"
        f"<b>Alert trigger:</b> {trig.description}<br>{status_text}"
        "</div>",
        unsafe_allow_html=True,
    )

    # 2b) Calibration stats with 95% CIs — makes the small-sample uncertainty
    # visible so nobody mistakes "precision 1.00" for "definitely never wrong."
    if trig.stats is not None:
        s = trig.stats
        with st.expander(f"How confident is this trigger? (calibrated on {s.n_years} years of SMAP data)"):
            st.markdown(
                f"""
                Calibrated against labeled El Niño impact years from
                [el_nino_agricultural_risks.md](el_nino/el_nino_agricultural_risks.md).
                95% intervals are shown alongside point estimates — they are
                wide because the calibration set is small.

                | Metric | Point estimate | 95% CI |
                |---|---:|---:|
                | **Precision** — when the trigger fires, fraction that match a labeled impact year | {s.precision:.2f} | [{s.precision_ci[0]:.2f}–{s.precision_ci[1]:.2f}] |
                | **Recall** — fraction of labeled impact years that the trigger catches | {s.recall:.2f} | [{s.recall_ci[0]:.2f}–{s.recall_ci[1]:.2f}] |
                | **Severe recall** — fraction of catastrophic events (e.g. 2015) that the trigger catches | {s.severe_recall:.2f} | [{s.severe_recall_ci[0]:.2f}–{s.severe_recall_ci[1]:.2f}] |
                | **False positives per decade** — fires in years without labeled impact | {s.fp_per_decade:.2f} | [{s.fp_per_decade_ci[0]:.2f}–{s.fp_per_decade_ci[1]:.2f}] |

                **How to read these intervals.** Wilson score interval for proportions,
                Garwood exact Poisson for the FP rate. Wide intervals mean we don't
                have enough data to rule out worse performance — re-run
                `python -m el_nino.experiments.trigger_calibration` annually to tighten them
                as more SMAP years accumulate.

                **Caveats.** Labels are drawn from a published narrative
                document, not an exhaustive ground-truth crop-yield series. Years not
                discussed in the source were treated as negatives — some may be
                undocumented impact years, which would lower the apparent precision.
                """,
                unsafe_allow_html=False,
            )

    # 3) Historical fire-year summary (always shown, collapsed)
    fires_hist = status["fires_history"]
    if fires_hist:
        by_year: dict[int, list[str]] = defaultdict(list)
        for f in fires_hist:
            by_year[f["year"]].append(f["departamento"])
        with st.expander(
            f"📜 Past fire years on record: {len(by_year)} ({', '.join(str(y) for y in sorted(by_year, reverse=True))})"
        ):
            for y in sorted(by_year, reverse=True):
                deps = sorted(by_year[y])
                st.markdown(
                    f"- **{y}** — {len(deps)} departamento{'s' if len(deps) != 1 else ''}: "
                    f"{', '.join(deps)}"
                )


def _doy_to_label(doy: int, year: int) -> str:
    from datetime import datetime, timedelta
    d = datetime(year, 1, 1) + timedelta(days=int(doy) - 1)
    return d.strftime("%b %d")
