"""Arm comparison: classification and paired statistics over run reports."""
from __future__ import annotations

import json

from harness.eval import arm_comparison as cmp


def _run(rep: str, task: str, arm: str, hidden: bool, oracle: list[str]) -> dict:
    return {
        "live": {"status": "finished", "cycle_time_s": 100.0,
                 "tokens": {"total_tokens": 1000}, "gate_calls": 2},
        "summary": {"governance": {"policy_violations": 0}},
        "hidden_and_oracle": {"hidden_tests_passed": hidden,
                              "oracle": {"findings": [{"rule": rule} for rule in oracle]}},
        "task": task, "arm": arm,
    }


def _write(root, rep, task, arm, hidden, oracle):
    path = root / f"{rep}_{task}_{arm}.json"
    path.write_text(json.dumps(_run(rep, task, arm, hidden, oracle)), encoding="utf-8")


def test_classification_uses_the_four_cells():
    assert cmp.classify({"hidden_ok": False, "oracle_rules": ["r"]}) == "confirmed_violation"
    assert cmp.classify({"hidden_ok": False, "oracle_rules": []}) == "behavioral_failure"
    assert cmp.classify({"hidden_ok": True, "oracle_rules": ["r"]}) == "latent_risk"
    assert cmp.classify({"hidden_ok": True, "oracle_rules": []}) == "clean"


def test_load_runs_reads_each_report(tmp_path):
    _write(tmp_path, "rep1", "T31", "gate_only", True, [])
    _write(tmp_path, "rep1", "T31", "rules_skills_gate", False, ["r"])
    rows = cmp.load_runs(tmp_path)
    assert len(rows) == 2
    assert {row["arm"] for row in rows} == {"gate_only", "rules_skills_gate"}
    assert rows[0]["tokens"] == 1000


def test_summary_counts_each_class(tmp_path):
    _write(tmp_path, "rep1", "T31", "gate_only", False, ["r"])
    _write(tmp_path, "rep2", "T31", "gate_only", True, [])
    rows = cmp.load_runs(tmp_path)
    summary = cmp.summarize(rows, "gate_only")
    assert summary["runs"] == 2
    assert summary["confirmed"] == 1
    assert summary["clean"] == 1
    assert summary["failed"] == 1


def test_mcnemar_counts_discordant_pairs_only():
    left = [True, True, False, False]
    right = [False, True, False, True]
    left_only, right_only, p = cmp.mcnemar(left, right)
    assert (left_only, right_only) == (1, 1)
    assert p == 1.0


def test_mcnemar_is_significant_with_enough_one_sided_pairs():
    left = [True] * 8 + [False] * 2
    right = [False] * 8 + [False] * 2
    left_only, right_only, p = cmp.mcnemar(left, right)
    assert (left_only, right_only) == (8, 0)
    assert p < 0.01


def test_paired_only_uses_runs_present_in_both_arms(tmp_path):
    _write(tmp_path, "rep1", "T31", "gate_only", True, [])
    _write(tmp_path, "rep1", "T31", "rules_skills_gate", True, [])
    _write(tmp_path, "rep2", "T31", "gate_only", True, [])
    rows = cmp.load_runs(tmp_path)
    result = cmp.paired(rows, "gate_only", "rules_skills_gate")
    assert result["pairs"] == 1
    assert result["left_only_failed"] == 0
