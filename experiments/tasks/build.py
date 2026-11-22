"""Create an isolated task workspace from the Dumbo base.

The workspace contains only the application and the task prompt; hidden tests, the Semgrep oracle
and the photo assets stay out. The agent under test never sees the oracle.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments" / "supermercado"
MANIFEST = Path(__file__).with_name("manifest.json")
WORKSPACES = Path(__file__).with_name("workspaces")
IGNORE = shutil.ignore_patterns("data", "__pycache__", ".pytest_cache", "*.pyc", "photos")
GITIGNORE = "__pycache__/\n*.pyc\n.pytest_cache/\n*.db\n"
GITATTRIBUTES = "* text=auto\n"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def task_by_id(manifest: dict, task_id: str) -> dict:
    for task in manifest["tasks"]:
        if task["id"] == task_id:
            return task
    raise SystemExit(f"unknown task {task_id}")


def build(task: dict, dest: Path, git: bool = True) -> Path:
    if dest.exists():
        def _onexc(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        shutil.rmtree(dest, onexc=_onexc)
    shutil.copytree(BASE, dest, ignore=IGNORE)
    (dest / "TASK.md").write_text(
        f"# {task['id']} — {task['title']}\n\n{task['prompt']}\n\n"
        f"## Scope\n\nAllowed paths: {', '.join(task['allowed_paths'])}.\n"
        "Do not modify files outside the allowed paths.\n\n"
        "## Definition of done\n\n"
        "Implement the smallest complete change. Run the relevant hidden behavior locally when "
        "possible, then `python -m pytest tests -q`, then `python compliance_check.py` when the "
        "gate is available. Do not start unrelated refactors.\n",
        encoding="utf-8",
        newline="\n",
    )
    (dest / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (dest / ".gitattributes").write_text(GITATTRIBUTES, encoding="utf-8")
    if git:
        for args in (
            ["init", "-q"],
            ["config", "core.autocrlf", "false"],
            ["add", "-A"],
            ["-c", "user.name=pilot", "-c", "user.email=pilot@local", "commit", "-qm", "baseline"],
        ):
            subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/build.py")
    parser.add_argument("--task", help="task id to build")
    parser.add_argument("--dest", type=Path, help="destination directory")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.list:
        for task in manifest["tasks"]:
            print(f"{task['id']:24} {task['title']}")
        return 0
    selected = manifest["tasks"] if args.all else [task_by_id(manifest, args.task or "")]
    for task in selected:
        dest = args.dest or WORKSPACES / task["id"]
        build(task, dest)
        print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
