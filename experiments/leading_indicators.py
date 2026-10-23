"""Is there a non-rainfall leading indicator of primera crop stress?

A leading indicator has to be readable *before* silking and still point at the
departments whose crop later fails. Each candidate is read over two lead
windows that end before the canícula damage (establishment, pre-canícula) and
scored against the crop outcome that follows: cropland NDVI over Jul 15-Sep 10.

Three scores per candidate (window, mask):
  field_2026   La Union and Morazan both in the 5 most stressed of 14 and
               worse than Santa Ana — Acceso's field assessment for 2026
  rho_2026     Spearman across the 14 departments, lead z vs outcome z, 2026
  r_panel      Pearson over every department-year 2001-2025, lead z vs outcome z
  auc_panel    how well the lead z separates department-years whose outcome z
               fell below -1 (0.5 = chance)

Rainfall metrics are kept in the table as the baseline to beat. Reuses the
cached pulls from primera_2026_eval and adds LST, VPD and SMAP surface.

    python -m el_nino.experiments.leading_indicators            # fetch (cached) + analyze
    python -m el_nino.experiments.leading_indicators --analyze
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from el_nino.experiments import primera_2026_eval as ev  # noqa: E402

LEAD_PERIODS = {
    "establishment": ((4, 20), (6, 15)),
    "pre_canicula":  ((6, 15), (7, 10)),
}
OUTCOME_PERIOD = ((7, 15), (9, 10))
OUTCOME_THRESHOLD_Z = -1.0

# metric -> (cached source key, aggregation, higher is worse, is rainfall)
METRICS = {
    "lst_day_c":      ("lst", "mean", True, False),
    "vpd_kpa":        ("vpd", "mean", True, False),
    "ssm_smap":       ("smap_surface", "mean", False, False),
    "rzsm_smap":      ("smap", "mean", False, False),
    "sm_era5":        ("era5", "mean", False, False),
    "aeti_mm":        ("aeti", "sum", False, False),
    "ndvi":           ("ndvi", "mean", False, False),
    "rain_mm":        ("chirps", "sum", False, True),
    "dry_spell_days": ("chirps", "dry", True, True),
}

REPORT_PATH = Path(__file__).with_name("leading_indicators_report.md")


def _new_sources() -> list:
    import ee
    from el_nino.etl.indicators.base import Indicator
    Source = ev.Source

    def lst(s, e):
        return (ee.ImageCollection("MODIS/061/MOD11A2").filterDate(s, e)
                .map(lambda i: ee.Image(i.select("LST_Day_1km").multiply(0.02).subtract(273.15)
                                        .rename("v").copyProperties(i, ["system:time_start"]))))

    def vpd(s, e):
        # Daily-max VPD from ERA5-Land: es(Tmax) - ea(Td), Tetens, kPa.
        def one(i):
            t = i.select("temperature_2m_max").subtract(273.15)
            td = i.select("dewpoint_temperature_2m").subtract(273.15)
            es = t.multiply(17.27).divide(t.add(237.3)).exp().multiply(0.6108)
            ea = td.multiply(17.27).divide(td.add(237.3)).exp().multiply(0.6108)
            return ee.Image(es.subtract(ea).rename("v").copyProperties(i, ["system:time_start"]))
        return ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate(s, e).map(one)

    def smap_surface(s, e):
        raw = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").filterDate(s, e).select("sm_surface")
        return Indicator.daily_aggregate(raw, lambda ic: ic.mean(), "v")

    return [
        Source("lst", 2001, lst),
        Source("vpd", 2001, vpd),
        Source("smap_surface", 2015, smap_surface),
    ]


def _in(df: pd.DataFrame, window) -> pd.DataFrame:
    (m0, d0), (m1, d1) = window
    md = df["date"].dt.month * 100 + df["date"].dt.day
    return df[(md >= m0 * 100 + d0) & (md <= m1 * 100 + d1)]


def _panel_z(values: pd.Series, worse_is_higher: bool) -> pd.Series:
    """z per department-year against that department's pre-2026 years,
    oriented so negative = more stressed."""
    df = values.rename("v").reset_index()
    base = df[df["year"] < ev.YEAR].groupby(["mask", "departamento"])["v"].agg(["mean", "std"])
    df = df.join(base, on=["mask", "departamento"])
    z = (df["v"] - df["mean"]) / df["std"]
    df["z"] = -z if worse_is_higher else z
    return df.set_index(["mask", "departamento", "year"])["z"]


def _auc(score: np.ndarray, positive: np.ndarray) -> float:
    """P(a positive scores lower than a negative) — lower z = more stressed."""
    pos, neg = score[positive], score[~positive]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    ranks = pd.Series(np.concatenate([pos, neg])).rank().to_numpy()
    u = ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2
    return 1 - u / (len(pos) * len(neg))


def analyze() -> pd.DataFrame:
    keys = ["mask", "departamento", "year"]
    data = {k: ev._load(k) for k in {m[0] for m in METRICS.values()}}

    outcome = _panel_z(_in(data["ndvi"], OUTCOME_PERIOD).groupby(keys)["v"].mean(), False)
    outcome = outcome.xs("crop", level="mask")

    rows = []
    for metric, (src, how, worse_high, is_rain) in METRICS.items():
        if data[src].empty:
            continue
        for period, window in LEAD_PERIODS.items():
            g = _in(data[src], window).sort_values("date").groupby(keys)["v"]
            vals = g.apply(ev._longest_dry_run) if how == "dry" else g.agg(how)
            z = _panel_z(vals, worse_high)
            for mask in ["all", "crop"]:
                zm = z.xs(mask, level="mask").dropna()
                both = pd.concat([zm.rename("lead"), outcome.rename("out")], axis=1, join="inner").dropna()
                hist = both[both.index.get_level_values("year") < ev.YEAR]
                cur = both[both.index.get_level_values("year") == ev.YEAR].droplevel("year")
                if len(cur) < 10:
                    continue
                gap = cur.loc[ev.EAST, "lead"].mean() - cur.loc[ev.WEST, "lead"].mean()
                rank = cur["lead"].rank(method="min")
                rows.append({
                    "metric": metric, "rainfall": is_rain, "window": period, "mask": mask,
                    "rank_La Union": int(rank["La Union"]), "rank_Morazan": int(rank["Morazan"]),
                    "rank_Santa Ana": int(rank["Santa Ana"]),
                    "field_2026": bool((rank[ev.EAST] <= ev.TOP_N).all() and gap < 0),
                    "rho_2026": cur["lead"].corr(cur["out"], method="spearman"),
                    "r_panel": hist["lead"].corr(hist["out"]),
                    "auc_panel": _auc(hist["lead"].to_numpy(), (hist["out"] < OUTCOME_THRESHOLD_Z).to_numpy()),
                    "n_panel": len(hist),
                    "years": f"{hist.index.get_level_values('year').min()}-{ev.YEAR - 1}",
                })
    res = pd.DataFrame(rows).sort_values(["field_2026", "auc_panel"], ascending=False)
    res.to_csv(ev.OUT_DIR / "leading_scores.csv", index=False)

    fmt = res.copy()
    for c in ["rho_2026", "r_panel", "auc_panel"]:
        fmt[c] = fmt[c].round(2)
    REPORT_PATH.write_text("\n".join([
        f"# Leading indicators of primera crop stress — {ev.YEAR} check + 2001-{ev.YEAR - 1} track record",
        "",
        "Lead windows end before silking; outcome is cropland NDVI z, Jul 15-Sep 10. "
        "Rank 1 = most stressed of 14 in 2026. `rho_2026` and `r_panel` > 0 mean early "
        "stress went with poor later crop condition; `auc_panel` is skill at flagging "
        f"department-years with outcome z < {OUTCOME_THRESHOLD_Z} (0.5 = chance).",
        "",
        fmt.to_markdown(index=False),
        "",
    ]), encoding="utf-8")
    print(fmt.to_string(index=False))
    print(f"\nReport: {REPORT_PATH}")
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--analyze", action="store_true", help="skip fetching; use cached pulls")
    args = ap.parse_args()
    if not args.analyze:
        ev.fetch(sources=_new_sources())
    analyze()


if __name__ == "__main__":
    main()
