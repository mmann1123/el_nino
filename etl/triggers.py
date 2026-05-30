"""Calibrated runtime trigger evaluator.

TODO(haiti-calibration): silking window and thresholds below are calibrated to
El Salvador maize. When COUNTRY=haiti these values still fire but reflect ES
phenology, not Haiti's printemps/été/automne seasons. Follow-up PR will define
country-specific trigger configurations.

Operating point from `el_nino/experiments/trigger_calibration_report.md`:

    SPI-3 < -1.5 AND SMAP root-zone soil moisture anomaly < -0.5σ
    during the silking window (DOY 196-227, mid-Jul to mid-Aug)

Performance against the labeled record (2015-2025):
    Precision: 1.00 (no false positives in 11 years)
    Recall:    0.67 (catches 2015 severe + 2018 moderate)
    Severe recall: 1.00 (catches the 2015 catastrophic event)
    False positives per decade: 0.00

For each departamento and each year of overlap (CHIRPS 1981+, SMAP 2015+),
the evaluator records whether both conditions were met during silking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from .. import config
from . import storage

SILKING_WINDOW = (196, 227)  # mid-July to mid-August


@dataclass
class CalibrationStats:
    """Calibration metrics for this trigger configuration, with 95% CIs.

    Populated from el_nino/experiments/trigger_calibration_report.md. CIs are
    Wilson score for proportions, Garwood exact Poisson for the FP rate.
    """
    n_years: int          # years used for calibration (SMAP overlap window)
    precision: float
    precision_ci: tuple[float, float]
    recall: float
    recall_ci: tuple[float, float]
    severe_recall: float
    severe_recall_ci: tuple[float, float]
    fp_per_decade: float
    fp_per_decade_ci: tuple[float, float]


@dataclass
class CalibratedTrigger:
    name: str
    description: str
    window_doy: tuple[int, int]
    spi3_threshold: float
    rzsm_threshold: float
    severity: str
    stats: CalibrationStats | None = None


# Calibration numbers below are from the 2025-05 sweep over 2015-2025 SMAP data.
# Re-run `python -m el_nino.experiments.trigger_calibration` after every annual
# data refresh to update them.
CALIBRATED_TRIGGERS: list[CalibratedTrigger] = [
    CalibratedTrigger(
        name="silking_drought_v1",
        description=(
            "SPI-3 < −1.5 AND SMAP root-zone anomaly < −0.5σ during silking "
            "(DOY 196-227, mid-Jul to mid-Aug)"
        ),
        window_doy=SILKING_WINDOW,
        spi3_threshold=-1.5,
        rzsm_threshold=-0.5,
        severity="high",
        stats=CalibrationStats(
            n_years=11,
            precision=1.00,    precision_ci=(0.34, 1.00),
            recall=0.67,       recall_ci=(0.21, 0.94),
            severe_recall=1.00, severe_recall_ci=(0.21, 1.00),
            fp_per_decade=0.00, fp_per_decade_ci=(0.00, 4.61),
        ),
    ),
]


@dataclass
class FireRecord:
    trigger_name: str
    severity: str
    year: int
    departamento: str
    fire_date: date | None
    spi3_min: float
    rzsm_min_z: float

    def to_dict(self) -> dict:
        return {
            "trigger_name": self.trigger_name,
            "severity": self.severity,
            "year": self.year,
            "departamento": self.departamento,
            "fire_date": self.fire_date.isoformat() if self.fire_date else None,
            "spi3_min": float(self.spi3_min),
            "rzsm_min_z": float(self.rzsm_min_z),
        }


def _load_per_dep(indicator: str, col: str) -> dict[str, pd.DataFrame]:
    """Load the per-departamento series for a given indicator/column."""
    out: dict[str, pd.DataFrame] = {}
    indicator_dir = config.RAW_DIR / indicator
    if not indicator_dir.exists():
        return out
    for parquet in indicator_dir.glob("*.parquet"):
        df = storage.read_parquet(parquet)
        if df.empty or col not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["doy"] = df["date"].dt.dayofyear
        dep = df["departamento"].iloc[0]
        out[dep] = df[["date", "year", "doy", col]].rename(columns={col: "value"})
    return out


def evaluate_history(trigger: CalibratedTrigger = CALIBRATED_TRIGGERS[0]) -> list[FireRecord]:
    """Return one FireRecord per (year, departamento) where the trigger fired.
    Limited to years where both indicators have data overlapping the window.
    """
    spi = _load_per_dep("chirps", "spi_3")
    rzsm = _load_per_dep("smap", "value_anom_z")

    fires: list[FireRecord] = []
    for dep, spi_df in spi.items():
        rzsm_df = rzsm.get(dep)
        if rzsm_df is None or rzsm_df.empty:
            continue
        years = sorted(set(spi_df["year"]) & set(rzsm_df["year"]))
        for year in years:
            spi_window = spi_df[(spi_df["year"] == year) &
                                (spi_df["doy"] >= trigger.window_doy[0]) &
                                (spi_df["doy"] <= trigger.window_doy[1])]
            rzsm_window = rzsm_df[(rzsm_df["year"] == year) &
                                  (rzsm_df["doy"] >= trigger.window_doy[0]) &
                                  (rzsm_df["doy"] <= trigger.window_doy[1])]
            if spi_window.empty or rzsm_window.empty:
                continue
            spi_min = spi_window["value"].min()
            rzsm_min = rzsm_window["value"].min()
            if pd.isna(spi_min) or pd.isna(rzsm_min):
                continue
            if spi_min < trigger.spi3_threshold and rzsm_min < trigger.rzsm_threshold:
                spi_min_row = spi_window.loc[spi_window["value"].idxmin()]
                fires.append(FireRecord(
                    trigger_name=trigger.name,
                    severity=trigger.severity,
                    year=int(year),
                    departamento=dep,
                    fire_date=pd.to_datetime(spi_min_row["date"]).date(),
                    spi3_min=float(spi_min),
                    rzsm_min_z=float(rzsm_min),
                ))
    return fires


def current_status(today: date | None = None,
                   trigger: CalibratedTrigger = CALIBRATED_TRIGGERS[0]) -> dict:
    """Return a dashboard-friendly summary of the trigger state."""
    today = today or config.today()
    fires = evaluate_history(trigger)
    fires_this_year = [f for f in fires if f.year == today.year]
    fires_history = sorted([f for f in fires if f.year < today.year],
                           key=lambda f: (f.year, f.departamento))

    doy = today.timetuple().tm_yday
    window_active = trigger.window_doy[0] <= doy <= trigger.window_doy[1]
    window_passed = doy > trigger.window_doy[1]

    return {
        "trigger": trigger,
        "today": today,
        "window_active": window_active,
        "window_passed": window_passed,
        "doy": doy,
        "fires_this_year": [f.to_dict() for f in fires_this_year],
        "fires_history": [f.to_dict() for f in fires_history],
    }


def write_history(path: Path | None = None) -> Path:
    """Persist all historical fires to a JSON file for offline review."""
    import json
    out = path or (config.STORAGE_ROOT / "trigger_fires.json")
    fires = evaluate_history()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        json.dump([fire.to_dict() for fire in fires], f, indent=2)
    return out
