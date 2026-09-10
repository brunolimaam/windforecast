"""Vertical extrapolation of wind speed, and the plots of the result.

The logarithmic profile, parameterised by roughness length z0 - method V2 of
Lazar et al. (2024), "Comparative examinations of wind speed and energy
extrapolation methods using remotely sensed data". It is the route this project
can take: it needs wind at a single height plus a roughness estimate, whereas
the power law needs two measured heights and the station has only one.

Caveats that belong in the report, not buried here:

* The ratio form below cancels the friction velocity, which assumes both heights
  sit in the same equilibrium surface layer over a homogeneous upwind fetch. The
  rule of thumb is a fetch of order 100x the measurement height - about 1 km for
  a 10 m sensor. Roughness assigned per direction sector is a pragmatic
  approximation to that, not a derivation of it.
* The displacement height d is neglected, as in Lazar et al. eq. 5. Over low
  vegetation that is harmless; near trees it is not, and d ~ 0.7 x obstacle
  height would shift the profile.
* Near-field obstacles are a different problem from surface roughness. An
  effective z0 lumps them in; a shelter model would treat them properly.
"""


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def add_z0(df: pd.DataFrame, sectors: list[tuple[float, float, float]],
           dir_col: str = "D", default: float = np.nan,
           out_col: str = "z0") -> pd.DataFrame:
    """Assign roughness length by wind direction.

    sectors: [(from_deg, to_deg, z0_m), ...], each interval [from, to).
             Sectors crossing north work too, e.g. (330, 30, 0.1).
    default: z0 for directions not covered by any sector.
    """
    d = df[dir_col] % 360
    z0 = pd.Series(default, index=df.index, dtype=float)
    for lo, hi, value in sectors:
        lo, hi = lo % 360, hi % 360
        if lo < hi:
            mask = (d >= lo) & (d < hi)
        else:  # wraps around 0°
            mask = (d >= lo) | (d < hi)
        z0[mask] = value
    z0[df[dir_col].isna()] = np.nan
    df[out_col] = z0
    return df


def log_extrapolate(df: pd.DataFrame, speed_col: str, z0_col: str,
                    from_height: float, to_height: float) -> pd.DataFrame:
    """Logarithmic wind profile, row by row: v2 = v1 * ln(z2/z0) / ln(z1/z0)."""
    z0 = df[z0_col]
    if (z0 <= 0).any() or (z0 >= min(from_height, to_height)).any():
        raise ValueError("every z0 must be > 0 and below both heights")
    factor = np.log(to_height / z0) / np.log(from_height / z0)
    df[f"F{to_height:g}_extrapol"] = df[speed_col] * factor
    return df


def windrose(sector, speed, n_sectors=12, speed_bins=(0, 4, 6, 8, 10, 12, np.inf),
             ax=None, cmap="Blues", title=None):
    """Frequency of (sector, speed-bin) as a stacked polar bar chart.

    sector : integer sector index, 0 = North, as built in the notebook
             (((DD + 15) % 360) // 30) -> sector 0 spans 345-15 deg.
    speed  : wind speed aligned with `sector`.

    Bars are drawn at the sector CENTRE with the full sector width, so the
    plotted geometry is the same binning the sector regression used. Heights
    are percent of all valid hours, so the sum over the whole rose is 100.
    """
    df = pd.concat({"sec": sector, "u": speed}, axis=1).dropna()
    width = 2 * np.pi / n_sectors

    bins = np.asarray(speed_bins, dtype=float)
    labels = [f"{bins[i]:.0f}-{bins[i+1]:.0f}" for i in range(len(bins) - 2)]
    labels.append(f">{bins[-2]:.0f}")
    df["ubin"] = pd.cut(df["u"], bins=bins, right=False, labels=labels)

    table = (df.groupby(["sec", "ubin"], observed=False).size()
               .unstack(fill_value=0)
               .reindex(range(n_sectors), fill_value=0))
    table = 100 * table / len(df)

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    ax.set_theta_zero_location("N")   # 0 deg at the top
    ax.set_theta_direction(-1)        # clockwise: meteorological convention

    theta = np.deg2rad(table.index.values * (360 / n_sectors))
    colors = plt.get_cmap(cmap)(np.linspace(0.25, 1.0, table.shape[1]))

    bottom = np.zeros(n_sectors)
    for color, col in zip(colors, table.columns, strict=True):
        ax.bar(theta, table[col].values, width=width, bottom=bottom,
               color=color, edgecolor="white", linewidth=0.5, label=str(col))
        bottom += table[col].values

    ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
    ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
    ax.set_rlabel_position(112.5)
    ax.grid(alpha=0.3)
    ax.set_title(title or "", pad=20)
    ax.legend(title="u [m/s]", loc="lower left", bbox_to_anchor=(1.02, 0.0),
              frameon=False, fontsize=9)
    return ax, table


def speed_distribution(speed, bin_width=0.25, speed_bins=(0, 4, 6, 8, 10, 12, np.inf),
                       ax=None, cmap="Blues", title=None):
    """Relative frequency of wind speed, coloured by the rose's speed classes.

    bin_width is the resolution of the histogram itself; speed_bins only drive
    the colouring, so the two panels share one legend and a bar's colour says
    which rose class it belongs to.
    """
    u = pd.Series(speed).dropna().values
    edges = np.arange(0, np.ceil(u.max()) + bin_width, bin_width)
    freq, edges = np.histogram(u, bins=edges)
    freq = 100 * freq / freq.sum()
    centres = 0.5 * (edges[:-1] + edges[1:])

    class_bins = np.asarray(speed_bins, dtype=float)
    colors = plt.get_cmap(cmap)(np.linspace(0.25, 1.0, len(class_bins) - 1))
    idx = np.clip(np.digitize(centres, class_bins) - 1, 0, len(colors) - 1)

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    ax.bar(centres, freq, width=bin_width * 0.95, color=colors[idx])

    mean_u = u.mean()
    ax.axvline(mean_u, color="black", linestyle="--", linewidth=1)
    ax.annotate(f"mean {mean_u:.2f} m/s", xy=(mean_u, ax.get_ylim()[1]),
                xytext=(4, -4), textcoords="offset points",
                va="top", ha="left", fontsize=9)

    ax.set_xlabel("wind speed [m/s]")
    ax.set_ylabel(f"relative frequency [% per {bin_width:g} m/s]")
    ax.set_title(title or "", pad=20)
    ax.grid(alpha=0.3, axis="y")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return ax, pd.Series(freq, index=centres, name="freq_pct")
