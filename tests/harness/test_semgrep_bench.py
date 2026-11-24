"""The Semgrep benchmark maps rules to controls and scores a confusion matrix."""
from __future__ import annotations

from harness.eval import semgrep_bench as bench


def _case(case_id: str, control: str, expected: str) -> dict:
    return {"id": case_id, "control": control, "expected": expected, "path": "app/x.py", "code": ""}


def test_the_mapping_covers_the_seven_scored_controls():
    assert set(bench.RULE_TO_CONTROL.values()) == {
        "v2.log_pii",
        "v2.admin_exposure",
        "v2.customer_hard_delete",
        "v2.billing_retention",
        "v2.reset_token",
        "v2.api_key",
        "v2.credential_response",
    }


def test_rule_key_ignores_the_config_prefix():
    assert bench._rule_key("oracle.dumbo.log-sensitive") == "dumbo.log-sensitive"
    assert bench._rule_key("dumbo.log-sensitive") == "dumbo.log-sensitive"
    assert bench._rule_key("dumbo.card-persist") == "dumbo.card-persist"


def test_score_counts_the_four_cells_per_control():
    cases = [
        _case("a", "v2.log_pii", "violation"),   # flagged -> tp
        _case("b", "v2.log_pii", "violation"),   # not flagged -> fn
        _case("c", "v2.log_pii", "clean"),       # flagged -> fp
        _case("d", "v2.log_pii", "clean"),       # not flagged -> tn
    ]
    flagged = {"a": {"v2.log_pii"}, "c": {"v2.log_pii"}}
    result = bench.score(cases, flagged)
    assert result["per_control"]["v2.log_pii"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert result["correct"] == 2
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5


def test_a_finding_for_another_control_does_not_count():
    cases = [_case("a", "v2.log_pii", "violation")]
    result = bench.score(cases, {"a": {"v2.api_key"}})
    assert result["per_control"]["v2.log_pii"] == {"tp": 0, "fp": 0, "fn": 1, "tn": 0}


def test_wilson_interval_brackets_the_point_estimate():
    low, high = bench.wilson(4, 6)
    assert low < 4 / 6 < high
    assert 0.0 <= low <= high <= 1.0


def test_format_table_renders_the_totals_row():
    cases = [_case("a", "v2.log_pii", "violation")]
    table = bench.format_table(bench.score(cases, {"a": {"v2.log_pii"}}))
    assert "| **Total** |" in table
    assert "Aciertos: 1/1" in table
