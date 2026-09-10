"""Download hourly DWD wind observations for the site station.

Source: DWD Climate Data Center, Open Data server. A plain HTTPS file server -
filenames carry their date range, so they are discovered from the directory
listing rather than constructed.

Only hourly wind (FF) is downloaded, for the site station
(`reference_data.dwd.primary`). Air density comes from COSMO-R6G2, not from the
station.

The historical archives run to 2025-12-31 and therefore already contain the
2021-2022 measurement window; the `recent` files are not needed.

Usage:  uv run python -m windforecast.download.dwd
"""

import re
import sys

import requests

from .. import config
from ..paths import RAW_DWD

BASE = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany"
    "/climate/hourly"
)


def fetch(url: str, dest) -> None:
    if dest.exists():
        print(f"  have   {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"  got    {dest.name} ({len(r.content) / 1e6:.1f} MB)")


def listing(folder: str, prefix: str) -> set[str]:
    r = requests.get(f"{BASE}/{folder}/historical/", timeout=120)
    r.raise_for_status()
    return set(re.findall(rf"stundenwerte_{prefix}_\d{{5}}_\d{{8}}_\d{{8}}_hist\.zip", r.text))


def main() -> int:
    site = config.load()["reference_data"]["dwd"]["primary"]
    RAW_DWD.mkdir(parents=True, exist_ok=True)

    print(f"wind (FF) - hourly mean wind speed and direction at 10 m, station {site:05d}:")
    match = [n for n in listing("wind", "FF") if n.split("_")[2] == f"{site:05d}"]
    if not match:
        print(f"  MISSING  no historical FF file for station {site:05d}")
        return 1
    name = sorted(match)[-1]
    fetch(f"{BASE}/wind/historical/{name}", RAW_DWD / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
