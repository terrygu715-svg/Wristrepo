"""Small real-sample acquisition from local Kaggledata (T08, Kaggle §7).

No network: selects a representative subset, verifies integrity against the
T07 manifest, and writes a sample manifest + integrity log. Selected
inspection records are reserved for development (T18 exclusion list).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from sleep_apnea.data.ingest import npy_header, sha256_file
from sleep_apnea.labels import load_patients

# Deterministic, pre-registered before any signal inspection: one severe,
# one near-boundary night; both 6-channel labelled nights.
SAMPLE_FILES = ("User-16-Night-1.npy", "User-17-Night-1.npy")


def build_sample(
    data_dir: str | os.PathLike, out_path: str | os.PathLike,
    files: tuple[str, ...] = SAMPLE_FILES,
    source_manifest: dict | None = None,
) -> dict:
    """Verify selected files against T07's manifest and write T08 output."""
    poly = Path(data_dir) / "polysomnographics"
    if not files:
        raise ValueError("sample must contain at least one file")
    if len(set(files)) != len(files):
        raise ValueError("sample file list contains duplicates")
    patient_rows = load_patients(Path(data_dir) / "patients.csv")
    label_by_id = {row["recording_id"]: row for row in patient_rows}
    expected = {
        record["file"]: record
        for record in (source_manifest or {}).get("records", [])
    }
    records = []
    for name in files:
        relative = Path(name)
        if relative.name != name or relative.is_absolute():
            raise ValueError(f"sample file must be a direct night filename: {name!r}")
        match = re.fullmatch(r"User-([^/]+)-Night-([^/]+)\.npy", name)
        if match is None:
            raise ValueError(f"sample file has invalid night name: {name!r}")
        label_id = f"KAGGLE_U{match.group(1)}_N{match.group(2)}"
        if label_id not in label_by_id:
            raise ValueError(f"sample file has no patients.csv row: {name}")
        path = poly / relative
        if not path.exists():
            raise ValueError(f"sample file missing: {name}")
        if source_manifest is not None:
            if name not in expected:
                raise ValueError(f"sample file is absent from source manifest: {name}")
            source = expected[name]
            if path.stat().st_size != source["bytes"]:
                raise ValueError(f"sample file size differs from source manifest: {name}")
            digest = sha256_file(path)
            if source.get("sha256") and digest != source["sha256"]:
                raise ValueError(f"sample file hash differs from source manifest: {name}")
        else:
            digest = sha256_file(path)
        header = npy_header(path)
        records.append({
            "file": name,
            "bytes": path.stat().st_size,
            "sha256": digest,
            "header": header,
            "label_recording_id": label_id,
            "label_present": label_by_id[label_id]["ahi"] is not None,
            "reserved_for": "development",
        })
    manifest = {
        "schema_version": 1,
        "source": "local Kaggledata (see docs/kaggle_access.md)",
        "records": records,
        "inspection_ids": [r["file"].replace(".npy", "") for r in records],
        "source_manifest_verified": source_manifest is not None,
        "note": "inspection records: development-only in T18 splits",
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    os.replace(tmp, out)
    return manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="T08 local sample manifest")
    parser.add_argument("--data-dir", default="Kaggledata")
    parser.add_argument("--out", default="outputs/sample_manifest.json")
    parser.add_argument("--manifest", default=None,
                        help="T07 manifest JSON to verify selected files against")
    args = parser.parse_args(argv)
    source_manifest = (
        json.loads(Path(args.manifest).read_text()) if args.manifest else None
    )
    manifest = build_sample(args.data_dir, args.out, source_manifest=source_manifest)
    print(f"sample: {len(manifest['records'])} files -> {args.out}")
    print(f"reserved inspection ids: {manifest['inspection_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
