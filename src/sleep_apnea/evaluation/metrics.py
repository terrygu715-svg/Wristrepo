"""Metric and prediction validation (T24). Stdlib-only.

Computes accuracy, macro/weighted F1, macro precision/recall, per-class
scores, and the confusion matrix (rows = true, cols = predicted, in
class_order) from saved prediction dicts. Validates structure with the T03
contract validators first, so malformed inputs fail before scoring.

Undefined-score policy (explicit per T24 Done): precision/recall/F1 with a
zero denominator are 0.0.
"""

from __future__ import annotations

from sleep_apnea.contracts import validate_class_order, validate_predictions


def confusion_matrix(predictions: dict) -> list[list[int]]:
    """4x4 confusion matrix as nested lists in class_order."""
    validate_predictions(predictions)
    order = predictions["class_order"]
    index = {label: i for i, label in enumerate(order)}
    matrix = [[0] * len(order) for _ in order]
    for row in predictions["rows"]:
        matrix[index[row["y_true"]]][index[row["y_pred"]]] += 1
    return matrix


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def summarize(predictions: dict) -> dict:
    """Full metric summary incl. per-class scores and both matrix layouts."""
    validate_predictions(predictions)
    order = predictions["class_order"]
    matrix = confusion_matrix(predictions)
    n_classes = len(order)
    total = sum(sum(row) for row in matrix)
    per_class = {}
    for i, label in enumerate(order):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(n_classes)) - tp
        fn = sum(matrix[i]) - tp
        precision, recall, f1 = _prf(tp, fp, fn)
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(matrix[i]),
        }
    accuracy = sum(matrix[i][i] for i in range(n_classes)) / total if total else 0.0
    macro = {
        key: sum(per_class[label][key] for label in order) / n_classes
        for key in ("precision", "recall", "f1")
    }
    weighted_f1 = (
        sum(per_class[label]["f1"] * per_class[label]["support"] for label in order)
        / total
        if total
        else 0.0
    )
    return {
        "class_order": list(order),
        "confusion_matrix": matrix,
        "confusion_matrix_transposed": [list(col) for col in zip(*matrix)],
        "accuracy": accuracy,
        "macro_precision": macro["precision"],
        "macro_recall": macro["recall"],
        "macro_f1": macro["f1"],
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "n": total,
    }
