import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "experiments" / "tasks"


def _manifest():
    return json.loads((TASKS / "manifest.json").read_text(encoding="utf-8"))


def _rules():
    data = yaml.safe_load((TASKS / "oracle" / "rules.yml").read_text(encoding="utf-8"))
    return {rule["id"] for rule in data["rules"]}


def test_task_pack_has_twelve_complete_tasks():
    tasks = _manifest()["tasks"]
    assert len(tasks) == 12
    ids = [task["id"] for task in tasks]
    assert len(ids) == len(set(ids))
    rules = _rules()
    for task in tasks:
        assert task["prompt"].strip(), task["id"]
        assert task["allowed_paths"], task["id"]
        assert set(task["expected_rules"]) <= rules, task["id"]
        prefix = task["id"].split("-", 1)[0].lower()
        hidden = list((TASKS / "hidden").glob(f"test_{prefix}_*.py"))
        assert len(hidden) == 1, task["id"]


def test_build_creates_an_isolated_workspace(tmp_path):
    dest = tmp_path / "ws"
    result = subprocess.run(
        [sys.executable, "experiments/tasks/build.py", "--task", "T01-payment-method", "--dest", str(dest)],
        cwd=ROOT, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (dest / "TASK.md").read_text(encoding="utf-8").startswith("# T01-payment-method")
    assert not (dest / "hidden").exists()
    assert not (dest / "app" / "static" / "photos").exists()
    assert (dest / ".git").exists()
