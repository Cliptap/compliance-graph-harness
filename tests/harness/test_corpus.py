from harness.eval.corpus import (
    WARNING_TARGETS,
    detect,
    detect_warnings,
    load_cases,
    score,
    score_warnings,
)


def test_no_false_positives_on_clean_controls():
    for case in load_cases():
        if case["kind"] == "clean":
            assert detect(case) == set(), case["id"]


def test_warning_only_detectors_are_measured():
    stats = score_warnings(load_cases())
    for policy in WARNING_TARGETS:
        assert stats[policy]["precision"] == 1.0, policy
        assert stats[policy]["recall"] == 1.0, policy


def test_every_warning_detector_has_a_seeded_and_a_clean_case():
    cases = load_cases()
    for policy in WARNING_TARGETS:
        assert any(policy in c.get("expected_warnings", []) for c in cases), policy
        assert any(policy in c.get("warning_clean", []) for c in cases), policy


def test_warning_clean_cases_do_not_warn_for_the_named_policy():
    for case in load_cases():
        got = detect_warnings(case)
        for policy in case.get("warning_clean", []):
            assert policy not in got, (case["id"], policy)


def test_all_easy_seeded_defects_are_detected():
    for case in load_cases():
        if case["kind"] == "seeded":
            assert detect(case) == set(case["expected"]), case["id"]


def test_hard_cases_are_documented_known_misses():
    # Recall limits are published, not hidden: update this list when a detector improves.
    missed = sorted(c["id"] for c in load_cases() if c["kind"] == "seeded-hard" and not detect(c))
    assert missed == ["api-imported-model-password", "api-model-dump-all", "del-raw-sql", "pay-json-blob"]


def test_score_reports_precision_and_recall_per_policy():
    stats = score(load_cases())
    assert stats["privacy.cwe_532"]["precision"] == 1.0
    assert 0 < stats["domain.prohibited_deletion"]["recall"] < 1
