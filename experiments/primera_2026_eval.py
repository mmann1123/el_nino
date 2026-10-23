"""Did the drought inputs see the 2026 primera damage where the field saw it?

Acceso's field assessment: irreversible primera maize damage concentrated in the
far east (La Union, Morazan); the west (Santa Ana) needed far less intervention.
FEWS NET's April 2026 update placed the *early-season* soil-moisture deficits
mainly in the west, so the test is run per crop stage, not just per season.

Run from the parent directory, like the rest of the package:

    python -m el_nino.experiments.primera_2026_eval            # fetch (cached) + analyze
    python -m el_nino.experiments.primera_2026_eval --analyze  # analyze cached pulls only

For every department, metric, crop stage and mask, the 2026 value is turned
into a z-score against that department's own baseline years, oriented so that
negative = drier / more stressed. A metric "agrees with the field" for a stage
when La Union and Morazan both rank among the 5 most stressed of 14
departments and are more stressed on average than Santa Ana.

Two masks per metric:
  all   — whole-department mean, which is what the dashboard ETL does today
  crop  — mean weighted by ESA WorldCover 2021 cropland fraction (300 m)

Metrics:
  rain_mm        CHIRPS daily, stage total
  dry_spell_days CHIRPS daily, longest run of days < 1 mm (on the dept mean)
  rzsm_smap      SMAP L4 root-zone soil moisture (the dashboard's input)
  sm_era5        ERA5-Land soil water layer 2 (7-28 cm)
  aeti_mm        WaPOR v3 L1 actual ET (the dashboard's input)
  rel_et         WaPOR AETI / RET — ET relative to atmospheric demand
  ndvi           MODIS MOD13Q1 250 m

Outputs: <STORAGE_ROOT>/eval_primera_2026/ (cached pulls, scores.csv) and
el_nino/experiments/primera_2026_eval_report.md (+ heatmap png).
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from el_nino import config  # noqa: E402

YEAR = 2026
EAST = ["La Union", "Morazan"]
WEST = ["Santa Ana"]
TOP_N = 5  # "among the most stressed" = rank <= TOP_N of 14

# West → east, for the heatmap.
DEPT_ORDER = [
    "Ahuachapan", "Santa Ana", "Sonsonate", "La Libertad", "Chalatenango",
    "San Salvador", "Cuscatlan", "La Paz", "Cabanas", "San Vicente",
    "Usulutan", "San Miguel", "Morazan", "La Union",
]

# Primera maize stages. Planting advised late April (FEWS NET Apr 2026);
# canícula overlaps silking/grain fill; "response" lags it for NDVI/ET.
PERIODS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "establishment": ((4, 20), (6, 15)),
    "canicula":      ((7, 1), (8, 20)),
    "response":      ((7, 15), (9, 10)),
    "season":        ((4, 20), (8, 31)),
}
FETCH_WINDOW = ((4, 15), (9, 15))
SCALE = 300  # one reduce scale so the cropland weights mean the same thing everywhere

OUT_DIR = config.STORAGE_ROOT / "eval_primera_2026"
REPORT_PATH = Path(__file__).with_name("primera_2026_eval_report.md")
HEATMAP_PATH = Path(__file__).with_name("primera_2026_eval_heatmap.png")


@dataclass
class Source:
    key: str
    first_year: int
    build: Callable[[str, str], object]  # (start, end) -> ee.ImageCollection with band "v"


def _sources() -> list[Source]:
    import ee
    from el_nino.etl.indicators.base import Indicator

    def chirps(s, e):
        return ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(s, e).select(["precipitation"], ["v"])

    def smap(s, e):
        raw = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").filterDate(s, e).select("sm_rootzone")
        return Indicator.daily_aggregate(raw, lambda ic: ic.mean(), "v")

    def era5(s, e):
        return (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate(s, e)
                .select(["volumetric_soil_water_layer_2"], ["v"]))

    def aeti(s, e):
        return ee.ImageCollection("FAO/WAPOR/3/L1_AETI_D").filterDate(s, e).select(["L1-AETI-D"], ["v"])

    def ret(s, e):
        return ee.ImageCollection("FAO/WAPOR/3/L1_RET_D").filterDate(s, e).select(["L1-RET-D"], ["v"])

    def ndvi(s, e):
        return (ee.ImageCollection("MODIS/061/MOD13Q1").filterDate(s, e)
                .map(lambda i: i.select(["NDVI"], ["v"]).multiply(0.0001)
                     .copyProperties(i, ["system:time_start"])))

    return [
        Source("chirps", 2001, chirps),
        Source("smap", 2015, smap),
        Source("era5", 2001, era5),
        Source("aeti", 2018, aeti),
        Source("ret", 2018, ret),
        Source("ndvi", 2001, ndvi),
    ]


# ---- fetch ----

def _crop_fraction():
    """Cropland fraction as a fractional mask: GEE's mean reducer weights each
    pixel by its mask, so coarse SMAP/CHIRPS cells count in proportion to their
    cropland."""
    from el_nino.etl.indicators.base import cropland_fraction
    return cropland_fraction()


def _reduce(coll, aoi, crop) -> pd.DataFrame:
    import ee

    def per_image(img):
        v = ee.Image(img).select("v")
        both = v.rename("all").addBands(v.updateMask(crop).rename("crop"))
        stats = both.reduceRegions(collection=aoi, reducer=ee.Reducer.mean(), scale=SCALE, tileScale=4)
        d = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd")
        return stats.map(lambda f: ee.Feature(None, {
            "date": d, "departamento": f.get("ADM1_NAME"), "all": f.get("all"), "crop": f.get("crop"),
        }))

    info = ee.FeatureCollection(coll.map(per_image)).flatten().getInfo()
    return pd.DataFrame([f["properties"] for f in info["features"]])


def fetch(refresh: bool = False, sources: list[Source] | None = None) -> None:
    import ee
    from el_nino.etl import gee
    from ee.ee_exception import EEException

    gee.init()
    aoi = ee.FeatureCollection(_load_aoi())
    crop = _crop_fraction()
    (OUT_DIR / "raw").mkdir(parents=True, exist_ok=True)

    def pull(src: Source, year: int) -> None:
        path = OUT_DIR / "raw" / f"{src.key}_{year}.parquet"
        start, end = date(year, *FETCH_WINDOW[0]), date(year, *FETCH_WINDOW[1])
        try:
            df = _reduce(src.build(start.isoformat(), end.isoformat()), aoi, crop)
        except EEException as e:
            # One window too heavy for an interactive call: fall back to months.
            print(f"    {src.key} {year}: splitting by month after: {e}", flush=True)
            parts = []
            for m in range(start.month, end.month + 1):
                ms = date(year, m, 1) if m != start.month else start
                me = date(year + (m == 12), m % 12 + 1, 1) if m != end.month else end
                parts.append(_reduce(src.build(ms.isoformat(), me.isoformat()), aoi, crop))
            df = pd.concat(parts, ignore_index=True)
        df.to_parquet(path, index=False)
        print(f"  {src.key} {year}: {len(df)} rows", flush=True)

    jobs = [
        (src, year)
        for src in (sources or _sources())
        for year in range(src.first_year, YEAR + 1)
        if not (OUT_DIR / "raw" / f"{src.key}_{year}.parquet").exists() or (refresh and year == YEAR)
    ]
    print(f"{len(jobs)} source-years to pull", flush=True)
    # Earth Engine serves concurrent interactive requests; each call is mostly
    # waiting on the server, so threads cut wall time roughly by the pool size.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fut in as_completed([pool.submit(pull, s, y) for s, y in jobs]):
            try:
                fut.result()
            except Exception as e:  # a failed year is reported and retried on the next run
                print(f"    FAILED: {e}", flush=True)


def _load_aoi() -> dict:
    import json
    with open(config.AOI_PATH) as f:
        return json.load(f)


# ---- analyze ----

def _load(key: str) -> pd.DataFrame:
    files = sorted((OUT_DIR / "raw").glob(f"{key}_*.parquet"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df = df[df["departamento"].isin(DEPT_ORDER)]
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    long = df.melt(id_vars=["date", "year", "departamento"], value_vars=["all", "crop"],
                   var_name="mask", value_name="v")
    long["v"] = pd.to_numeric(long["v"], errors="coerce")
    return long.dropna(subset=["v"])


def _in_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    (m0, d0), (m1, d1) = PERIODS[period]
    md = df["date"].dt.month * 100 + df["date"].dt.day
    return df[(md >= m0 * 100 + d0) & (md <= m1 * 100 + d1)]


def _longest_dry_run(v: pd.Series, thr_mm: float = 1.0) -> int:
    best = run = 0
    for dry in (v.to_numpy() < thr_mm):
        run = run + 1 if dry else 0
        best = max(best, run)
    return best


def stage_values() -> pd.DataFrame:
    """One row per (metric, period, mask, departamento, year) with the stage value."""
    keys = ["mask", "departamento", "year"]
    data = {k: _load(k) for k in ["chirps", "smap", "era5", "aeti", "ret", "ndvi"]}
    out = []
    for period in PERIODS:
        p = {k: _in_period(v, period) for k, v in data.items() if not v.empty}
        metrics = {}
        if "chirps" in p:
            g = p["chirps"].sort_values("date").groupby(keys)["v"]
            metrics["rain_mm"] = g.sum()
            metrics["dry_spell_days"] = g.apply(_longest_dry_run)
        for key, name, how in [("smap", "rzsm_smap", "mean"), ("era5", "sm_era5", "mean"),
                               ("aeti", "aeti_mm", "sum"), ("ndvi", "ndvi", "mean")]:
            if key in p:
                metrics[name] = p[key].groupby(keys)["v"].agg(how)
        if "aeti" in p and "ret" in p:
            # Ratio of stage totals; unit convention cancels as long as both
            # WaPOR layers share it.
            metrics["rel_et"] = p["aeti"].groupby(keys)["v"].sum() / p["ret"].groupby(keys)["v"].sum()
        for name, s in metrics.items():
            df = s.rename("value").reset_index()
            df["metric"], df["period"] = name, period
            out.append(df)
    return pd.concat(out, ignore_index=True)


WORSE_IS_HIGHER = {"dry_spell_days"}


def zscores(vals: pd.DataFrame) -> pd.DataFrame:
    """Orient each 2026 value as a z-score against its own dept's baseline years."""
    rows = []
    for (metric, period, mask, dep), g in vals.groupby(["metric", "period", "mask", "departamento"]):
        base = g.loc[g["year"] < YEAR, "value"]
        cur = g.loc[g["year"] == YEAR, "value"]
        if cur.empty or len(base) < 5 or base.std(ddof=1) == 0:
            continue
        z = (cur.iloc[0] - base.mean()) / base.std(ddof=1)
        rows.append({
            "metric": metric, "period": period, "mask": mask, "departamento": dep,
            "value_2026": cur.iloc[0], "baseline_mean": base.mean(), "n_baseline": len(base),
            "z": -z if metric in WORSE_IS_HIGHER else z,
        })
    return pd.DataFrame(rows)


def field_test(z: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (metric, period, mask), g in z.groupby(["metric", "period", "mask"]):
        g = g.assign(rank=g["z"].rank(method="min"))  # 1 = most stressed
        r = g.set_index("departamento")
        if not set(EAST + WEST) <= set(r.index):
            continue
        east_rank = r.loc[EAST, "rank"]
        gap = r.loc[EAST, "z"].mean() - r.loc[WEST, "z"].mean()
        rows.append({
            "metric": metric, "period": period, "mask": mask, "n_depts": len(g),
            **{f"z_{d}": r.loc[d, "z"] for d in EAST + WEST},
            **{f"rank_{d}": int(r.loc[d, "rank"]) for d in EAST + WEST},
            "east_minus_west_z": gap,
            "agrees": bool((east_rank <= TOP_N).all() and gap < 0),
        })
    return pd.DataFrame(rows).sort_values(["period", "east_minus_west_z"])


def heatmap(z: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = [(p, m) for p in ["establishment", "canicula"] for m in ["all", "crop"]]
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True, sharey=True)
    for ax, (period, mask) in zip(axes.flat, panels):
        sub = z[(z["period"] == period) & (z["mask"] == mask)]
        grid = sub.pivot(index="metric", columns="departamento", values="z").reindex(columns=DEPT_ORDER)
        im = ax.imshow(grid.to_numpy(), cmap="RdBu", vmin=-2.5, vmax=2.5, aspect="auto")
        ax.set_yticks(range(len(grid.index)), grid.index)
        ax.set_xticks(range(len(DEPT_ORDER)), DEPT_ORDER, rotation=60, ha="right")
        ax.set_title(f"{period} — {mask} pixels")
        for d in EAST + WEST:
            x = DEPT_ORDER.index(d)
            ax.axvline(x - 0.5, color="k", lw=0.5)
            ax.axvline(x + 0.5, color="k", lw=0.5)
    fig.colorbar(im, ax=axes, shrink=0.6, label="2026 z-score (negative = drier / more stressed)")
    fig.suptitle(f"Primera {YEAR}: 2026 anomaly by department, west → east")
    fig.savefig(HEATMAP_PATH, dpi=150, bbox_inches="tight")


def write_report(test: pd.DataFrame) -> None:
    cols = ["metric", "mask", "rank_La Union", "rank_Morazan", "rank_Santa Ana",
            "east_minus_west_z", "agrees"]
    lines = [
        f"# Primera {YEAR} — do the inputs see the field-reported damage?",
        "",
        f"Field: irreversible damage in {' and '.join(EAST)}; {WEST[0]} much less affected.",
        f"A metric agrees when both eastern departments rank in the {TOP_N} most stressed "
        "of 14 and their mean z is below Santa Ana's. Rank 1 = most stressed. "
        "`east_minus_west_z` < 0 means the east looks worse, as the field reported.",
        "",
        f"![heatmap]({HEATMAP_PATH.name})",
        "",
    ]
    for period in PERIODS:
        t = test[test["period"] == period][cols].copy()
        t["east_minus_west_z"] = t["east_minus_west_z"].round(2)
        lines += [f"## {period} ({PERIODS[period][0][0]}/{PERIODS[period][0][1]}–"
                  f"{PERIODS[period][1][0]}/{PERIODS[period][1][1]})", "", t.to_markdown(index=False), ""]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def analyze() -> None:
    vals = stage_values()
    z = zscores(vals)
    test = field_test(z)
    z.to_csv(OUT_DIR / "zscores.csv", index=False)
    test.to_csv(OUT_DIR / "scores.csv", index=False)
    heatmap(z)
    write_report(test)
    print(test.to_string(index=False))
    print(f"\nReport: {REPORT_PATH}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--analyze", action="store_true", help="skip fetching; use cached pulls")
    ap.add_argument("--refresh", action="store_true", help=f"re-pull {YEAR} even if cached")
    args = ap.parse_args()
    if not args.analyze:
        fetch(refresh=args.refresh)
    analyze()


if __name__ == "__main__":
    main()
