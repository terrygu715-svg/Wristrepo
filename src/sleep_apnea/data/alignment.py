"""Motion/synchronization feasibility (T11, Kaggle §7).

No channel map exists for this source and the publisher describes 6 EEG
channels (M09) — there is no motion representation and no HR/SpO2 time
series, only per-night vitals in patients.csv. A documented no-motion
result completes this ticket per its Done criterion; the omit path is
taken here with the evidence that forces it. T20 scope consequences are
flagged for the T12 freeze, not decided here.
"""

from __future__ import annotations

import math


def _validated_overlap_evidence(evidence) -> dict | None:
    """Require quantified evidence before selecting a motion proxy."""
    if not isinstance(evidence, dict):
        return None
    source = evidence.get("source")
    coverage = evidence.get("overlap_fraction")
    offset = evidence.get("max_abs_offset_seconds")
    if not isinstance(source, str) or not source.strip():
        return None
    if (isinstance(coverage, bool) or not isinstance(coverage, (int, float))
            or not math.isfinite(coverage) or not 0.0 <= coverage <= 1.0):
        return None
    if (isinstance(offset, bool) or not isinstance(offset, (int, float))
            or not math.isfinite(offset) or offset < 0.0):
        return None
    return {
        "source": source.strip(),
        "overlap_fraction": float(coverage),
        "max_abs_offset_seconds": float(offset),
    }

def assess(
    channel_count: int,
    channel_identities_known: bool,
    motion_channels: list[int] | None = None,
    overlap_evidence: dict | None = None,
) -> dict:
    """Feasibility decision: named proxy or documented omission."""
    if isinstance(channel_count, bool) or not isinstance(channel_count, int) or channel_count <= 0:
        raise ValueError("channel_count must be a positive integer")
    if not isinstance(channel_identities_known, bool):
        raise ValueError("channel_identities_known must be a boolean")
    if motion_channels is not None and not isinstance(motion_channels, list):
        raise ValueError("motion_channels must be a list of channel indices")
    motion_channels = list(motion_channels or [])
    if len(set(motion_channels)) != len(motion_channels):
        raise ValueError("motion_channels must not contain duplicates")
    if any(isinstance(channel, bool) or not isinstance(channel, int)
           or not 0 <= channel < channel_count
           for channel in motion_channels):
        raise ValueError("motion_channels contains an out-of-range channel index")
    validated_evidence = _validated_overlap_evidence(overlap_evidence)
    if motion_channels and channel_identities_known and validated_evidence:
        return {
            "decision": "proxy",
            "motion_channels": motion_channels,
            "overlap_evidence": validated_evidence,
            "warning": "proxy enters both Full and Reduced (T12); never raw IMU claims",
        }
    reasons = []
    if not channel_identities_known:
        reasons.append("no channel map: 6 channels are positional indices (U03)")
    if not motion_channels:
        reasons.append("no motion representation in source (M09: 6 EEG channels)")
    if motion_channels and not validated_evidence:
        reasons.append(
            "claimed motion channels lack quantified PSG-overlap evidence "
            "(source, coverage, and offset required; E03)"
        )
    return {
        "decision": "omit",
        "reasons": reasons,
        "consequence": (
            "no motion in either input set; T12 must also resolve T20 scope "
            "(no HR/SpO2 time series in this source — EEG-derived features "
            "or vitals-as-covariates, versioned at freeze)"
        ),
    }
