"""Loading ERA5 single-level reanalysis retrieved from the Copernicus CDS.

Files come from ``windforecast/download/era5.py``, one per year, already subset to
a small box around the site by the CDS itself.

Wind speed is formed per hour from the u and v components and only then
averaged. Averaging the components first and taking the magnitude afterwards
gives the VECTOR mean, which is systematically lower than the mean scalar speed
whenever the direction varies - a different quantity, and not the one that
pairs with COSMO's SP fields.
"""

import numpy as np
import pandas as pd
import xarray as xr

from ..paths import RAW_ERA5


def load_hourly_point(lat: float, lon: float, level: str = "100") -> pd.DataFrame:
    """Hourly wind speed and direction at the ERA5 grid point nearest a site.

    Returns columns ``speed`` (m/s) and ``direction`` (degrees, meteorological -
    the direction the wind blows FROM), indexed by UTC hour.
    """
    files = sorted(RAW_ERA5.glob("era5_*.nc"))
    if not files:
        raise FileNotFoundError(
            f"no ERA5 files in {RAW_ERA5} - run python -m windforecast.download.era5"
        )

    frames = []
    for path in files:
        with xr.open_dataset(path) as ds:
            point = ds.sel(latitude=lat, longitude=lon, method="nearest")
            u = point[f"u{level}"].values
            v = point[f"v{level}"].values
            time = pd.DatetimeIndex(point["valid_time"].values)
            frames.append(pd.DataFrame({"u": u, "v": v}, index=time))

    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated()]
    df["speed"] = np.hypot(df["u"], df["v"])
    # Meteorological convention: 0/360 = from the north, 90 = from the east.
    df["direction"] = (np.degrees(np.arctan2(-df["u"], -df["v"])) + 360.0) % 360.0
    return df[["speed", "direction"]].rename_axis("time")


def monthly_mean_speed(hourly: pd.DataFrame, min_coverage: float = 0.9) -> pd.Series:
    """Monthly mean of the hourly SCALAR speed, indexed by month start.

    Months with less than ``min_coverage`` of their hours present are dropped
    rather than averaged from a partial sample.
    """
    speed = hourly["speed"]
    grouped = speed.groupby([speed.index.year, speed.index.month])
    means, counts = grouped.mean(), grouped.count()
    hours = pd.Series(
        [pd.Period(f"{y}-{m:02d}").days_in_month * 24 for y, m in means.index],
        index=means.index,
    )
    means = means.where(counts / hours >= min_coverage)
    means.index = pd.to_datetime(
        [f"{y}-{m:02d}-01" for y, m in means.index], format="%Y-%m-%d"
    )
    return means.rename("era5_speed").rename_axis("month").dropna()
