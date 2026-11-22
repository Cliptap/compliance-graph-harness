"""Per-control corpus metrics for the v2 catalog.

Each case names the control it exercises and whether the control should fire.
The runner does not reward other controls firing on the same code: it measures
precision, recall and F1 for the named control.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

CORPUS = ROOT / "harness" / "eval" / "catalog_corpus.json"
PACKS = ROOT / ".harness" / "packs"
CATALOG = PACKS / "catalog.full.json"
if not CATALOG.is_file():
    CATALOG = PACKS / "catalog.v2.json"
SPEC = TaskSpec(task_id="corpus", goal="corpus", allowed_paths=["*"], forbidden_paths=[])


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def evaluate(engine: CatalogEngine, case: dict) -> dict:
    findings = engine.evaluate(SPEC, {case["path"]: case["code"]})
    detected = any(finding.policy_id == case["control"] for finding in findings)
    expected = case["expected"] == "violation"
    return {
        "id": case["id"],
        "control": case["control"],
        "expected": case["expected"],
        "detected": detected,
        "other_findings": sorted({finding.policy_id for finding in findings
                                  if finding.policy_id != case["control"]}),
        "passed": detected == expected,
    }


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson interval for a proportion; small corpora need the interval, not the point."""
    if n == 0:
        return None
    p = k / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return (round(max(0.0, center - half), 3), round(min(1.0, center + half), 3))


def metrics(rows: list[dict]) -> dict:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    for row in rows:
        bucket = counts[row["control"]]
        if row["expected"] == "violation" and row["detected"]:
            bucket["tp"] += 1
        elif row["expected"] == "violation":
            bucket["fn"] += 1
        elif row["detected"]:
            bucket["fp"] += 1
        else:
            bucket["tn"] += 1
    out = {}
    for control, values in sorted(counts.items()):
        tp, fp, fn, tn = values["tp"], values["fp"], values["fn"], values["tn"]
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = (2 * precision * recall / (precision + recall)) if precision and recall else None
        out[control] = {**values, "precision": precision, "recall": recall, "f1": f1,
                        "precision_ci": _wilson(tp, tp + fp), "recall_ci": _wilson(tp, tp + fn)}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(prog="python harness/eval/catalog_corpus.py")
    parser.add_argument("--corpus", default=str(CORPUS))
    parser.add_argument("--catalog", default=str(CATALOG))
    parser.add_argument("--out", default=str(ROOT / "qa_reports" / "catalog-corpus" / "metrics.json"))
    args = parser.parse_args()

    engine = CatalogEngine(load_catalog(args.catalog), include_legacy=False)
    rows = [evaluate(engine, case) for case in load_cases(Path(args.corpus))]
    summary = metrics(rows)
    result = {"corpus": args.corpus, "catalog": args.catalog, "cases": len(rows),
              "passed": sum(1 for row in rows if row["passed"]), "controls": summary, "rows": rows}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"cases: {result['passed']}/{result['cases']} passed")
    print(f"{'control':28}{'TP':>3}{'FP':>3}{'FN':>3}{'TN':>3}{'precision':>11}{'recall':>8}{'f1':>7}")
    for control, values in summary.items():
        print(f"{control:28}{values['tp']:>3}{values['fp']:>3}{values['fn']:>3}{values['tn']:>3}"
              f"{(values['precision'] if values['precision'] is not None else 0):>11.2f}"
              f"{(values['recall'] if values['recall'] is not None else 0):>8.2f}"
              f"{(values['f1'] if values['f1'] is not None else 0):>7.2f}")
    for control, values in summary.items():
        print(f"CI {control}: precision {values['precision_ci']} recall {values['recall_ci']}")
    failures = [row for row in rows if not row["passed"]]
    for row in failures:
        print(f"FAIL {row['id']} control={row['control']} expected={row['expected']} "
              f"detected={row['detected']} other={row['other_findings']}")
    print("wrote", out)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
