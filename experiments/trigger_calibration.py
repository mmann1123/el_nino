"""Trigger calibration against labeled historical El Niño impact events.

Inputs:
  - SPI-3 (CHIRPS, 1981+)   — long baseline, single-indicator triggers
  - RZSM anomaly (SMAP, 2015+) — short baseline, for confirmation
  - ETa anomaly (WAPOR, 2018+) — short baseline, confirmation

Labels (from el_nino/el_nino_agricultural_risks.md):
  Severe positives:   2015 (60% maize / 80% beans loss, Dry Corridor)
  Moderate positives: 1997, 2002, 2009, 2014, 2018, 2023
  Negatives:          all neutral / La Niña / non-event years 1981-2024

Method:
  Aggregate the four eastern Dry Corridor departamentos (Morazán, San Miguel,
  La Unión, Usulután) by mean. For each candidate threshold + window, ask:
  did SPI-3 (or the AND of SPI-3 + RZSM) cross below the threshold during the
  silking window (mid-Jul to mid-Aug, DOY 196-227)? Score precision / recall
  / lead-time / false-positive rate vs the labels.

Output:
  el_nino/experiments/trigger_calibration_report.md
"""

from __future__ import annotations

import sys
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

DRY_CORRIDOR = ["Morazan", "San Miguel", "La Union", "Usulutan"]

SILKING_DOY_START = 196   # mid-July
SILKING_DOY_END = 227     # mid-August
DEKAD_FOLLOWING = 10      # days after window-end to look for ETa confirmation

# (year, label, note) — drawn from el_nino_agricultural_risks.md
LABELED_EVENTS: dict[int, tuple[str, str]] = {
    1997: ("severe-moderate", "Super El Niño; FAO 'considerably below-average' 2nd-season maize"),
    2002: ("moderate",        "Moderate El Niño"),
    2009: ("moderate",        "Moderate El Niño"),
    2014: ("moderate",        "Weak El Niño precursor; CHIRPS deficits documented late summer"),
    2015: ("severe",          "Very Strong El Niño; 60% maize / 80% beans loss in Dry Corridor"),
    2018: ("moderate",        "Weak El Niño; postrera impact even at weak strength (FAO 2018)"),
    2023: ("moderate",        "Strong El Niño; one-month delay to postrera; 25%+ subsistence yield reduction"),
}
POSITIVE_YEARS = set(LABELED_EVENTS.keys())


@dataclass
class TriggerConfig:
    name: str
    spi3_thr: float
    require_rzsm: bool
    rzsm_thr: float
    require_eta: bool
    eta_thr: float
    window: tuple[int, int]


def load_indicator(indicator: str, value_col: str) -> pd.DataFrame:
    """Load and average the eastern Dry Corridor for a given indicator."""
    frames = []
    for dep in DRY_CORRIDOR:
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
        frames.append(df[["date", "year", "doy", value_col]])
    if not frames:
        return pd.DataFrame()
    full = pd.concat(frames, ignore_index=True)
    # Average across departamentos by (date)
    agg = full.groupby("date", as_index=False).agg(
        year=("year", "first"),
        doy=("doy", "first"),
        value=(value_col, "mean"),
    )
    return agg.sort_values("date").reset_index(drop=True)


def years_available(df: pd.DataFrame, doy_window: tuple[int, int]) -> set[int]:
    if df.empty:
        return set()
    in_window = df[(df["doy"] >= doy_window[0]) & (df["doy"] <= doy_window[1])]
    return set(in_window["year"].unique())


def evaluate_spi_only(spi: pd.DataFrame, cfg: TriggerConfig) -> dict:
    """Single-indicator (SPI-3) trigger. Used for the long-baseline analysis."""
    years = sorted(years_available(spi, cfg.window))
    fires: dict[int, dict] = {}
    for y in years:
        sub = spi[(spi["year"] == y) &
                  (spi["doy"] >= cfg.window[0]) &
                  (spi["doy"] <= cfg.window[1])]
        if sub.empty or sub["value"].dropna().empty:
            continue
        min_val = sub["value"].min()
        idx_min = sub["value"].idxmin()
        fire = bool(min_val < cfg.spi3_thr)
        fires[y] = {
            "fire": fire,
            "min_spi3": float(min_val),
            "fire_date": pd.to_datetime(sub.loc[idx_min, "date"]).date() if fire else None,
        }
    return _score(fires, cfg)


def evaluate_combo(spi: pd.DataFrame, rzsm: pd.DataFrame, eta: pd.DataFrame, cfg: TriggerConfig) -> dict:
    """Combined SPI + RZSM (and optionally ETa) trigger."""
    years = sorted(years_available(spi, cfg.window) &
                   (years_available(rzsm, cfg.window) if cfg.require_rzsm else years_available(spi, cfg.window)))
    fires: dict[int, dict] = {}
    for y in years:
        sub_spi = spi[(spi["year"] == y) &
                      (spi["doy"] >= cfg.window[0]) &
                      (spi["doy"] <= cfg.window[1])]
        if sub_spi.empty or sub_spi["value"].dropna().empty:
            continue
        min_spi = sub_spi["value"].min()
        cond_spi = min_spi < cfg.spi3_thr

        cond_rzsm = True
        min_rzsm = None
        if cfg.require_rzsm:
            sub_rzsm = rzsm[(rzsm["year"] == y) &
                            (rzsm["doy"] >= cfg.window[0]) &
                            (rzsm["doy"] <= cfg.window[1])]
            if sub_rzsm.empty or sub_rzsm["value"].dropna().empty:
                cond_rzsm = False
            else:
                min_rzsm = sub_rzsm["value"].min()
                cond_rzsm = min_rzsm < cfg.rzsm_thr

        cond_eta = True
        min_eta = None
        if cfg.require_eta:
            sub_eta = eta[(eta["year"] == y) &
                          (eta["doy"] >= cfg.window[0]) &
                          (eta["doy"] <= cfg.window[1] + DEKAD_FOLLOWING)]
            if sub_eta.empty or sub_eta["value"].dropna().empty:
                cond_eta = False
            else:
                min_eta = sub_eta["value"].min()
                cond_eta = min_eta < cfg.eta_thr

        fire = bool(cond_spi and cond_rzsm and cond_eta)
        fires[y] = {
            "fire": fire,
            "min_spi3": float(min_spi),
            "min_rzsm": float(min_rzsm) if min_rzsm is not None else None,
            "min_eta": float(min_eta) if min_eta is not None else None,
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
    fp_per_decade = fp / n_years * 10 if n_years else float("nan")

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


def sweep_spi_only(spi: pd.DataFrame) -> list[dict]:
    thresholds = [-0.8, -1.0, -1.3, -1.5, -1.7]
    windows = [
        (196, 227),  # mid-Jul to mid-Aug — silking
        (181, 243),  # full Jul-Aug
        (213, 273),  # postrera planting/early growth
    ]
    results = []
    for thr in thresholds:
        for window in windows:
            cfg = TriggerConfig(
                name=f"SPI3<{thr} in DOY {window[0]}-{window[1]}",
                spi3_thr=thr,
                require_rzsm=False, rzsm_thr=0.0,
                require_eta=False, eta_thr=0.0,
                window=window,
            )
            results.append(evaluate_spi_only(spi, cfg))
    return results


def sweep_combo(spi: pd.DataFrame, rzsm: pd.DataFrame, eta: pd.DataFrame) -> list[dict]:
    spi_thrs = [-1.0, -1.3, -1.5]
    rzsm_thrs = [-0.5, -1.0]
    window = (196, 227)
    results = []
    for s in spi_thrs:
        for r in rzsm_thrs:
            for require_eta in (False, True):
                cfg = TriggerConfig(
                    name=(f"SPI3<{s} ∧ RZSM<{r}σ" +
                          (" ∧ ETa<0" if require_eta else "")),
                    spi3_thr=s,
                    require_rzsm=True, rzsm_thr=r,
                    require_eta=require_eta, eta_thr=0.0,
                    window=window,
                )
                results.append(evaluate_combo(spi, rzsm, eta, cfg))
    return results


def _fmt(p: float) -> str:
    return f"{p:.2f}" if p == p else "—"  # NaN-safe


def _fmt_ci(ci: tuple[float, float]) -> str:
    lo, hi = ci
    if lo != lo or hi != hi:
        return "—"
    return f"[{lo:.2f}–{hi:.2f}]"


def render_report(spi_results: list[dict], combo_results: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# Trigger Calibration Report")
    lines.append("")
    lines.append("Generated from `el_nino/experiments/trigger_calibration.py`.")
    lines.append("")
    lines.append("**Region:** eastern Dry Corridor (mean of Morazán, San Miguel, La Unión, Usulután).")
    lines.append("**Labels:** drawn from `el_nino/el_nino_agricultural_risks.md`.")
    lines.append("")
    lines.append("**Severe positive:** 2015 (60% maize / 80% beans loss in Dry Corridor).")
    pos_text = ", ".join(str(y) for y in sorted(POSITIVE_YEARS) if not LABELED_EVENTS[y][0].startswith("severe"))
    lines.append(f"**Moderate positives:** {pos_text}.")
    lines.append("**Negatives:** all other years with available data.")
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
    lines.append("## SPI-3 only (long baseline, 1981+)")
    lines.append("")
    lines.append("| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |")
    lines.append("|---|---:|---:|---:|---:|---|---|---|---|")
    for r in spi_results:
        cfg = r["cfg"]
        lines.append(
            f"| {cfg.name} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | "
            f"{_fmt(r['precision'])} {_fmt_ci(r['precision_ci'])} | "
            f"{_fmt(r['recall'])} {_fmt_ci(r['recall_ci'])} | "
            f"{_fmt(r['severe_recall'])} {_fmt_ci(r['severe_recall_ci'])} | "
            f"{_fmt(r['fp_per_decade'])} {_fmt_ci(r['fp_per_decade_ci'])} |"
        )
    lines.append("")

    # Combo table
    lines.append("## Combined SPI-3 ∧ SMAP RZSM (± WAPOR ETa) — recent baseline (2015+)")
    lines.append("")
    lines.append("| Trigger | TP | FP | FN | TN | Precision (95% CI) | Recall (95% CI) | Severe recall (95% CI) | FP/decade (95% CI) |")
    lines.append("|---|---:|---:|---:|---:|---|---|---|---|")
    for r in combo_results:
        cfg = r["cfg"]
        lines.append(
            f"| {cfg.name} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | "
            f"{_fmt(r['precision'])} {_fmt_ci(r['precision_ci'])} | "
            f"{_fmt(r['recall'])} {_fmt_ci(r['recall_ci'])} | "
            f"{_fmt(r['severe_recall'])} {_fmt_ci(r['severe_recall_ci'])} | "
            f"{_fmt(r['fp_per_decade'])} {_fmt_ci(r['fp_per_decade_ci'])} |"
        )
    lines.append("")

    # Per-event detail for the best SPI-only configuration
    lines.append("## Per-year detail (best SPI-3 single-indicator configuration)")
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
    lines.append("| Year | Label | Min SPI-3 | Fired? | Notes |")
    lines.append("|---|---|---:|:---:|---|")
    for y in best_spi["years"]:
        f = best_spi["fires"][y]
        label = LABELED_EVENTS.get(y, ("negative", ""))
        symbol = "✓" if f["fire"] else "—"
        lines.append(f"| {y} | {label[0]} | {f['min_spi3']:.2f} | {symbol} | {label[1]} |")
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
        lines.append("| Year | Label | SPI-3 min | RZSM min (σ) | ETa min (σ) | Fired? |")
        lines.append("|---|---|---:|---:|---:|:---:|")
        for y in best_combo["years"]:
            f = best_combo["fires"][y]
            label = LABELED_EVENTS.get(y, ("negative", ""))
            symbol = "✓" if f["fire"] else "—"
            spi = f.get("min_spi3"); rzsm = f.get("min_rzsm"); eta = f.get("min_eta")
            lines.append(f"| {y} | {label[0]} | {spi:.2f} | "
                         f"{(f'{rzsm:.2f}' if rzsm is not None else '—')} | "
                         f"{(f'{eta:.2f}' if eta is not None else '—')} | {symbol} |")

    lines.append("")
    lines.append("## Operational recommendations")
    lines.append("")
    lines.append("1. Use the **SPI-only** trigger for the long-baseline alert (will fire whenever SPI-3 falls below threshold during silking).")
    lines.append("2. Use the **combined trigger** as a higher-confidence escalation: only fires when soil-moisture and ET independently confirm the rainfall deficit.")
    lines.append("3. SMAP-based combined triggers only have ~10 years of history (2015+), so confidence in their FP rate is limited — re-run this calibration annually as more data accumulates.")
    return "\n".join(lines)


def _pick_recommended(results: list[dict]) -> dict | None:
    """Pick the configuration that catches the most severe events while keeping
    FP rate below ~1 per decade. Tiebreak: prefer higher precision."""
    candidates = [r for r in results if r.get("severe_recall", 0) >= 0.99
                  and r.get("fp_per_decade", 99) <= 1.0]
    if not candidates:
        # Fall back to highest severe recall + lowest FP/decade
        candidates = sorted(results,
                            key=lambda r: (-r.get("severe_recall", 0), r.get("fp_per_decade", 99)))[:3]
    return max(candidates, key=lambda r: (r.get("severe_recall", 0), r.get("precision", 0)))


def main() -> None:
    spi = load_indicator("chirps", "spi_3")
    rzsm = load_indicator("smap", "value_anom_z")
    eta = load_indicator("wapor", "value_anom_z")

    if spi.empty:
        print("ERROR: no CHIRPS SPI-3 data available. Run `python -m el_nino.etl.run_etl finalize` first.")
        return

    spi_results = sweep_spi_only(spi)
    combo_results = sweep_combo(spi, rzsm, eta)

    report = render_report(spi_results, combo_results)
    out = Path(__file__).parent / "trigger_calibration_report.md"
    out.write_text(report)
    print(f"Wrote {out}")

    # Console summary
    print()
    print("=== TOP SPI-only configurations (by severe recall, then lowest FP/decade) ===")
    top_spi = sorted(spi_results,
                     key=lambda r: (-r.get("severe_recall", 0), r.get("fp_per_decade", 99)))[:5]
    for r in top_spi:
        cfg = r["cfg"]
        print(f"  {cfg.name:<55} prec={r['precision']:.2f} rec={r['recall']:.2f} "
              f"severe={r['severe_recall']:.2f} fp/dec={r['fp_per_decade']:.2f}")


if __name__ == "__main__":
    main()
