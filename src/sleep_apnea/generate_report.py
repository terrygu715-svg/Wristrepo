"""Report generation from fixtures (T35). Stdlib-only, no training.

Pure function of saved inputs: metric summaries, comparison outputs,
cohort counts, and run metadata. Regeneration performs no training and no
test-driven selection. Every report carries an unmistakable SYNTHETIC
banner while inputs are fixtures; the banner text is driven by the
`synthetic` flag so real-data reports cannot inherit it silently.
"""

from __future__ import annotations

import os
from pathlib import Path

REQUIRED_SECTIONS = (
    "Cohort",
    "Metrics",
    "Full vs Reduced comparison",
    "Provenance",
    "Limitations",
)


def _bars(per_class: dict[str, dict]) -> str:
    """Inline SVG bar chart of per-class F1 (no plotting dependency)."""
    rows = []
    for i, (label, scores) in enumerate(sorted(per_class.items())):
        width = max(0.0, min(1.0, scores["f1"])) * 300
        y = i * 24
        rows.append(
            f'<text x="0" y="{y + 15}">{label}</text>'
            f'<rect x="90" y="{y + 2}" width="{width:.1f}" height="16"/>'
            f'<text x="{95 + width:.0f}" y="{y + 15}">{scores["f1"]:.2f}</text>'
        )
    height = len(rows) * 24 + 6
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}">' + "".join(rows) + "</svg>"


def _table(headers: list[str], rows: list[list[object]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return "\n".join([head, rule, body])


def generate(
    metrics: dict,
    comparison: dict,
    cohort: dict,
    run_metadata: dict,
    synthetic: bool = True,
) -> str:
    """Render the Markdown report. Raises on missing required inputs."""
    for name, payload in (("metrics", metrics), ("comparison", comparison),
                          ("cohort", cohort), ("run_metadata", run_metadata)):
        if not isinstance(payload, dict) or not payload:
            raise ValueError(f"report: {name} must be a non-empty object")
    order = metrics["class_order"]
    banner = (
        "> SYNTHETIC REPORT — fixture inputs only, not research results.\n"
        if synthetic else
        "> FINAL REPORT — held-out results. Verify release hash before citing.\n"
    )
    per_class = metrics["per_class"]
    sections = [
        "# Sleep Apnea Full vs Reduced Report",
        banner,
        "## Cohort",
        _table(["Group", "Nights"], [[k, v] for k, v in sorted(cohort.items())]),
        "## Metrics",
        _table(
            ["Class", "Precision", "Recall", "F1", "Support"],
            [[label, f"{per_class[label]['precision']:.3f}",
              f"{per_class[label]['recall']:.3f}", f"{per_class[label]['f1']:.3f}",
              per_class[label]["support"]] for label in order],
        ),
        f"\nAccuracy {metrics['accuracy']:.3f}, macro F1 {metrics['macro_f1']:.3f}, "
        f"weighted F1 {metrics['weighted_f1']:.3f}.",
        _bars(per_class),
        "## Full vs Reduced comparison",
        f"Metric {comparison['metric']}: mean gap {comparison['mean_gap']:+.4f} "
        f"(95% CI {comparison['ci_low_95']:+.4f} … {comparison['ci_high_95']:+.4f}, "
        f"n_bootstrap={comparison['n_bootstrap']}, seed={comparison['seed']}).",
        comparison["conditioning"],
        "## Provenance",
        _table(["Field", "Value"], [[k, run_metadata[k]] for k in sorted(run_metadata)]),
        "## Limitations",
        "- Fixture inputs; absolute performance is meaningless." if synthetic else
        "- Conditioning: gaps condition on fitted models and class composition.",
    ]
    return "\n\n".join(sections) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI: render report.json inputs to Markdown (no training imports)."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate report from saved inputs (T35)")
    parser.add_argument("--inputs", required=True, help="JSON with metrics/comparison/cohort/run_metadata/synthetic")
    parser.add_argument("--out", default="outputs/report.md")
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.inputs).read_text())
    text = generate(payload["metrics"], payload["comparison"], payload["cohort"],
                    payload["run_metadata"], payload.get("synthetic", True))
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in text, f"missing section {section}"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(text)
    os.replace(tmp, out)
    print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
