"""Compare two experiment arms over the same tasks and repetitions.

Reads the per-run reports the task runner writes (``rep<N>_<task>_<arm>.json``) and produces the
classification the report uses, plus a paired comparison between arms.

Usage::

    python -m harness.eval.arm_comparison --root qa_reports/gate-only \\
        --left baseline --right gate_only
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_runs(root: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(root.glob("rep*_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        live = data.get("live") or {}
        summary = data.get("summary") or {}
        hidden = data.get("hidden_and_oracle") or {}
        findings = (hidden.get("oracle") or {}).get("findings") or []
        rows.append({
            "file": path.name,
            "rep": path.name.split("_", 1)[0],
            "task": data.get("task"),
            "arm": data.get("arm"),
            "status": live.get("status"),
            "cycle_s": live.get("cycle_time_s"),
            "tokens": (live.get("tokens") or {}).get("total_tokens"),
            "gate_calls": live.get("gate_calls"),
            "policy_violations": (summary.get("governance") or {}).get("policy_violations"),
            "hidden_ok": hidden.get("hidden_tests_passed"),
            "oracle_rules": sorted({finding["rule"] for finding in findings}),
        })
    return rows


def classify(row: dict) -> str:
    """The four cells of the oracle table used in the report."""
    hidden_ok = row.get("hidden_ok")
    oracle = bool(row.get("oracle_rules"))
    if hidden_ok is False and oracle:
        return "confirmed_violation"
    if hidden_ok is False:
        return "behavioral_failure"
    if oracle:
        return "latent_risk"
    return "clean"


def summarize(rows: list[dict], arm: str) -> dict:
    runs = [row for row in rows if row["arm"] == arm]
    classes = Counter(classify(row) for row in runs)
    cycles = [row["cycle_s"] for row in runs if isinstance(row["cycle_s"], (int, float))]
    tokens = [row["tokens"] for row in runs if isinstance(row["tokens"], (int, float))]
    gate_calls = [row["gate_calls"] for row in runs if isinstance(row["gate_calls"], (int, float))]
    return {
        "arm": arm,
        "runs": len(runs),
        "confirmed": classes["confirmed_violation"],
        "behavioral": classes["behavioral_failure"],
        "latent": classes["latent_risk"],
        "clean": classes["clean"],
        "failed": classes["confirmed_violation"] + classes["behavioral_failure"],
        "median_cycle_s": round(statistics.median(cycles), 1) if cycles else None,
        "median_tokens": int(statistics.median(tokens)) if tokens else None,
        "median_gate_calls": statistics.median(gate_calls) if gate_calls else None,
        "statuses": dict(Counter(row["status"] for row in runs)),
    }


def mcnemar(left: list[bool], right: list[bool]) -> tuple[int, int, float]:
    """Exact two-sided McNemar on paired outcomes; returns (left_only, right_only, p)."""
    left_only = sum(1 for a, b in zip(left, right) if a and not b)
    right_only = sum(1 for a, b in zip(left, right) if b and not a)
    discordant = left_only + right_only
    if discordant == 0:
        return (0, 0, 1.0)
    smaller = min(left_only, right_only)
    tail = sum(math.comb(discordant, k) for k in range(smaller + 1)) / 2 ** discordant
    return (left_only, right_only, min(1.0, 2 * tail))


def paired(rows: list[dict], left: str, right: str) -> dict:
    index = {(row["task"], row["rep"], row["arm"]): row for row in rows}
    keys = sorted({(task, rep) for (task, rep, arm) in index if arm == left}
                  & {(task, rep) for (task, rep, arm) in index if arm == right})
    left_failed, right_failed = [], []
    for task, rep in keys:
        left_failed.append(classify(index[(task, rep, left)]) in
                           ("confirmed_violation", "behavioral_failure"))
        right_failed.append(classify(index[(task, rep, right)]) in
                            ("confirmed_violation", "behavioral_failure"))
    lo, ro, p = mcnemar(left_failed, right_failed)
    return {"pairs": len(keys), "left_only_failed": lo, "right_only_failed": ro, "p": p}


def format_report(rows: list[dict], arms: list[str], comparison: dict | None = None) -> str:
    lines = ["| Brazo | Corridas | Confirmadas | Comportamiento | Latentes | Limpias | Ciclo mediana | Tokens mediana | Llamadas a la compuerta |",
             "| - | -: | -: | -: | -: | -: | -: | -: | -: |"]
    for arm in arms:
        s = summarize(rows, arm)
        lines.append(
            f"| `{arm}` | {s['runs']} | {s['confirmed']} | {s['behavioral']} | {s['latent']} | "
            f"{s['clean']} | {s['median_cycle_s']} | {s['median_tokens']} | {s['median_gate_calls']} |")
    if comparison:
        lines.append("")
        lines.append(f"Pares comparables: {comparison['pairs']}. "
                     f"Discordantes a favor de `{comparison['left']}`: {comparison['left_only_failed']}; "
                     f"a favor de `{comparison['right']}`: {comparison['right_only_failed']}; "
                     f"McNemar exacto bilateral p = {comparison['p']:.4f}.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two experiment arms.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--json", default=None, help="write the result as JSON")
    args = parser.parse_args(argv)
    rows = load_runs(Path(args.root))
    arms = [args.left, args.right]
    comparison = paired(rows, args.left, args.right)
    comparison["left"], comparison["right"] = args.left, args.right
    print(format_report(rows, arms, comparison))
    if args.json:
        payload = {"runs": rows, "summary": {arm: summarize(rows, arm) for arm in arms},
                   "comparison": comparison}
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
