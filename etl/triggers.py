"""Calibrated runtime trigger evaluator.

Country- and season-aware: each trigger belongs to one of the country's
growing seasons (`config.CC['seasons']`) and takes that season's
`alert_window_doy`. TRIGGERS_BY_COUNTRY lists them per country; a season
without a calibrated trigger has no alert.

Operating points are calibrated per-country via
`el_nino/experiments/trigger_calibration.py` (see the
`trigger_calibration_report_{code}.md` files for the full sweep).

For each department and each year of overlap (CHIRPS 1981+, SMAP 2015+),
the evaluator records whether the conditions were met inside the window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from .. import config
from . import storage

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
    spi3_threshold: float           # threshold on `spi_column`
    rzsm_threshold: float | None    # None → rainfall-only trigger
    severity: str
    stats: CalibrationStats | None = None
    season: str = ""                # key into config.CC["seasons"]
    spi_column: str = "spi_3"       # "spi_3" or "spi_1"
    provisional: bool = False       # shown with a caveat until validated (TODO.md)


def _window(country: str, season: str) -> tuple[int, int]:
    return next(s["alert_window_doy"] for s in config.COUNTRIES[country]["seasons"]
                if s["key"] == season)


# Per-country, per-season calibrated triggers. Re-run
# `COUNTRY=<key> python -m el_nino.experiments.trigger_calibration --season <key>`
# after every annual data refresh to update these. Stats come from the
# deployed data (Oct 2026), scored on evidence-labeled years only
# (experiments/evidence/labels.csv): documented droughts vs documented normal
# seasons; hurricane and mixed years excluded. FP/decade is per decade of
# negative (documented normal) years.
TRIGGERS_BY_COUNTRY: dict[str, list[CalibratedTrigger]] = {
    "el_salvador": [
        CalibratedTrigger(
            name="silking_drought_v2",
            description=(
                "SPI-3 < −1.5 AND SMAP root-zone anomaly < −1.0σ during silking "
                "(DOY 196-227, mid-Jul to mid-Aug), in any department"
            ),
            season="primera",
            window_doy=_window("el_salvador", "primera"),
            spi3_threshold=-1.5,
            rzsm_threshold=-1.0,
            severity="high",
            stats=CalibrationStats(
                # experiments/trigger_calibration_report_es_primera.md — all
                # 14 departments, labeled SMAP-era years. Catches 2015
                # (severe), 2018, 2023 and 2026; quiet in 2016, 2017, 2019,
                # 2021, 2022, 2025. Ties SPI-3 < −1.3 on every metric; 4/4 is
                # the best of the sweep on the same 10 years, so expect worse
                # out of sample.
                n_years=10,
                precision=1.00,    precision_ci=(0.51, 1.00),
                recall=1.00,       recall_ci=(0.51, 1.00),
                severe_recall=1.00, severe_recall_ci=(0.21, 1.00),
                fp_per_decade=0.00, fp_per_decade_ci=(0.00, 6.15),
            ),
        ),
        CalibratedTrigger(
            name="postrera_drought_v1",
            description=(
                "SPI-1 < −1.0 AND SMAP root-zone anomaly < −1.5σ in the "
                "postrera planting window (DOY 245-275, Sep 2 to Oct 2), in any "
                "department. Provisional."
            ),
            season="postrera",
            window_doy=_window("el_salvador", "postrera"),
            spi3_threshold=-1.0,
            rzsm_threshold=-1.5,
            severity="high",
            spi_column="spi_1",
            provisional=True,
            stats=CalibrationStats(
                # experiments/trigger_calibration_report_es_postrera.md. Only
                # two documented postrera droughts (2023, 2025), both caught
                # (2025 in Chalatenango alone); false alarm in 2015 (dry
                # September, rescued by late-September rain). Thresholds were
                # chosen on those same two years. Fires at the window's first
                # day in 2023 and 2026: dry primera soil carries over.
                # Provisional until the 2026 postrera outcome is documented
                # (TODO.md).
                n_years=6,
                precision=0.67,    precision_ci=(0.21, 0.94),
                recall=1.00,       recall_ci=(0.34, 1.00),
                severe_recall=float("nan"), severe_recall_ci=(float("nan"), float("nan")),
                fp_per_decade=2.50, fp_per_decade_ci=(0.06, 13.93),
            ),
        ),
    ],
    "haiti": [
        CalibratedTrigger(
            name="printemps_drought_v3",
            description=(
                "SPI-3 < −1.0 AND SMAP root-zone anomaly < −1.0σ from May 15 "
                "to Jul 31 (DOY 135-212), in any department."
            ),
            season="printemps",
            window_doy=_window("haiti", "printemps"),
            spi3_threshold=-1.0,
            rzsm_threshold=-1.0,
            severity="high",
            stats=CalibrationStats(
                # experiments/trigger_calibration_report_ht_printemps.md —
                # labeled SMAP-era years. Catches 2015 (severe), 2020, 2022,
                # 2025 and one more of 8 droughts; quiet in both documented
                # normal years (2016, 2021). The old Jun 1–Aug 15 window
                # missed spring droughts (2012, 2020, 2022, 2024) and ran
                # past the Jul 31 season end.
                n_years=10,
                precision=1.00,    precision_ci=(0.57, 1.00),
                recall=0.62,       recall_ci=(0.31, 0.86),
                severe_recall=1.00, severe_recall_ci=(0.21, 1.00),
                fp_per_decade=0.00, fp_per_decade_ci=(0.00, 18.44),
            ),
        ),
        CalibratedTrigger(
            name="automne_drought_v1",
            description=(
                "SPI-1 < −1.3 from Sep 15 to Nov 1 (DOY 258-305), in any "
                "department. Rainfall only."
            ),
            season="automne",
            window_doy=_window("haiti", "automne"),
            spi3_threshold=-1.3,
            rzsm_threshold=None,
            severity="high",
            spi_column="spi_1",
            # Fires in 29 of 45 years since 1981; most of those years have no
            # automne evidence either way. Tighter rules (deeper SPI, ≥2-3
            # departments) cut that to ~30% but lose a documented drought and
            # double the documented false alarms. Provisional until the
            # unlabeled years are filled in (TODO.md).
            provisional=True,
            stats=CalibrationStats(
                # experiments/trigger_calibration_report_ht_automne.md —
                # CHIRPS-era labeled years. Catches 6 of 7 droughts (2013,
                # 2015, 2019, 2021, 2022, 2023, 2026 — 2026 with the window
                # still open); one false alarm in 4 documented normal years.
                # SPI-1 beats SPI-3 here: its one-month lookback leaves out
                # printemps rain.
                n_years=11,
                precision=0.86,    precision_ci=(0.49, 0.97),
                recall=0.86,       recall_ci=(0.49, 0.97),
                severe_recall=1.00, severe_recall_ci=(0.21, 1.00),
                fp_per_decade=2.50, fp_per_decade_ci=(0.06, 13.93),
            ),
        ),
    ],
}

CALIBRATED_TRIGGERS: list[CalibratedTrigger] = TRIGGERS_BY_COUNTRY.get(config.COUNTRY, [])


def trigger_for(season: str) -> CalibratedTrigger | None:
    """The active country's calibrated trigger for a season, if any."""
    return next((t for t in CALIBRATED_TRIGGERS if t.season == season), None)


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
    # would first have shown. `fire_date` is the day of the SPI minimum.
    first_date: date | None = None
    season: str = ""

    def to_dict(self) -> dict:
        return {
            "trigger_name": self.trigger_name,
            "severity": self.severity,
            "year": self.year,
            "departamento": self.departamento,
            "fire_date": self.fire_date.isoformat() if self.fire_date else None,
            "spi3_min": float(self.spi3_min),
            # None for rainfall-only triggers (NaN is not valid JSON).
            "rzsm_min_z": None if self.rzsm_min_z != self.rzsm_min_z else float(self.rzsm_min_z),
            "first_date": self.first_date.isoformat() if self.first_date else None,
            "season": self.season,
        }


# (indicator, column, file signature) → per-department series. The banner, the
# season panel and every season's trigger read the same columns; over gcsfuse
# in Cloud Run each re-read costs latency and instance time.
_LOAD_CACHE: dict[tuple, dict[str, pd.DataFrame]] = {}


def _load_per_dep(indicator: str, col: str) -> dict[str, pd.DataFrame]:
    """Load the active country's per-departamento series for an indicator/column.
    ES and HT can share one STORAGE_ROOT, so other countries' files are skipped.
    Cached until any of the indicator's parquets changes."""
    indicator_dir = config.RAW_DIR / indicator
    if not indicator_dir.exists():
        return {}
    files = sorted(indicator_dir.glob("*.parquet"))
    key = (config.COUNTRY, str(indicator_dir), col,
           tuple((f.name, f.stat().st_mtime_ns, f.stat().st_size) for f in files))
    if key not in _LOAD_CACHE:
        if len(_LOAD_CACHE) >= 8:  # a handful of columns; stale signatures age out
            del _LOAD_CACHE[next(iter(_LOAD_CACHE))]
        _LOAD_CACHE[key] = _read_per_dep(files, col)
    return _LOAD_CACHE[key]


def _read_per_dep(files: list[Path], col: str) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    country = config.country_departments()
    for parquet in files:
        df = storage.read_parquet(parquet)
        if df.empty or col not in df.columns:
            continue
        dep = df["departamento"].iloc[0]
        if country and dep not in country:
            continue
        if "is_forecast" in df.columns:
            # GFS forecast pentads carry SPI too; an alert must come from observations.
            df = df[~df["is_forecast"].fillna(False).astype(bool)]
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
    triggers = [trigger] if trigger is not None else CALIBRATED_TRIGGERS
    return [fire for t in triggers for fire in _evaluate(t)]


def _evaluate(trigger: CalibratedTrigger) -> list[FireRecord]:
    spi = _load_per_dep("chirps", trigger.spi_column)
    rzsm = _load_per_dep("smap", "value_anom_z") if trigger.rzsm_threshold is not None else {}
    lo, hi = trigger.window_doy

    fires: list[FireRecord] = []
    for dep, spi_df in spi.items():
        rzsm_df = rzsm.get(dep)
        if trigger.rzsm_threshold is not None:
            if rzsm_df is None or rzsm_df.empty:
                continue
            years = sorted(set(spi_df["year"]) & set(rzsm_df["year"]))
        else:
            years = sorted(set(spi_df["year"]))
        for year in years:
            spi_window = spi_df[(spi_df["year"] == year) & (spi_df["doy"] >= lo) & (spi_df["doy"] <= hi)]
            if spi_window.empty or pd.isna(spi_min := spi_window["value"].min()):
                continue
            if not spi_min < trigger.spi3_threshold:
                continue
            first = spi_window.loc[spi_window["value"] < trigger.spi3_threshold, "date"].min()
            rzsm_min = float("nan")
            if trigger.rzsm_threshold is not None:
                rzsm_window = rzsm_df[(rzsm_df["year"] == year) & (rzsm_df["doy"] >= lo) & (rzsm_df["doy"] <= hi)]
                if rzsm_window.empty or pd.isna(rzsm_min := rzsm_window["value"].min()):
                    continue
                if not rzsm_min < trigger.rzsm_threshold:
                    continue
                first = max(first, rzsm_window.loc[rzsm_window["value"] < trigger.rzsm_threshold, "date"].min())
            spi_min_row = spi_window.loc[spi_window["value"].idxmin()]
            fires.append(FireRecord(
                trigger_name=trigger.name,
                severity=trigger.severity,
                year=int(year),
                departamento=dep,
                fire_date=pd.to_datetime(spi_min_row["date"]).date(),
                spi3_min=float(spi_min),
                rzsm_min_z=float(rzsm_min),
                first_date=first.date(),
                season=trigger.season,
            ))
    return fires


def current_status(today: date | None = None,
                   trigger: CalibratedTrigger | None = None,
                   span=None) -> dict | None:
    """Return a dashboard-friendly summary of the trigger state for the
    season on screen (`span`, an etl.season.SeasonSpan), so the banner and the
    season panel agree. Returns None if that season has no calibrated trigger.
    Without a span: the country's first trigger, keyed on today's year."""
    if trigger is None:
        trigger = trigger_for(span.key) if span is not None else (
            CALIBRATED_TRIGGERS[0] if CALIBRATED_TRIGGERS else None)
    if trigger is None:
        return None
    today = today or config.today()
    year = span.year if span is not None else today.year
    fires = evaluate_history(trigger)
    fires_this_year = [f for f in fires if f.year == year]
    fires_history = sorted([f for f in fires if f.year < year],
                           key=lambda f: (f.year, f.departamento))

    jan1 = date(year, 1, 1).toordinal() - 1
    win_start = date.fromordinal(jan1 + trigger.window_doy[0])
    win_end = date.fromordinal(jan1 + trigger.window_doy[1])

    return {
        "trigger": trigger,
        "today": today,
        "window_active": win_start <= today <= win_end,
        "window_passed": today > win_end,
        "window_start": win_start,
        "window_end": win_end,
        "fires_this_year": [f.to_dict() for f in fires_this_year],
        "fires_history": [f.to_dict() for f in fires_history],
    }
