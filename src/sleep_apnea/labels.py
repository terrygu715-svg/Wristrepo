"""Reference label adapter for Kaggle patients.csv (T10, Kaggle §7).

Preferred path per the ticket: a verified summary AHI variable — which is
what patients.csv provides, so no XML/event reconstruction (C01 is Not
applicable; recorded in docs/kaggle_evidence.md). Handles the source's
comma decimals, exact 5/15/30 lower-inclusive boundaries, and the 20
unlabelled users as documented exclusions with reasons.
"""

from __future__ import annotations

import csv
import math
import os
import re

REQUIRED_COLUMNS = ("user_id", "night_id", "AHI")
DEFAULT_BOUNDARIES = (5.0, 15.0, 30.0)


def _validate_boundaries(boundaries: tuple[float, float, float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in boundaries)
    if len(values) != 3 or any(not math.isfinite(value) for value in values):
        raise ValueError("class boundaries must contain three finite values")
    if not values[0] < values[1] < values[2]:
        raise ValueError("class boundaries must be strictly increasing")
    return values


def class_of(ahi: float, boundaries: tuple[float, float, float] = DEFAULT_BOUNDARIES) -> str:
    """Map AHI to four lower-inclusive classes using explicit boundaries."""
    if not math.isfinite(float(ahi)):
        raise ValueError(f"AHI must be finite, got {ahi!r}")
    lower = _validate_boundaries(boundaries)
    if ahi < lower[0]:
        return "normal"
    if ahi < lower[1]:
        return "mild"
    if ahi < lower[2]:
        return "moderate"
    return "severe"


def parse_decimal(raw: str | None) -> float | None:
    """Parse comma- or dot-decimal numbers; blank/NA -> None."""
    text = (raw or "").strip()
    if text == "" or text.casefold() in ("na", "nan"):
        return None
    try:
        value = float(text.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"unparsable numeric {raw!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"numeric value must be finite, got {raw!r}")
    return value


def load_patients(
    csv_path: str | os.PathLike,
    boundaries: tuple[float, float, float] = DEFAULT_BOUNDARIES,
) -> list[dict]:
    """All rows with parsed AHI (None when absent) + exclusion reasons."""
    boundaries = _validate_boundaries(boundaries)
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"patients.csv missing columns: {missing}")
        rows = []
        seen: set[tuple[str, str]] = set()
        for line in reader:
            user_id = (line.get("user_id") or "").strip()
            night_id = (line.get("night_id") or "").strip()
            if not user_id or not night_id:
                raise ValueError("patients.csv rows require non-empty user_id and night_id")
            key = (user_id, night_id)
            if key in seen:
                raise ValueError(f"duplicate patients.csv row for user/night {key}")
            seen.add(key)
            ahi = parse_decimal(line.get("AHI"))
            rows.append({
                "participant_id": f"KAGGLE_U{user_id}",
                "night": night_id,
                "recording_id": f"KAGGLE_U{user_id}_N{night_id}",
                "ahi": ahi,
                "class": class_of(ahi, boundaries) if ahi is not None else None,
                "exclusion_reason": None if ahi is not None
                else "no AHI in source row (U06)",
            })
        return rows


def build_label_table(
    rows: list[dict],
    one_night: str = "1",
    boundaries: tuple[float, float, float] = DEFAULT_BOUNDARIES,
) -> dict:
    """One-night-per-participant label table + participant exclusions."""
    boundaries = _validate_boundaries(boundaries)
    if not one_night:
        raise ValueError("one_night must be non-empty")
    by_participant: dict[str, dict[str, dict]] = {}
    for row in rows:
        try:
            participant_id = row["participant_id"]
            night = row["night"]
            recording_id = row["recording_id"]
            ahi = row["ahi"]
        except KeyError as exc:
            raise ValueError(f"label row missing required field {exc.args[0]!r}") from exc
        if not all(isinstance(value, str) and value for value in
                   (participant_id, night, recording_id)):
            raise ValueError("label rows require non-empty participant/night/recording IDs")
        if night in by_participant.setdefault(participant_id, {}):
            raise ValueError(f"duplicate label row for {participant_id!r}, night {night!r}")
        by_participant[participant_id][night] = row

    if not by_participant:
        raise ValueError("no labelled rows; check decimal parsing")
    records: list[dict] = []
    excluded: list[dict] = []
    all_missing_rows: list[dict] = []
    for participant_id in sorted(by_participant):
        selected = by_participant[participant_id].get(one_night)
        if selected is None:
            excluded.append({
                "participant_id": participant_id,
                "recording_id": None,
                "reason": f"selected night {one_night!r} is absent (U06)",
            })
            continue
        if selected["ahi"] is None:
            excluded.append({
                "participant_id": participant_id,
                "recording_id": selected["recording_id"],
                "reason": selected.get("exclusion_reason") or "no AHI in source row (U06)",
            })
            continue
        record = dict(selected)
        record["class"] = class_of(float(record["ahi"]), boundaries)
        records.append(record)
    for row in rows:
        if row["ahi"] is None:
            all_missing_rows.append({
                "participant_id": row["participant_id"],
                "recording_id": row["recording_id"],
                "reason": row.get("exclusion_reason") or "no AHI in source row (U06)",
            })
    if not records:
        raise ValueError(f"one-night={one_night!r} selected nothing")
    return {
        "schema_version": 1,
        "one_night": one_night,
        "class_boundaries": list(boundaries),
        "records": records,
        "excluded_unlabelled": excluded,
        "excluded_source_rows": all_missing_rows,
    }


def reconcile(sample_keys: list[str], table: dict) -> list[str]:
    """Sample recording keys (User-<id>-Night-<n>) must resolve to labels."""
    by_id = {row["recording_id"] for row in table.get("records", [])}
    missing = []
    for key in sample_keys:
        match = re.fullmatch(r"User-([^/]+)-Night-([^/]+)", key)
        if match is None:
            missing.append(key)
            continue
        recording_id = f"KAGGLE_U{match.group(1)}_N{match.group(2)}"
        if recording_id not in by_id:
            missing.append(key)
    return missing
