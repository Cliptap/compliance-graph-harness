import pytest

from harness.eval.flow_bench import log_cases, run

pytestmark = [pytest.mark.harness]


@pytest.fixture(scope="module")
def bench():
    return run()


def _flow_seeded() -> list[str]:
    return sorted(c["id"] for c in log_cases() if "flow" in c.get("tags", []) and c["expected"])


def test_call_level_detects_every_seeded_log_case_without_false_positives(bench):
    s = bench["call_level"]
    assert s["missed"] == []
    assert s["false_positives"] == []
    assert s["precision"] == 1.0 and s["recall"] == 1.0


def test_local_detector_misses_exactly_the_flow_cases(bench):
    s = bench["local"]
    assert sorted(s["missed"]) == _flow_seeded()
    assert s["false_positives"] == []


def test_call_level_raises_recall_over_local_without_losing_precision(bench):
    assert bench["call_level"]["recall"] > bench["local"]["recall"]
    assert bench["call_level"]["precision"] >= bench["local"]["precision"]


def test_lineage_control_flags_every_clean_file_that_logs(bench):
    # File-level lineage links every sensitive model field to every sink of a file that logs.
    s = bench["lineage"]
    clean_with_sink = sorted(c["id"] for c in log_cases() if not c["expected"] and c["id"] != "log-word-in-comment")
    assert s["recall"] == 1.0
    assert sorted(s["false_positives"]) == clean_with_sink
