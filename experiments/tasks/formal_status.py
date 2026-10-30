"""Progress monitor for the formal T7 run."""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qa_reports" / "formal"
ARMS = ["baseline", "harness", "harness_compliance"]
REPS = [1, 2, 3]
TASKS = 12


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    rows = []
    for path in sorted(OUT.glob("rep*_*.json")):
        report = load(path)
        if not report:
            continue
        live = report.get("live", {})
        hidden = report.get("hidden_and_oracle", {})
        findings = (hidden.get("oracle") or {}).get("findings", [])
        rows.append({
            "path": path,
            "arm": report.get("arm"),
            "task": report.get("task"),
            "status": live.get("status"),
            "time": live.get("cycle_time_s"),
            "hidden": hidden.get("hidden_tests_passed"),
            "oracle": len(findings),
            "mtime": path.stat().st_mtime,
        })
    total = len(REPS) * len(ARMS) * TASKS
    print(f"completed {len(rows)}/{total} runs")
    for arm in ARMS:
        for rep in REPS:
            subset = [row for row in rows if row["arm"] == arm and f"rep{rep}_" in row["path"].name]
            if not subset:
                continue
            times = [row["time"] for row in subset if row["time"]]
            hidden = sum(1 for row in subset if row["hidden"])
            oracle = sum(row["oracle"] for row in subset)
            print(f"  rep{rep} {arm:20} n={len(subset):2} "
                  f"mean={sum(times)/len(times):6.1f}s hidden={hidden}/{len(subset)} oracle={oracle}")
    failed = [row for row in rows if row["hidden"] is False or row["oracle"]]
    if failed:
        print("attention:")
        for row in failed:
            print(f"  {row['path'].name}: hidden={row['hidden']} oracle={row['oracle']}")
    if rows:
        latest = max(row["mtime"] for row in rows)
        print("last report:", time.strftime("%H:%M:%S", time.localtime(latest)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
