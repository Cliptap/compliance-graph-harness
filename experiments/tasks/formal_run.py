"""Formal T7 run: one repetition of all task instances for one arm."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = [
    "T01-payment-method", "T02-csv-export", "T03-order-tracking", "T04-newsletter",
    "T05-account-delete", "T06-points-redeem", "T07-profile-edit", "T08-birthday",
    "T09-geolocation", "T10-analytics", "T11-password-reset", "T12-admin-customers",
]
ARMS = ["baseline", "harness", "harness_compliance"]


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def row(report: dict, task: str, arm: str) -> dict:
    live = report.get("live", {})
    summary = report.get("summary", {})
    hidden = report.get("hidden_and_oracle", {})
    findings = (hidden.get("oracle") or {}).get("findings", [])
    return {
        "task": task,
        "arm": arm,
        "status": live.get("status"),
        "cycle_time_s": live.get("cycle_time_s"),
        "tokens": (summary.get("efficiency") or {}).get("tokens"),
        "rounds": (summary.get("efficiency") or {}).get("rounds"),
        "hidden_tests_passed": hidden.get("hidden_tests_passed"),
        "oracle_findings": len(findings),
        "oracle_rules": sorted({finding["rule"] for finding in findings}),
        "tests": (summary.get("quality") or {}).get("tests"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/formal_run.py")
    parser.add_argument("--rep", type=int, required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--tasks", default=",".join(TASKS))
    parser.add_argument("--model", default="composer-2.5")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    tasks = [task for task in args.tasks.split(",") if task]
    out_dir = ROOT / "qa_reports" / "formal"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for task in tasks:
        out = out_dir / f"rep{args.rep}_{task}_{args.arm}.json"
        report = load(out) if args.resume else None
        if report is None:
            command = [sys.executable, "experiments/tasks/run_arm.py", "--task", task,
                       "--arm", args.arm, "--model", args.model,
                       "--max-rounds", str(args.max_rounds), "--timeout", str(args.timeout),
                       "--out", str(out)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            report = load(out)
            if report is None:
                rows.append({"task": task, "arm": args.arm, "error": (result.stdout + result.stderr)[-2000:]})
                print(f"{task:22} ERROR", flush=True)
                continue
        row_data = row(report, task, args.arm)
        rows.append(row_data)
        print(f"{task:22} {args.arm:20} status={row_data['status']} time={row_data['cycle_time_s']} "
              f"hidden={row_data['hidden_tests_passed']} oracle={row_data['oracle_findings']}", flush=True)
    aggregate = out_dir / f"aggregate_rep{args.rep}_{args.arm}.json"
    aggregate.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", aggregate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
