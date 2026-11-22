"""Run one task in one arm with the Cursor SDK and evaluate it with the independent oracle."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for path in (str(ROOT), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from arms import prepare_workspace  # noqa: E402
from evaluate import evaluate, load_manifest, task_by_id  # noqa: E402
from harness.eval.cursor_runner import (  # noqa: E402
    LiveSettings, RunPlan, load_api_key, run_live, summarize_run,
)
from harness.eval.pilot_arms import ARMS  # noqa: E402


def scope_for(task: dict) -> dict:
    return {
        "task_id": task["id"],
        "goal": task["prompt"],
        "allowed_paths": task["allowed_paths"],
        "forbidden_paths": ["oracle/", "hidden/", ".harness/"],
        "relevant_paths": ["app/main.py", "schema.sql", "app/templates/", "app/db.py"],
        "test_targets": ["tests/"],
    }


async def run(args) -> dict:
    task = task_by_id(load_manifest(), args.task)
    workspace = Path(args.workspace_root) / f"{args.task}-{args.arm}"
    prepare_workspace(args.arm, task, workspace)
    plan = RunPlan(ARMS[args.arm], workspace, (workspace / "TASK.md").read_text(encoding="utf-8"),
                   scope_for(task))
    if args.dry_run:
        return {"task": task["id"], "arm": args.arm, "workspace": str(workspace), "dry_run": True,
                "scope": plan.scope}
    api_key = load_api_key(ROOT / ".env")
    if not api_key:
        raise SystemExit("CURSOR_API_KEY is not set")
    settings = LiveSettings(model=args.model, api_key=api_key, max_rounds=args.max_rounds,
                            timeout_s=args.timeout)
    live = await run_live(plan, settings)
    report = {"task": task["id"], "arm": args.arm, "workspace": str(workspace),
              "model": args.model, "live": {k: v for k, v in live.items() if k != "messages"},
              "hidden_and_oracle": evaluate(workspace, task)}
    if live.get("rounds"):
        report["summary"] = summarize_run(plan, live)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/run_arm.py")
    parser.add_argument("--task", required=True)
    parser.add_argument("--arm", choices=sorted(ARMS), required=True)
    parser.add_argument("--workspace-root", default=str(ROOT / "experiments" / "tasks" / "workspaces"))
    parser.add_argument("--model", default="composer-2.5")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--out", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.out:
        args.out = f"qa_reports/pilot/dumbo_{args.task}_{args.arm}.json"
    report = asyncio.run(run(args))
    print(json.dumps({k: report[k] for k in report if k not in ("live", "summary")}, ensure_ascii=False,
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
