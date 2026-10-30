"""Run all T7 formal repetitions sequentially in the background."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARMS = ["baseline", "harness", "harness_compliance"]


def main() -> int:
    for rep in (1, 2, 3):
        for arm in ARMS:
            print(f"=== rep {rep} arm {arm} ===", flush=True)
            subprocess.run(
                [sys.executable, "experiments/tasks/formal_run.py", "--rep", str(rep), "--arm", arm,
                 "--resume"],
                cwd=ROOT,
            )
    print("=== formal run finished ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
