"""Loading DWD Climate Data Center hourly observations.

The archives are semicolon-separated text inside a zip, with conventions that
are easy to get wrong and produce no visible error when you do:

* ``-999`` marks a missing value.
* Missing observations are absent ROWS, not NaN, so the series has to be
  reindexed onto a complete hourly axis before any availability statistic.
* ``MESS_DATUM`` is not always UTC. Hohn (02303) is MEZ (UTC+1) for its whole
  record; List (03032) and Fehmarn (05516) switch from MEZ to UTC on 2003-09-01.
  The per-station value is in ``Metadaten_Parameter_ff_stunde_<id>.txt``.
* Direction is on a 36-part rose: ``0`` means calm or undetermined, NOT north -
  north is reported as ``360`` - and ``990`` means variable direction.
"""

import zipfile

import pandas as pd

from ..paths import RAW_DWD

#: Direction codes that are not directions.
DIRECTION_NON_VALUES = (0.0, 990.0)


def _open_product(prefix: str, station_id: int) -> pd.DataFrame:
    matches = sorted(RAW_DWD.glob(f"stundenwerte_{prefix}_{station_id:05d}_*_hist.zip"))
    if not matches:
        raise FileNotFoundError(
            f"no {prefix} archive for station {station_id:05d} in {RAW_DWD} - "
            "run python -m windforecast.download.dwd"
        )
    with zipfile.ZipFile(matches[-1]) as z:
        name = next(n for n in z.namelist() if n.startswith("produkt_"))
        with z.open(name) as fh:
            df = pd.read_csv(
                fh, sep=";", skipinitialspace=True, na_values=["-999", "-999.0"]
            )
    df.columns = df.columns.str.strip()
    return df


def load_hourly_wind(station_id: int, time_base: str = "MEZ") -> pd.DataFrame:
    """Hourly wind for one station, on a complete UTC hourly index.

    Returns columns ``F`` (mean speed, m/s), ``D`` (direction in degrees, with
    the non-direction codes set to NaN), ``D_raw`` (as delivered) and ``QN_3``.
    """
    if time_base.upper() not in {"MEZ", "UTC"}:
        raise ValueError("time_base must be 'MEZ' or 'UTC'")

    df = _open_product("FF", station_id)
    shift = pd.Timedelta(hours=1) if time_base.upper() == "MEZ" else pd.Timedelta(0)
    df["time"] = pd.to_datetime(df["MESS_DATUM"], format="%Y%m%d%H") - shift
    df = df.set_index("time").sort_index()

    out = df[["F", "D", "QN_3"]].copy()
    out["D_raw"] = out["D"]
    out.loc[out["D"].isin(DIRECTION_NON_VALUES), "D"] = pd.NA
    # A speed of zero has no direction either, whatever the code says.
    out.loc[out["F"] == 0, "D"] = pd.NA

    full = pd.date_range(out.index.min(), out.index.max(), freq="h")
    return out.reindex(full).rename_axis("time")
