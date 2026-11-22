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
CURSOR_ARMS = ["baseline", "harness", "harness_compliance"]
DOSE_ARMS = ["baseline", "rules", "rules_skills", "rules_skills_gate",
             "rules_skills_gate_enforced"]


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/cost_pilot.py")
    parser.add_argument("--tasks", default=",".join(TASKS))
    parser.add_argument("--arms", default="")
    parser.add_argument("--runner", choices=("cursor", "opencode"), default="cursor")
    parser.add_argument("--model", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    tasks = [task for task in args.tasks.split(",") if task]
    if args.arms:
        arms = [arm for arm in args.arms.split(",") if arm]
    else:
        arms = list(DOSE_ARMS if args.runner == "opencode" else CURSOR_ARMS)
    model = args.model or ("opencode-go/deepseek-v4.1-flash" if args.runner == "opencode"
                           else "composer-2.5")
    default_dir = "qa_reports/pilot-opencode" if args.runner == "opencode" else "qa_reports/pilot"
    out_dir = ROOT / (args.out_dir or default_dir)
    if args.out:
        aggregate = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out
    else:
        aggregate = out_dir / "cost_pilot.json"
    rows = []
    for task in tasks:
        for arm in arms:
            out = out_dir / f"cost_{task}_{arm}.json"
            if args.runner == "opencode":
                command = [sys.executable, "experiments/tasks/opencode_run.py", "--task", task,
                           "--arm", arm, "--model", model, "--timeout", str(args.timeout),
                           "--out", str(out)]
            else:
                command = [sys.executable, "experiments/tasks/run_arm.py", "--task", task,
                           "--arm", arm, "--model", model, "--max-rounds", str(args.max_rounds),
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
    aggregate.parent.mkdir(parents=True, exist_ok=True)
    aggregate.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", aggregate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
