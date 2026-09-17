"""Contract tests for T03 Done criteria (stdlib unittest, CPU-only).

Covers: valid fixtures pass; missing IDs rejected; ambiguous class order
rejected; example config marks unverified fields; source/output dirs distinct.
Prominently synthetic: all IDs use the SYNTH_ prefix, never empirical results.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.contracts import (  # noqa: E402
    validate_class_order,
    validate_comparison,
    validate_config,
    validate_manifest,
    validate_metrics,
    validate_predictions,
    validate_run_metadata,
)

ORDER = ["normal", "mild", "moderate", "severe"]


def load_example(name):
    return json.loads((ROOT / "schemas" / "examples" / name).read_text())


class TestManifestContracts(unittest.TestCase):
    def test_valid_fixture_passes(self):
        validate_manifest(load_example("valid_manifest.json"))

    def test_missing_recording_id_rejected(self):
        with self.assertRaises(ValueError):
            validate_manifest(
                {"records": [{"participant_id": "SYNTH_P001"}]}
            )

    def test_missing_participant_id_rejected(self):
        with self.assertRaises(ValueError):
            validate_manifest(
                {"records": [{"recording_id": "SYNTH_P001_N1"}]}
            )


class TestPredictionContracts(unittest.TestCase):
    def test_valid_fixture_passes(self):
        validate_predictions(load_example("valid_predictions.json"))

    def test_missing_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate_predictions(
                {
                    "class_order": list(ORDER),
                    "rows": [
                        {
                            "participant_id": "SYNTH_P001",
                            "y_true": "normal",
                            "y_pred": "normal",
                        }
                    ],
                }
            )

    def test_missing_class_order_rejected(self):
        with self.assertRaises(ValueError):
            validate_predictions(
                {
                    "rows": [
                        {
                            "participant_id": "SYNTH_P001",
                            "recording_id": "SYNTH_P001_N1",
                            "y_true": "normal",
                            "y_pred": "normal",
                        }
                    ]
                }
            )

    def test_duplicate_class_order_rejected(self):
        with self.assertRaises(ValueError):
            validate_class_order(["normal", "mild", "mild", "severe"])

    def test_wrong_length_class_order_rejected(self):
        with self.assertRaises(ValueError):
            validate_class_order(["normal", "mild", "severe"])

    def test_off_order_label_rejected(self):
        with self.assertRaises(ValueError):
            validate_predictions(
                {
                    "class_order": list(ORDER),
                    "rows": [
                        {
                            "participant_id": "SYNTH_P001",
                            "recording_id": "SYNTH_P001_N1",
                            "y_true": "normal",
                            "y_pred": "critical",
                        }
                    ],
                }
            )


class TestOtherContracts(unittest.TestCase):
    def test_metrics_rejects_bad_matrix(self):
        with self.assertRaises(ValueError):
            validate_metrics(
                {
                    "class_order": list(ORDER),
                    "confusion_matrix": [[1, 0], [0, 1]],
                    "accuracy": 0.5,
                    "macro_f1": 0.5,
                    "weighted_f1": 0.5,
                }
            )

    def test_comparison_requires_2000_bootstraps(self):
        with self.assertRaises(ValueError):
            validate_comparison(
                {
                    "class_order": list(ORDER),
                    "full_run_id": "SYNTH_FULL",
                    "reduced_run_id": "SYNTH_RED",
                    "metric_gaps": {"macro_f1": 0.01},
                    "n_bootstrap": 500,
                }
            )

    def test_run_metadata_rejects_missing_hash(self):
        with self.assertRaises(ValueError):
            validate_run_metadata(
                {
                    "run_id": "SYNTH_R1",
                    "config_hash": "abc",
                    "input_version": "full",
                    "class_order": list(ORDER),
                }
            )

    def test_example_config_marks_unverified_and_splits_dirs(self):
        config = json.loads((ROOT / "configs" / "example_config.json").read_text())
        validate_config(config)
        self.assertTrue(
            any("UNVERIFIED" in str(v) for v in config.values()),
            "example config must mark unverified fields",
        )
        self.assertNotEqual(config["output_dir"], config["source_dir"])
        self.assertNotEqual(config["run_dir"], config["source_dir"])

    def test_source_and_output_dirs_distinct(self):
        for dirname in ("src", "configs", "schemas"):
            self.assertTrue((ROOT / dirname).is_dir(), f"missing source dir {dirname}")
        for dirname in ("outputs", "runs"):
            self.assertTrue((ROOT / dirname).is_dir(), f"missing output dir {dirname}")
        source = {str((ROOT / d).resolve()) for d in ("src", "configs", "schemas")}
        generated = {str((ROOT / d).resolve()) for d in ("outputs", "runs")}
        self.assertTrue(source.isdisjoint(generated))


if __name__ == "__main__":
    unittest.main()
