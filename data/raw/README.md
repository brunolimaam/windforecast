# Raw data

Contents are not versioned (see `.gitignore`). Every file here must be
reproducible by a module in `windforecast.download`, and every download records:

- source and exact URL or CDS request,
- retrieval date,
- licence / terms of use of the source.

Sources used in this project:

- **DWD Open Data** (Deutscher Wetterdienst, Climate Data Center) - hourly wind
  observations at station Hohn (02303), 10 m measurement height, in `dwd/`.
  Free re-use with attribution under GeoNutzV.
- **COSMO-R6G2** (DWD regional reanalysis, 6 km rotated-pole grid, 2002-2025)
  via `opendata.dwd.de/climate_environment/REA/COSMO_R6G2`. Licence: CC BY 4.0,
  attribution "Deutscher Wetterdienst". Hourly fields for the one grid cell that
  contains the station: wind speed and direction at 100 m in `cosmo/hourly_zlev/`,
  2 m temperature and humidity and surface pressure in `cosmo/hourly/`. The
  server offers no spatial subsetting, so each month of the European domain
  (~1 GB per variable) is downloaded, the cell is written to a CSV and the
  `.nc4` is deleted. Its predecessor COSMO-REA6 ends 2019-08 and is not used.
- **Global Wind Atlas** v4 - mean wind speed rasters (GeoTIFF, 250 m) for
  Germany at 10, 50, 100, 150 and 200 m, in `gwa/`. The notebook uses the 100 m
  layer. DTU / World Bank, CC BY 4.0.

`era5/` stays empty: ERA5 (`windforecast.download.era5`) is not used.
