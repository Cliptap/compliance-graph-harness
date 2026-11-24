"""Benchmark a Semgrep ruleset against a sealed corpus.

The point of this tool is not to prove that a pattern engine cannot express these
controls. It measures what a ruleset written against one application's idioms
obtains when it faces code it has never seen, on the same cases and the same
labels the calibrated detector was scored on.

Usage::

    python -m harness.eval.semgrep_bench \
        --corpus harness/eval/blind/cases_blind_round21.json \
        --rules experiments/tasks/oracle/rules.yml \
        --out qa_reports/catalog-corpus/semgrep_round21.json
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

# Rule id suffix -> control it competes for. Rules outside this map are ignored:
# they cover controls the corpus does not score.
RULE_TO_CONTROL = {
    "dumbo.log-sensitive": "v2.log_pii",
    "dumbo.log-request-body": "v2.log_pii",
    "dumbo.admin-raw-row": "v2.admin_exposure",
    "dumbo.unmasked-rut": "v2.admin_exposure",
    "dumbo.unmasked-rut-list": "v2.admin_exposure",
    "dumbo.hard-delete": "v2.customer_hard_delete",
    "dumbo.hard-delete-orders": "v2.billing_retention",
    "dumbo.reset-token-response": "v2.reset_token",
    "dumbo.reset-token-redirect": "v2.reset_token",
    "dumbo.api-key-response": "v2.api_key",
    "dumbo.password-response": "v2.credential_response",
}


def wilson(successes: int, total: int) -> tuple[float, float]:
    """95 % Wilson interval, the same estimator the calibration report uses."""
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    z = 1.959963985
    divisor = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / divisor
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / divisor
    return (max(0.0, centre - half), min(1.0, centre + half))


def _rule_key(check_id: str) -> str:
    """Resolve a Semgrep check id to the rule key, tolerating a config prefix."""
    if check_id in RULE_TO_CONTROL:
        return check_id
    for rule in RULE_TO_CONTROL:
        if check_id.endswith(rule):
            return rule
    return check_id


def run_semgrep(cases: list[dict], rules: Path, workdir: Path) -> dict[str, set[str]]:
    """Write one file per case, run Semgrep, return case id -> controls flagged."""
    for case in cases:
        (workdir / f"{case['id']}.py").write_text(case["code"], encoding="utf-8")
    completed = subprocess.run(
        ["semgrep", "--config", str(rules), "--json", "--metrics=off",
         "--disable-version-check", "--no-git-ignore", "--quiet", str(workdir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"semgrep failed ({completed.returncode}): {completed.stderr[:800]}")
    payload = json.loads(completed.stdout)
    flagged: dict[str, set[str]] = defaultdict(set)
    for result in payload.get("results", []):
        control = RULE_TO_CONTROL.get(_rule_key(result["check_id"]))
        if control is None:
            continue
        flagged[Path(result["path"]).stem].add(control)
    return flagged


def score(cases: list[dict], flagged: dict[str, set[str]]) -> dict:
    per_control: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    for case in cases:
        hit = case["control"] in flagged.get(case["id"], set())
        truth = case["expected"] == "violation"
        cell = per_control[case["control"]]
        if hit and truth:
            cell["tp"] += 1
        elif hit:
            cell["fp"] += 1
        elif truth:
            cell["fn"] += 1
        else:
            cell["tn"] += 1
    totals = {key: sum(cell[key] for cell in per_control.values())
              for key in ("tp", "fp", "fn", "tn")}
    precision = totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else 0.0
    recall = totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else 0.0
    correct = totals["tp"] + totals["tn"]
    return {
        "per_control": {control: dict(cell) for control, cell in sorted(per_control.items())},
        "totals": totals,
        "correct": correct,
        "total": len(cases),
        "precision": precision,
        "precision_ci": wilson(totals["tp"], totals["tp"] + totals["fp"]),
        "recall": recall,
        "recall_ci": wilson(totals["tp"], totals["tp"] + totals["fn"]),
        "accuracy": correct / len(cases) if cases else 0.0,
        "accuracy_ci": wilson(correct, len(cases)),
    }


def format_table(result: dict) -> str:
    lines = ["| Control | TP | FP | FN | TN | Precisión | Exhaustividad |",
             "| - | :-: | :-: | :-: | :-: | - | - |"]
    for control, cell in result["per_control"].items():
        precision = cell["tp"] / (cell["tp"] + cell["fp"]) if cell["tp"] + cell["fp"] else 0.0
        recall = cell["tp"] / (cell["tp"] + cell["fn"]) if cell["tp"] + cell["fn"] else 0.0
        pl, ph = wilson(cell["tp"], cell["tp"] + cell["fp"])
        rl, rh = wilson(cell["tp"], cell["tp"] + cell["fn"])
        lines.append(f"| `{control}` | {cell['tp']} | {cell['fp']} | {cell['fn']} | {cell['tn']} | "
                     f"{precision:.3f} [{pl:.3f}; {ph:.3f}] | {recall:.3f} [{rl:.3f}; {rh:.3f}] |")
    pl, ph = result["precision_ci"]
    rl, rh = result["recall_ci"]
    al, ah = result["accuracy_ci"]
    lines.append(f"| **Total** | **{result['totals']['tp']}** | **{result['totals']['fp']}** | "
                 f"**{result['totals']['fn']}** | **{result['totals']['tn']}** | "
                 f"**{result['precision']:.3f} [{pl:.3f}; {ph:.3f}]** | "
                 f"**{result['recall']:.3f} [{rl:.3f}; {rh:.3f}]** |")
    lines.append("")
    lines.append(f"Aciertos: {result['correct']}/{result['total']} "
                 f"({result['accuracy']:.3f} [{al:.3f}; {ah:.3f}]).")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a Semgrep ruleset on a sealed corpus.")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--out", default=None, help="write the JSON result here")
    args = parser.parse_args(argv)
    cases = json.loads(Path(args.corpus).read_text(encoding="utf-8"))["cases"]
    workdir = Path(tempfile.mkdtemp(prefix="semgrep-bench-"))
    try:
        flagged = run_semgrep(cases, Path(args.rules).resolve(), workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    result = score(cases, flagged)
    result["corpus"] = Path(args.corpus).as_posix()
    result["rules"] = Path(args.rules).as_posix()
    print(format_table(result))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
