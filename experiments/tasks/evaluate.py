"""Evaluate a task workspace with the hidden tests and the independent Semgrep oracle.

Neither the hidden tests nor the Semgrep rules are imported by the target; the oracle starts from
outside the harness, as the preregistration requires.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
HIDDEN = HERE / "hidden"
RULES = HERE / "oracle" / "rules.yml"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def task_by_id(manifest: dict, task_id: str) -> dict:
    for task in manifest["tasks"]:
        if task["id"] == task_id:
            return task
    raise SystemExit(f"unknown task {task_id}")


def _prefix(task: dict) -> str:
    return task["id"].split("-", 1)[0].lower()


def run_hidden(workspace: Path, task: dict) -> tuple[bool, str]:
    tests = sorted(HIDDEN.glob(f"test_{_prefix(task)}_*.py"))
    if len(tests) != 1:
        return False, f"expected one hidden test for {task['id']}, found {len(tests)}"
    target = workspace / "hidden"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    shutil.copy2(HIDDEN / "conftest.py", target / "conftest.py")
    shutil.copy2(tests[0], target / tests[0].name)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", f"hidden/{tests[0].name}", "-q", "-p", "no:cacheprovider"],
            cwd=workspace, capture_output=True, text=True, timeout=180,
        )
        return result.returncode == 0, (result.stdout + result.stderr)[-4000:]
    finally:
        shutil.rmtree(target, ignore_errors=True)


def run_semgrep(workspace: Path) -> dict:
    result = subprocess.run(
        ["semgrep", "--config", str(RULES), "--json", "--quiet", str(workspace)],
        capture_output=True, text=True, timeout=300,
    )
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {"error": (result.stdout + result.stderr)[-2000:], "findings": []}
    findings = []
    for item in data.get("results", []):
        path = Path(item.get("path", ""))
        try:
            relative = path.resolve().relative_to(workspace.resolve()).as_posix()
        except ValueError:
            relative = path.as_posix()
        if not (relative.startswith("app/") or relative == "schema.sql"):
            continue
        findings.append({
            "rule": item.get("check_id"),
            "path": relative,
            "line": (item.get("start") or {}).get("line"),
            "message": ((item.get("extra") or {}).get("message") or "").strip(),
        })
    return {"error": None if result.returncode in (0, 1) else (result.stderr or "")[-2000:],
            "findings": findings}


def evaluate(workspace: Path, task: dict) -> dict:
    passed, output = run_hidden(workspace, task)
    oracle = run_semgrep(workspace)
    return {
        "task": task["id"],
        "hidden_tests_passed": passed,
        "hidden_output": output,
        "oracle": oracle,
        "expected_rules": task.get("expected_rules", []),
        "expected_control": task.get("expected_control"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/evaluate.py")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    task = task_by_id(load_manifest(), args.task)
    report = evaluate(args.workspace, task)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{task['id']}: hidden_tests_passed={report['hidden_tests_passed']}")
        for finding in report["oracle"]["findings"]:
            print(f"  {finding['rule']} {finding['path']}:{finding['line']}")
        if report["oracle"].get("error"):
            print("  semgrep error:", report["oracle"]["error"][:200])
    return 0 if report["hidden_tests_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
