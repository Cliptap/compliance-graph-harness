import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_base_skills_declared_in_vibecoding_json_exist():
    config = json.loads((REPO_ROOT / "vibecoding.json").read_text(encoding="utf-8"))
    skills_dir = REPO_ROOT / config["harness"]["skills_dir"]

    missing = [name for name in config["skills"]["base"]
               if not (skills_dir / name / "SKILL.md").is_file()]

    assert missing == []
