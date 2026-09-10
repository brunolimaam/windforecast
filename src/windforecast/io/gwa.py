"""Global Wind Atlas: sampling the 250 m rasters and the horizontal transfer.

Source: globalwindatlas.info (DTU / World Bank), CC BY 4.0, 250 m resolution.
Rasters are fetched by ``windforecast/download/gwa.py``.

GWA is itself the output of a WAsP microscale calculation - the class of model
II.4 calls for. This project cannot license WAsP, so GWA stands in for a flow
model run we cannot perform.

**Use the ratios, not the levels.** GWA's absolute speeds come from its own model
chain (reanalysis downscaled to 250 m) and are not this site's wind: the level
comes from the measurement and the long-term correction. What is taken from GWA
is the spatial gradient between two points, which is exactly what a flow model
supplies in II.4 - a transfer is always relative.
"""

import numpy as np
import pandas as pd
import rasterio

from ..paths import RAW_GWA
from .geo import haversine_km

COUNTRY = "DEU"
HEIGHTS = (10, 50, 100, 150, 200)


def raster_path(height: int, layer: str = "wind-speed"):
    path = RAW_GWA / f"{COUNTRY}_{layer}_{height}m.tif"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing - run python -m windforecast.download.gwa"
        )
    return path


def read_points(points, height: int = 100, layer: str = "wind-speed"):
    """Sample a GWA raster at a sequence of (lat, lon) pairs.

    Returns a numpy array in the order given. Points are sampled at the cell
    that contains them; no interpolation, because the 250 m cell is the model's
    own resolution and smoothing between cells would invent detail.
    """
    with rasterio.open(raster_path(height, layer)) as src:
        values = [v[0] for v in src.sample([(lon, lat) for lat, lon in points])]
        nodata = src.nodata
    values = np.asarray(values, dtype=float)
    return np.where(values == nodata, np.nan, values)


def transfer_factors(
    station,
    turbines,
    height: int = 100,
    names=None,
    layer: str = "wind-speed",
) -> pd.DataFrame:
    """Horizontal transfer of the wind climate from the mast to each turbine.

        factor = GWA(turbine) / GWA(station)

    ``station`` and each entry of ``turbines`` are (lat, lon) in degrees. The
    returned frame carries the position, its distance from the station, the GWA
    speed at both, and the factor - the whole transfer, auditable in one table.

    Multiply a wind speed established at the mast by ``factor`` to obtain the
    corresponding speed at that turbine.
    """
    turbines = list(turbines)
    names = list(names) if names is not None else [
        f"T{i}" for i in range(1, len(turbines) + 1)
    ]
    if len(names) != len(turbines):
        raise ValueError("names and turbines must be the same length")

    at_station = float(read_points([station], height, layer)[0])
    if not np.isfinite(at_station) or at_station <= 0:
        raise ValueError("the GWA cell at the station carries no usable value")
    at_turbines = read_points(turbines, height, layer)

    return pd.DataFrame(
        {
            "lat": [t[0] for t in turbines],
            "lon": [t[1] for t in turbines],
            "distance_km": [haversine_km(*station, *t) for t in turbines],
            f"gwa_{height}m": at_turbines,
            "factor": at_turbines / at_station,
        },
        index=pd.Index(names, name="turbine"),
    ).assign(**{f"gwa_station_{height}m": at_station})
