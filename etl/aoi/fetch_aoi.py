"""One-time script: fetch the active country's ADM1 polygons from FAO/GAUL via
Earth Engine, save as GeoJSON. Run once per country with GEE access.

    python -m el_nino.etl.aoi.fetch_aoi                  # active COUNTRY
    COUNTRY=haiti python -m el_nino.etl.aoi.fetch_aoi    # specific country
"""

from __future__ import annotations

import json
from pathlib import Path

import ee

from ... import config
from .. import gee


def main() -> None:
    gee.init()
    adm0 = config.CC["gaul_adm0_name"]
    fc = (
        ee.FeatureCollection("FAO/GAUL/2015/level1")
        .filter(ee.Filter.eq("ADM0_NAME", adm0))
    )
    geojson = fc.getInfo()

    out = Path(config.AOI_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        json.dump(geojson, f)

    names = sorted(feat["properties"]["ADM1_NAME"] for feat in geojson["features"])
    print(f"Wrote {out} with {len(names)} ADM1 features for {adm0}:")
    for n in names:
        print(f"  - {n}")


if __name__ == "__main__":
    main()
