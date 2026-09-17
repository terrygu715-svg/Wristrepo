"""Train-only fitted transformations (T19). numpy + stdlib.

fit/transform interface for scaling (mean/std) and median imputation using
synthetic features for now. Parameters are learned ONLY from rows whose
ids are passed as training ids; anything else raises. This is the seam
(S07) that prevents scaler/imputer leakage.

Missing values are NaN. Feature ordering is fixed at fit time and enforced
at transform time; unknown or reordered features fail deterministically.
"""

from __future__ import annotations

import numpy as np

_MISSING = "missing-feature failures are deterministic (T19)"


class FittedTransform:
    """Mean/std scaler + median imputation fitted on training ids only."""

    def __init__(self, feature_order: list[str], means: np.ndarray,
                 stds: np.ndarray, medians: np.ndarray) -> None:
        self.feature_order = list(feature_order)
        self.means = np.asarray(means, dtype=float)
        self.stds = np.asarray(stds, dtype=float)
        self.medians = np.asarray(medians, dtype=float)

    def transform(self, matrix: np.ndarray, feature_order: list[str]) -> np.ndarray:
        """Impute NaN with training medians, then standardize."""
        if list(feature_order) != self.feature_order:
            raise ValueError(f"feature order mismatch: {_MISSING}")
        values = np.asarray(matrix, dtype=float)
        if values.ndim != 2 or values.shape[1] != len(self.feature_order):
            raise ValueError(
                f"expected (*, {len(self.feature_order)}) matrix, got {values.shape}"
            )
        filled = np.where(np.isnan(values), self.medians, values)
        return (filled - self.means) / self.stds

    def state(self) -> dict:
        """JSON-safe metadata (arrays travel via T26 bundles)."""
        return {
            "feature_order": list(self.feature_order),
            "means": self.means.tolist(),
            "stds": self.stds.tolist(),
            "medians": self.medians.tolist(),
        }


def fit(
    by_id: dict[str, np.ndarray],
    feature_order: list[str],
    train_ids: list[str],
) -> FittedTransform:
    """Fit on training ids only. Held-out ids in by_id are ignored entirely.

    Raises KeyError for unknown train ids (fail loud, never silently subset).
    Zero-variance features get std 1.0 (no-op scaling, documented here).
    """
    if not train_ids:
        raise ValueError("train_ids must be non-empty")
    missing = [i for i in train_ids if i not in by_id]
    if missing:
        raise KeyError(f"unknown train ids: {missing[:5]}")
    stacked = np.vstack([np.asarray(by_id[i], dtype=float) for i in train_ids])
    if stacked.ndim != 2 or stacked.shape[1] != len(feature_order):
        raise ValueError(f"row width {stacked.shape[1]} != {len(feature_order)} features")
    medians = np.nanmedian(stacked, axis=0)
    filled = np.where(np.isnan(stacked), medians, stacked)
    means = filled.mean(axis=0)
    stds = filled.std(axis=0)
    stds[stds == 0.0] = 1.0
    return FittedTransform(feature_order, means, stds, medians)
