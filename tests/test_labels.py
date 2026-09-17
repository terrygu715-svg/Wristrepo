"""T10 label tests: comma decimals, boundaries, exclusions (S04)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleep_apnea.labels import (  # noqa: E402
    build_label_table,
    class_of,
    load_patients,
    parse_decimal,
    reconcile,
)


class TestParseDecimal(unittest.TestCase):
    def test_comma_decimal(self):
        self.assertAlmostEqual(parse_decimal("17,7"), 17.7)

    def test_dot_decimal(self):
        self.assertAlmostEqual(parse_decimal("56.5"), 56.5)

    def test_blank_is_none(self):
        self.assertIsNone(parse_decimal(""))
        self.assertIsNone(parse_decimal("NA"))

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_decimal("not-a-number")


class TestLabelTable(unittest.TestCase):
    CSV = ROOT / "Kaggledata" / "patients.csv"

    @classmethod
    def setUpClass(cls):
        if not cls.CSV.exists():
            raise unittest.SkipTest("Kaggledata not present")
        cls.rows = load_patients(cls.CSV)
        cls.table = build_label_table(cls.rows)

    def test_comma_row_parsed(self):
        self.assertTrue(any(r["ahi"] == 17.7 for r in self.rows),
                        "comma decimal 17,7 must parse")
        row = next(r for r in self.rows if r["recording_id"] == "KAGGLE_U16_N1")
        self.assertAlmostEqual(row["ahi"], 56.5)

    def test_boundary_inclusivity(self):
        cases = [(4.9, "normal"), (5.0, "mild"), (14.9, "mild"), (15.0, "moderate"),
                 (29.9, "moderate"), (30.0, "severe"), (125.0, "severe")]
        for ahi, expected in cases:
            self.assertEqual(class_of(ahi), expected, ahi)

    def test_comma_boundaries_end_to_end(self):
        rows = [
            {"participant_id": "KAGGLE_UA", "night": "1",
             "recording_id": "KAGGLE_UA_N1", "ahi": parse_decimal("5,0"),
             "class": "mild", "exclusion_reason": None},
            {"participant_id": "KAGGLE_UB", "night": "1",
             "recording_id": "KAGGLE_UB_N1", "ahi": parse_decimal("15,0"),
             "class": "moderate", "exclusion_reason": None},
        ]
        table = build_label_table(rows)
        by_id = {r["recording_id"]: (r["ahi"], r["class"]) for r in table["records"]}
        self.assertEqual(by_id["KAGGLE_UA_N1"], (5.0, "mild"))
        self.assertEqual(by_id["KAGGLE_UB_N1"], (15.0, "moderate"))

    def test_one_night_twenty_labelled(self):
        self.assertEqual(len(self.table["records"]), 20)

    def test_twenty_participants_excluded_with_reasons(self):
        excluded = self.table["excluded_unlabelled"]
        self.assertEqual(len(excluded), 20)
        self.assertTrue(all(e["reason"] for e in excluded))
        self.assertEqual(len(self.table["excluded_source_rows"]), 40)

    def test_sample_ids_reconcile(self):
        self.assertEqual(
            reconcile(["User-16-Night-1", "User-17-Night-1"], self.table), []
        )

    def test_unknown_sample_reported(self):
        self.assertEqual(reconcile(["User-99-Night-9"], self.table), ["User-99-Night-9"])

    def test_duplicate_source_rows_rejected(self):
        row = dict(self.rows[0])
        with self.assertRaises(ValueError):
            build_label_table([row, dict(row)])

    def test_invalid_boundaries_rejected(self):
        with self.assertRaises(ValueError):
            class_of(5.0, (15.0, 5.0, 30.0))

    def test_selected_night_missing_is_not_replaced_by_other_night(self):
        rows = [
            {"participant_id": "KAGGLE_UX", "night": "1",
             "recording_id": "KAGGLE_UX_N1", "ahi": None,
             "class": None, "exclusion_reason": "no AHI"},
            {"participant_id": "KAGGLE_UX", "night": "2",
             "recording_id": "KAGGLE_UX_N2", "ahi": 20.0,
             "class": "moderate", "exclusion_reason": None},
            {"participant_id": "KAGGLE_UY", "night": "1",
             "recording_id": "KAGGLE_UY_N1", "ahi": 10.0,
             "class": "mild", "exclusion_reason": None},
        ]
        table = build_label_table(rows, one_night="1")
        self.assertEqual([row["participant_id"] for row in table["records"]], ["KAGGLE_UY"])
        self.assertEqual(table["excluded_unlabelled"][0]["participant_id"], "KAGGLE_UX")


if __name__ == "__main__":
    unittest.main()
