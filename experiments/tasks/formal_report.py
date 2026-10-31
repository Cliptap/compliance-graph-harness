"""Render the formal T7 analysis as a markdown report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "qa_reports" / "formal" / "analysis.json"
OUT = ROOT / "docs" / "research" / "formal-results.md"


def fmt(value, digits=2):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/formal_report.py")
    parser.add_argument("--analysis", default=str(DEFAULT))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    data = json.loads(Path(args.analysis).read_text(encoding="utf-8"))
    lines = [
        "# Formal T7 results",
        "",
        "Generated from `qa_reports/formal/analysis.json`; the formal run uses 12 tasks × 3 repetitions.",
        "",
    ]
    finished = data.get("finished")
    total = data.get("runs")
    if finished is not None and total is not None and finished < total:
        lines += [
            f"> **PROVISIONAL**: {finished}/{total} runs finished; "
            f"{data.get('invalid', 0)} invalid. Rerun the invalid cells before using these results.",
            "> Invalid runs failed with the Cursor SDK message: "
            "`You're out of usage. Switch to Auto, or ask your admin to increase your limit.`",
            "",
        ]
    lines += [
        "## Arms",
        "",
        "| Arm | n | Invalid | Cycle mean | Cycle median | Hidden pass | Oracle findings | Tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, values in data.get("arms", {}).items():
        lines.append(
            f"| {arm} | {values['n']} | {values.get('invalid', 0)} | {fmt(values['cycle_mean'])}s | "
            f"{fmt(values['cycle_median'])}s | {values['hidden_pass']}/{values['n']} | "
            f"{values['oracle_findings']} | {values['tokens']} |")
    paired = data.get("paired", {})
    lines += [
        "",
        "## Paired comparison (compliance − baseline)",
        "",
        f"- Pairs: {paired.get('n', 0)}",
        f"- Mean difference: {fmt(paired.get('delta_compliance_mean'))}s",
        f"- SD: {fmt(paired.get('delta_compliance_sd'))}s",
        f"- Wilcoxon: {paired.get('wilcoxon', {})}",
        f"- McNemar (hidden pass): {paired.get('mcnemar_hidden', {})}",
        "",
        "## Detector vs oracle",
        "",
        "| Arm | TP | FP | FN | TN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, values in data.get("detector_vs_oracle", {}).items():
        lines.append(
            f"| {arm} | {values['tp']} | {values['fp']} | {values['fn']} | {values['tn']} | "
            f"{fmt(values['precision'])} | {fmt(values['recall'])} |")
    rows = paired.get("rows", [])
    if rows:
        lines += [
            "",
            "## Per-task pairs",
            "",
            "| Rep | Task | Baseline | Harness | Compliance | Δ compliance | Hidden baseline / harness / compliance |",
            "|---:|---|---:|---:|---:|---:|---|",
        ]
        for row in rows:
            lines.append(
                f"| {row['rep']} | {row['task']} | {fmt(row['baseline'])}s | {fmt(row['harness'])}s | "
                f"{fmt(row['compliance'])}s | {fmt(row['delta_compliance'])}s | "
                f"{row['hidden_baseline']} / {row['hidden_harness']} / {row['hidden_compliance']} |")
    lines += [
        "",
        "> Note: the formal run is the only source of the T7 result. The cost pilot in `cost-pilot.md`",
        "> is descriptive and not part of this comparison.",
        "",
    ]
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
