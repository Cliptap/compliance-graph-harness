"""Run all T7 formal repetitions sequentially in the background."""
from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURSOR_ARMS = ["baseline", "harness", "harness_compliance"]
DOSE_ARMS = ["baseline", "rules", "rules_skills", "rules_skills_gate",
             "rules_skills_gate_enforced"]


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/formal_all.py")
    parser.add_argument("--runner", choices=("cursor", "opencode"), default="cursor")
    parser.add_argument("--model", default="")
    parser.add_argument("--reps", default="1,2,3")
    parser.add_argument("--tasks", default="")
    parser.add_argument("--arms", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--seed", type=int, default=20261031,
                        help="seed for the per-repetition arm order")
    args = parser.parse_args()
    model = args.model or ("opencode-go/deepseek-v4.1-flash" if args.runner == "opencode"
                           else "composer-2.5")
    selected = [arm for arm in args.arms.split(",") if arm] or (
        list(DOSE_ARMS) if args.runner == "opencode" else list(CURSOR_ARMS))
    for rep in [int(rep) for rep in args.reps.split(",") if rep]:
        arms = list(selected)
        random.Random(args.seed + rep).shuffle(arms)
        print(f"=== rep {rep} arm order {arms} ===", flush=True)
        for arm in arms:
            print(f"=== rep {rep} arm {arm} ===", flush=True)
            command = [sys.executable, "experiments/tasks/formal_run.py", "--rep", str(rep),
                       "--arm", arm, "--runner", args.runner, "--model", model,
                       "--timeout", str(args.timeout), "--resume"]
            if args.out_dir:
                command += ["--out-dir", args.out_dir]
            if args.tasks:
                command += ["--tasks", args.tasks]
            subprocess.run(command, cwd=ROOT)
    print("=== formal execution finished ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
