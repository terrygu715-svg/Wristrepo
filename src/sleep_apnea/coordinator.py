"""Coordinator scheduling and resume (T34). Stdlib-only.

Schedules configured pipeline/input dependencies with mocked jobs first.
Tracks pending/running/succeeded/failed states with exact artifact hashes.
Resume rejects stale hashes: a job whose recorded artifact hash no longer
matches the expected hash goes back to pending instead of being marked
succeeded. Concurrent workers must write distinct outputs; only one
process owns the run ledger (lock-file guard).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

STATES = ("pending", "running", "succeeded", "failed")


def artifact_hash(payload: object) -> str:
    """Stable hash of a JSON-serializable artifact description."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


class LedgerBusy(RuntimeError):
    """Raised when a second writer tries to own the same run ledger."""


class RunLedger:
    """Single-writer job ledger persisted as one JSON file."""

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise LedgerBusy(f"ledger {self.path} already owned") from exc
        os.close(fd)
        if self.path.exists():
            self.jobs: dict = json.loads(self.path.read_text()).get("jobs", {})
        else:
            self.jobs = {}
            self._write()

    def _write(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"jobs": self.jobs}, indent=2, sort_keys=True))
        os.replace(tmp, self.path)

    def release(self) -> None:
        """Release ledger ownership (removes the lock)."""
        try:
            os.remove(self.lock_path)
        except FileNotFoundError:
            pass

    def add_job(self, job_id: str, deps: list[str] | None = None,
                out_path: str | None = None) -> None:
        if job_id in self.jobs:
            raise ValueError(f"duplicate job {job_id!r}")
        self.jobs[job_id] = {
            "state": "pending",
            "deps": list(deps or []),
            "out_path": out_path,
            "artifact_hash": None,
            "error": None,
        }
        self._write()

    def _set(self, job_id: str, state: str, **fields) -> None:
        if state not in STATES:
            raise ValueError(f"bad state {state!r}")
        self.jobs[job_id].update({"state": state, **fields})
        self._write()

    def order(self) -> list[str]:
        """Topological order over deps; cycles and unknown deps raise."""
        ordered: list[str] = []
        visiting: set[str] = set()

        def visit(job_id: str) -> None:
            if job_id in ordered:
                return
            if job_id in visiting:
                raise ValueError(f"dependency cycle at {job_id!r}")
            if job_id not in self.jobs:
                raise ValueError(f"unknown dependency {job_id!r}")
            visiting.add(job_id)
            for dep in self.jobs[job_id]["deps"]:
                visit(dep)
            visiting.remove(job_id)
            ordered.append(job_id)

        for job_id in self.jobs:
            visit(job_id)
        return ordered

    def run_all(self, handlers: dict[str, object]) -> dict[str, str]:
        """Run jobs in dependency order. handlers[job_id]() -> artifact payload.

        A handler exception marks the job failed (stays visible); dependent
        jobs are skipped, never silently marked succeeded. Returns states.
        """
        out_paths: dict[str, str | None] = {}
        for job_id in self.order():
            job = self.jobs[job_id]
            if any(self.jobs[d]["state"] != "succeeded" for d in job["deps"]):
                self._set(job_id, "failed", error="blocked: dependency not succeeded")
                continue
            out = job["out_path"]
            if out is not None and out in out_paths.values():
                self._set(job_id, "failed", error=f"output collision on {out!r}")
                continue
            out_paths[job_id] = out
            self._set(job_id, "running")
            try:
                payload = handlers[job_id]()  # type: ignore[operator]
            except Exception as exc:  # noqa: BLE001 - recorded, not hidden
                self._set(job_id, "failed", error=f"{type(exc).__name__}: {exc}")
                continue
            self._set(job_id, "succeeded", artifact_hash=artifact_hash(payload),
                      error=None)
        return {job_id: self.jobs[job_id]["state"] for job_id in self.jobs}

    def resume(self, expected_hashes: dict[str, str]) -> list[str]:
        """Reconcile ledger against current artifacts.

        Jobs whose recorded hash differs from expected go back to pending;
        failed jobs stay failed and visible. Returns re-queued job ids.
        """
        requeued = []
        for job_id, expected in expected_hashes.items():
            if job_id not in self.jobs:
                raise ValueError(f"unknown job {job_id!r}")
            job = self.jobs[job_id]
            if job["state"] == "succeeded" and job["artifact_hash"] != expected:
                self._set(job_id, "pending", artifact_hash=None,
                          error="stale hash: artifact changed since success")
                requeued.append(job_id)
        return requeued
