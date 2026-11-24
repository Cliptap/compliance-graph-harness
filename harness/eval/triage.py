"""Run the catalog engine over a directory and emit a triage sheet.

The sheet is the input for a human (or independent) adjudication: one row per finding with the
file, line, control and evidence, and an empty verdict column. A filled sheet is the measurement of
precision on real code.

Usage:
    python harness/eval/triage.py --root experiments/supermercado/app \
        --out qa_reports/triage/supermercado.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

DEFAULT_CATALOG = ROOT / ".harness" / "packs" / "catalog.full.json"


def collect(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        resolved = path.resolve()
        try:
            key = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            key = resolved.as_posix()
        files[key] = resolved.read_text(encoding="utf-8")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(prog="python harness/eval/triage.py")
    parser.add_argument("--root", type=Path, required=True, help="directory to scan")
    parser.add_argument("--out", type=Path, required=True, help="markdown sheet to write")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()

    files = collect(args.root)
    engine = CatalogEngine(load_catalog(args.catalog), include_legacy=False)
    spec = TaskSpec(task_id="triage", goal="triage", allowed_paths=["*"], forbidden_paths=[])
    findings = engine.evaluate(spec, files)
    findings.sort(key=lambda finding: (finding.file, finding.line or 0, finding.policy_id))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "root": args.root.as_posix(),
        "files": len(files),
        "findings": len(findings),
        "by_control": dict(Counter(finding.policy_id for finding in findings)),
        "rows": [
            {
                "id": finding.id,
                "file": finding.file,
                "line": finding.line,
                "control": finding.policy_id,
                "severity": finding.severity,
                "evidence": finding.evidence,
                "message": finding.message,
                "verdict": "",
                "notes": "",
            }
            for finding in findings
        ],
    }
    args.out.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Triage: `{args.root.as_posix()}`",
        "",
        f"- Archivos analizados: **{len(files)}**",
        f"- Hallazgos: **{len(findings)}**",
        "",
    ]
    if payload["by_control"]:
        lines += ["| Control | Hallazgos |", "|---|---:|"]
        for control, count in sorted(payload["by_control"].items()):
            lines.append(f"| `{control}` | {count} |")
        lines.append("")
    lines += [
        "## Planilla",
        "",
        "Marcar `veredicto` como `TP` (exposición real) o `FP` (no lo es) y anotar el motivo.",
        "",
        "| # | Archivo:línea | Control | Severidad | Evidencia | Veredicto | Notas |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, row in enumerate(payload["rows"], 1):
        evidence = (row["evidence"] or "").replace("|", "\\|").replace("\n", " ")[:120]
        location = f"`{row['file']}:{row['line']}`" if row["line"] else f"`{row['file']}`"
        lines.append(
            f"| {index} | {location} | `{row['control']}` | {row['severity']} | {evidence} |  |  |")
    if not payload["rows"]:
        lines.append("| - | - | - | - | sin hallazgos | - | - |")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"files={len(files)} findings={len(findings)}")
    for control, count in sorted(payload["by_control"].items()):
        print(f"  {control}: {count}")
    print(f"wrote {args.out} and {args.out.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
