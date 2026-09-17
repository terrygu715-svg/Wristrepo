"""Synthetic recording fixtures (T06). Prominently synthetic, never results.

Builds tiny 6-channel .npy nights plus a fixture manifest that exercises:
class boundaries (AHI exactly 5.0/15.0/30.0), a NaN missing block, and a
repeated participant ID placed in two splits as a leakage tripwire.

All IDs use the SYNTH_ prefix. Layout imitates the Kaggle source
(channels x samples, float64) at 1/1000th scale so tests stay fast.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np

from sleep_apnea.labels import class_of

N_CHANNELS = 6
N_SAMPLES = 6000
RNG_SEED = 20260917

# (participant_id, ahi, split, missing_block)
FIXTURE_ROWS = (
    ("SYNTH_P001", 2.0, "development", False),   # normal
    ("SYNTH_P002", 5.0, "development", False),   # mild boundary (inclusive lower)
    ("SYNTH_P003", 15.0, "development", True),   # moderate boundary + NaN block
    ("SYNTH_P004", 30.0, "development", False),  # severe boundary
    ("SYNTH_P005", 45.0, "development", False),  # severe
    # Leakage tripwire: same participant, second night staged in "test".
    ("SYNTH_P005", 45.0, "test", False),
)


def _night_id(pid: str, split: str, seen: set[str]) -> str:
    """Unique night per (participant, split); tripwire keeps its own night."""
    candidate = f"{pid}_N1"
    n = 1
    while candidate in seen:
        n += 1
        candidate = f"{pid}_N{n}"
    seen.add(candidate)
    return candidate


def make_night(rng: np.random.Generator, missing_block: bool) -> np.ndarray:
    """Deterministic (6, N_SAMPLES) float64 night; optional NaN block on ch 0."""
    night = rng.normal(loc=0.0, scale=5.0, size=(N_CHANNELS, N_SAMPLES))
    if missing_block:
        night[0, 2000:3000] = np.nan
    return night


def check_participant_disjointness(records: list[dict]) -> list[str]:
    """Leakage check: participant_ids must not span splits. Returns violations."""
    seen: dict[str, str] = {}
    violations: list[str] = []
    for row in records:
        pid, split = row["participant_id"], row["split"]
        if pid in seen and seen[pid] != split:
            violations.append(f"{pid} spans splits {seen[pid]!r} and {split!r}")
        seen.setdefault(pid, split)
    return violations


def build_fixtures(fixture_dir: str | os.PathLike) -> dict:
    """Write .npy nights + manifest.json + labels.csv. Returns the manifest."""
    out = Path(fixture_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    records = []
    seen_nights: set[str] = set()
    for pid, ahi, split, missing in FIXTURE_ROWS:
        night_id = _night_id(pid, split, seen_nights)
        np.save(out / f"{night_id}.npy", make_night(rng, missing))
        records.append(
            {
                "participant_id": pid,
                "recording_id": night_id,
                "split": split,
                "ahi": ahi,
                "class": class_of(ahi),
                "missing_block": missing,
                "synthetic": True,
            }
        )
    manifest = {"schema_version": 1, "synthetic": True, "records": records}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    with open(out / "labels.csv", "w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["participant_id", "recording_id", "ahi", "class", "split"]
        )
        writer.writeheader()
        for row in records:
            writer.writerow({k: row[k] for k in writer.fieldnames})
    return manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build T06 synthetic fixtures")
    parser.add_argument("--out", default="tests/fixtures")
    args = parser.parse_args(argv)
    manifest = build_fixtures(args.out)
    n = len(manifest["records"])
    print(f"fixtures: {n} records -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
