"""Versioned data-contract validators (T03).

Stdlib-only so contract tests run on the verified CPU backend with no new
dependencies. Each validator raises ValueError on violation, returns None
on success. JSON Schema files in schemas/ are the normative declarations;
these functions enforce the two T03 Done properties without a jsonschema
dependency:

  1. Missing IDs are rejected (every row carries participant_id/recording_id).
  2. Ambiguous class order is rejected (class_order present, length 4, unique).
"""

from __future__ import annotations

import math

from . import N_CLASSES

_ID_FIELDS = ("participant_id", "recording_id")


def _require_object(doc, where: str) -> dict:
    if not isinstance(doc, dict):
        raise ValueError(f"{where}: document must be an object")
    return doc


def _require_schema_version(doc: dict, where: str) -> None:
    if doc.get("schema_version") != 1:
        raise ValueError(f"{where}: schema_version must be 1")


def _require_nonempty_str(mapping: dict, field: str, where: str) -> None:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: missing or empty required ID field '{field}'")


def validate_class_order(class_order) -> list:
    """Validate an explicit class order; reject ambiguous orders."""
    if not isinstance(class_order, list):
        raise ValueError("class_order must be a list of 4 unique class names")
    if len(class_order) != N_CLASSES:
        raise ValueError(
            f"class_order must have exactly {N_CLASSES} entries, got {len(class_order)}"
        )
    if any(not isinstance(c, str) or not c.strip() for c in class_order):
        raise ValueError("class_order entries must be non-empty strings")
    if len(set(class_order)) != N_CLASSES:
        raise ValueError(f"class_order entries must be unique, got {class_order}")
    return list(class_order)


def validate_manifest(doc: dict) -> None:
    """Cohort/acquisition/split manifest: every record needs both IDs."""
    doc = _require_object(doc, "manifest")
    _require_schema_version(doc, "manifest")
    rows = doc.get("records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest: 'records' must be a non-empty list")
    seen = set()
    for i, row in enumerate(rows):
        where = f"manifest.records[{i}]"
        if not isinstance(row, dict):
            raise ValueError(f"{where}: must be an object")
        for field in _ID_FIELDS:
            _require_nonempty_str(row, field, where)
        key = (row["participant_id"], row["recording_id"])
        if key in seen:
            raise ValueError(f"{where}: duplicate (participant_id, recording_id) {key}")
        seen.add(key)


def validate_predictions(doc: dict) -> None:
    """Prediction files: IDs on every row + explicit unambiguous class order."""
    doc = _require_object(doc, "predictions")
    _require_schema_version(doc, "predictions")
    class_order = validate_class_order(doc.get("class_order"))
    allowed = set(class_order)
    rows = doc.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("predictions: 'rows' must be a non-empty list")
    seen = set()
    for i, row in enumerate(rows):
        where = f"predictions.rows[{i}]"
        if not isinstance(row, dict):
            raise ValueError(f"{where}: must be an object")
        for field in _ID_FIELDS:
            _require_nonempty_str(row, field, where)
        if row["recording_id"] in seen:
            raise ValueError(f"{where}: duplicate recording_id '{row['recording_id']}'")
        seen.add(row["recording_id"])
        for field in ("y_true", "y_pred"):
            if row.get(field) not in allowed:
                raise ValueError(
                    f"{where}: '{field}' must be one of {class_order}, "
                    f"got {row.get(field)!r}"
                )


def validate_metrics(doc: dict) -> None:
    """Metric files: explicit class order + reconciling confusion matrix."""
    doc = _require_object(doc, "metrics")
    _require_schema_version(doc, "metrics")
    required = ("accuracy", "macro_f1", "weighted_f1")
    missing = [field for field in required if field not in doc]
    if missing:
        raise ValueError(f"metrics: missing required fields {missing}")
    class_order = validate_class_order(doc.get("class_order"))
    matrix = doc.get("confusion_matrix")
    if not isinstance(matrix, list) or len(matrix) != N_CLASSES:
        raise ValueError("metrics: 'confusion_matrix' must be a 4x4 list")
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != N_CLASSES:
            raise ValueError(f"metrics: confusion_matrix row {i} must have 4 entries")
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in row):
            raise ValueError(
                f"metrics: confusion_matrix row {i} must hold non-negative ints"
            )
    for field in ("accuracy", "macro_f1", "weighted_f1", "macro_precision", "macro_recall"):
        if field not in doc:
            continue
        value = doc.get(field)
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0.0 <= value <= 1.0):
            raise ValueError(f"metrics: '{field}' must be a number in [0, 1]")
    if "n" in doc:
        n = doc["n"]
        matrix_total = sum(sum(row) for row in matrix)
        if isinstance(n, bool) or not isinstance(n, int) or n != matrix_total:
            raise ValueError(f"metrics: n must equal confusion-matrix total {matrix_total}")


def validate_comparison(doc: dict) -> None:
    """Paired Full/Reduced comparison: shared class order + matched pair IDs."""
    doc = _require_object(doc, "comparison")
    _require_schema_version(doc, "comparison")
    class_order = validate_class_order(doc.get("class_order"))
    for side in ("full_run_id", "reduced_run_id"):
        _require_nonempty_str(doc, side, "comparison")
    gaps = doc.get("metric_gaps")
    if not isinstance(gaps, dict) or not gaps:
        raise ValueError("comparison: 'metric_gaps' must be a non-empty object")
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in gaps.values()):
        raise ValueError("comparison: metric_gaps values must be finite numbers")
    n_boot = doc.get("n_bootstrap")
    if n_boot != 2000:
        raise ValueError(
            f"comparison: 'n_bootstrap' must be 2000 per T25, got {n_boot!r}"
        )


def validate_run_metadata(doc: dict) -> None:
    """Run metadata: identity + provenance hashes; no training outputs inline."""
    doc = _require_object(doc, "run_metadata")
    _require_schema_version(doc, "run_metadata")
    for field in ("run_id", "config_hash", "split_hash", "input_version"):
        _require_nonempty_str(doc, field, "run_metadata")
    if doc.get("input_version") not in ("full", "reduced"):
        raise ValueError("run_metadata: 'input_version' must be 'full' or 'reduced'")
    validate_class_order(doc.get("class_order"))


def validate_config(doc: dict) -> None:
    """Example config: class order explicit; unverified fields must say so."""
    doc = _require_object(doc, "config")
    validate_class_order(doc.get("class_order"))
    unverified = doc.get("unverified_fields")
    if (not isinstance(unverified, list) or not unverified
            or any(not isinstance(value, str) or not value.strip() for value in unverified)):
        raise ValueError("config: 'unverified_fields' must list pending items (T03)")
    for field in ("task", "input_versions", "source_dir", "output_dir", "run_dir"):
        if field not in doc:
            raise ValueError(f"config: missing required field '{field}'")
    input_versions = doc["input_versions"]
    if (not isinstance(input_versions, list)
            or any(not isinstance(value, str) for value in input_versions)
            or set(input_versions) != {"full", "reduced"}):
        raise ValueError("config: input_versions must contain exactly full and reduced")
    if doc["task"] != "night-level four-class severity classification":
        raise ValueError("config: unsupported task")
    for field in ("source_dir", "output_dir", "run_dir"):
        if not isinstance(doc[field], str) or not doc[field].strip():
            raise ValueError(f"config: '{field}' must be a non-empty string")
    if doc["output_dir"] == doc["source_dir"] or doc["run_dir"] == doc["source_dir"]:
        raise ValueError("config: source and generated output directories must differ")
