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


CORE_TASKS = {f"T{index:02d}" for index in range(1, 13)}


def test_task_pack_is_complete():
    tasks = _manifest()["tasks"]
    ids = [task["id"] for task in tasks]
    assert len(ids) == len(set(ids))
    assert {task_id.split("-", 1)[0] for task_id in ids} >= CORE_TASKS, "the 12 core tasks must be present"
    rules = _rules()
    for task in tasks:
        assert task["prompt"].strip(), task["id"]
        assert task["allowed_paths"], task["id"]
        assert set(task["expected_rules"]) <= rules, task["id"]
        prefix = task["id"].split("-", 1)[0].lower()
        hidden = list((TASKS / "hidden").glob(f"test_{prefix}_*.py"))
        assert len(hidden) == 1, task["id"]


def test_expected_gap_checks_are_informational():
    for task in _manifest()["tasks"]:
        for check in task.get("evidence", {}).get("checks", []):
            if check.get("expect_pass") is False:
                assert check.get("informational") is True, (task["id"], check)


def test_build_creates_an_isolated_workspace(tmp_path):
    dest = tmp_path / "ws"
    result = subprocess.run(
        [sys.executable, "experiments/tasks/build.py", "--task", "T01-payment-method", "--dest", str(dest)],
        cwd=ROOT, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (dest / "TASK.md").read_text(encoding="utf-8").startswith("# T01-payment-method")
    assert "Definition of done" in (dest / "TASK.md").read_text(encoding="utf-8")
    assert not (dest / "hidden").exists()
    assert not (dest / "app" / "static" / "photos").exists()
    assert (dest / ".git").exists()
