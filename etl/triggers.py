"""Trigger evaluation. Thresholds are placeholders until the calibration
experiment (el_nino/experiments/trigger_calibration.ipynb) lands and the
report fixes them. Until then the dashboard renders the drought-status badge
purely from per-DOY anomaly z-scores; no email/Slack dispatch fires.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Trigger:
    name: str
    window_doy: tuple[int, int]
    conditions: list[tuple[str, str, float]] = field(default_factory=list)
    severity: str = "medium"


# Placeholders — DO NOT USE FOR ALERTS YET. Pending calibration.
PLACEHOLDER_TRIGGERS: list[Trigger] = [
    Trigger(
        name="silking_drought_trigger",
        window_doy=(196, 227),  # mid-Jul to mid-Aug
        conditions=[
            ("spi_3", "<", -1.0),
            ("rzsm_anom_z", "<", -1.0),
        ],
        severity="high",
    ),
]


def evaluate(latest: pd.DataFrame, triggers: list[Trigger] = PLACEHOLDER_TRIGGERS) -> list[dict]:
    """Return list of fired-trigger records: [{trigger, departamento, date, conditions_met}]"""
    fires: list[dict] = []
    if latest.empty:
        return fires

    latest = latest.copy()
    latest["date"] = pd.to_datetime(latest["date"])
    latest["doy"] = latest["date"].dt.dayofyear

    for trig in triggers:
        in_window = latest[(latest["doy"] >= trig.window_doy[0]) & (latest["doy"] <= trig.window_doy[1])]
        for _, row in in_window.iterrows():
            ok = all(_check(row, col, op, thr) for col, op, thr in trig.conditions)
            if ok:
                fires.append({
                    "trigger": trig.name,
                    "departamento": row["departamento"],
                    "date": row["date"].date().isoformat(),
                    "severity": trig.severity,
                    "values": {col: row.get(col) for col, _, _ in trig.conditions},
                })
    return fires


def _check(row: pd.Series, col: str, op: str, thr: float) -> bool:
    val = row.get(col)
    if pd.isna(val):
        return False
    if op == "<":
        return val < thr
    if op == ">":
        return val > thr
    if op == "<=":
        return val <= thr
    if op == ">=":
        return val >= thr
    return False
