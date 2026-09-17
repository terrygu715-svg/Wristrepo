"""Checkpoint bundle persistence (T26). numpy + stdlib.

A bundle is a directory: model.json (identity, provenance, ordered
channels/features, class mapping) + arrays.npz (fitted parameters).
Writes are atomic (temp dir + os.replace). Loads reject incompatible
feature/config versions instead of silently misshaping.

Round-trip inference matching itself lives in the model adapters
(T28–T30/T33); this module proves state survives the trip bit-for-bit
for arrays and exactly for metadata, which is what makes adapter
round-trips meaningful.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from sleep_apnea.contracts import validate_class_order

SCHEMA_VERSION = 1


def save_bundle(
    path: str | os.PathLike,
    *,
    run_id: str,
    config_hash: str,
    split_hash: str,
    input_version: str,
    class_order: list[str],
    feature_order: list[str],
    model_type: str,
    arrays: dict[str, np.ndarray] | None = None,
    meta: dict | None = None,
) -> Path:
    """Persist a bundle atomically. Returns the bundle path."""
    if input_version not in ("full", "reduced"):
        raise ValueError("input_version must be 'full' or 'reduced'")
    order = validate_class_order(class_order)
    if not feature_order or any(not isinstance(f, str) for f in feature_order):
        raise ValueError("feature_order must be a non-empty list of names")
    for field, value in (
        ("run_id", run_id),
        ("config_hash", config_hash),
        ("split_hash", split_hash),
        ("model_type", model_type),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"bundle: missing or empty {field!r}")

    dest = Path(path)
    tmp_root = Path(tempfile.mkdtemp(prefix=dest.name + ".", dir=str(dest.parent)))
    try:
        (tmp_root / "model.json").write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "config_hash": config_hash,
                    "split_hash": split_hash,
                    "input_version": input_version,
                    "class_order": order,
                    "feature_order": list(feature_order),
                    "model_type": model_type,
                    "meta": dict(meta or {}),
                },
                indent=2,
            )
        )
        with open(tmp_root / "arrays.npz", "wb") as fh:
            np.savez(fh, **(arrays or {}))
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(tmp_root, dest)
    except BaseException:
        shutil.rmtree(tmp_root, ignore_errors=True)
        raise
    return dest


def load_bundle(
    path: str | os.PathLike,
    *,
    expect_config_hash: str | None = None,
    expect_feature_order: list[str] | None = None,
    expect_class_order: list[str] | None = None,
) -> dict:
    """Load a bundle; version mismatches raise instead of proceeding."""
    dest = Path(path)
    try:
        model = json.loads((dest / "model.json").read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"bundle {dest}: unreadable model.json ({exc})") from exc
    if model.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"bundle {dest}: schema_version {model.get('schema_version')!r} "
            f"!= {SCHEMA_VERSION}"
        )
    validate_class_order(model.get("class_order"))
    if expect_config_hash is not None and model.get("config_hash") != expect_config_hash:
        raise ValueError(
            f"bundle {dest}: config_hash {model.get('config_hash')!r} "
            f"!= expected {expect_config_hash!r}"
        )
    if expect_feature_order is not None and list(model.get("feature_order", [])) != list(
        expect_feature_order
    ):
        raise ValueError(f"bundle {dest}: feature_order mismatch")
    if expect_class_order is not None and list(model.get("class_order", [])) != list(
        expect_class_order
    ):
        raise ValueError(f"bundle {dest}: class_order mismatch")
    try:
        arrays = dict(np.load(dest / "arrays.npz", allow_pickle=False))
    except (OSError, ValueError) as exc:
        raise ValueError(f"bundle {dest}: unreadable arrays.npz ({exc})") from exc
    model["arrays"] = arrays
    return model
