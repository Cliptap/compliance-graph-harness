import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "harness" / "eval" / "label_agreement.py"
_spec = importlib.util.spec_from_file_location("label_agreement", MODULE)
label_agreement = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(label_agreement)


def test_cohen_kappa_perfect_agreement():
    agree, kappa = label_agreement.cohen_kappa(
        [("violation", "violation"), ("clean", "clean")])
    assert agree == 1.0
    assert kappa == 1.0


def test_cohen_kappa_detects_disagreement():
    agree, kappa = label_agreement.cohen_kappa([
        ("violation", "clean"),
        ("clean", "violation"),
        ("violation", "violation"),
        ("clean", "clean"),
    ])
    assert agree == 0.5
    assert kappa == 0.0


def test_stratified_sample_keeps_both_labels():
    cases = [
        {"id": f"{control}-{label}", "control": control, "expected": label}
        for control in ("v2.log_pii", "v2.admin_exposure")
        for label in ("violation", "clean")
    ]
    sample = label_agreement.stratified_sample(cases, 4, seed=1)
    assert len(sample) == 4
    assert {case["expected"] for case in sample} == {"violation", "clean"}
