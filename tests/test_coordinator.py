"""T34/T35 tests: scheduling, stale-hash resume, report sections (S14)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.coordinator import LedgerBusy, RunLedger, artifact_hash  # noqa: E402
from sleep_apnea.generate_report import REQUIRED_SECTIONS, generate  # noqa: E402


def _ledger(tmpdir: str) -> RunLedger:
    ledger = RunLedger(Path(tmpdir) / "run.json")
    ledger.add_job("a", out_path="out/a.json")
    ledger.add_job("b", deps=["a"], out_path="out/b.json")
    return ledger


class TestCoordinator(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_dependency_order_and_success(self):
        ledger = _ledger(self._tmp.name)
        calls = []
        states = ledger.run_all({
            "a": lambda: calls.append("a") or {"n": 1},
            "b": lambda: calls.append("b") or {"n": 2},
        })
        ledger.release()
        self.assertEqual(calls, ["a", "b"])
        self.assertEqual(states, {"a": "succeeded", "b": "succeeded"})

    def test_failure_visible_and_blocks_dependents(self):
        ledger = _ledger(self._tmp.name)

        def boom():
            raise RuntimeError("mocked crash")

        states = ledger.run_all({"a": boom, "b": lambda: {"n": 2}})
        ledger.release()
        self.assertEqual(states["a"], "failed")
        self.assertEqual(states["b"], "failed")
        self.assertIn("mocked crash", ledger.jobs["a"]["error"])

    def test_output_collision_fails(self):
        ledger = RunLedger(Path(self._tmp.name) / "run.json")
        ledger.add_job("a", out_path="same.json")
        ledger.add_job("b", out_path="same.json")
        states = ledger.run_all({"a": lambda: {}, "b": lambda: {}})
        ledger.release()
        self.assertEqual(states["b"], "failed")

    def test_resume_rejects_stale_hash(self):
        ledger = _ledger(self._tmp.name)
        ledger.run_all({"a": lambda: {"v": 1}, "b": lambda: {"v": 2}})
        stale = artifact_hash({"v": "changed"})
        requeued = ledger.resume({"a": stale, "b": ledger.jobs["b"]["artifact_hash"]})
        ledger.release()
        self.assertEqual(requeued, ["a"])
        self.assertEqual(ledger.jobs["a"]["state"], "pending")

    def test_resume_requeues_interrupted_running_job(self):
        ledger = _ledger(self._tmp.name)
        ledger.jobs["a"]["state"] = "running"
        requeued = ledger.resume({})
        ledger.release()
        self.assertEqual(requeued, ["a"])
        self.assertEqual(ledger.jobs["a"]["state"], "pending")

    def test_artifact_hash_rejects_non_json_payload(self):
        with self.assertRaises(TypeError):
            artifact_hash({"bad": object()})

    def test_failed_job_survives_resume(self):
        ledger = _ledger(self._tmp.name)
        ledger.run_all({"a": lambda: 1 / 0, "b": lambda: {"v": 2}})
        requeued = ledger.resume({"a": artifact_hash({"other": 1})})
        ledger.release()
        self.assertEqual(requeued, [])
        self.assertEqual(ledger.jobs["a"]["state"], "failed")

    def test_release_allows_reacquire(self):
        path = Path(self._tmp.name) / "run.json"
        first = RunLedger(path)
        first.release()
        second = RunLedger(path)
        second.release()

    def test_dead_owner_lock_is_recovered(self):
        from unittest.mock import patch

        path = Path(self._tmp.name) / "run.json"
        lock = path.with_suffix(".json.lock")
        path.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text('{"pid": 12345}')
        with patch("sleep_apnea.coordinator.os.kill", side_effect=ProcessLookupError):
            ledger = RunLedger(path)
        ledger.release()

    def test_single_writer_enforced(self):
        first = RunLedger(Path(self._tmp.name) / "run.json")
        with self.assertRaises(LedgerBusy):
            RunLedger(Path(self._tmp.name) / "run.json")
        first.release()

    def test_cycle_raises(self):
        ledger = RunLedger(Path(self._tmp.name) / "run.json")
        ledger.add_job("a", deps=["b"])
        ledger.add_job("b", deps=["a"])
        with self.assertRaises(ValueError):
            ledger.order()
        ledger.release()


class TestReport(unittest.TestCase):
    def _inputs(self):
        order = ["normal", "mild", "moderate", "severe"]
        return {
            "metrics": {
                "class_order": order,
                "accuracy": 0.5, "macro_f1": 0.4, "weighted_f1": 0.45,
                "per_class": {c: {"precision": 0.5, "recall": 0.5, "f1": 0.5,
                                  "support": 2} for c in order},
            },
            "comparison": {"metric": "macro_f1", "mean_gap": 0.01,
                           "ci_low_95": -0.02, "ci_high_95": 0.04,
                           "n_bootstrap": 2000, "seed": 0,
                           "conditioning": "synthetic conditioning note"},
            "cohort": {"development": 4, "test": 1},
            "run_metadata": {"run_id": "SYNTH_R1", "config_hash": "cfg"},
        }

    def test_all_sections_and_synthetic_banner(self):
        text = generate(**self._inputs(), synthetic=True)
        for section in REQUIRED_SECTIONS:
            self.assertIn(f"## {section}", text)
        self.assertIn("SYNTHETIC", text)

    def test_non_synthetic_banner(self):
        text = generate(**self._inputs(), synthetic=False)
        self.assertNotIn("SYNTHETIC", text)
        self.assertIn("FINAL REPORT", text)

    def test_deterministic_regeneration(self):
        self.assertEqual(generate(**self._inputs()), generate(**self._inputs()))

    def test_missing_input_rejected(self):
        inputs = self._inputs()
        inputs["metrics"] = {}
        with self.assertRaises(ValueError):
            generate(**inputs)


if __name__ == "__main__":
    unittest.main()
