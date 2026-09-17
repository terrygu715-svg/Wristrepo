"""Signal I/O package: T07 ingest + T06 fixtures live here (E-B Done).

T09 sample inventory and T13 canonical readers are later epics (E-C) and
remain unimplemented.
"""

from sleep_apnea.data.fixtures import build_fixtures, check_participant_disjointness
from sleep_apnea.data.ingest import build_manifest, scan_for_secrets, verify_manifest

__all__ = [
    "build_fixtures",
    "check_participant_disjointness",
    "build_manifest",
    "scan_for_secrets",
    "verify_manifest",
]
