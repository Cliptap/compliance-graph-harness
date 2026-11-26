"""Two-human adjudication of the blind sample.

The blind sheet already exists (``labels_sample30.json``). Two people label it independently,
without the answer key and without seeing each other's file. This tool writes the template and
reports three numbers: each rater's agreement with the corpus labels, and the agreement between the
two people. The last one is the only one that does not involve a model.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.eval.label_agreement import cohen_kappa, score  # noqa: E402

VALID = {"violation", "clean"}


def build_template(sheet_path: Path, out_path: Path, rater: str) -> dict:
    sheet = json.loads(sheet_path.read_text(encoding="utf-8"))
    payload = {
        "rater": rater,
        "sheet": sheet_path.name,
        "instructions": (
            "Para cada caso, escribí 'violation' o 'clean' en el campo verdict, según el control "
            "indicado. No abras el archivo de respuestas ni el del otro evaluador."
        ),
        "verdicts": [{"id": case["id"], "verdict": ""} for case in sheet["cases"]],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _verdicts(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["id"]: row.get("verdict", "") for row in data.get("verdicts", [])}


def inter_rater(first: Path, second: Path) -> tuple[int, float, float]:
    left, right = _verdicts(first), _verdicts(second)
    pairs = [(left[key], right[key]) for key in left
             if key in right and left[key] in VALID and right[key] in VALID]
    agree, kappa = cohen_kappa(pairs)
    return len(pairs), agree, kappa


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Two-human adjudication of the blind sample.")
    parser.add_argument("--template", type=Path, help="blind sheet to turn into a rater template")
    parser.add_argument("--out", type=Path, help="where to write the template")
    parser.add_argument("--rater", default="rater", help="name that goes in the template")
    parser.add_argument("--score", nargs=2, type=Path, metavar=("A", "B"),
                        help="two filled rater files to compare")
    parser.add_argument("--key", type=Path, default=None, help="answer key for the corpus comparison")
    args = parser.parse_args(argv)

    if args.template:
        if not args.out:
            parser.error("--template needs --out")
        build_template(args.template, args.out, args.rater)
        print(f"template -> {args.out}")
        return 0
    if not args.score:
        parser.error("pass --template/--out or --score A B")

    first, second = args.score
    if args.key:
        print("== contra las etiquetas del corpus")
        score(first, args.key)
        print()
        score(second, args.key)
        print()
    total, agree, kappa = inter_rater(first, second)
    print("== acuerdo entre las dos personas")
    print(f"casos comparables: {total}")
    print(f"acuerdo: {agree:.3f}")
    print(f"cohen kappa: {kappa:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
