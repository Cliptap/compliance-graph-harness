"""Evidence checks: an informational gap must never fail a run that closed the gap."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "experiments" / "tasks"
if str(TASKS) not in sys.path:
    sys.path.insert(0, str(TASKS))

from evidence_check import checks_passed  # noqa: E402


def test_informational_check_does_not_gate():
    results = [{"passed": True}, {"passed": False, "informational": True}]
    assert checks_passed(results) is True


def test_informational_check_can_also_match():
    results = [{"passed": True}, {"passed": True, "informational": True}]
    assert checks_passed(results) is True


def test_gating_check_still_fails_the_run():
    assert checks_passed([{"passed": True}, {"passed": False}]) is False
