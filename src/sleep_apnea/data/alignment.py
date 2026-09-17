"""Motion/synchronization feasibility (T11, Kaggle §7).

No channel map exists for this source and the publisher describes 6 EEG
channels (M09) — there is no motion representation and no HR/SpO2 time
series, only per-night vitals in patients.csv. A documented no-motion
result completes this ticket per its Done criterion; the omit path is
taken here with the evidence that forces it. T20 scope consequences are
flagged for the T12 freeze, not decided here.
"""

from __future__ import annotations


def assess(
    channel_count: int,
    channel_identities_known: bool,
    motion_channels: list[int] | None = None,
    overlap_evidence: str | None = None,
) -> dict:
    """Feasibility decision: named proxy or documented omission."""
    motion_channels = list(motion_channels or [])
    if motion_channels and channel_identities_known and overlap_evidence:
        return {
            "decision": "proxy",
            "motion_channels": motion_channels,
            "overlap_evidence": overlap_evidence,
            "warning": "proxy enters both Full and Reduced (T12); never raw IMU claims",
        }
    reasons = []
    if not channel_identities_known:
        reasons.append("no channel map: 6 channels are positional indices (U03)")
    if not motion_channels:
        reasons.append("no motion representation in source (M09: 6 EEG channels)")
    if motion_channels and not overlap_evidence:
        reasons.append("claimed motion channels lack PSG-overlap quantification (E03)")
    return {
        "decision": "omit",
        "reasons": reasons,
        "consequence": (
            "no motion in either input set; T12 must also resolve T20 scope "
            "(no HR/SpO2 time series in this source — EEG-derived features "
            "or vitals-as-covariates, versioned at freeze)"
        ),
    }
