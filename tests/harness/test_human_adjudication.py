"""Two-human adjudication: template and inter-rater agreement."""
from __future__ import annotations

import json

from harness.eval import human_adjudication as human


def _sheet(root):
    sheet = {"cases": [{"id": "a", "control": "v2.x", "path": "p.py", "code": "x"},
                       {"id": "b", "control": "v2.x", "path": "p.py", "code": "y"}]}
    path = root / "sheet.json"
    path.write_text(json.dumps(sheet), encoding="utf-8")
    return path


def _rater(root, name, verdicts):
    path = root / f"{name}.json"
    path.write_text(json.dumps({"rater": name,
                                "verdicts": [{"id": k, "verdict": v} for k, v in verdicts.items()]}),
                    encoding="utf-8")
    return path


def test_template_blanks_every_verdict(tmp_path):
    sheet = _sheet(tmp_path)
    payload = human.build_template(sheet, tmp_path / "a.json", "A")
    assert payload["rater"] == "A"
    assert [row["verdict"] for row in payload["verdicts"]] == ["", ""]
    assert (tmp_path / "a.json").is_file()


def test_identical_raters_agree_perfectly(tmp_path):
    left = _rater(tmp_path, "A", {"a": "violation", "b": "clean"})
    right = _rater(tmp_path, "B", {"a": "violation", "b": "clean"})
    total, agree, kappa = human.inter_rater(left, right)
    assert total == 2
    assert agree == 1.0
    assert kappa == 1.0


def test_disagreement_lowers_kappa(tmp_path):
    left = _rater(tmp_path, "A", {"a": "violation", "b": "clean"})
    right = _rater(tmp_path, "B", {"a": "clean", "b": "violation"})
    total, agree, kappa = human.inter_rater(left, right)
    assert total == 2
    assert agree == 0.0
    assert kappa == -1.0


def test_blank_verdicts_are_ignored(tmp_path):
    left = _rater(tmp_path, "A", {"a": "violation", "b": ""})
    right = _rater(tmp_path, "B", {"a": "violation", "b": "clean"})
    total, agree, kappa = human.inter_rater(left, right)
    assert total == 1
    assert agree == 1.0
