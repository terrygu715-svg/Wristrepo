"""Kaggle local ingestion: manifest build + verification (T07, Kaggleamendment §7).

The .docx specified a manifest-based network downloader with mock resume.
For this source the data is local (Kaggledata/, git-ignored), so this module
builds a manifest of byte sizes + SHA-256 + .npy header census and verifies
a directory against a saved manifest. Network resume/retry is Not
applicable (no network, no credentials); manifest + integrity + the
no-secrets guard below are the applicable Done properties.

Secrets guard: data paths and manifests must never contain credentials.
`scan_for_secrets` fails on common credential patterns so T07 handoffs can
prove logs/configs are clean.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from numpy.lib.format import read_magic, read_array_header_1_0

CHUNK = 1 << 20

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|passwd|password|secret|token)\b\s*[:=]"),
    re.compile(r"(?i)\bkaggle[_-]?key\b"),
)


def sha256_file(path: str | os.PathLike, chunk: int = CHUNK) -> str:
    """Streamed SHA-256; never loads whole nights into memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def npy_header(path: str | os.PathLike) -> dict:
    """Read only the .npy header (magic + shape/dtype), not the data."""
    with open(path, "rb") as fh:
        read_magic(fh)
        shape, fortran, dtype = read_array_header_1_0(fh)
    return {"shape": list(shape), "dtype": str(dtype), "fortran_order": bool(fortran)}


def iter_nights(data_dir: str | os.PathLike) -> list[Path]:
    """Sorted User-<id>-Night-<n>.npy paths under polysomnographics/."""
    poly = Path(data_dir) / "polysomnographics"
    files = sorted(poly.glob("User-*-Night-*.npy"))
    if not files:
        raise ValueError(f"no night files found under {poly}")
    return files


def build_manifest(data_dir: str | os.PathLike, hash_files: bool = True) -> dict:
    """Manifest with per-file bytes, sha256, and header census.

    Set hash_files=False for a fast header-only census (T09-style audit).
    """
    files = iter_nights(data_dir)
    records = []
    for path in files:
        stat = path.stat()
        header = npy_header(path)
        records.append(
            {
                "file": path.name,
                "bytes": stat.st_size,
                "sha256": sha256_file(path) if hash_files else None,
                "header": header,
            }
        )
    patients = Path(data_dir) / "patients.csv"
    manifest = {
        "schema_version": 1,
        "source": "local Kaggledata (see docs/kaggle_access.md)",
        "n_files": len(records),
        "total_bytes": sum(r["bytes"] for r in records),
        "records": records,
        "patients_csv": {
            "present": patients.exists(),
            "bytes": patients.stat().st_size if patients.exists() else 0,
            "sha256": sha256_file(patients) if patients.exists() else None,
        },
    }
    return manifest


def verify_manifest(data_dir: str | os.PathLike, manifest: dict) -> list[str]:
    """Re-check sizes (+ hashes where recorded). Returns failure strings."""
    failures: list[str] = []
    by_name = {r["file"]: r for r in manifest.get("records", [])}
    files = {p.name: p for p in iter_nights(data_dir)}
    for name, expected in sorted(by_name.items()):
        path = files.pop(name, None)
        if path is None:
            failures.append(f"missing file: {name}")
            continue
        size = path.stat().st_size
        if size != expected["bytes"]:
            failures.append(f"{name}: size {size} != manifest {expected['bytes']}")
            continue
        if expected.get("sha256") and sha256_file(path) != expected["sha256"]:
            failures.append(f"{name}: sha256 mismatch (corrupt or replaced)")
    for name in sorted(files):
        failures.append(f"unmanifested file: {name}")
    return failures


def scan_for_secrets(text: str) -> list[str]:
    """Return matched secret-pattern descriptions; empty means clean."""
    hits = []
    for pattern in _SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            hits.append(match.group(0).strip())
    return hits


def main(argv: list[str] | None = None) -> int:
    """CLI: build manifest or verify a directory against one."""
    import argparse

    parser = argparse.ArgumentParser(description="Kaggle ingestion manifest tool (T07)")
    parser.add_argument("--data-dir", default="Kaggledata")
    parser.add_argument("--out", default="outputs/kaggle_manifest.json",
                        help="manifest destination (generated dir, never committed)")
    parser.add_argument("--verify", default=None,
                        help="verify --data-dir against this manifest instead of building")
    parser.add_argument("--header-only", action="store_true",
                        help="skip hashing (fast census)")
    args = parser.parse_args(argv)

    if args.verify:
        manifest = json.loads(Path(args.verify).read_text())
        failures = verify_manifest(args.data_dir, manifest)
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"{'OK' if not failures else 'FAILED'}: {args.data_dir}")
        return 1 if failures else 0

    manifest = build_manifest(args.data_dir, hash_files=not args.header_only)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    os.replace(tmp, out)  # atomic write
    print(f"manifest: {manifest['n_files']} files, {manifest['total_bytes']} bytes -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
