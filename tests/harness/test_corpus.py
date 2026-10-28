from harness.eval.corpus import detect, load_cases, score


def test_no_false_positives_on_clean_controls():
    for case in load_cases():
        if case["kind"] == "clean":
            assert detect(case) == set(), case["id"]


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
