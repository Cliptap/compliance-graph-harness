"""Sample corpus cases for independent labeling and score the agreement.

The sample sheet omits the expected label, so a rater (human or an independent model) can label it
blind. The score step compares the rater verdicts with the corpus labels and reports raw agreement
and Cohen's kappa.

Usage:
    python harness/eval/label_agreement.py --sample 50 --out qa_reports/validation/labels_sample.json
    python harness/eval/label_agreement.py --score qa_reports/validation/rater.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CORPUS = ROOT / "harness" / "eval" / "catalog_corpus_heldout.json"


def stratified_sample(cases: list[dict], size: int, seed: int) -> list[dict]:
    """Take a balanced sample: round-robin over (control, expected) strata."""
    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for case in cases:
        strata[(case["control"], case["expected"])].append(case)
    for bucket in strata.values():
        rng.shuffle(bucket)
    keys = sorted(strata)
    sample: list[dict] = []
    index = 0
    while len(sample) < size and any(strata[key] for key in keys):
        key = keys[index % len(keys)]
        if strata[key]:
            sample.append(strata[key].pop())
        index += 1
    return sample


def build_sample(corpus: Path, size: int, seed: int, out: Path) -> dict:
    data = json.loads(corpus.read_text(encoding="utf-8"))
    sample = stratified_sample(data["cases"], size, seed)
    sheet = {
        "corpus": corpus.relative_to(ROOT).as_posix(),
        "size": len(sample),
        "seed": seed,
        "instructions": (
            "Label each case as 'violation' or 'clean' for its named control. "
            "Do not use the corpus or the repository; judge the code as written."
        ),
        "cases": [
            {
                "id": case["id"],
                "control": case["control"],
                "path": case["path"],
                "code": case["code"],
            }
            for case in sample
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    answer_key = out.with_name(out.stem + "_key.json")
    answer_key.write_text(
        json.dumps({case["id"]: case["expected"] for case in sample}, indent=2) + "\n",
        encoding="utf-8",
    )
    return sheet


def cohen_kappa(pairs: list[tuple[str, str]]) -> tuple[float, float]:
    total = len(pairs)
    if total == 0:
        return 0.0, 0.0
    agree = sum(1 for truth, verdict in pairs if truth == verdict) / total
    labels = {label for pair in pairs for label in pair}
    expected = 0.0
    for label in labels:
        truth_rate = sum(1 for truth, _ in pairs if truth == label) / total
        verdict_rate = sum(1 for _, verdict in pairs if verdict == label) / total
        expected += truth_rate * verdict_rate
    kappa = 0.0 if expected == 1.0 else (agree - expected) / (1.0 - expected)
    return agree, kappa


def score(rater_path: Path, key_path: Path) -> int:
    rater = json.loads(rater_path.read_text(encoding="utf-8"))
    key = json.loads(key_path.read_text(encoding="utf-8"))
    verdicts = {row["id"]: row.get("verdict", "") for row in rater.get("verdicts", [])}
    pairs: list[tuple[str, str]] = []
    missing: list[str] = []
    for case_id, truth in key.items():
        verdict = verdicts.get(case_id, "")
        if verdict not in {"violation", "clean"}:
            missing.append(case_id)
            continue
        pairs.append((truth, verdict))
    agree, kappa = cohen_kappa(pairs)
    print(f"rater: {rater.get('rater', 'unknown')}")
    print(f"labeled: {len(pairs)}/{len(key)}" + (f" missing={missing}" if missing else ""))
    print(f"agreement: {agree:.3f}")
    print(f"cohen kappa: {kappa:.3f}")
    for label in ("violation", "clean"):
        truth_label = [pair for pair in pairs if pair[0] == label]
        if truth_label:
            hit = sum(1 for truth, verdict in truth_label if verdict == label)
            print(f"  {label}: {hit}/{len(truth_label)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python harness/eval/label_agreement.py")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--sample", type=int, default=0, help="build a sheet of N cases")
    parser.add_argument("--seed", type=int, default=20261124)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "qa_reports" / "validation" / "labels_sample.json")
    parser.add_argument("--score", type=Path, help="rater JSON to compare against the key")
    args = parser.parse_args()

    if args.score:
        key = args.out.with_name(args.out.stem + "_key.json")
        if not key.is_file():
            key = args.score.with_name(args.score.stem + "_key.json")
        return score(args.score, key)
    if not args.sample:
        parser.error("pass --sample N or --score <file>")
    sheet = build_sample(args.corpus, args.sample, args.seed, args.out)
    print(f"sampled {sheet['size']} cases -> {args.out}")
    print(f"key -> {args.out.with_name(args.out.stem + '_key.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
