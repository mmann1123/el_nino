"""Trigger calibration against labeled historical El Niño impact events.

Country- and season-aware: departments come from `config.CC`, and the alert
window and labeled events from one of its `seasons`, so the same sweep runs
for ES (default) and HT (COUNTRY=haiti), first or later season. Run with:

    python -m el_nino.experiments.trigger_calibration                      # ES primera
    python -m el_nino.experiments.trigger_calibration --season postrera    # ES postrera
    COUNTRY=haiti python -m el_nino.experiments.trigger_calibration --season automne

A season without an alert window yet is swept over the candidate windows in
CANDIDATE_WINDOWS. Labels with severity "normal" are documented negatives;
"excluded" years (e.g. hurricane losses) are left out of scoring. A season
that has documented normal years is scored on labeled years only: an
unlabeled year is unknown, not a negative.

Inputs:
  - SPI-3 and SPI-1 (CHIRPS, 1981+) — long baseline, single-indicator triggers
  - RZSM anomaly (SMAP, 2015+) — short baseline, for confirmation
  - ETa anomaly (WAPOR, 2018+) — short baseline, confirmation

Method:
  Evaluate every department in the country. For each candidate threshold +
  window, ask: did SPI-3 (or the AND of SPI-3 + RZSM) cross below the
  threshold during the silking window in any department? The current year is
  left out until it is labeled. Score precision / recall / lead-time /
  false-positive rate against the labeled events.

Output:
  el_nino/experiments/trigger_calibration_report_{country_code}_{season}.md
"""

from __future__ import annotations

import argparse
import csv
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from el_nino import config  # noqa: E402

# Every department, not just the priority ones: the labels are national
# years, and restricting to the eastern dry corridor missed the 2018 and 2023
# ES droughts, which hit Cabanas and the west.
DEPARTMENTS = sorted(config.country_departments())
DEKAD_FOLLOWING = 10      # days after window-end to look for ETa confirmation
EVIDENCE_CSV = Path(__file__).parent / "evidence" / "labels.csv"

# Candidate alert windows (DOY) for seasons not yet calibrated, from the
# critical windows in FEWS NET / GIEWS crop calendars: postrera planting and
# bean flowering (Sep–Oct); automne Sep–Oct, plus a later one because the
# 2013/14 Nord-Ouest losses came from Nov–Mar rain.
CANDIDATE_WINDOWS: dict[str, list[tuple[int, int]]] = {
    "postrera": [(245, 275), (258, 288), (258, 305), (275, 305)],
    "automne": [(245, 275), (245, 300), (258, 305), (275, 334)],
}
SPI_COLUMNS = ("spi_3", "spi_1")

# Set by configure() for the season being calibrated.
SEASON: dict = {}
LABELED_EVENTS: dict[int, tuple[str, str]] = {}
POSITIVE_YEARS: set[int] = set()
EXCLUDED_YEARS: set[int] = set()
SCORED_YEARS: set[int] | None = None   # None → every year with data
WINDOWS: list[tuple[int, int]] = []


def configure(season_key: str | None = None, window: tuple[int, int] | None = None) -> None:
    """Point the sweep at one of the active country's seasons, optionally
    trying a different base window than the configured one."""
    global SEASON, LABELED_EVENTS, POSITIVE_YEARS, EXCLUDED_YEARS, WINDOWS, SCORED_YEARS
    SEASON = config.season_cfg(season_key) if season_key else config.CC["seasons"][0]
    if window is not None:
        SEASON = dict(SEASON, alert_window_doy=window, _first=SEASON is config.CC["seasons"][0])
    LABELED_EVENTS = SEASON["labeled_events"]
    POSITIVE_YEARS = {y for y, (sev, _) in LABELED_EVENTS.items()
                      if sev not in ("normal", "excluded")}
    EXCLUDED_YEARS = {y for y, (sev, _) in LABELED_EVENTS.items() if sev == "excluded"}
    normal = {y for y, (sev, _) in LABELED_EVENTS.items() if sev == "normal"}
    SCORED_YEARS = (POSITIVE_YEARS | normal) if normal else None
    if SEASON["alert_window_doy"] is not None:
        s, e = SEASON["alert_window_doy"]
        mid = (s + e) // 2
        half = max(15, (e - s) // 2)
        WINDOWS = [
            (s, e),                                                 # configured window
            (max(1, mid - half // 2), min(365, mid + half // 2)),   # tighter, centered
            (s, min(365, e + 46)),                                  # wider, ~1.5 months later
        ]
    else:
        WINDOWS = CANDIDATE_WINDOWS[SEASON["key"]]


def _norm_dep(name: str) -> str:
    """Report spelling → GAUL ADM1_NAME (no accents, spaces not hyphens)."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    plain = plain.replace("-", " ").replace("Grand'Anse", "Grande Anse").strip()
    return plain


def reported_departments() -> dict[int, set[str]]:
    """Departments named in the evidence for each positive year of this season
    (experiments/evidence/labels.csv). Used only as hits: a department that
    isn't named is not evidence of no drought."""
    if not EVIDENCE_CSV.exists():
        return {}
    out: dict[int, set[str]] = {}
    with EVIDENCE_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row["country"] != config.CC["short_code"].lower()
                    or row["season"] != SEASON["key"] or row["verdict"] != "drought"):
                continue
            deps = {_norm_dep(d) for d in row["departments"].split(";") if d.strip()}
            deps &= set(DEPARTMENTS)
            if deps:
                out.setdefault(int(row["year"]), set()).update(deps)
    return out


@dataclass
class TriggerConfig:
    name: str
    spi3_thr: float                 # threshold on spi_col
    require_rzsm: bool
    rzsm_thr: float
    require_eta: bool
    eta_thr: float
    window: tuple[int, int]
    spi_col: str = "spi_3"


def load_indicator(indicator: str, value_col: str) -> pd.DataFrame:
    """Load per-department time series for every department.

    Returns a long DataFrame with columns: date, year, doy, departamento, value.
    Per-dep granularity preserves regional heterogeneity — the evaluators below
    fire per (year, dep) and aggregate to a binary 'any dep fired this
    year' for binary scoring against the labeled events.
    """
    frames = []
    for dep in DEPARTMENTS:
        f = config.RAW_DIR / indicator / f"{dep.replace(' ', '_')}.parquet"
        if not f.exists():
            continue
        df = pd.read_parquet(f)
        if df.empty or value_col not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["doy"] = df["date"].dt.dayofyear
        # The current year counts only once it is labeled (e.g. a field-confirmed
        # drought); otherwise it is not yet known to be a negative.
        df = df[(df["year"] < config.today().year) | df["year"].isin(POSITIVE_YEARS)]
        df["departamento"] = dep
        frames.append(df[["date", "year", "doy", "departamento", value_col]]
                      .rename(columns={value_col: "value"}))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(["departamento", "date"]).reset_index(drop=True)


def years_available(df: pd.DataFrame, doy_window: tuple[int, int]) -> set[int]:
    if df.empty:
        return set()
    in_window = df[(df["doy"] >= doy_window[0]) & (df["doy"] <= doy_window[1])]
    return set(in_window["year"].unique())


def _per_dep_min(df: pd.DataFrame, year: int, window: tuple[int, int]) -> pd.Series:
    """Return Series of {dep: min(value)} across the window for a given year.
    Empty/all-NaN deps are omitted."""
    sub = df[(df["year"] == year) &
             (df["doy"] >= window[0]) & (df["doy"] <= window[1])]
    if sub.empty:
        return pd.Series(dtype=float)
    return sub.groupby("departamento")["value"].min().dropna()


def evaluate_spi_only(spi: pd.DataFrame, cfg: TriggerConfig) -> dict:
    """Single-indicator (SPI-3) trigger.

    Per-department evaluation: a year fires if ANY department's
    SPI-3 minimum during the window falls below the threshold.
    """
    years = sorted(years_available(spi, cfg.window))
    fires: dict[int, dict] = {}
    for y in years:
        per_dep = _per_dep_min(spi, y, cfg.window)
        if per_dep.empty:
            continue
        firing_deps = per_dep[per_dep < cfg.spi3_thr]
        fires[y] = {
            "fire": bool(len(firing_deps) > 0),
            "min_spi3": float(per_dep.min()),
            "worst_dep": str(per_dep.idxmin()),
            "firing_deps": list(firing_deps.index),
            "n_deps_fired": int(len(firing_deps)),
            "n_deps_evaluated": int(len(per_dep)),
        }
    return _score(fires, cfg)


def evaluate_combo(spi: pd.DataFrame, rzsm: pd.DataFrame, eta: pd.DataFrame, cfg: TriggerConfig) -> dict:
    """Combined SPI + RZSM (± ETa) trigger.

    Per-department evaluation: a year fires if ANY department meets
    ALL required conditions (SPI < thr) ∧ (RZSM < thr) [∧ (ETa < thr)] during
    the window. Departments without coverage for a required indicator are
    excluded from the fire test for that year.
    """
    years = sorted(years_available(spi, cfg.window) &
                   (years_available(rzsm, cfg.window) if cfg.require_rzsm else years_available(spi, cfg.window)))
    fires: dict[int, dict] = {}
    for y in years:
        spi_min = _per_dep_min(spi, y, cfg.window)
        if spi_min.empty:
            continue
        rzsm_min = _per_dep_min(rzsm, y, cfg.window) if cfg.require_rzsm else pd.Series(dtype=float)
        eta_win = (cfg.window[0], cfg.window[1] + DEKAD_FOLLOWING)
        eta_min = _per_dep_min(eta, y, eta_win) if cfg.require_eta else pd.Series(dtype=float)

        firing_deps = []
        for dep in spi_min.index:
            spi_ok = spi_min[dep] < cfg.spi3_thr
            rzsm_ok = (dep in rzsm_min.index and rzsm_min[dep] < cfg.rzsm_thr) if cfg.require_rzsm else True
            eta_ok = (dep in eta_min.index and eta_min[dep] < cfg.eta_thr) if cfg.require_eta else True
            if spi_ok and rzsm_ok and eta_ok:
                firing_deps.append(dep)
        fires[y] = {
            "fire": bool(len(firing_deps) > 0),
            "min_spi3": float(spi_min.min()),
            "min_rzsm": float(rzsm_min.min()) if not rzsm_min.empty else None,
            "min_eta": float(eta_min.min()) if not eta_min.empty else None,
            "worst_dep": str(spi_min.idxmin()),
            "firing_deps": firing_deps,
            "n_deps_fired": len(firing_deps),
            "n_deps_evaluated": int(len(spi_min)),
        }
    return _score(fires, cfg)


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n. Better than normal
    approximation at small N and near 0/1, which is exactly where we are."""
    if n == 0:
        return (float("nan"), float("nan"))
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    halfwidth = z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5) / denom
    return (max(0.0, center - halfwidth), min(1.0, center + halfwidth))


def poisson_ci(k: int, exposure_decades: float, alpha: float = 0.05) -> tuple[float, float]:
    """Exact Poisson (Garwood) interval on count rate per decade.

    exposure_decades = n_years / 10. Returns CI on events-per-decade.
    """
    if exposure_decades <= 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else chi2.ppf(alpha / 2, 2 * k) / 2 / exposure_decades
    hi = chi2.ppf(1 - alpha / 2, 2 * (k + 1)) / 2 / exposure_decades
    return (lo, hi)


def _score(fires: dict, cfg: TriggerConfig) -> dict:
    years = sorted(fires)
    if not years:
        return {"cfg": cfg, "tp": 0, "fp": 0, "fn": 0, "tn": 0, "fires": fires, "years": years}
    tp = fp = fn = tn = 0
    caught_severe = 0
    severe_total = 0
    years = [y for y in years if y not in EXCLUDED_YEARS
             and (SCORED_YEARS is None or y in SCORED_YEARS)]
    for y in years:
        positive = y in POSITIVE_YEARS
        severe = positive and LABELED_EVENTS[y][0].startswith("severe")
        fired = fires[y]["fire"]
        if positive and fired:
            tp += 1
            if severe:
                caught_severe += 1
        elif positive and not fired:
            fn += 1
        elif not positive and fired:
            fp += 1
        else:
            tn += 1
        if severe:
            severe_total += 1

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    severe_recall = caught_severe / severe_total if severe_total else float("nan")
    n_years = len(years)
    n_neg = n_years - len(set(years) & POSITIVE_YEARS)
    # False alarms per decade of negative years (only those can be false
    # alarms), the same exposure the Poisson CI below uses.
    fp_per_decade = fp / n_neg * 10 if n_neg else float("nan")

    # Confidence intervals (Wilson for proportions, Poisson for the FP rate).
    precision_ci = wilson_ci(tp, tp + fp)
    recall_ci = wilson_ci(tp, tp + fn)
    severe_recall_ci = wilson_ci(caught_severe, severe_total) if severe_total else (float("nan"), float("nan"))
    # FP/decade exposure is the negative-year exposure (only neg years can yield FP).
    fp_per_decade_ci = poisson_ci(fp, n_neg / 10) if n_neg > 0 else (float("nan"), float("nan"))

    return {
        "cfg": cfg,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "severe_recall": severe_recall,
        "fp_per_decade": fp_per_decade,
        "precision_ci": precision_ci, "recall_ci": recall_ci,
        "severe_recall_ci": severe_recall_ci, "fp_per_decade_ci": fp_per_decade_ci,
        "n_years": n_years, "n_neg": n_neg,
        "fires": fires,
        "years": years,
    }


def sweep_spi_only(spis: dict[str, pd.DataFrame]) -> list[dict]:
    thresholds = [-0.8, -1.0, -1.3, -1.5, -1.7]
    results = []
    for col in _spi_cols():
        for thr in thresholds:
            for window in WINDOWS:
                cfg = TriggerConfig(
                    name=f"{_spi_label(col)}<{thr} in DOY {window[0]}-{window[1]}",
                    spi3_thr=thr,
                    require_rzsm=False, rzsm_thr=0.0,
                    require_eta=False, eta_thr=0.0,
                    window=window, spi_col=col,
                )
                results.append(evaluate_spi_only(spis[col], cfg))
    return results


def sweep_combo(spis: dict[str, pd.DataFrame], rzsm: pd.DataFrame, eta: pd.DataFrame) -> list[dict]:
    spi_thrs = [-1.0, -1.3, -1.5]
    rzsm_thrs = [-0.5, -1.0, -1.5]
    # A calibrated season keeps its window; a new one sweeps the candidates.
    windows = WINDOWS[:1] if SEASON["alert_window_doy"] is not None else WINDOWS
    results = []
    for col in _spi_cols():
        for window in windows:
            for s in spi_thrs:
                for r in rzsm_thrs:
                    for require_eta in (False, True):
                        cfg = TriggerConfig(
                            name=(f"{_spi_label(col)}<{s} ∧ RZSM<{r}σ" +
                                  (" ∧ ETa<0" if require_eta else "") +
                                  (f" in DOY {window[0]}-{window[1]}" if len(windows) > 1 else "")),
                            spi3_thr=s,
                            require_rzsm=True, rzsm_thr=r,
                            require_eta=require_eta, eta_thr=0.0,
                            window=window, spi_col=col,
                        )
                        results.append(evaluate_combo(spis[col], rzsm, eta, cfg))
    return results


def _spi_cols() -> tuple[str, ...]:
    """The first season keeps SPI-3; a later season also tries SPI-1, whose
    one-month lookback leaves out the previous season's rain."""
    first = SEASON.get("_first", SEASON is config.CC["seasons"][0])
    return ("spi_3",) if first else SPI_COLUMNS


def _spi_label(col: str) -> str:
    return col.upper().replace("_", "-")


def _geo_hits(result: dict, reported: dict[int, set[str]]) -> tuple[int, int]:
    """(positive years where the alert fired in a reported department,
    positive years with reported departments)."""
    hits = total = 0
    for y, deps in reported.items():
        if y not in result["fires"] or y not in POSITIVE_YEARS:
            continue
        total += 1
        fired = set(result["fires"][y].get("firing_deps", []))
        hits += bool(fired & deps)
    return hits, total


def _fmt(p: float) -> str:
    return f"{p:.2f}" if p == p else "—"  # NaN-safe


def _fmt_ci(ci: tuple[float, float]) -> str:
    lo, hi = ci
    if lo != lo or hi != hi:
        return "—"
    return f"[{lo:.2f}–{hi:.2f}]"


def render_report(spi_results: list[dict], combo_results: list[dict]) -> str:
    lines: list[str] = []
    reported = reported_departments()
    season_name = SEASON["key"].capitalize()
    lines.append(f"# Trigger Calibration Report — {config.CC['display_name']}, {season_name}")
    lines.append("")
    lines.append("Generated from `el_nino/experiments/trigger_calibration.py`.")
    lines.append("")
    lines.append(f"**Country:** {config.CC['display_name']} ({config.CC['short_code']}).")
    lines.append(f"**Region:** all {len(DEPARTMENTS)} {config.CC['dept_term_plural']}; "
                 "a year fires if any one of them meets the conditions.")
    lines.append(f"**Season:** {season_name}. **Windows swept:** "
                 + ", ".join(f"DOY {a}-{b}" for a, b in WINDOWS) + ".")
    lines.append("**Labels:** the season's `labeled_events` in `config.CC['seasons']`, "
                 "traced to highlighted sources in `experiments/evidence/`.")
    lines.append("")
    severe_yrs = [y for y in POSITIVE_YEARS if LABELED_EVENTS[y][0].startswith("severe")]
    if severe_yrs:
        sev_text = ", ".join(f"{y} ({LABELED_EVENTS[y][1]})" for y in sorted(severe_yrs))
        lines.append(f"**Severe positive(s):** {sev_text}.")
    pos_text = ", ".join(str(y) for y in sorted(POSITIVE_YEARS) if not LABELED_EVENTS[y][0].startswith("severe"))
    lines.append(f"**Moderate positives:** {pos_text}.")
    normal = sorted(y for y, (sev, _) in LABELED_EVENTS.items() if sev == "normal")
    if normal:
        lines.append(f"**Documented normal seasons:** {', '.join(map(str, normal))}.")
    if EXCLUDED_YEARS:
        lines.append(f"**Excluded (non-drought losses, e.g. hurricanes):** "
                     f"{', '.join(map(str, sorted(EXCLUDED_YEARS)))}.")
    if SCORED_YEARS is not None:
        lines.append("**Negatives:** the documented normal seasons only; unlabeled years "
                     "are not scored.")
    else:
        lines.append("**Negatives:** all other years with available data.")
    if reported:
        lines.append("**Geo hits:** positive years where the alert fired in at least one "
                     "department the evidence names, out of positive years that name any. "
                     "Unnamed departments are not counted against the alert.")
    lines.append("")
    lines.append("## Confidence intervals")
    lines.append("")
    lines.append("All point estimates here come from small samples (the longest series, CHIRPS-only, "
                 "has ~45 years; SMAP-combined has only ~11). 95% confidence intervals are reported "
                 "alongside the point estimate to make the uncertainty visible:")
    lines.append("")
    lines.append("- **Precision, Recall, Severe recall** — **Wilson score interval** (binomial proportion).")
    lines.append("- **FP/decade** — **Garwood exact Poisson interval** on the false-positive rate "
                 "given exposure = number of negative years / 10.")
    lines.append("")

    # SPI-only table
    lines.append("## SPI only (long baseline, 1981+)")
    lines.append("")
    lines.append("| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |")
    lines.append("|---|---:|---:|---:|---:|---|---|---|---|---:|")
    for r in spi_results:
        cfg = r["cfg"]
        lines.append(
            f"| {cfg.name} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | "
            f"{_fmt(r['precision'])} {_fmt_ci(r['precision_ci'])} | "
            f"{_fmt(r['recall'])} {_fmt_ci(r['recall_ci'])} | "
            f"{_fmt(r['severe_recall'])} {_fmt_ci(r['severe_recall_ci'])} | "
            f"{_fmt(r['fp_per_decade'])} {_fmt_ci(r['fp_per_decade_ci'])} | "
            f"{'%d/%d' % _geo_hits(r, reported) if reported else '—'} |"
        )
    lines.append("")

    # Combo table
    lines.append("## Combined SPI ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)")
    lines.append("")
    lines.append("| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) | Geo hits |")
    lines.append("|---|---:|---:|---:|---:|---|---|---|---|---:|")
    for r in combo_results:
        cfg = r["cfg"]
        lines.append(
            f"| {cfg.name} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | "
            f"{_fmt(r['precision'])} {_fmt_ci(r['precision_ci'])} | "
            f"{_fmt(r['recall'])} {_fmt_ci(r['recall_ci'])} | "
            f"{_fmt(r['severe_recall'])} {_fmt_ci(r['severe_recall_ci'])} | "
            f"{_fmt(r['fp_per_decade'])} {_fmt_ci(r['fp_per_decade_ci'])} | "
            f"{'%d/%d' % _geo_hits(r, reported) if reported else '—'} |"
        )
    lines.append("")

    # Per-event detail for the best SPI-only configuration
    lines.append("## Per-year detail (best SPI-only configuration)")
    lines.append("")
    best_spi = _pick_recommended(spi_results)
    cfg = best_spi["cfg"]
    lines.append(f"**Recommended SPI-only trigger:** `{cfg.name}`")
    lines.append(
        f"- Precision: {_fmt(best_spi['precision'])} {_fmt_ci(best_spi['precision_ci'])} | "
        f"Recall: {_fmt(best_spi['recall'])} {_fmt_ci(best_spi['recall_ci'])} | "
        f"Severe recall: {_fmt(best_spi['severe_recall'])} {_fmt_ci(best_spi['severe_recall_ci'])} | "
        f"FP/decade: {_fmt(best_spi['fp_per_decade'])} {_fmt_ci(best_spi['fp_per_decade_ci'])}"
    )
    lines.append("")
    lines.append("| Year | Label | Worst dep | Min SPI | Deps fired | Fired? | Notes |")
    lines.append("|---|---|---|---:|:---:|:---:|---|")
    for y in best_spi["years"]:
        f = best_spi["fires"][y]
        label = LABELED_EVENTS.get(y, ("negative", ""))
        symbol = "✓" if f["fire"] else "—"
        n_fired = f.get("n_deps_fired", 0)
        n_eval = f.get("n_deps_evaluated", 0)
        deps_cell = f"{n_fired}/{n_eval}"
        lines.append(f"| {y} | {label[0]} | {f.get('worst_dep', '—')} | "
                     f"{f['min_spi3']:.2f} | {deps_cell} | {symbol} | {label[1]} |")
    lines.append("")

    best_combo = _pick_recommended(combo_results)
    if best_combo and best_combo["n_years"] > 0:
        cfg = best_combo["cfg"]
        lines.append("## Recommended combined trigger (where SMAP/WAPOR available)")
        lines.append("")
        lines.append(f"**`{cfg.name}`** in DOY {cfg.window[0]}-{cfg.window[1]}")
        lines.append(
            f"- Precision: {_fmt(best_combo['precision'])} {_fmt_ci(best_combo['precision_ci'])} | "
            f"Recall: {_fmt(best_combo['recall'])} {_fmt_ci(best_combo['recall_ci'])} | "
            f"Severe recall: {_fmt(best_combo['severe_recall'])} {_fmt_ci(best_combo['severe_recall_ci'])} | "
            f"FP/decade: {_fmt(best_combo['fp_per_decade'])} {_fmt_ci(best_combo['fp_per_decade_ci'])}"
        )
        lines.append("")
        lines.append("| Year | Label | Worst dep | SPI min | RZSM min (σ) | ETa min (σ) | Deps fired | Fired? |")
        lines.append("|---|---|---|---:|---:|---:|:---:|:---:|")
        for y in best_combo["years"]:
            f = best_combo["fires"][y]
            label = LABELED_EVENTS.get(y, ("negative", ""))
            symbol = "✓" if f["fire"] else "—"
            spi = f.get("min_spi3"); rzsm = f.get("min_rzsm"); eta = f.get("min_eta")
            n_fired = f.get("n_deps_fired", 0)
            n_eval = f.get("n_deps_evaluated", 0)
            deps_cell = f"{n_fired}/{n_eval}"
            lines.append(f"| {y} | {label[0]} | {f.get('worst_dep', '—')} | "
                         f"{spi:.2f} | "
                         f"{(f'{rzsm:.2f}' if rzsm is not None else '—')} | "
                         f"{(f'{eta:.2f}' if eta is not None else '—')} | "
                         f"{deps_cell} | {symbol} |")

    lines.append("")
    lines.append("## Operational recommendations")
    lines.append("")
    lines.append("1. Use the **SPI-only** trigger for the long-baseline alert (fires whenever SPI falls below threshold inside the window).")
    lines.append("2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.")
    lines.append("3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.")
    return "\n".join(lines)


def _pick_recommended(results: list[dict]) -> dict | None:
    """Pick the configuration that catches the most severe events while keeping
    FP rate below ~1 per decade. Tiebreak: prefer higher precision."""
    # A season with no severe label is judged on recall instead.
    metric = "severe_recall" if any(LABELED_EVENTS[y][0].startswith("severe")
                                    for y in POSITIVE_YEARS) else "recall"

    def m(r: dict, key: str, default: float) -> float:
        v = r.get(key, default)
        return default if v != v else v  # NaN → default

    results = [r for r in results if r.get("n_years", 0) > 0]
    if not results:
        return None
    candidates = [r for r in results if m(r, metric, 0) >= 0.99 and m(r, "fp_per_decade", 99) <= 1.0]
    if not candidates:
        # Fall back to highest recall + lowest FP/decade
        candidates = sorted(results, key=lambda r: (-m(r, metric, 0), m(r, "fp_per_decade", 99)))[:3]
    return max(candidates, key=lambda r: (m(r, metric, 0), m(r, "precision", 0)))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", default=None,
                        help="season key from config.CC['seasons'] (default: the first)")
    parser.add_argument("--window", nargs=2, type=int, metavar=("START_DOY", "END_DOY"),
                        help="base alert window to try instead of the configured one")
    args = parser.parse_args(argv)
    configure(args.season, tuple(args.window) if args.window else None)

    spis = {col: load_indicator("chirps", col) for col in _spi_cols()}
    rzsm = load_indicator("smap", "value_anom_z")
    eta = load_indicator("wapor", "value_anom_z")

    if spis["spi_3"].empty:
        print("ERROR: no CHIRPS SPI data available. Run `python -m el_nino.etl.run_etl finalize` first.")
        return
    if not POSITIVE_YEARS:
        print(f"ERROR: no labeled drought years for {SEASON['key']}; add them to "
              "config.CC['seasons'] (see experiments/evidence/labels.csv).")
        return

    spi_results = sweep_spi_only(spis)
    combo_results = sweep_combo(spis, rzsm, eta)

    report = render_report(spi_results, combo_results)
    code = config.CC["short_code"].lower()
    out = Path(__file__).parent / f"trigger_calibration_report_{code}_{SEASON['key']}.md"
    out.write_text(report)
    print(f"Wrote {out}")

    # Console summary
    print()
    print("=== TOP SPI-only configurations (by recall, then lowest FP/decade) ===")
    top_spi = sorted(spi_results,
                     key=lambda r: (-r.get("recall", 0), r.get("fp_per_decade", 99)))[:5]
    for r in top_spi:
        cfg = r["cfg"]
        print(f"  {cfg.name:<55} prec={r['precision']:.2f} rec={r['recall']:.2f} "
              f"severe={r['severe_recall']:.2f} fp/dec={r['fp_per_decade']:.2f}")


if __name__ == "__main__":
    main()
