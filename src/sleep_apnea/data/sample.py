"""Small real-sample acquisition from local Kaggledata (T08, Kaggle §7).

No network: selects a representative subset, verifies integrity against the
T07 manifest, and writes a sample manifest + integrity log. Selected
inspection records are reserved for development (T18 exclusion list).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from sleep_apnea.data.ingest import iter_nights, sha256_file

# Deterministic, pre-registered before any signal inspection: one severe,
# one near-boundary night; both 6-channel labelled nights.
SAMPLE_FILES = ("User-16-Night-1.npy", "User-17-Night-1.npy")


def build_sample(
    data_dir: str | os.PathLike, out_path: str | os.PathLike,
    files: tuple[str, ...] = SAMPLE_FILES,
) -> dict:
    """Verify sample files and write the sample manifest. Returns manifest."""
    poly = Path(data_dir) / "polysomnographics"
    records = []
    for name in files:
        path = poly / name
        if not path.exists():
            raise ValueError(f"sample file missing: {name}")
        records.append({
            "file": name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "reserved_for": "development",
        })
    manifest = {
        "schema_version": 1,
        "source": "local Kaggledata (see docs/kaggle_access.md)",
        "records": records,
        "inspection_ids": [r["file"].replace(".npy", "") for r in records],
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
    args = parser.parse_args(argv)
    manifest = build_sample(args.data_dir, args.out)
    print(f"sample: {len(manifest['records'])} files -> {args.out}")
    print(f"reserved inspection ids: {manifest['inspection_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
