# Wind Resource and Energy Yield Assessment - Schleswig-Holstein

Recreation of the methodological workflow of a wind energy yield assessment for a
hypothetical five-turbine site, using **only publicly available data and
open-source tools**.

The study is [`notebooks/analysis.ipynb`](notebooks/analysis.ipynb). The story: the
Hohn airfield has been decommissioned, and five Nordex N100/2500 turbines (100 m
rotor, 100 m hub height) are planned in a row along it. The DWD station Hohn
(02303), just north of the row, stands in for the on-site measurement campaign.
The steps follow the MEASNET procedure for site assessment and the DFBEW /
Fraunhofer IWES background paper.

| Step | What happens |
| --- | --- |
| 1 | Measurement campaign: DWD Hohn, 2021-2022 at 10 m, extrapolated to 100 m with the logarithmic profile |
| 2 | Long-term reference: COSMO-R6G2, 2002-2025 |
| 3 | Long-term correction: sector-wise MCP (linear regression in 12 sectors) |
| 4 | Horizontal transfer from the station to each turbine (Global Wind Atlas) |
| 5 | Air density at hub height (COSMO-R6G2) |
| 6 | Gross energy yield per turbine and for the farm (sector-wise Weibull fits, checked against the hourly series) |

The notebook ends at the **gross** energy yield. Losses (wakes, availability,
curtailment) and the uncertainty budget are not covered yet.

## What this is not

This is **not** a guideline-compliant assessment. It does not satisfy FGW TR6 or
IEC 61400-15-2, and it never claims to. The central weakness is structural: the
wind climate is derived from a 10 m anemometer and extrapolated to hub height.
In real world situation this data would come from LiDAR or mast measurements.
The documented limits of the method are part of the result, not a disclaimer.

## Data sources

| Source | Use | Licence |
| --- | --- | --- |
| DWD Open Data, station Hohn (02303) | "measurement campaign" (Step 1): hourly wind speed and direction at 10 m, 2021-2022 | GeoNutzV |
| COSMO-R6G2 (DWD regional reanalysis, 6 km) | hourly, 2002-2025: wind speed and direction at 100 m as the long-term reference (Steps 2-3); 2 m temperature and humidity and surface pressure for air density (Step 5) | CC BY 4.0 |
| Global Wind Atlas v4 (DTU Wind Energy) | mean wind speed at 100 m (250 m grid) for the horizontal transfer to each turbine (Step 4) | CC BY 4.0 |
| Nordex N100/2500 power curve at 1.225 kg/m³, from I. Staffell (no date), *Wind Turbine Power Curves*, Imperial College London | gross yield (Step 6) | public |
| MEASNET (2022), *Evaluation of Site-Specific Wind Conditions*, version 3 | methodological workflow | cited with attribution |
| Basse, Callies, Hahn (2017), Fraunhofer IWES / DFBEW | methodological workflow; cited numbers only | copyrighted, cited with attribution |

The full reference list is in the notebook.

## Layout

```text
notebooks/analysis.ipynb   the study: six steps, ends at the gross yield
src/windforecast/
  config/    site.yaml (site, turbines, method parameters), the power curve, and its loader
  paths.py   the one module every layer imports
  download/  acquisition, one module per source; the only network code
  io/        reading those files into pandas / xarray
  analysis/  log-profile extrapolation (Step 1), wind rose and speed distribution (Step 3)
data/raw/    downloads (not versioned, reproducible via windforecast.download)
docs/figures figures the notebook saves (not versioned)
```

`download/era5.py` and `io/era5.py` are not used by the notebook. They are kept
for a possible second long-term reference.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync                      # create .venv and install the locked dependency set
uv run python -c "import windforecast; print(windforecast.__version__)"
uv run jupyter lab           # open notebooks/analysis.ipynb
```

The raw data is not versioned. The download calls sit in the notebook, commented
out, in Steps 1, 2, 4 and 5; uncomment them on the first run. COSMO-R6G2 has no
spatial subsetting: each month of the whole European domain is downloaded (about
1 GB per month and variable), the site's grid cell is written to a CSV, and the
file is deleted again.
