"""Run the T7 cost pilot for the Dumbo task pack and aggregate the per-run reports."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ["T01-payment-method", "T03-order-tracking", "T04-newsletter",
         "T05-account-delete", "T07-profile-edit"]
ARMS = ["baseline", "harness", "harness_compliance"]


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/cost_pilot.py")
    parser.add_argument("--tasks", default=",".join(TASKS))
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--model", default="composer-2.5")
    parser.add_argument("--out", default="qa_reports/pilot/cost_pilot.json")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    tasks = [task for task in args.tasks.split(",") if task]
    arms = [arm for arm in args.arms.split(",") if arm]
    rows = []
    for task in tasks:
        for arm in arms:
            out = ROOT / "qa_reports" / "pilot" / f"cost_{task}_{arm}.json"
            command = [sys.executable, "experiments/tasks/run_arm.py", "--task", task, "--arm", arm,
                       "--model", args.model, "--max-rounds", str(args.max_rounds),
                       "--timeout", str(args.timeout), "--out", str(out)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if not out.is_file():
                rows.append({"task": task, "arm": arm, "error": (result.stdout + result.stderr)[-2000:]})
                print(f"{task:22} {arm:20} ERROR", flush=True)
                continue
            report = json.loads(out.read_text(encoding="utf-8"))
            live = report.get("live", {})
            summary = report.get("summary", {})
            hidden = report.get("hidden_and_oracle", {})
            findings = (hidden.get("oracle") or {}).get("findings", [])
            rows.append({
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
            })
            print(f"{task:22} {arm:20} status={live.get('status')} time={live.get('cycle_time_s')} "
                  f"hidden={hidden.get('hidden_tests_passed')} oracle={len(findings)}", flush=True)
    aggregate = ROOT / args.out
    aggregate.parent.mkdir(parents=True, exist_ok=True)
    aggregate.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", aggregate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
