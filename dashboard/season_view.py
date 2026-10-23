"""The Overview's "This season" table: every departamento that fired this
season, kept until the season ends. Logic lives in etl/season.py; this module
only renders it. Between seasons it shows the last season's events — never
more than that one season — until the next season starts.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from .. import config
from ..etl import season
from . import i18n

ALERT_COLOR = "#c62828"
CONFIRMED_COLOR = "#7f0000"


@st.cache_data(ttl=300)
def _record(today_: date) -> season.SeasonRecord | None:
    return season.season_record(today_)


def _chip(d: date | None, color: str) -> str:
    if d is None:
        return "<span style='color:#90a4ae;'>—</span>"
    return (
        f"<span style='background-color:{color};color:white;padding:2px 10px;"
        f"border-radius:10px;font-size:0.85em;white-space:nowrap;'>{i18n.fmt_mon_day(d)}</span>"
    )


def _table(rec: season.SeasonRecord) -> str:
    has_confirm = bool(config.CC.get("confirm_rule"))
    head = [config.CC["dept_term"].capitalize(), i18n.t("season_col_alert")]
    if has_confirm:
        head.append(i18n.t("season_col_confirmed"))
    th = "".join(
        f"<th style='text-align:left;padding:6px 12px;border-bottom:2px solid #cfd8dc;"
        f"font-weight:600;color:#37474f;'>{h}</th>"
        for h in head
    )
    rows = []
    for e in rec.entries:
        cells = [e.departamento, _chip(e.alert_date, ALERT_COLOR)]
        if has_confirm:
            cells.append(_chip(e.confirmed_date, CONFIRMED_COLOR))
        rows.append("".join(
            f"<td style='padding:6px 12px;border-bottom:1px solid #eceff1;'>{c}</td>" for c in cells
        ))
    body = "".join(f"<tr>{r}</tr>" for r in rows)
    return (
        "<div style='overflow-x:auto;'><table style='border-collapse:collapse;width:100%;'>"
        f"<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _body(rec: season.SeasonRecord) -> None:
    if rec.entries:
        st.markdown(_table(rec), unsafe_allow_html=True)
    else:
        st.markdown(i18n.t("season_none", depts=config.CC["dept_term_plural"]))
    key = "season_caption" if config.CC.get("confirm_rule") else "season_caption_alert_only"
    st.caption(i18n.t(key, dept=config.CC["dept_term"]))


def render(today_: date) -> None:
    rec = _record(today_)
    if rec is None:
        return
    name = i18n.t(f"season_{rec.key}")
    span = f"{i18n.fmt_mon_day(rec.start)} – {i18n.fmt_mon_day(rec.end)}"
    key = "season_header_active" if rec.active else "season_header_ended"
    st.markdown(i18n.t(key, season=name, year=rec.year, span=span))
    _body(rec)
