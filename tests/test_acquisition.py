"""T07 ingestion tests: manifest round-trip, corruption, secrets (S02)."""

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.data.ingest import (  # noqa: E402
    build_manifest,
    npy_header,
    scan_for_secrets,
    verify_manifest,
)


def _tiny_tree(root: Path) -> None:
    poly = root / "polysomnographics"
    poly.mkdir(parents=True)
    rng = np.random.default_rng(0)
    np.save(poly / "User-1-Night-1.npy", rng.normal(size=(6, 600)))
    np.save(poly / "User-1-Night-2.npy", rng.normal(size=(6, 610)))
    (root / "patients.csv").write_text("user_id,night_id,AHI\n1,1,\"17,7\"\n")


class TestIngest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _tiny_tree(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_header_only_census(self):
        header = npy_header(self.root / "polysomnographics" / "User-1-Night-1.npy")
        self.assertEqual(header["shape"], [6, 600])

    def test_build_and_verify_round_trip(self):
        manifest = build_manifest(self.root)
        self.assertEqual(manifest["n_files"], 2)
        self.assertEqual(verify_manifest(self.root, manifest), [])

    def test_header_only_manifest_verifies(self):
        manifest = build_manifest(self.root, hash_files=False)
        self.assertTrue(all(r["sha256"] is None for r in manifest["records"]))
        self.assertEqual(verify_manifest(self.root, manifest), [])

    def test_corrupt_bytes_fail(self):
        manifest = build_manifest(self.root)
        target = self.root / "polysomnographics" / "User-1-Night-1.npy"
        with open(target, "r+b") as fh:
            fh.seek(200)
            fh.write(b"\x00\x01\x02\x03")
        failures = verify_manifest(self.root, manifest)
        self.assertTrue(any("sha256 mismatch" in f for f in failures), failures)

    def test_missing_file_fails(self):
        manifest = build_manifest(self.root)
        (self.root / "polysomnographics" / "User-1-Night-2.npy").unlink()
        failures = verify_manifest(self.root, manifest)
        self.assertTrue(any("missing file" in f for f in failures), failures)

    def test_secret_scan(self):
        self.assertEqual(scan_for_secrets("data-dir=Kaggledata\nout=outputs/m.json"), [])
        self.assertTrue(scan_for_secrets("kaggle_key = abc123"))
        self.assertTrue(scan_for_secrets("password: hunter2"))

    def test_manifest_json_serializable(self):
        json.dumps(build_manifest(self.root))


if __name__ == "__main__":
    unittest.main()
