"""Labelled corpus: precision/recall of privacy and domain detectors (kind: seeded, seeded-hard, clean)."""
from __future__ import annotations

import json
from pathlib import Path

from src.harness.contracts import TaskSpec
from src.harness.policy_engine import PolicyEngine

CASES = Path(__file__).with_name("corpus") / "cases.json"
TARGETS = ("privacy.cwe_532", "privacy.api_exposure", "domain.prohibited_deletion")
SPEC = TaskSpec(task_id="corpus", goal="corpus", allowed_paths=["*"], forbidden_paths=[])


def load_cases(path: Path = CASES) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def detect(case: dict) -> set[str]:
    found = PolicyEngine().evaluate_changes(SPEC, {case["path"]: case["code"]})
    return {f.policy_id for f in found if f.status == "VIOLATION" and f.policy_id in TARGETS}


def score(cases: list[dict], kinds: tuple[str, ...] | None = None) -> dict[str, dict]:
    """Per-policy tp/fp/fn with precision and recall (None when undefined, never 0)."""
    stats = {p: {"tp": 0, "fp": 0, "fn": 0} for p in TARGETS}
    for case in cases:
        if kinds and case["kind"] not in kinds:
            continue
        expected, got = set(case["expected"]), detect(case)
        for p in TARGETS:
            if p in got and p in expected:
                stats[p]["tp"] += 1
            elif p in got:
                stats[p]["fp"] += 1
            elif p in expected:
                stats[p]["fn"] += 1
    for s in stats.values():
        s["precision"] = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else None
        s["recall"] = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else None
    return stats


if __name__ == "__main__":
    for label, kinds in (("all", None), ("easy (seeded+clean)", ("seeded", "clean"))):
        print(label)
        for p, s in score(load_cases(), kinds).items():
            print(f"  {p}: {s}")
