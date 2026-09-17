"""T26 bundle tests: round-trip, version reject, atomicity (S11)."""

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.artifacts.checkpoints import load_bundle, save_bundle  # noqa: E402

ORDER = ["normal", "mild", "moderate", "severe"]
FEATURES = ["hr_mean", "spo2_dip_rate"]


def _bundle_kwargs(**over):
    kwargs = {
        "run_id": "SYNTH_R1",
        "config_hash": "cfg1",
        "split_hash": "split1",
        "input_version": "full",
        "class_order": list(ORDER),
        "feature_order": list(FEATURES),
        "model_type": "dummy",
        "arrays": {"coef": np.arange(8, dtype=float).reshape(4, 2)},
        "meta": {"seed": 0},
    }
    kwargs.update(over)
    return kwargs


class TestBundles(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_round_trip_bit_exact(self):
        save_bundle(self.root / "b", **_bundle_kwargs())
        loaded = load_bundle(
            self.root / "b", expect_config_hash="cfg1",
            expect_feature_order=FEATURES, expect_class_order=ORDER,
        )
        np.testing.assert_array_equal(
            loaded["arrays"]["coef"], np.arange(8, dtype=float).reshape(4, 2)
        )
        self.assertEqual(loaded["meta"], {"seed": 0})

    def test_wrong_config_rejected(self):
        save_bundle(self.root / "b", **_bundle_kwargs())
        with self.assertRaises(ValueError):
            load_bundle(self.root / "b", expect_config_hash="other")

    def test_wrong_features_rejected(self):
        save_bundle(self.root / "b", **_bundle_kwargs())
        with self.assertRaises(ValueError):
            load_bundle(self.root / "b", expect_feature_order=["hr_mean"])

    def test_schema_bump_rejected(self):
        save_bundle(self.root / "b", **_bundle_kwargs())
        model_path = self.root / "b" / "model.json"
        model = json.loads(model_path.read_text())
        model["schema_version"] = 999
        model_path.write_text(json.dumps(model))
        with self.assertRaises(ValueError):
            load_bundle(self.root / "b")

    def test_overwrite_replaces_bundle(self):
        save_bundle(self.root / "b", **_bundle_kwargs())
        save_bundle(self.root / "b", **_bundle_kwargs(run_id="SYNTH_R2"))
        loaded = load_bundle(self.root / "b")
        self.assertEqual(loaded["run_id"], "SYNTH_R2")

    def test_failed_save_leaves_no_partial_bundle(self):
        kwargs = _bundle_kwargs(meta={"bad": object()})  # not JSON-serializable
        with self.assertRaises(TypeError):
            save_bundle(self.root / "b", **kwargs)
        self.assertFalse((self.root / "b").exists())

    def test_missing_bundle_rejected(self):
        with self.assertRaises(ValueError):
            load_bundle(self.root / "nope")


if __name__ == "__main__":
    unittest.main()
