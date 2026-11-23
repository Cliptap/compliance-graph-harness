"""Validate and seal a blind held-out corpus before the one-shot run.

The validator checks structure, Python syntax, per-control coverage and label balance, and refuses
codes that already appear in the curated or held-out round-1 corpora. The seal is the SHA-256 of
the file; the runner must not edit a sealed file after the first run.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLIND_DIR = Path(__file__).resolve().parent
CONTROLS = {
    "v2.log_pii",
    "v2.admin_exposure",
    "v2.credential_response",
    "v2.customer_hard_delete",
    "v2.billing_retention",
    "v2.reset_token",
    "v2.api_key",
}
MIN_CASES_PER_CONTROL = 5
MIN_PER_LABEL = 2
KNOWN_CORPORA = [
    ROOT / "harness" / "eval" / "catalog_corpus.json",
    ROOT / "harness" / "eval" / "catalog_corpus_heldout.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round1.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round2.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round3.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round4.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round5.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round6.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round7.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round8.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round9.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round10.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round11.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round12.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round13.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round14.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round15.json",
    ROOT / "harness" / "eval" / "blind" / "cases_blind_round16.json",
]


def _canonical(code: str) -> str:
    return ast.unparse(ast.parse(code))


def _code_hashes(paths: list[Path]) -> set[str]:
    hashes: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("cases", []):
            try:
                hashes.add(hashlib.sha256(_canonical(case["code"]).encode()).hexdigest())
            except (SyntaxError, KeyError):
                continue
    return hashes


def validate(corpus: Path) -> list[str]:
    errors: list[str] = []
    if not corpus.is_file():
        return [f"corpus not found: {corpus}"]
    try:
        data = json.loads(corpus.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty list"]

    known = _code_hashes(KNOWN_CORPORA)
    seen_ids: set[str] = set()
    seen_codes: set[str] = set()
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"violation": 0, "clean": 0})

    for index, case in enumerate(cases):
        prefix = f"case[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix}: not an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{prefix}: missing id")
        elif case_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {case_id}")
        else:
            seen_ids.add(case_id)
        control = case.get("control")
        if control not in CONTROLS:
            errors.append(f"{prefix}: unknown control {control!r}")
            continue
        expected = case.get("expected")
        if expected not in {"violation", "clean"}:
            errors.append(f"{prefix}: expected must be violation|clean, got {expected!r}")
            continue
        path = case.get("path")
        if not isinstance(path, str) or not path.startswith("app/"):
            errors.append(f"{prefix}: path must start with app/, got {path!r}")
        code = case.get("code")
        if not isinstance(code, str) or not code.strip():
            errors.append(f"{prefix}: missing code")
            continue
        try:
            canonical = _canonical(code)
        except SyntaxError as exc:
            errors.append(f"{prefix}: code does not parse: {exc}")
            continue
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        if digest in seen_codes:
            errors.append(f"{prefix}: duplicated code inside the blind set")
        if digest in known:
            errors.append(f"{prefix}: code already appears in a known corpus")
        seen_codes.add(digest)
        counts[control][expected] += 1

    for control in sorted(CONTROLS):
        total = sum(counts[control].values())
        if total < MIN_CASES_PER_CONTROL:
            errors.append(f"{control}: {total} cases, need at least {MIN_CASES_PER_CONTROL}")
        for label in ("violation", "clean"):
            if counts[control][label] < MIN_PER_LABEL:
                errors.append(
                    f"{control}: {counts[control][label]} {label} cases, need at least {MIN_PER_LABEL}")
    return errors


def report(corpus: Path) -> dict:
    data = json.loads(corpus.read_text(encoding="utf-8"))
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"violation": 0, "clean": 0})
    for case in data["cases"]:
        counts[case["control"]][case["expected"]] += 1
    print(f"{'control':28}{'violation':>10}{'clean':>7}{'total':>7}")
    for control in sorted(counts):
        values = counts[control]
        total = values["violation"] + values["clean"]
        print(f"{control:28}{values['violation']:>10}{values['clean']:>7}{total:>7}")
    print(f"cases: {len(data['cases'])}")
    return counts


def seal(corpus: Path) -> Path:
    digest = hashlib.sha256(corpus.read_bytes()).hexdigest()
    seal_path = corpus.with_name(corpus.name + ".sha256")
    seal_path.write_text(digest + "\n", encoding="utf-8")
    return seal_path


def verify_seal(corpus: Path) -> bool:
    seal_path = corpus.with_name(corpus.name + ".sha256")
    if not seal_path.is_file():
        return False
    expected = seal_path.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(corpus.read_bytes()).hexdigest()
    return expected == actual


def main() -> int:
    parser = argparse.ArgumentParser(prog="python harness/eval/blind/check_blind_set.py")
    parser.add_argument("--corpus", type=Path,
                        default=BLIND_DIR / "cases_blind_round1.json")
    parser.add_argument("--seal", action="store_true", help="write <corpus>.sha256 after validation")
    parser.add_argument("--verify-seal", action="store_true", help="check the existing seal")
    args = parser.parse_args()

    if args.verify_seal:
        ok = verify_seal(args.corpus)
        print("seal:", "OK" if ok else "MISMATCH")
        return 0 if ok else 1

    errors = validate(args.corpus)
    if errors:
        print(f"invalid: {len(errors)} error(s)")
        for error in errors:
            print(" -", error)
        return 1
    report(args.corpus)
    if args.seal:
        path = seal(args.corpus)
        print("sealed:", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
