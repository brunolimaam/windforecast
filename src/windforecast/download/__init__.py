"""Data acquisition: DWD Open Data, COSMO-R6G2, ERA5 via CDS, Global Wind Atlas.

One module per source. Each writes to ``data/raw/<source>/`` and records what
was requested, so a retrieval can be reproduced from the repo alone. Every
module has a ``main()`` and runs as a script::

    uv run python -m windforecast.download.dwd

Kept apart from ``windforecast.io`` on purpose: this is the only code in the
package that touches the network, and nothing under ``io`` or ``analysis``
imports it.
"""
