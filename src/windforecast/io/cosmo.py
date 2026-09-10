"""COSMO-R6G2 regional reanalysis: grid geometry and point extraction.

Source: DWD Climate Data Center,
https://opendata.dwd.de/climate_environment/REA/COSMO_R6G2 (CC BY 4.0).

The fields are stored on a rotated-pole grid whose 1-D ``rlat``/``rlon``
coordinates are not geographic, so a site has to be transformed into that frame
before a grid cell can be selected. The predecessor COSMO-REA6 ends 2019-08 and
has no overlap with the 2021-2022 measurement window.
"""

import numpy as np

from .geo import haversine_km  # re-exported: callers already import it from here


def geographic_to_rotated(
    lat: float, lon: float, pole_lat: float, pole_lon: float
) -> tuple[float, float]:
    """Transform geographic degrees into the grid's rotated-pole frame.

    Convention (COSMO / CF ``rotated_latitude_longitude``): the rotated prime
    meridian runs through the geographic north pole, so the geographic pole sits
    at rotated longitude 0 and rotated latitude ``pole_lat``.

    Returns (rotated latitude, rotated longitude) in degrees.
    """
    phi, lam = np.radians(lat), np.radians(lon)
    phi_p, lam_p = np.radians(pole_lat), np.radians(pole_lon)
    d_lam = lam - lam_p

    z = np.sin(phi) * np.sin(phi_p) + np.cos(phi) * np.cos(phi_p) * np.cos(d_lam)
    x = np.sin(phi) * np.cos(phi_p) - np.cos(phi) * np.sin(phi_p) * np.cos(d_lam)
    y = -np.cos(phi) * np.sin(d_lam)

    # arctan2 against the horizontal component rather than arcsin(z): the two
    # are identical on a unit vector, but arcsin is ill-conditioned near the
    # poles, where a one-ulp error in z becomes ~1e-6 degrees.
    rlat = np.degrees(np.arctan2(z, np.hypot(x, y)))
    return float(rlat), float(np.degrees(np.arctan2(y, x)))


def rotated_to_geographic(
    rlat: float, rlon: float, pole_lat: float, pole_lon: float
) -> tuple[float, float]:
    """Inverse of :func:`geographic_to_rotated`. Returns (latitude, longitude)."""
    phi_r, lam_r = np.radians(rlat), np.radians(rlon)
    phi_p, lam_p = np.radians(pole_lat), np.radians(pole_lon)

    x = np.cos(phi_r) * np.cos(lam_r)
    y = np.cos(phi_r) * np.sin(lam_r)
    z = np.sin(phi_r)

    sin_phi = x * np.cos(phi_p) + z * np.sin(phi_p)
    cos_phi_cos_dlam = -x * np.sin(phi_p) + z * np.cos(phi_p)
    phi = np.arctan2(sin_phi, np.hypot(-y, cos_phi_cos_dlam))
    d_lam = np.arctan2(-y, cos_phi_cos_dlam)

    lon = np.degrees(lam_p + d_lam)
    return float(np.degrees(phi)), float((lon + 180.0) % 360.0 - 180.0)


def nearest_cell(ds, lat: float, lon: float, pole_lat: float, pole_lon: float) -> dict:
    """Locate the grid cell containing a geographic point.

    Returns the rotated coordinates of the site, the selected indices, the
    geographic centre of the chosen cell and its distance from the site - the
    last of these is the number that says whether the substitution is acceptable.
    """
    rlat, rlon = geographic_to_rotated(lat, lon, pole_lat, pole_lon)
    i_lat = int(np.abs(ds["rlat"].values - rlat).argmin())
    i_lon = int(np.abs(ds["rlon"].values - rlon).argmin())
    cell_rlat = float(ds["rlat"].values[i_lat])
    cell_rlon = float(ds["rlon"].values[i_lon])
    cell_lat, cell_lon = rotated_to_geographic(cell_rlat, cell_rlon, pole_lat, pole_lon)
    return {
        "site_rlat": rlat,
        "site_rlon": rlon,
        "i_rlat": i_lat,
        "i_rlon": i_lon,
        "cell_rlat": cell_rlat,
        "cell_rlon": cell_rlon,
        "cell_lat": cell_lat,
        "cell_lon": cell_lon,
        "distance_km": haversine_km(lat, lon, cell_lat, cell_lon),
    }
