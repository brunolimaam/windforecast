"""Project paths, resolved relative to the repository root.

Keeps every module free of hard-coded absolute paths so that notebooks,
scripts and tests all read and write the same locations.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Site and method parameters, and the power curve. Inside the package rather
#: than at the repository root, so they resolve the same way whether the package
#: is imported from a checkout, a notebook or an installed wheel.
CONFIG = Path(__file__).resolve().parent / "config"
DATA = ROOT / "data"
RAW = DATA / "raw"

RAW_DWD = RAW / "dwd"
RAW_ERA5 = RAW / "era5"
RAW_COSMO = RAW / "cosmo"
RAW_GWA = RAW / "gwa"

PROCESSED = DATA / "processed"

DOCS = ROOT / "docs"

FIGURES = DOCS / "figures"

RAW_COSMO_HOURLY = RAW_COSMO / "hourly_zlev"
RAW_COSMO_THERMO = RAW_COSMO / "hourly"
