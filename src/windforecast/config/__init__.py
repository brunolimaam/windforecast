"""The run configuration, and the loader for it.

Every site and method parameter lives in the YAML beside this module rather than
in code, so that each number used in the assessment has one traceable place of
definition. ``site.yaml`` and the power curve sit here, next to the only code
that reads them, rather than in a separate top-level folder.
"""

from pathlib import Path
from typing import Any

import yaml

from ..paths import CONFIG


def load(name: str = "site.yaml") -> dict[str, Any]:
    """Return the parsed YAML configuration file ``name`` from ``config/``."""
    path = name if Path(name).is_absolute() else CONFIG / name
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
