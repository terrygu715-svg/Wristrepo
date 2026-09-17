"""T24/T25 tests: score correctness + comparison validity (S09/S10)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.evaluation.compare import compare  # noqa: E402
from sleep_apnea.evaluation.metrics import summarize  # noqa: E402

ORDER = ["normal", "mild", "moderate", "severe"]


def _preds(pairs, order=ORDER):
    return {
        "class_order": list(order),
        "rows": [
            {
                "participant_id": f"SYNTH_P{i // 2 + 1:03d}",
                "recording_id": f"SYNTH_P{i // 2 + 1:03d}_N{(i % 2) + 1}",
                "y_true": true,
                "y_pred": pred,
            }
            for i, (true, pred) in enumerate(pairs)
        ],
    }


EIGHT_PERFECT = _preds(
    [("normal", "normal"), ("normal", "normal"), ("mild", "mild"),
     ("mild", "mild"), ("moderate", "moderate"), ("moderate", "moderate"),
     ("severe", "severe"), ("severe", "severe")]
)


class TestMetrics(unittest.TestCase):
    def test_perfect_scores(self):
        summary = summarize(EIGHT_PERFECT)
        self.assertEqual(summary["accuracy"], 1.0)
        self.assertEqual(summary["macro_f1"], 1.0)
        self.assertEqual(summary["weighted_f1"], 1.0)
        self.assertEqual(sum(sum(r) for r in summary["confusion_matrix"]), 8)

    def test_all_wrong_zero_f1(self):
        preds = _preds([(t, "severe" if t != "severe" else "normal")
                        for t, _ in [(r, None) for r in ORDER for _ in (0, 1)]])
        summary = summarize(preds)
        self.assertEqual(summary["accuracy"], 0.0)
        self.assertEqual(summary["macro_f1"], 0.0)

    def test_known_matrix_matches_hand_computation(self):
        # 4 rows: 2 true normal (1 right, 1 called mild), 2 true mild (both right).
        preds = {
            "class_order": list(ORDER),
            "rows": [
                {"participant_id": "SYNTH_P001", "recording_id": "SYNTH_P001_N1",
                 "y_true": "normal", "y_pred": "normal"},
                {"participant_id": "SYNTH_P001", "recording_id": "SYNTH_P001_N2",
                 "y_true": "normal", "y_pred": "mild"},
                {"participant_id": "SYNTH_P002", "recording_id": "SYNTH_P002_N1",
                 "y_true": "mild", "y_pred": "mild"},
                {"participant_id": "SYNTH_P002", "recording_id": "SYNTH_P002_N2",
                 "y_true": "mild", "y_pred": "mild"},
            ],
        }
        summary = summarize(preds)
        self.assertEqual(summary["accuracy"], 0.75)
        # normal: P=1/1, R=1/2 -> F1=2/3; mild: P=2/3, R=1 -> F1=0.8
        self.assertAlmostEqual(summary["per_class"]["normal"]["f1"], 2 / 3)
        self.assertAlmostEqual(summary["per_class"]["mild"]["f1"], 0.8)
        # moderate/severe have no support -> explicit 0.0 policy
        self.assertEqual(summary["per_class"]["severe"]["f1"], 0.0)
        # weighted F1 = (2*(2/3) + 2*0.8) / 4
        self.assertAlmostEqual(summary["weighted_f1"], (4 / 3 + 1.6) / 4)
        self.assertAlmostEqual(
            summary["macro_precision"], (1.0 + 2 / 3 + 0.0 + 0.0) / 4
        )

    def test_duplicate_ids_rejected(self):
        preds = _preds([("normal", "normal")] * 2)
        preds["rows"][1]["recording_id"] = preds["rows"][0]["recording_id"]
        with self.assertRaises(ValueError):
            summarize(preds)


class TestCompare(unittest.TestCase):
    STRATA = {f"SYNTH_P{i:03d}": ORDER[(i - 1) % 4] for i in (1, 2, 3, 4)}

    def test_identical_predictions_zero_gap(self):
        out = compare(EIGHT_PERFECT, EIGHT_PERFECT, self.STRATA, "FULL", "RED")
        self.assertEqual(out["mean_gap"], 0.0)
        self.assertEqual(out["ci_low_95"], 0.0)
        self.assertEqual(out["ci_high_95"], 0.0)
        self.assertEqual(out["n_bootstrap"], 2000)

    def test_row_reorder_harmless(self):
        reordered = dict(EIGHT_PERFECT, rows=list(reversed(EIGHT_PERFECT["rows"])))
        out = compare(EIGHT_PERFECT, reordered, self.STRATA, "FULL", "RED")
        self.assertEqual(out["mean_gap"], 0.0)

    def test_unmatched_ids_fail(self):
        reduced = dict(EIGHT_PERFECT, rows=EIGHT_PERFECT["rows"][:-1])
        with self.assertRaises(ValueError):
            compare(EIGHT_PERFECT, reduced, self.STRATA, "FULL", "RED")

    def test_degraded_reduced_gives_positive_gap(self):
        degraded = dict(EIGHT_PERFECT, rows=[
            dict(r, y_pred="normal") for r in EIGHT_PERFECT["rows"]
        ])
        out = compare(EIGHT_PERFECT, degraded, self.STRATA, "FULL", "RED")
        self.assertGreater(out["mean_gap"], 0.0)
        self.assertLessEqual(out["ci_low_95"], out["mean_gap"])
        self.assertLessEqual(out["mean_gap"], out["ci_high_95"])
        self.assertIn("condition", out["conditioning"])

    def test_bootstrap_count_enforced(self):
        with self.assertRaises(ValueError):
            compare(EIGHT_PERFECT, EIGHT_PERFECT, self.STRATA, "FULL", "RED",
                    n_bootstrap=500)

    def test_missing_stratum_fails(self):
        with self.assertRaises(ValueError):
            compare(EIGHT_PERFECT, EIGHT_PERFECT, {}, "FULL", "RED")

    def test_participant_mismatch_fails(self):
        reduced = dict(EIGHT_PERFECT, rows=[dict(row) for row in EIGHT_PERFECT["rows"]])
        reduced["rows"][0]["participant_id"] = "SYNTH_OTHER"
        strata = dict(self.STRATA)
        strata["SYNTH_OTHER"] = "normal"
        with self.assertRaises(ValueError):
            compare(EIGHT_PERFECT, reduced, strata, "FULL", "RED")

    def test_true_label_mismatch_fails(self):
        reduced = dict(EIGHT_PERFECT, rows=[dict(row) for row in EIGHT_PERFECT["rows"]])
        reduced["rows"][0]["y_true"] = "severe"
        with self.assertRaises(ValueError):
            compare(EIGHT_PERFECT, reduced, self.STRATA, "FULL", "RED")

    def test_extra_stratum_participant_fails(self):
        strata = dict(self.STRATA, SYNTH_EXTRA="normal")
        with self.assertRaises(ValueError):
            compare(EIGHT_PERFECT, EIGHT_PERFECT, strata, "FULL", "RED")


if __name__ == "__main__":
    unittest.main()
