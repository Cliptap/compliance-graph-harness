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
    models = ", ".join(data.get("models") or []) or "—"
    lines = [
        "# Formal T7 results",
        "",
        f"Generated from `{args.analysis}`.",
        f"Model: `{models}`.",
        "",
    ]
    finished = data.get("finished")
    total = data.get("runs")
    if finished is not None and total is not None and finished < total:
        lines += [
            f"> **PROVISIONAL**: {finished}/{total} runs finished; "
            f"{data.get('invalid', 0)} invalid. Rerun the invalid cells before using these results.",
        ]
        if "composer" in models:
            lines.append("> Invalid runs failed with the Cursor SDK message: "
                         "`You're out of usage. Switch to Auto, or ask your admin to increase your limit.`")
        lines.append("")
    lines += [
        "## Arms",
        "",
        "| Arm | n | Invalid | Cycle mean | Cycle median | Hidden pass | Semgrep findings | Tokens | "
        "Gate rounds | Gate unresolved |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, values in data.get("arms", {}).items():
        lines.append(
            f"| {arm} | {values['n']} | {values.get('invalid', 0)} | {fmt(values['cycle_mean'])}s | "
            f"{fmt(values['cycle_median'])}s | {values['hidden_pass']}/{values['n']} | "
            f"{values['oracle_findings']} | {values['tokens']} | {values.get('gate_rounds', 0)} | "
            f"{values.get('gate_unresolved', 0)} |")

    lines += [
        "",
        "## Outcome classification (hidden test + Semgrep)",
        "",
        "`confirmed_violation` = hidden test failed and Semgrep found a violation; "
        "`behavioral_failure` = hidden test failed without a Semgrep finding (needs adjudication); "
        "`latent_risk` = hidden test passed but Semgrep found something; `clean` = neither.",
        "",
        "| Arm | Confirmed | Behavioral | Latent | Clean |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm, values in data.get("outcomes", {}).items():
        lines.append(
            f"| {arm} | {values.get('confirmed_violation', 0)} | {values.get('behavioral_failure', 0)} | "
            f"{values.get('latent_risk', 0)} | {values.get('clean', 0)} |")
    lines += [
        "",
        "## Behavioral failure split",
        "",
        "| Arm | Task completion | Test artifact | Privacy behavioral |",
        "|---|---:|---:|---:|",
    ]
    for arm, values in data.get("arms", {}).items():
        kinds = values.get("failure_kinds", {})
        lines.append(
            f"| {arm} | {kinds.get('task_completion', 0)} | {kinds.get('test_artifact', 0)} | "
            f"{kinds.get('privacy_behavioral', 0)} |")
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
        f"- McNemar (confirmed violation only): {paired.get('mcnemar_confirmed', {})}",
        f"- McNemar (any failure: confirmed or behavioral): {paired.get('mcnemar_any_failure', {})}",
    ]
    contrasts = data.get("contrasts", {})
    if contrasts:
        lines += [
            "",
            "## Dose contrasts (each arm vs baseline)",
            "",
            "| Arm | n | Δ mean | Δ SD | McNemar confirmed | McNemar any failure |",
            "|---|---:|---:|---:|---|---|",
        ]
        for arm, values in contrasts.items():
            lines.append(
                f"| {arm} | {values.get('n', 0)} | {fmt(values.get('delta_mean'))}s | "
                f"{fmt(values.get('delta_sd'))}s | {values.get('mcnemar_confirmed', {})} | "
                f"{values.get('mcnemar_any_failure', {})} |")
    lines += [
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
            "| Rep | Task | Baseline | Harness | Compliance | Δ compliance | Hidden baseline / harness / compliance | "
            "Outcome baseline / harness / compliance |",
            "|---:|---|---:|---:|---:|---:|---|---|",
        ]
        for row in rows:
            lines.append(
                f"| {row['rep']} | {row['task']} | {fmt(row['baseline'])}s | {fmt(row['harness'])}s | "
                f"{fmt(row['compliance'])}s | {fmt(row['delta_compliance'])}s | "
                f"{row['hidden_baseline']} / {row['hidden_harness']} / {row['hidden_compliance']} | "
                f"{row.get('outcome_baseline')} / {row.get('outcome_harness')} / {row.get('outcome_compliance')} |")
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
