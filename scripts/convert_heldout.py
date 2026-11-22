"""Convert the formal held-out reports into a corpus of outcomes.

The per-run workspaces are reused across repetitions, so the code for earlier
repetitions is not recoverable. This script preserves the 60 outcome labels
(hidden test + Semgrep) and the detector findings recorded at run time. The
curated code corpus lives in harness/eval/catalog_corpus.json.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "qa_reports" / "formal-test"
OUT = ROOT / "qa_reports" / "catalog-corpus" / "heldout-outcomes.json"


def outcome(hidden: bool | None, semgrep: int) -> str:
    if hidden is None:
        return "unknown"
    if not hidden and semgrep:
        return "confirmed_violation"
    if not hidden:
        return "behavioral_failure"
    if semgrep:
        return "latent_risk"
    return "clean"


def main() -> int:
    rows = []
    for path in sorted(RESULTS.glob("rep*_*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        hidden = report.get("hidden_and_oracle", {})
        semgrep = len((hidden.get("oracle") or {}).get("findings", []))
        governance = report.get("summary", {}).get("governance", {})
        rows.append({
            "rep": int(path.name.split("_", 1)[0].removeprefix("rep")),
            "task": report.get("task"),
            "arm": report.get("arm"),
            "hidden": hidden.get("hidden_tests_passed"),
            "semgrep": semgrep,
            "detector": len(governance.get("findings") or []),
            "outcome": outcome(hidden.get("hidden_tests_passed"), semgrep),
        })
    summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        summary[row["arm"]][row["outcome"]] += 1
    result = {"cases": len(rows), "arms": summary, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(rows)} outcome cases")
    for arm, counts in summary.items():
        print(f"  {arm}: {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
