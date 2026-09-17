"""Reference label adapter for Kaggle patients.csv (T10, Kaggle §7).

Preferred path per the ticket: a verified summary AHI variable — which is
what patients.csv provides, so no XML/event reconstruction (C01 is Not
applicable; recorded in docs/kaggle_evidence.md). Handles the source's
comma decimals, exact 5/15/30 lower-inclusive boundaries, and the 20
unlabelled users as documented exclusions with reasons.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

from sleep_apnea.data.fixtures import class_of

REQUIRED_COLUMNS = ("user_id", "night_id", "AHI")


def parse_decimal(raw: str | None) -> float | None:
    """Parse comma- or dot-decimal numbers; blank/NA -> None."""
    text = (raw or "").strip()
    if text in ("", "NA", "NaN", "nan"):
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"unparsable numeric {raw!r}") from exc


def load_patients(csv_path: str | os.PathLike) -> list[dict]:
    """All rows with parsed AHI (None when absent) + exclusion reasons."""
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"patients.csv missing columns: {missing}")
        rows = []
        for line in reader:
            ahi = parse_decimal(line.get("AHI"))
            rows.append({
                "participant_id": f"KAGGLE_U{line['user_id'].strip()}",
                "night": line["night_id"].strip(),
                "recording_id": f"KAGGLE_U{line['user_id'].strip()}_N{line['night_id'].strip()}",
                "ahi": ahi,
                "class": class_of(ahi) if ahi is not None else None,
                "exclusion_reason": None if ahi is not None
                else "no AHI in source row (U06)",
            })
        return rows


def build_label_table(rows: list[dict], one_night: str = "1") -> dict:
    """One-night-per-participant label table + documented exclusions."""
    labelled = [r for r in rows if r["ahi"] is not None]
    if not labelled:
        raise ValueError("no labelled rows; check decimal parsing")
    participants: dict[str, dict] = {}
    for row in labelled:
        if row["night"] == one_night:
            participants[row["participant_id"]] = row
    if not participants:
        raise ValueError(f"one-night={one_night!r} selected nothing")
    return {
        "schema_version": 1,
        "one_night": one_night,
        "records": [participants[pid] for pid in sorted(participants)],
        "excluded_unlabelled": [
            {"participant_id": r["participant_id"], "recording_id": r["recording_id"],
             "reason": r["exclusion_reason"]}
            for r in rows if r["ahi"] is None
        ],
    }


def reconcile(sample_keys: list[str], table: dict) -> list[str]:
    """Sample recording keys (User-<id>-Night-<n>) must resolve to labels."""
    by_key = {}
    for row in table["records"]:
        pid = row["participant_id"].replace("KAGGLE_U", "User-")
        by_key[f"{pid}-Night-{row['night']}"] = row["ahi"]
    return [key for key in sample_keys if key not in by_key]
