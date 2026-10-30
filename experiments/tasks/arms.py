"""Workspace preparation for the Dumbo task pack and the three experiment arms."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.eval.pilot_arms import (  # noqa: E402
    COMPLIANCE_GATE_RULE, COMPLIANCE_SKILLS, HARNESS_RULE_HEADER, PACK_REL, PIPELINE_SKILLS,
)

BASE = ROOT / "experiments" / "supermercado"
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.db", ".pytest_cache", "photos")
GITIGNORE = "__pycache__/\n*.pyc\n.pytest_cache/\n*.db\n"
GITATTRIBUTES = "* text=auto\n"


def _copy(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, ignore=COPY_IGNORE)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _remove(path: Path) -> None:
    def _onexc(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    shutil.rmtree(path, onexc=_onexc)


def prepare_workspace(arm: str, task: dict, dest: Path) -> Path:
    if dest.exists():
        _remove(dest)
    dest.mkdir(parents=True)
    _copy(BASE / "app", dest / "app")
    for name in ("schema.sql", "requirements.txt", "README.md", "run_dev.bat", "tests"):
        _copy(BASE / name, dest / name)
    (dest / "TASK.md").write_text(
        f"# {task['id']} — {task['title']}\n\n{task['prompt']}\n\n"
        f"## Scope\n\nAllowed paths: {', '.join(task['allowed_paths'])}.\n"
        "Do not modify files outside the allowed paths.\n",
        encoding="utf-8",
        newline="\n",
    )
    if arm in ("harness", "harness_compliance"):
        rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        (dest / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
        (dest / ".cursor" / "rules" / "vibecoding-harness.mdc").write_text(
            HARNESS_RULE_HEADER + rules, encoding="utf-8")
        for skill in PIPELINE_SKILLS:
            _copy(ROOT / ".agents" / "skills" / skill, dest / ".cursor" / "skills" / skill)
    if arm == "harness_compliance":
        for skill in COMPLIANCE_SKILLS:
            _copy(ROOT / ".agents" / "skills" / skill, dest / ".cursor" / "skills" / skill)
        _copy(ROOT / PACK_REL, dest / PACK_REL)
        (dest / ".cursor" / "rules" / "compliance-gate.mdc").write_text(
            COMPLIANCE_GATE_RULE, encoding="utf-8")
    (dest / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (dest / ".gitattributes").write_text(GITATTRIBUTES, encoding="utf-8")
    for args in (
        ["init", "-q"],
        ["config", "core.autocrlf", "false"],
        ["add", "-A"],
        ["-c", "user.name=pilot", "-c", "user.email=pilot@local", "commit", "-qm", "baseline"],
    ):
        subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)
    return dest
