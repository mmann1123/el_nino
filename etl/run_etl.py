"""ETL orchestrator. Local CLI entry point; identical entry on Cloud Run Job.

Examples:
    # Generate a full synthetic dataset (no GEE access needed)
    python -m el_nino.etl.run_etl synth --start 1995-01-01 --end 2026-05-28

    # Fetch a single indicator window from GEE (requires earthengine auth)
    python -m el_nino.etl.run_etl fetch --indicator chirps --start 2026-04-01 --end 2026-05-28

    # Recompute climatology after fetching/synth
    python -m el_nino.etl.run_etl climatology

    # Refresh NOAA ONI
    python -m el_nino.etl.run_etl enso

    # Full cycle on existing parquets (climatology + anomaly + freshness)
    python -m el_nino.etl.run_etl finalize
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta

from .. import config
from . import climatology, enso, synth
from .indicators import INDICATORS


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def cmd_synth(args) -> None:
    config.ensure_dirs()
    start = args.start or date(1995, 1, 1)
    end = args.end or config.today()
    print(f"Synthesizing data {start} -> {end}")
    enso_df = enso.load()
    if enso_df.empty:
        try:
            enso_df = enso.fetch()
            enso.save(enso_df)
            print(f"  fetched ONI ({len(enso_df)} rows)")
        except Exception as e:
            print(f"  could not fetch ONI ({e}); proceeding with default El Niño year set")

    print("  chirps...")
    synth.synth_chirps(start, end)
    print("  smap...")
    synth.synth_smap(start, end)
    print("  ssebop...")
    synth.synth_ssebop(start, end)
    print("  imerg...")
    synth.synth_imerg(start, end)

    cmd_finalize(args)


def cmd_fetch(args) -> None:
    config.ensure_dirs()
    indicator_cls = INDICATORS[args.indicator]
    indicator = indicator_cls()
    start = args.start or (config.today() - timedelta(days=14))
    end = args.end or config.today()
    print(f"Fetching {args.indicator} from GEE for {start} -> {end}")
    df = indicator.fetch(start, end)
    if df.empty:
        print("  (no rows returned)")
        return
    from . import storage
    for dep, group in df.groupby("departamento"):
        storage.upsert_raw(args.indicator, dep, group.copy())
    print(f"  wrote {len(df)} rows across {df['departamento'].nunique()} departamentos")


def cmd_backfill(args) -> None:
    """Chunked historical backfill — iterates the requested window, fetches each
    chunk, writes incrementally so a partial failure doesn't lose progress.
    """
    config.ensure_dirs()
    indicator_cls = INDICATORS[args.indicator]
    indicator = indicator_cls()
    start = args.start or date(1981, 1, 1)
    end = args.end or config.today()
    chunk = args.chunk_months or indicator.default_chunk_months
    print(f"Backfilling {args.indicator}: {start} -> {end} in {chunk}-month chunks")

    from . import storage

    def writer(dep: str, group):
        storage.upsert_raw(args.indicator, dep, group)

    total = indicator.backfill(start, end, writer=writer, chunk_months=chunk, on_progress=print)
    print(f"Done. {total} rows written.")

    # CHIRPS SPI must be recomputed across the *full* history once the parquets
    # are stitched together, otherwise per-chunk SPI fits would be wrong.
    if args.indicator == "chirps":
        print("Recomputing SPI across the full record...")
        from .indicators.chirps import recompute_spi_for_all_parquets
        recompute_spi_for_all_parquets()
        print("SPI updated.")


def cmd_climatology(args) -> None:
    config.ensure_dirs()
    for name, cls in INDICATORS.items():
        print(f"Climatology for {name}...")
        clim = climatology.compute_for_indicator(name, cls.value_columns)
        if clim.empty:
            print("  (no input data)")
            continue
        climatology.save(name, clim)
        print(f"  wrote {len(clim)} rows")


def cmd_enso(args) -> None:
    config.ensure_dirs()
    df = enso.fetch()
    enso.save(df)
    print(f"Saved ONI: {len(df)} rows; {len(enso.el_nino_years(df))} El Niño years on record")


def cmd_finalize(args) -> None:
    """Run SPI recompute + climatology + per-indicator anomaly attachment + freshness write."""
    # CHIRPS SPI depends on the full history; recompute first so the
    # value_anom_z attached below uses up-to-date SPI series.
    print("Recomputing CHIRPS SPI across full record...")
    from .indicators.chirps import recompute_spi_for_all_parquets
    recompute_spi_for_all_parquets()

    cmd_climatology(args)
    print("Attaching anomaly z-scores...")
    for name in INDICATORS:
        synth.attach_anomaly_z(name)
    print("Writing freshness.json...")
    synth.update_freshness(config.today())


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_synth = sub.add_parser("synth", help="generate synthetic dataset")
    p_synth.add_argument("--start", type=_parse_date, default=None)
    p_synth.add_argument("--end", type=_parse_date, default=None)
    p_synth.set_defaults(func=cmd_synth)

    p_fetch = sub.add_parser("fetch", help="pull a single window from GEE (small, one-shot)")
    p_fetch.add_argument("--indicator", required=True, choices=list(INDICATORS))
    p_fetch.add_argument("--start", type=_parse_date, default=None)
    p_fetch.add_argument("--end", type=_parse_date, default=None)
    p_fetch.set_defaults(func=cmd_fetch)

    p_back = sub.add_parser("backfill", help="chunked historical backfill from GEE")
    p_back.add_argument("--indicator", required=True, choices=list(INDICATORS))
    p_back.add_argument("--start", type=_parse_date, default=None,
                        help="default: 1981-01-01")
    p_back.add_argument("--end", type=_parse_date, default=None,
                        help="default: today")
    p_back.add_argument("--chunk-months", type=int, default=None,
                        help="default: per-indicator hint (CHIRPS 24, SMAP 12, SSEBop 60, IMERG 6)")
    p_back.set_defaults(func=cmd_backfill)

    p_clim = sub.add_parser("climatology", help="recompute per-DOY fences")
    p_clim.set_defaults(func=cmd_climatology)

    p_enso = sub.add_parser("enso", help="refresh NOAA ONI")
    p_enso.set_defaults(func=cmd_enso)

    p_final = sub.add_parser("finalize", help="climatology + anomaly + freshness")
    p_final.set_defaults(func=cmd_finalize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
