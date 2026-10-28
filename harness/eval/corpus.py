"""Labelled corpus: precision/recall of privacy and domain detectors (kind: seeded, seeded-hard, clean).

Violations (`VIOLATION`) are scored with `expected`. WARNING-only detectors (`potential_risk`) are
scored with `expected_warnings` and `warning_clean`; a case participates in a policy's warning score
only when it names that policy, so a clean case for one dimension is not a false positive for
another.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.harness.contracts import TaskSpec
from src.harness.policy_engine import PolicyEngine

CASES = Path(__file__).with_name("corpus") / "cases.json"
TARGETS = (
    "privacy.cwe_532",
    "privacy.api_exposure",
    "privacy.payment_data_storage",
    "domain.prohibited_deletion",
    "privacy.consent_transparency",
    "privacy.minors_and_sensitive",
)
WARNING_TARGETS = (
    "privacy.rights_reachability",
    "privacy.consent_transparency",
    "privacy.minors_and_sensitive",
    "privacy.retention_minimization",
    "privacy.third_party_transfers",
)
SPEC = TaskSpec(task_id="corpus", goal="corpus", allowed_paths=["*"], forbidden_paths=[])


def load_cases(path: Path = CASES) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _findings(case: dict):
    return PolicyEngine().evaluate_changes(SPEC, {case["path"]: case["code"]})


def detect(case: dict) -> set[str]:
    return {f.policy_id for f in _findings(case) if f.status == "VIOLATION" and f.policy_id in TARGETS}


def detect_warnings(case: dict) -> set[str]:
    return {f.policy_id for f in _findings(case) if f.status == "WARNING" and f.policy_id in WARNING_TARGETS}


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


def score_warnings(cases: list[dict]) -> dict[str, dict]:
    """WARNING precision/recall over the cases that name the policy (targeted, not pooled)."""
    stats = {p: {"tp": 0, "fp": 0, "fn": 0} for p in WARNING_TARGETS}
    for case in cases:
        expected = set(case.get("expected_warnings", []))
        clean = set(case.get("warning_clean", []))
        got = detect_warnings(case)
        for p in expected | clean:
            if p not in stats:
                continue
            if p in expected and p in got:
                stats[p]["tp"] += 1
            elif p in expected:
                stats[p]["fn"] += 1
            elif p in clean and p in got:
                stats[p]["fp"] += 1
    for s in stats.values():
        s["precision"] = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else None
        s["recall"] = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else None
    return stats


if __name__ == "__main__":
    for label, kinds in (("all", None), ("easy (seeded+clean)", ("seeded", "clean"))):
        print(label)
        for p, s in score(load_cases(), kinds).items():
            print(f"  {p}: {s}")
    print("warnings (targeted cases)")
    for p, s in score_warnings(load_cases()).items():
        print(f"  {p}: {s}")
