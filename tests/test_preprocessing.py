"""T19 tests: train-only fitting, sentinel, ordering (S07)."""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.preprocessing.fitted import fit  # noqa: E402

FEATURES = ["a", "b"]


def _by_id():
    return {
        "SYNTH_T1": np.array([[1.0, 10.0], [3.0, 30.0]]),
        "SYNTH_T2": np.array([[5.0, 50.0]]),
        "SYNTH_H1": np.array([[1000.0, -1000.0]]),  # held-out sentinel
    }


class TestFitted(unittest.TestCase):
    def test_held_out_sentinel_ignored(self):
        fitted_without = fit(
            {k: v for k, v in _by_id().items() if k != "SYNTH_H1"},
            FEATURES, ["SYNTH_T1", "SYNTH_T2"],
        )
        fitted_with = fit(_by_id(), FEATURES, ["SYNTH_T1", "SYNTH_T2"])
        np.testing.assert_array_equal(fitted_with.means, fitted_without.means)
        np.testing.assert_array_equal(fitted_with.stds, fitted_without.stds)

    def test_nan_imputed_with_training_median(self):
        by_id = {"SYNTH_T1": np.array([[np.nan, 1.0], [3.0, 5.0]])}
        fitted = fit(by_id, FEATURES, ["SYNTH_T1"])
        out = fitted.transform(np.array([[np.nan, 3.0]]), FEATURES)
        # median of col a is 3.0 -> (3-3)/std == 0
        self.assertAlmostEqual(out[0, 0], 0.0)

    def test_standardization_math(self):
        by_id = {"SYNTH_T1": np.array([[0.0, 10.0], [4.0, 30.0]])}
        fitted = fit(by_id, FEATURES, ["SYNTH_T1"])
        # col a: mean 2, std 2; col b: mean 20, std 10
        np.testing.assert_allclose(fitted.means, [2.0, 20.0])
        np.testing.assert_allclose(fitted.stds, [2.0, 10.0])
        out = fitted.transform(np.array([[4.0, 30.0]]), FEATURES)
        np.testing.assert_allclose(out, [[1.0, 1.0]])

    def test_feature_order_mismatch_rejected(self):
        fitted = fit(_by_id(), FEATURES, ["SYNTH_T1"])
        with self.assertRaises(ValueError):
            fitted.transform(np.ones((1, 2)), ["b", "a"])

    def test_unknown_train_id_raises(self):
        with self.assertRaises(KeyError):
            fit(_by_id(), FEATURES, ["SYNTH_NOPE"])

    def test_zero_variance_noop(self):
        by_id = {"SYNTH_T1": np.array([[2.0, 1.0], [2.0, 3.0]])}
        fitted = fit(by_id, FEATURES, ["SYNTH_T1"])
        out = fitted.transform(np.array([[2.0, 2.0]]), FEATURES)
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertAlmostEqual(out[0, 0], 0.0)


if __name__ == "__main__":
    unittest.main()
