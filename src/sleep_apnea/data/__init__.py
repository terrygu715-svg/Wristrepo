"""Signal I/O package.

T06/T07/T08/T09/T11 modules are imported explicitly to keep CLI module
execution free of package-import side effects (for example, ``python -m
sleep_apnea.data.ingest`` must not preload itself).
"""
