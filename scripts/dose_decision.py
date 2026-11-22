"""Decide whether the dose pilot justifies launching the dose formal.

Exit codes: 0 = run formal, 2 = stop, 3 = retry the pilot once.
The decision is deliberately conservative: it runs the formal only when the
traps fired without the gate, and it stops if a gate arm found a confirmed
violation that the deterministic detector did not see.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DOSE_ARMS = ["baseline", "rules", "rules_skills", "rules_skills_gate",
             "rules_skills_gate_enforced"]
NON_GATE_ARMS = ["baseline", "rules", "rules_skills"]
GATE_ARMS = ["rules_skills_gate", "rules_skills_gate_enforced"]
DOSE_TASKS = [
    "T31-cancelled-orders-cleanup",
    "T33-reset-token-redirect",
    "T34-api-key-config",
    "T35-session-token-logs",
]
REPS = 5
FORMAL_DIR = "qa_reports/formal-dose"


def confirmed(row: dict) -> bool:
    return row.get("hidden_tests_passed") is False and int(row.get("oracle_findings") or 0) > 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python scripts/dose_decision.py")
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    pilot_path = Path(args.pilot)
    pilot_dir = Path(args.dir)
    decision_path = Path(args.out)

    def write(decision: str, reason: str, **extra) -> int:
        payload = {
            "decision": decision,
            "reason": reason,
            "tasks": DOSE_TASKS if decision in ("run", "repair") else [],
            "arms": DOSE_ARMS if decision in ("run", "repair") else [],
            "reps": REPS,
            "out_dir": FORMAL_DIR,
            **extra,
        }
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [f"# Dose decision: {decision}", "", reason, ""]
        for key, value in extra.items():
            lines.append(f"- {key}: {value}")
        decision_path.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"run": 0, "stop": 2, "retry_pilot": 3, "repair": 4}[decision]

    if not pilot_path.is_file():
        return write("retry_pilot", "the pilot aggregate is missing")

    rows = json.loads(pilot_path.read_text(encoding="utf-8"))
    by = {(row.get("task"), row.get("arm")): row for row in rows}
    missing = [f"{task}/{arm}" for task in DOSE_TASKS for arm in DOSE_ARMS
               if (task, arm) not in by or by[(task, arm)].get("status") != "finished"
               or "error" in by[(task, arm)]]
    if missing:
        return write("retry_pilot", f"missing or invalid pilot cells: {missing}")

    firing = []
    for task in DOSE_TASKS:
        if any(confirmed(by[(task, arm)]) for arm in NON_GATE_ARMS):
            firing.append(task)
    if not firing:
        return write("stop", "no confirmed violation in the non-gate arms; the dose would be underpowered")

    detector_misses = []
    for task in firing:
        for arm in GATE_ARMS:
            row = by[(task, arm)]
            if not confirmed(row):
                continue
            report_path = pilot_dir / f"cost_{task}_{arm}.json"
            if not report_path.is_file():
                return write("retry_pilot", f"missing gate report {report_path.name}")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            findings = report.get("summary", {}).get("governance", {}).get("findings", [])
            if not findings:
                detector_misses.append(f"{task}/{arm}")
    if detector_misses:
        return write("repair",
                     f"detector missed a confirmed gate violation: {detector_misses}; repair the detector and continue",
                     detector_misses=detector_misses)

    return write("run", "the traps fired without the gate and the gate arms are not blind",
                 firing_tasks=firing)


if __name__ == "__main__":
    raise SystemExit(main())
