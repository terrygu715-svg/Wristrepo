"""T08/T09/T11 tests: sample manifest, value audit, omit/proxy (S02/S05)."""

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.data.alignment import assess  # noqa: E402
from sleep_apnea.data.audit import audit_night, audit_sample  # noqa: E402
from sleep_apnea.data.fixtures import build_fixtures  # noqa: E402
from sleep_apnea.data.sample import SAMPLE_FILES, build_sample  # noqa: E402


def _tiny_source(root: Path) -> None:
    poly = root / "polysomnographics"
    poly.mkdir(parents=True)
    rng = np.random.default_rng(1)
    np.save(poly / "User-16-Night-1.npy", rng.normal(size=(6, 600)))
    np.save(poly / "User-17-Night-1.npy", rng.normal(size=(6, 610)))
    (root / "patients.csv").write_text(
        "user_id,night_id,AHI\n16,1,\"56,5\"\n17,1,\"15,2\"\n"
    )


class TestSampleManifest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.src = Path(self._tmp.name) / "src"
        _tiny_source(self.src)

    def test_builds_with_reserved_ids(self):
        out = Path(self._tmp.name) / "sample_manifest.json"
        manifest = build_sample(self.src, out)
        self.assertEqual(
            manifest["inspection_ids"], ["User-16-Night-1", "User-17-Night-1"]
        )
        self.assertTrue(all(r["reserved_for"] == "development" for r in manifest["records"]))
        self.assertTrue(all(r["label_present"] for r in manifest["records"]))
        reread = json.loads(out.read_text())
        self.assertEqual(len(reread["records"]), 2)

    def test_missing_sample_file_raises(self):
        (self.src / "polysomnographics" / "User-17-Night-1.npy").unlink()
        with self.assertRaises(ValueError):
            build_sample(self.src, Path(self._tmp.name) / "out.json")

    def test_source_manifest_mismatch_raises(self):
        manifest = {
            "records": [{"file": "User-16-Night-1.npy", "bytes": 1, "sha256": "bad"}]
        }
        with self.assertRaises(ValueError):
            build_sample(self.src, Path(self._tmp.name) / "out.json",
                         files=("User-16-Night-1.npy",), source_manifest=manifest)

    def test_label_join_missing_raises(self):
        (self.src / "patients.csv").write_text("user_id,night_id,AHI\n16,1,\"56,5\"\n")
        with self.assertRaises(ValueError):
            build_sample(self.src, Path(self._tmp.name) / "out.json")

    def test_path_traversal_and_duplicate_selection_rejected(self):
        with self.assertRaises(ValueError):
            build_sample(self.src, Path(self._tmp.name) / "out.json",
                         files=("../patients.csv",))
        with self.assertRaises(ValueError):
            build_sample(self.src, Path(self._tmp.name) / "out.json",
                         files=("User-16-Night-1.npy",) * 2)

    def test_default_sample_pair_is_stable(self):
        self.assertEqual(SAMPLE_FILES, ("User-16-Night-1.npy", "User-17-Night-1.npy"))


class TestAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile

        cls._tmp = tempfile.TemporaryDirectory()
        cls.manifest = build_fixtures(cls._tmp.name)
        cls.dir = Path(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_shape_dtype_recorded(self):
        record = audit_night(self.dir / "SYNTH_P001_N1.npy")
        self.assertEqual(record["shape"], [6, 6000])
        self.assertEqual(record["dtype"], "float64")
        self.assertEqual(len(record["channels"]), 6)
        self.assertIn("std", record["channels"][0])
        self.assertGreater(record["channels"][0]["std"], 0.0)
        self.assertEqual(record["channels"][0]["extreme_count"], 0)

    def test_nan_block_detected_where_flagged(self):
        by_id = {r["recording_id"]: r for r in self.manifest["records"]}
        for rec_id, row in by_id.items():
            record = audit_night(self.dir / f"{rec_id}.npy")
            nan_any = any(ch["nan_fraction"] > 0 for ch in record["channels"])
            self.assertEqual(nan_any, row["missing_block"], rec_id)

    def test_non_6ch_quarantined_not_scored(self):
        odd = self.dir / "ODD_N1.npy"
        np.save(odd, np.zeros((16, 600)))
        inventory = audit_sample([self.dir / "SYNTH_P001_N1.npy", odd])
        self.assertEqual(len(inventory["records"]), 1)
        self.assertEqual(len(inventory["quarantined"]), 1)
        self.assertIn("quarantined", inventory["quarantined"][0]["reason"])
        self.assertIn("excluded", inventory["quarantined"][0]["reason"])

    def test_quarantined_record_retains_complete_evidence(self):
        odd = self.dir / "ODD_N1.npy"
        np.save(odd, np.zeros((16, 600)))
        record = audit_sample([odd])["quarantined"][0]
        self.assertEqual(record["dtype"], "float64")
        self.assertEqual(record["bytes"], odd.stat().st_size)
        self.assertEqual(len(record["sha256"]), 64)
        self.assertEqual(len(record["channels"]), 16)
        self.assertIn("nan_fraction", record["channels"][0])

    def test_non_2d_rejected(self):
        flat = self.dir / "FLAT_N1.npy"
        np.save(flat, np.zeros(600))
        with self.assertRaises(ValueError):
            audit_night(flat)

    def test_extreme_nan_inf_are_separately_counted(self):
        special = self.dir / "SPECIAL_N1.npy"
        arr = np.zeros((2, 4), dtype=float)
        arr[0] = [0.0, 2000.0, np.nan, np.inf]
        np.save(special, arr)
        record = audit_night(special)
        channel = record["channels"][0]
        self.assertEqual(channel["extreme_count"], 1)
        self.assertAlmostEqual(channel["nan_fraction"], 0.25)
        self.assertAlmostEqual(channel["inf_fraction"], 0.25)


class TestAlignmentDecision(unittest.TestCase):
    def test_kaggle_case_omits_with_reasons(self):
        out = assess(6, False)
        self.assertEqual(out["decision"], "omit")
        self.assertTrue(len(out["reasons"]) >= 2)
        self.assertIn("T12", out["consequence"])

    def test_evidenced_proxy_accepted(self):
        out = assess(
            6, True, motion_channels=[5],
            overlap_evidence={
                "source": "overlap.json",
                "overlap_fraction": 0.95,
                "max_abs_offset_seconds": 0.5,
            },
        )
        self.assertEqual(out["decision"], "proxy")
        self.assertEqual(out["motion_channels"], [5])
        self.assertEqual(out["overlap_evidence"]["overlap_fraction"], 0.95)

    def test_claimed_motion_without_overlap_omits(self):
        out = assess(6, True, motion_channels=[5])
        self.assertEqual(out["decision"], "omit")
        self.assertTrue(any("E03" in r for r in out["reasons"]))

    def test_invalid_motion_index_rejected(self):
        with self.assertRaises(ValueError):
            assess(6, True, motion_channels=[6], overlap_evidence="map.json")

    def test_boolean_channel_values_rejected(self):
        with self.assertRaises(ValueError):
            assess(True, True)
        with self.assertRaises(ValueError):
            assess(6, True, motion_channels=[True])

    def test_blank_overlap_evidence_does_not_clear_gate(self):
        out = assess(6, True, motion_channels=[1], overlap_evidence=" ")
        self.assertEqual(out["decision"], "omit")

    def test_unquantified_overlap_evidence_does_not_clear_gate(self):
        out = assess(6, True, motion_channels=[1], overlap_evidence={"source": "map.json"})
        self.assertEqual(out["decision"], "omit")
        self.assertIn("quantified", out["reasons"][0])


if __name__ == "__main__":
    unittest.main()
