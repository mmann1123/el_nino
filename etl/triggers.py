"""Calibrated runtime trigger evaluator.

Country-aware: the active country's silking window comes from
`config.CC['silking_window']`. The CALIBRATED_TRIGGERS list is keyed by
country in TRIGGERS_BY_COUNTRY — pick using `config.COUNTRY` at import time.

Operating points are calibrated per-country via
`el_nino/experiments/trigger_calibration.py` (see the
`trigger_calibration_report_{code}.md` files for the full sweep).

For each department and each year of overlap (CHIRPS 1981+, SMAP 2015+),
the evaluator records whether both conditions were met during silking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from .. import config
from . import storage

SILKING_WINDOW: tuple[int, int] = config.CC["silking_window"]


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


# Per-country calibrated triggers. Re-run
# `COUNTRY=<key> python -m el_nino.experiments.trigger_calibration` after every
# annual data refresh to update these.
TRIGGERS_BY_COUNTRY: dict[str, list[CalibratedTrigger]] = {
    "el_salvador": [
        CalibratedTrigger(
            name="silking_drought_v2",
            description=(
                "SPI-3 < −1.5 AND SMAP root-zone anomaly < −1.0σ during silking "
                "(DOY 196-227, mid-Jul to mid-Aug), in any department"
            ),
            window_doy=(196, 227),
            spi3_threshold=-1.5,
            rzsm_threshold=-1.0,
            severity="high",
            stats=CalibrationStats(
                # experiments/trigger_calibration_report_es.md — all 14
                # departments, 2015-2026. Catches 2015 (severe), 2018 (Cabanas),
                # 2023 (the west) and 2026 (field-confirmed in the east); the
                # eastern-corridor-only v1 caught 2015 alone. Ties SPI-3 < −1.3
                # on every metric. 4/4 is the best of a 15-point sweep on the
                # same 12 years, so expect worse out of sample.
                n_years=12,
                precision=1.00,    precision_ci=(0.51, 1.00),
                recall=1.00,       recall_ci=(0.51, 1.00),
                severe_recall=1.00, severe_recall_ci=(0.21, 1.00),
                fp_per_decade=0.00, fp_per_decade_ci=(0.00, 4.61),
            ),
        ),
    ],
    "haiti": [
        CalibratedTrigger(
            name="silking_drought_v2",
            description=(
                "SPI-3 < −1.3 AND SMAP root-zone anomaly < −0.5σ during the "
                "printemps→été silking window (DOY 152-227, Jun 1 to Aug 15), "
                "in any department."
            ),
            window_doy=(152, 227),
            spi3_threshold=-1.3,
            rzsm_threshold=-0.5,
            severity="high",
            stats=CalibrationStats(
                # See experiments/trigger_calibration_report_ht.md — combined
                # SPI+SMAP on 11 yrs (2015-2025), 3 labeled positives in window.
                # Any-department scoring over all 10 (matches runtime). Same
                # numbers as the v1 priority-only scoring: a non-priority
                # department never fired in a year a priority one did not.
                # Catches 2015 (severe) and 2018 (moderate). Misses 2023 —
                # rainfall stayed near normal despite FEWS-reported NW
                # peninsula impact.
                # FP/decade is high (2.73) reflecting the noisier HT signal;
                # the 95% CI is wide given only 11 years of SMAP overlap.
                n_years=11,
                precision=0.40,    precision_ci=(0.12, 0.77),
                recall=0.67,       recall_ci=(0.21, 0.94),
                severe_recall=1.00, severe_recall_ci=(0.21, 1.00),
                fp_per_decade=2.73, fp_per_decade_ci=(0.77, 10.96),
            ),
        ),
    ],
}

CALIBRATED_TRIGGERS: list[CalibratedTrigger] = TRIGGERS_BY_COUNTRY.get(config.COUNTRY, [])


@dataclass
class FireRecord:
    trigger_name: str
    severity: str
    year: int
    departamento: str
    fire_date: date | None
    spi3_min: float
    rzsm_min_z: float
    # The day both conditions had been met inside the window — when the alert
    # would first have shown. `fire_date` is the day of the SPI-3 minimum.
    first_date: date | None = None

    def to_dict(self) -> dict:
        return {
            "trigger_name": self.trigger_name,
            "severity": self.severity,
            "year": self.year,
            "departamento": self.departamento,
            "fire_date": self.fire_date.isoformat() if self.fire_date else None,
            "spi3_min": float(self.spi3_min),
            "rzsm_min_z": float(self.rzsm_min_z),
            "first_date": self.first_date.isoformat() if self.first_date else None,
        }


def _load_per_dep(indicator: str, col: str) -> dict[str, pd.DataFrame]:
    """Load the active country's per-departamento series for an indicator/column.
    ES and HT can share one STORAGE_ROOT, so other countries' files are skipped."""
    out: dict[str, pd.DataFrame] = {}
    indicator_dir = config.RAW_DIR / indicator
    if not indicator_dir.exists():
        return out
    country = config.country_departments()
    for parquet in indicator_dir.glob("*.parquet"):
        df = storage.read_parquet(parquet)
        if df.empty or col not in df.columns:
            continue
        dep = df["departamento"].iloc[0]
        if country and dep not in country:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["doy"] = df["date"].dt.dayofyear
        out[dep] = df[["date", "year", "doy", col]].rename(columns={col: "value"})
    return out


def evaluate_history(trigger: CalibratedTrigger | None = None) -> list[FireRecord]:
    """Return one FireRecord per (year, departamento) where the trigger fired.
    Every department is evaluated, matching the calibration's any-department
    scoring so the runtime alert means what the report's precision/recall say.
    Returns [] if no calibrated trigger is defined for the active country.
    """
    if trigger is None:
        if not CALIBRATED_TRIGGERS:
            return []
        trigger = CALIBRATED_TRIGGERS[0]
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
                first_spi = spi_window.loc[spi_window["value"] < trigger.spi3_threshold, "date"].min()
                first_rzsm = rzsm_window.loc[rzsm_window["value"] < trigger.rzsm_threshold, "date"].min()
                fires.append(FireRecord(
                    trigger_name=trigger.name,
                    severity=trigger.severity,
                    year=int(year),
                    departamento=dep,
                    fire_date=pd.to_datetime(spi_min_row["date"]).date(),
                    spi3_min=float(spi_min),
                    rzsm_min_z=float(rzsm_min),
                    first_date=max(first_spi, first_rzsm).date(),
                ))
    return fires


def current_status(today: date | None = None,
                   trigger: CalibratedTrigger | None = None) -> dict | None:
    """Return a dashboard-friendly summary of the trigger state.
    Returns None if no calibrated trigger is defined for the active country."""
    if trigger is None:
        if not CALIBRATED_TRIGGERS:
            return None
        trigger = CALIBRATED_TRIGGERS[0]
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
