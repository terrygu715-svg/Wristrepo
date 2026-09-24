"""Sample channel/format audit (T09, Kaggle §7). numpy + stdlib.

Header census (shapes/dtypes, no data loaded) plus chunked value statistics
(per-channel min/max/mean/std, NaN/Inf fractions, extreme-value report)
computed with mmap so whole nights never sit in RAM twice. Distinguishes
raw channels from derived fields: everything here is raw (no derived
fields exist in this source); modality-vs-count confusion is flagged when
the 16-channel anomalies are encountered.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from sleep_apnea.data.ingest import sha256_file

CHUNK_SAMPLES = 1 << 20
EXTREME_ABS = 1000.0  # report values beyond this; disposition in T14, not here


def audit_night(path: str | os.PathLike) -> dict:
    """Audit one .npy night. Returns inventory record (JSON-serializable)."""
    arr = np.load(path, mmap_mode="r")
    if arr.ndim != 2:
        raise ValueError(f"{path}: expected 2-D (channels x samples), got {arr.ndim}-D")
    n_channels, n_samples = (int(arr.shape[0]), int(arr.shape[1]))
    channels = []
    for ch in range(n_channels):
        count, total, total_sq = 0, 0.0, 0.0
        minimum, maximum, nan, inf, extreme = None, None, 0, 0, 0
        for start in range(0, n_samples, CHUNK_SAMPLES):
            block = np.asarray(arr[ch, start:start + CHUNK_SAMPLES], dtype=float)
            nan += int(np.isnan(block).sum())
            inf += int(np.isinf(block).sum())
            finite = block[np.isfinite(block)]
            if finite.size:
                count += int(finite.size)
                total += float(finite.sum())
                total_sq += float(np.square(finite).sum())
                block_min, block_max = float(finite.min()), float(finite.max())
                minimum = block_min if minimum is None else min(minimum, block_min)
                maximum = block_max if maximum is None else max(maximum, block_max)
                extreme += int((np.abs(finite) > EXTREME_ABS).sum())
        mean = (total / count) if count else None
        variance = (total_sq / count - mean * mean) if count and mean is not None else None
        channels.append({
            "index": ch,
            "identity": "UNVERIFIED (U03): positional index only",
            "min": minimum, "max": maximum,
            "mean": mean,
            "std": float(np.sqrt(max(variance, 0.0))) if variance is not None else None,
            "nan_fraction": nan / n_samples,
            "inf_fraction": inf / n_samples,
            "extreme_count": extreme,
            "extreme_beyond_1000": bool(
                (minimum is not None and abs(minimum) > EXTREME_ABS)
                or (maximum is not None and abs(maximum) > EXTREME_ABS)
            ),
        })
    return {
        "file": Path(path).name,
        "shape": [n_channels, n_samples],
        "dtype": str(arr.dtype),
        "channels": channels,
        "nonstandard_channel_count": n_channels != 6,
    }


def audit_sample(paths: list[str | os.PathLike]) -> dict:
    """Audit several nights; quarantines non-6-channel files with reasons."""
    records, quarantined = [], []
    for path in paths:
        record = audit_night(path)
        record["bytes"] = Path(path).stat().st_size
        record["sha256"] = sha256_file(path)
        (quarantined if record["nonstandard_channel_count"] else records).append(record)
    return {
        "schema_version": 1,
        "records": records,
        "quarantined": [
            {
                **r,
                "reason": "non-6-channel layout; T09 disposition required before T11-T14",
            }
            for r in quarantined
        ],
    }
