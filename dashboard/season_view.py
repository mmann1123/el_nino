"""The Overview's season panels: every departamento that fired in the season
on screen, kept until the season ends, with the previous season below it.
Confirmed ones get their own highlighted box; alert-only ones collapse into a
single line. Logic lives in etl/season.py; this module
only renders it. Between seasons it shows the last season's events — never
more than that one season — until the next season starts.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ..etl import season, triggers
from . import alerts, i18n

ALERT_COLOR = "#c62828"
CONFIRMED_COLOR = "#7f0000"


@st.cache_data(ttl=300)
def _record(today_: date) -> season.SeasonRecord | None:
    return season.season_record(today_)


def _chip(label: str, color: str) -> str:
    return (
        f"<span style='background-color:{color};color:white;padding:2px 10px;"
        f"border-radius:10px;font-size:0.85em;white-space:nowrap;'>{label}</span>"
    )


def _split(entries: list[season.SeasonEntry]) -> tuple[list[season.SeasonEntry], list[season.SeasonEntry]]:
    """(confirmed, alert-only), confirmed ordered by the dekad that confirmed it."""
    confirmed = sorted((e for e in entries if e.confirmed_date),
                       key=lambda e: (e.confirmed_date, e.departamento))
    alert_only = [e for e in entries if not e.confirmed_date]
    return confirmed, alert_only


def _confirmed_box(confirmed: list[season.SeasonEntry]) -> str:
    rows = []
    for e in confirmed:
        alert = (
            f"<span style='color:#78909c;'>{i18n.t('season_row_alert', date=i18n.fmt_mon_day(e.alert_date))}"
            " &rarr; </span>" if e.alert_date else ""
        )
        # The dekad whose data confirmed it, not just its start date.
        dekad = _chip(i18n.fmt_day_range(e.confirmed_date, e.confirmed_end), CONFIRMED_COLOR)
        rows.append(
            "<div style='display:flex;flex-wrap:wrap;gap:4px 16px;padding:5px 0;"
            "border-top:1px solid #f3d6d6;'>"
            f"<span style='font-weight:600;min-width:9em;'>{e.departamento}</span>"
            f"<span>{alert}{i18n.t('season_row_confirmed')} {dekad}</span></div>"
        )
    return (
        f"<div style='border:2px solid {CONFIRMED_COLOR};border-radius:8px;background:#fdf1f1;"
        "padding:8px 14px;margin-bottom:10px;'>"
        f"<div style='font-weight:700;color:{CONFIRMED_COLOR};padding-bottom:4px;'>"
        f"&#9632; {i18n.t('season_confirmed_header', n=len(confirmed))}</div>"
        f"{''.join(rows)}</div>"
    )


def _alert_line(alert_only: list[season.SeasonEntry], has_confirm: bool) -> str:
    label = i18n.t("season_alert_only_label" if has_confirm else "season_alert_label")
    dates = {e.alert_date for e in alert_only}
    if len(dates) == 1:
        # One shared start date: say it once instead of on every name.
        lead = i18n.t("season_alert_since", label=label,
                      date=i18n.fmt_mon_day(dates.pop()), n=len(alert_only))
        names = [e.departamento for e in alert_only]
    else:
        lead = i18n.t("season_alert_group", label=label, n=len(alert_only))
        names = [f"{e.departamento} <span style='color:#78909c;'>{i18n.fmt_mon_day(e.alert_date)}</span>"
                 for e in alert_only]
    return (
        f"<div style='padding:2px 2px 6px;'><span style='color:{ALERT_COLOR};font-weight:600;'>"
        f"&#9650; {lead}</span> {' &middot; '.join(names)}</div>"
    )


def _layout(rec: season.SeasonRecord) -> str:
    has_confirm = rec.has_confirm
    confirmed, alert_only = _split(rec.entries)
    parts = []
    if confirmed:
        parts.append(_confirmed_box(confirmed))
    if alert_only:
        parts.append(_alert_line(alert_only, has_confirm))
    return "".join(parts)


def _body(rec: season.SeasonRecord) -> None:
    if rec.entries:
        st.markdown(_layout(rec), unsafe_allow_html=True)
    else:
        st.markdown(i18n.t("season_none", depts=i18n.dept_term(plural=True)))
    key = "season_caption" if rec.has_confirm else "season_caption_alert_only"
    st.caption(i18n.t(key, dept=i18n.dept_term(), rule=alerts.rule_text(triggers.trigger_for(rec.key))))


def _season(rec: season.SeasonRecord, header_key: str) -> None:
    name = i18n.t(f"season_{rec.key}")
    span = f"{i18n.fmt_mon_day(rec.start)} – {i18n.fmt_mon_day(rec.end)}"
    st.markdown(i18n.t(header_key, season=name, year=rec.year, span=span))
    _body(rec)


def render(today_: date) -> None:
    """The season on screen, then the one before it. Each keeps its own
    departments: nothing carries over from one season to the next."""
    rec = _record(today_)
    if rec is None:
        return
    _season(rec, "season_header_active" if rec.active else "season_header_ended")
    if rec.previous is not None:
        _season(rec.previous, "season_header_previous")
