"""Paired bootstrap comparisons, Full vs Reduced (T25). Stdlib-only.

2,000 seeded participant resamples within reference strata; the same draws
are reused for each Full/Reduced pair. Output states its conditioning: gaps
are conditional on the fitted models and the observed class composition.

Inputs are two validated prediction dicts plus a stratum per
participant_id (e.g. the reference class). Rows are matched on
recording_id, so row reordering is harmless and unmatched IDs fail.
"""

from __future__ import annotations

import random

from sleep_apnea.contracts import validate_class_order, validate_predictions

from .metrics import summarize

N_BOOTSTRAP = 2000


def _index_rows(predictions: dict) -> dict:
    validate_predictions(predictions)
    return {row["recording_id"]: row for row in predictions["rows"]}


def _macro_f1_of(rows: list[dict], class_order: list[str]) -> float:
    return summarize({"class_order": list(class_order), "rows": rows})["macro_f1"]


def compare(
    full: dict,
    reduced: dict,
    strata: dict[str, str],
    full_run_id: str,
    reduced_run_id: str,
    metric: str = "macro_f1",
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 0,
) -> dict:
    """Paired bootstrap gap (full minus reduced) for one metric.

    Only macro_f1 is supported in the core baseline; other metrics require
    a versioned extension, not a silent swap.
    """
    if metric != "macro_f1":
        raise ValueError(f"core baseline supports metric='macro_f1', got {metric!r}")
    if n_bootstrap != N_BOOTSTRAP:
        raise ValueError(f"n_bootstrap must be {N_BOOTSTRAP} per T25, got {n_bootstrap!r}")
    order = validate_class_order(full.get("class_order"))
    validate_class_order(reduced.get("class_order"))
    if list(reduced["class_order"]) != list(order):
        raise ValueError("Full/Reduced class_order must match for a paired comparison")

    full_rows, reduced_rows = _index_rows(full), _index_rows(reduced)
    if set(full_rows) != set(reduced_rows):
        missing = set(full_rows) ^ set(reduced_rows)
        raise ValueError(f"unmatched recording_ids between Full/Reduced: {sorted(missing)[:5]}")

    participants: dict[str, list[str]] = {}
    for rec_id, row in full_rows.items():
        reduced_row = reduced_rows[rec_id]
        if reduced_row["participant_id"] != row["participant_id"]:
            raise ValueError(
                f"participant mismatch for recording_id {rec_id!r}: "
                f"{row['participant_id']!r} != {reduced_row['participant_id']!r}"
            )
        if reduced_row["y_true"] != row["y_true"]:
            raise ValueError(f"true-label mismatch for recording_id {rec_id!r}")
        pid = row["participant_id"]
        if pid not in strata:
            raise ValueError(f"participant {pid!r} has no reference stratum")
        if strata[pid] not in order:
            raise ValueError(f"participant {pid!r} has unknown reference stratum {strata[pid]!r}")
        participants.setdefault(pid, []).append(rec_id)
    if set(strata) != set(participants):
        extra = sorted(set(strata) - set(participants))
        raise ValueError(f"strata contains unknown participants: {extra[:5]}")
    # Stratum buckets of participant ids; resample participants within strata.
    buckets: dict[str, list[str]] = {}
    for pid in participants:
        buckets.setdefault(strata[pid], []).append(pid)
    for stratum in buckets:
        buckets[stratum] = sorted(buckets[stratum])

    rng = random.Random(seed)
    gaps: list[float] = []
    for _ in range(n_bootstrap):
        draw: list[str] = []  # resampled recording_ids, reused for both inputs
        for members in buckets.values():
            for pid in rng.choices(members, k=len(members)):
                draw.extend(participants[pid])
        full_sample = [full_rows[r] for r in draw]
        reduced_sample = [reduced_rows[r] for r in draw]
        gaps.append(_macro_f1_of(full_sample, order) - _macro_f1_of(reduced_sample, order))

    ordered = sorted(gaps)
    low = ordered[int(0.025 * n_bootstrap)]
    high = ordered[int(0.975 * n_bootstrap) - 1]
    return {
        "class_order": list(order),
        "full_run_id": full_run_id,
        "reduced_run_id": reduced_run_id,
        "metric": metric,
        "metric_gaps": {"macro_f1": sum(gaps) / len(gaps)},
        "mean_gap": sum(gaps) / len(gaps),
        "ci_low_95": low,
        "ci_high_95": high,
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "conditioning": (
            "gaps condition on the fitted models and the observed class "
            "composition; resampling is over participants within strata"
        ),
    }
