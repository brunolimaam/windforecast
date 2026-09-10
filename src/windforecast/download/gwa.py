"""Download Global Wind Atlas rasters covering the site.

Source: globalwindatlas.info (DTU / World Bank), CC BY 4.0. 250 m resolution.

The API redirects to a country-wide GeoTIFF on the CDN:
    /api/gis/country/<ISO3>/<layer>/<height>
        -> country_tifs_v4/<ISO3>_<layer>_<height>m.tif

Only some layers are reachable this way. Verified available: wind-speed (10, 50,
100, 150, 200 m), power-density, combined-Weibull-A, combined-Weibull-k.
Returning 403: RIX, roughness, elevation, air-density - they exist in the web
application but not on this path.

Usage:  uv run python -m windforecast.download.gwa
"""

import sys

import requests

from ..paths import RAW_GWA

API = "https://globalwindatlas.info/api/gis/country"
COUNTRY = "DEU"
WANTED = [("wind-speed", h) for h in (10, 50, 100, 150, 200)]


def main() -> int:
    RAW_GWA.mkdir(parents=True, exist_ok=True)
    print(f"Global Wind Atlas v4, {COUNTRY}, 250 m, CC BY 4.0\n")
    for layer, height in WANTED:
        dest = RAW_GWA / f"{COUNTRY}_{layer}_{height}m.tif"
        if dest.exists():
            print(f"  have {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
            continue
        r = requests.get(f"{API}/{COUNTRY}/{layer}/{height}", timeout=600)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  got  {dest.name} ({len(r.content) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
