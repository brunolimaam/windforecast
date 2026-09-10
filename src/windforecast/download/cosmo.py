"""Download COSMO-R6G2 reanalysis fields at the site's grid cell.

Source: DWD Climate Data Center, CC BY 4.0,
https://opendata.dwd.de/climate_environment/REA/COSMO_R6G2

The server offers no spatial subsetting - files cover the whole European domain
(824 x 848 cells at 6 km) one month at a time. So each file is downloaded, the
cell containing the site is appended to one CSV per variable, and the file is
deleted again. Only the CSVs are kept.

One flag per group:

* --hourly: wind speed and direction at 100 m (SP_100m, DD_100m), the long-term
  reference (notebook Steps 2-3). Written to data/raw/cosmo/hourly_zlev/.
* --thermo: 2 m temperature, surface pressure and 2 m specific humidity
  (1hrPt_tas, 1hrPt_ps, 1hrPt_huss) for air density (Step 5). Written to
  data/raw/cosmo/hourly/.
* --monthly: monthly means at 100, 150 and 200 m (monthly_variables in
  site.yaml), ~1.9 MB per file. Not used by the notebook.

Hourly fields are ~1 GB per month per variable AND are chunked one full 2D field
per timestep, so extracting a single grid point still costs ~1.38 MB per hour:
roughly 290 GB of transfer per variable for 2002-2025.

Usage:
  uv run python -m windforecast.download.cosmo --hourly
  uv run python -m windforecast.download.cosmo --thermo
  uv run python -m windforecast.download.cosmo --monthly
"""

import argparse
import re
import sys
import xarray as xr
import pandas as pd
import numpy as np 


import requests

from windforecast import config
from windforecast.paths import RAW_COSMO # PATH FOR DOWNLOAD
from windforecast.io.cosmo import nearest_cell


def listing(url: str) -> list[str]:
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    return sorted(set(re.findall(r'href="([^"/]+\.nc4?)"', r.text)))


def fetch(url: str, dest) -> int:
    """Download unless already present. Returns bytes transferred."""
    if dest.exists():
        return 0
    r = requests.get(url, timeout=600)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return len(r.content)


def download_group(
    base: str,
    kind: str,
    variables: list[str],
    lat: float,
    lon: float,
    keep=None,
) -> None:
    """kind is the folder on the server and under data/raw/cosmo/: 'hourly_zlev',
    'hourly' or 'monthly_zlev'. `keep` filters filenames."""
    loc = None

    for var in variables:
        var_dir = RAW_COSMO / kind / var
        var_dir.mkdir(parents=True, exist_ok=True)
        csv_path = var_dir / f"cosmo_{var}.csv"

        filenames = listing(f"{base}/{kind}/{var}/")
        if keep is not None:
            filenames = [fn for fn in filenames if keep(fn)]

        n_present = sum(1 for fn in filenames if (var_dir / fn).exists())
        print(f"  {kind}/{var}: {len(filenames)} files, {n_present} already present")

        bytes_downloaded = 0
        for i, fn in enumerate(filenames, 1):
            url = f"{base}/{kind}/{var}/{fn}"
            dest = var_dir / fn # path to downloaded file
            m = re.search(r"(\d{4})(\d{2})", fn)
            period = f"{m.group(1)}-{m.group(2)}" if m else fn
            print(f"     {i}/{len(filenames)}  {period}", flush=True)
            bytes_downloaded += fetch(url, dest)
            if i % 50 == 0 or i == len(filenames):
                print(f"     {i}/{len(filenames)}  (+{bytes_downloaded/1e6:.0f} MB this run)")
            ds = xr.open_dataset(dest)

            if loc is None:
                name = next(v for v in ds.variables
                            if "grid_north_pole_latitude" in ds[v].attrs)
                pole = ds[name].attrs
                loc = nearest_cell(
                    ds, lat, lon,
                    float(pole["grid_north_pole_latitude"]),
                    float(pole["grid_north_pole_longitude"]),
                )

            point = ds.isel(rlat=loc["i_rlat"], rlon=loc["i_rlon"])

            field = next(v for v in ds.data_vars
                         if {"rlat", "rlon", "time"} <= set(ds[v].dims))
            block = pd.DataFrame(
                {var: np.asarray(point[field].squeeze(drop=True).values).ravel()},
                index=pd.DatetimeIndex(pd.to_datetime(ds["time"].values.ravel()), name="time"),
            )

            if csv_path.exists():
                old = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                old.index.name = "time"
                block = pd.concat([old, block])
                block = block[~block.index.duplicated(keep="last")]

            block.sort_index().to_csv(csv_path, index_label="time")

            ds.close()
            dest.unlink(missing_ok=True)
            


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--hourly",
        action="store_true",
        help="fetch hourly fields",
    )
    ap.add_argument(
        "--monthly",
        action="store_true",
        help="fetch monthly fields",
    )
    ap.add_argument(
        "--thermo",
        action="store_true",
        help="fetch hourly surface fields for air density",
    )
    args = ap.parse_args()

    cfg = config.load()
    cosmo = cfg["reference_data"]["cosmo"]
    base = cosmo["base_url"]
    site = cfg["site"]
    lat, lon = float(site["latitude"]), float(site["longitude"])
    print(f"{cosmo['product']} - {base}")
    print(f"licence CC BY 4.0 (DWD), available {cosmo['available_from']} "
          f"to {cosmo['available_to']}\n")

    
    if args.monthly:
        download_group(
            base, 
            "monthly_zlev", 
            cosmo["monthly_variables"],
            lat,
            lon,
        )

    if args.hourly:
#        window = cfg["analysis"]["measurement_window"]
#        years = {str(window["start"])[:4], str(window["end"])[:4]}
#        print(f"\nhourly fields, measurement window {window['start']}..{window['end']}:")
        download_group(
            base,
            "hourly_zlev",
            ["SP_100m", "DD_100m"],
            lat,
            lon,
#            keep=lambda n: any(f".{y}" in n for y in years),
        )
    if args.thermo:
#        window = cfg["analysis"]["measurement_window"]
#        years = {str(window["start"])[:4], str(window["end"])[:4]}
#        print(f"\nhourly surface fields, {window['start']}..{window['end']}:")
        download_group(
            base,
            "hourly",
            ["1hrPt_tas", "1hrPt_ps", "1hrPt_huss"],
            lat,
            lon,
#            keep=lambda n: any(f".{y}" in n for y in years),
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
