"""The gate_only arm isolates the analyzer from the harness procedures.

It exists to answer one question: does the compliance tool change the outcome by itself, or does
the value come from the rules and skills around it? The arm must therefore carry the CLI, the pack
and the hook, and nothing else.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parents[2] / "experiments" / "tasks"
if str(TASKS) not in sys.path:
    sys.path.insert(0, str(TASKS))

from opencode_arms import ARMS, prepare_workspace, skill_permissions  # noqa: E402

TASK = {
    "id": "T01-payment-method",
    "title": "Payment method",
    "prompt": "Add a payment method field.",
    "allowed_paths": ["app/", "schema.sql", "tests/"],
}


def test_gate_only_has_the_tool_and_nothing_else(tmp_path):
    workspace = prepare_workspace("gate_only", TASK, tmp_path / "gate_only")
    assert (workspace / "compliance_check.py").is_file()
    assert (workspace / ".harness" / "packs" / "cl-ley-21719.json").is_file()
    assert (workspace / ".git" / "hooks" / "pre-commit").is_file()
    assert not (workspace / ".agents" / "skills").exists()
    instructions = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert "compliance_check.py" in instructions
    assert "Protocolo de ejecución obligatorio" not in instructions


def test_the_full_gate_arm_keeps_the_procedures(tmp_path):
    workspace = prepare_workspace("rules_skills_gate", TASK, tmp_path / "full")
    assert (workspace / "compliance_check.py").is_file()
    assert (workspace / ".agents" / "skills" / "compliance-dev" / "SKILL.md").is_file()
    assert (workspace / ".agents" / "skills" / "05-backend" / "SKILL.md").is_file()
    instructions = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert "Protocolo de ejecución obligatorio" in instructions


def test_baseline_has_no_gate(tmp_path):
    workspace = prepare_workspace("baseline", TASK, tmp_path / "baseline")
    assert not (workspace / "compliance_check.py").exists()
    assert not (workspace / "AGENTS.md").exists()


def test_gate_only_denies_every_skill():
    assert skill_permissions("gate_only") == {"*": "deny"}


@pytest.mark.parametrize("arm", ["baseline", "gate_only", "rules_skills_gate"])
def test_the_three_compared_arms_differ_only_in_the_expected_fields(arm):
    config = ARMS[arm]
    expected = {
        "baseline": (False, False, False),
        "gate_only": (False, False, True),
        "rules_skills_gate": (True, True, True),
    }[arm]
    assert (config.harness_files, config.skills, config.gate) == expected
