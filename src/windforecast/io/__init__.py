"""Reading the raw files into pandas and xarray objects.

One module per source, mirroring ``windforecast.download``. These modules own
the file-format knowledge - missing-value codes, time bases, column names that
read backwards - and nothing else. No network access, so the analysis steps
above them can be tested against a handful of hand-written rows.
"""
