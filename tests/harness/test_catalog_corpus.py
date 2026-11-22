import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_heldout_regression_corpus_passes():
    """The held-out round-1 cases are now a regression set; they are no longer a calibration set."""
    result = subprocess.run(
        [sys.executable, "harness/eval/catalog_corpus.py",
         "--corpus", "harness/eval/catalog_corpus_heldout.json",
         "--out", "qa_reports/catalog-corpus/heldout_metrics.json"],
        cwd=ROOT, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    metrics = json.loads(
        (ROOT / "qa_reports" / "catalog-corpus" / "heldout_metrics.json").read_text(encoding="utf-8"))
    assert metrics["passed"] == metrics["cases"]


def test_curated_corpus_passes():
    result = subprocess.run(
        [sys.executable, "harness/eval/catalog_corpus.py"],
        cwd=ROOT, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    metrics = json.loads(
        (ROOT / "qa_reports" / "catalog-corpus" / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["passed"] == metrics["cases"]
    for control, values in metrics["controls"].items():
        assert values["precision"] == 1.0, control
        assert values["recall"] == 1.0, control
        assert values["precision_ci"][0] <= values["precision"] <= values["precision_ci"][1]
        assert values["recall_ci"][0] <= values["recall"] <= values["recall_ci"][1]
