from pathlib import Path

from harness.eval.context_semantic import TASKS, Task, grep_retriever, run, score, summarize

ROOT = Path(__file__).resolve().parents[2]


def test_every_gold_file_exists_in_the_app():
    for task in TASKS:
        for rel in task.gold:
            assert (ROOT / rel).is_file(), (task.id, rel)


def test_score_reports_recall_precision_and_tokens(tmp_path):
    (tmp_path / "a.py").write_text("x" * 400, encoding="utf-8")
    task = Task("t", "q", ("x",), frozenset({"a.py", "b.py"}))
    row = score(task, {"a.py", "c.py"}, tmp_path)
    assert row["recall"] == 0.5 and row["precision"] == 0.5 and row["approx_tokens_if_read"] == 100


def test_empty_result_has_undefined_precision_not_zero(tmp_path):
    row = score(Task("t", "q", ("x",), frozenset({"a.py"})), set(), tmp_path)
    assert row["precision"] is None and row["recall"] == 0.0
    assert summarize([row])["mean_precision"] is None


def test_unavailable_tool_is_none_not_zero():
    results = run(ROOT, {"missing": None, "grep": lambda t: set()})
    assert results["missing"] is None and summarize(results["missing"]) is None
    assert summarize(results["grep"])["mean_recall"] == 0.0


def test_grep_baseline_uses_task_keywords(tmp_path):
    (tmp_path / "hit.py").write_text("def get_current_user(): pass", encoding="utf-8")
    (tmp_path / "miss.py").write_text("pass", encoding="utf-8")
    got = grep_retriever(tmp_path)(Task("t", "q", ("get_current_user",), frozenset()))
    assert got == {"hit.py"}
