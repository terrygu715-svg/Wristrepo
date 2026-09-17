"""T06 fixture tests: boundaries, missingness, leakage tripwire (S01/S03)."""

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.contracts import validate_manifest  # noqa: E402
from sleep_apnea.data.fixtures import (  # noqa: E402
    build_fixtures,
    check_participant_disjointness,
    class_of,
)


class TestFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile

        cls._tmp = tempfile.TemporaryDirectory()
        cls.manifest = build_fixtures(cls._tmp.name)
        cls.dir = Path(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_manifest_validates_against_contracts(self):
        validate_manifest(self.manifest)

    def test_boundary_classes(self):
        self.assertEqual(class_of(4.999), "normal")
        self.assertEqual(class_of(5.0), "mild")
        self.assertEqual(class_of(15.0), "moderate")
        self.assertEqual(class_of(30.0), "severe")

    def test_nights_are_tiny_float64(self):
        for row in self.manifest["records"]:
            arr = np.load(self.dir / f"{row['recording_id']}.npy")
            self.assertEqual(arr.shape, (6, 6000))
            self.assertEqual(str(arr.dtype), "float64")

    def test_missing_block_present(self):
        flagged = [r for r in self.manifest["records"] if r["missing_block"]]
        self.assertTrue(flagged, "need at least one missing-block fixture")
        for row in flagged:
            arr = np.load(self.dir / f"{row['recording_id']}.npy")
            self.assertTrue(np.isnan(arr).any())

    def test_leakage_tripwire_fires(self):
        violations = check_participant_disjointness(self.manifest["records"])
        self.assertTrue(
            any("SYNTH_P005" in v for v in violations),
            f"repeated participant must be flagged, got {violations}",
        )

    def test_clean_manifest_passes_disjointness(self):
        dev_only = [r for r in self.manifest["records"] if r["split"] == "development"]
        self.assertEqual(check_participant_disjointness(dev_only), [])


if __name__ == "__main__":
    unittest.main()
