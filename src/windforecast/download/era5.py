"""Download ERA5 hourly wind for the site, one file per year.

Second long-term reference alongside COSMO-R6G2 (II.3.2, IV). The CDS subsets
server-side, so each year is a small file despite the long record.

One request per year: the whole period in a single request exceeds the CDS field
limit, and one request per month would spend the day in the queue. Existing files
are skipped, so an interrupted run resumes.

Requires a CDS key in ~/.cdsapirc - see https://cds.climate.copernicus.eu/how-to-api

Usage:  uv run python -m windforecast.download.era5
"""

import sys

import cdsapi

from .. import config
from ..paths import RAW_ERA5


def main() -> int:
    cfg = config.load()["reference_data"]["era5"]
    first = int(str(cfg["period_start"])[:4])
    last = int(str(cfg["period_end"])[:4])
    years = list(range(first, last + 1))

    RAW_ERA5.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client()

    print(f"{cfg['dataset']}  {cfg['variables']}")
    print(f"area {cfg['area']}  years {first}-{last}\n")

    for year in years:
        target = RAW_ERA5 / f"era5_{year}.nc"
        if target.exists():
            print(f"  have {target.name} ({target.stat().st_size / 1e3:.0f} kB)")
            continue
        client.retrieve(
            cfg["dataset"],
            {
                "product_type": ["reanalysis"],
                "variable": list(cfg["variables"]),
                "year": [str(year)],
                "month": [f"{m:02d}" for m in range(1, 13)],
                "day": [f"{d:02d}" for d in range(1, 32)],
                "time": [f"{h:02d}:00" for h in range(24)],
                "area": list(cfg["area"]),
                "data_format": "netcdf",
                "download_format": "unarchived",
            },
            str(target),
        )
        print(f"  got  {target.name} ({target.stat().st_size / 1e3:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
