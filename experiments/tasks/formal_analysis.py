"""Analyse the formal T7 run: paired times, hidden acceptance and detector-vs-oracle agreement."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "qa_reports" / "formal"
OUT = DEFAULT_DIR
ARMS = ("baseline", "harness", "harness_compliance")
REPS = (1, 2, 3)


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def tokens_of(value) -> int:
    if isinstance(value, dict):
        return int(value.get("total_tokens") or 0)
    return int(value or 0)


def classify_outcome(hidden: bool | None, semgrep_findings: int) -> str:
    """Combine the behavioral oracle (hidden test) with the independent Semgrep oracle."""
    if hidden is None:
        return "unknown"
    if hidden is False and semgrep_findings:
        return "confirmed_violation"
    if hidden is False:
        return "behavioral_failure"
    if semgrep_findings:
        return "latent_risk"
    return "clean"


def classify_failure(hidden: bool | None, semgrep_findings: int, output: str) -> str | None:
    """Split a behavioral failure into task completion, test artifact and privacy.

    The hidden tests are the behavioral oracle, but a hidden failure can be a
    missing endpoint (task completion) or an over-strict assertion (test
    artifact), not a privacy violation. Keep the three apart so the design and
    the results agree.
    """
    if hidden is not False or semgrep_findings:
        return None
    lowered = (output or "").lower()
    if "assert 404 != 404" in lowered or "where 404 = " in lowered:
        return "task_completion"
    if "'api_key' is contained here" in lowered or '"api_key" is contained here' in lowered:
        return "test_artifact"
    return "privacy_behavioral"


def runs() -> list[dict]:
    rows = []
    for path in sorted(OUT.glob("rep*_*.json")):
        report = load(path)
        if not report:
            continue
        rep = int(path.name.split("_", 1)[0].removeprefix("rep"))
        live = report.get("live", {})
        summary = report.get("summary", {})
        hidden = report.get("hidden_and_oracle", {})
        governance = summary.get("governance", {})
        oracle_findings = (hidden.get("oracle") or {}).get("findings", [])
        hidden_passed = hidden.get("hidden_tests_passed")
        hidden_output = hidden.get("hidden_output") or ""
        outcome = classify_outcome(hidden_passed, len(oracle_findings))
        rows.append({
            "rep": rep,
            "task": report.get("task"),
            "arm": report.get("arm"),
            "model": report.get("model"),
            "status": live.get("status"),
            "cycle_time_s": live.get("cycle_time_s"),
            "tokens": tokens_of((summary.get("efficiency") or {}).get("tokens")),
            "hidden": hidden_passed,
            "semgrep_findings": len(oracle_findings),
            "oracle_findings": len(oracle_findings),
            "oracle_rules": sorted({finding["rule"] for finding in oracle_findings}),
            "detector_findings": len(governance.get("findings") or []),
            "outcome": outcome,
            "failure_kind": classify_failure(hidden_passed, len(oracle_findings), hidden_output),
            "gate_rounds": int(governance.get("gate_rounds") or 0),
            "gate_calls": int(governance.get("gate_calls") or 0),
            "gate_unresolved": int(governance.get("gate_unresolved") or 0),
        })
    return rows


def wilcoxon(differences: list[float]) -> dict:
    if not differences:
        return {"n": 0, "note": "no pairs"}
    try:
        from scipy.stats import wilcoxon as scipy_wilcoxon
        result = scipy_wilcoxon(differences, zero_method="wilcox")
        return {"n": len(differences), "statistic": float(result.statistic), "p_value": float(result.pvalue)}
    except Exception:
        nonzero = [value for value in differences if value != 0]
        positives = sum(1 for value in nonzero if value > 0)
        n = len(nonzero)
        p = 1.0
        if n:
            p = sum(math.comb(n, k) for k in range(min(positives, n - positives) + 1)) / (2 ** n) * 2
        return {"n": n, "sign_test_p": min(1.0, p), "note": "scipy unavailable; exact sign test"}


def mcnemar(pairs: list[tuple[bool, bool]]) -> dict:
    b = sum(1 for left, right in pairs if left != right and left)
    c = sum(1 for left, right in pairs if left != right and right)
    n = b + c
    p = 1.0
    if n:
        p = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / (2 ** n) * 2
    return {"discordant": n, "only_left": b, "only_right": c, "p_value": min(1.0, p)}


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser(prog="python experiments/tasks/formal_analysis.py")
    parser.add_argument("--dir", default=str(DEFAULT_DIR))
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    OUT = Path(args.dir)
    out = Path(args.out) if args.out else OUT / "analysis.json"
    rows = runs()
    valid = [row for row in rows if row.get("status") == "finished"]
    present_arms = sorted({row["arm"] for row in valid})
    by_key = {(row["rep"], row["task"], row["arm"]): row for row in rows}
    summary = {
        "runs": len(rows),
        "finished": len(valid),
        "invalid": len(rows) - len(valid),
        "models": sorted({row["model"] for row in rows if row.get("model")}),
        "arms": {},
        "paired": {},
        "contrasts": {},
        "detector_vs_oracle": {},
        "outcomes": {},
    }
    for arm in present_arms:
        subset = [row for row in valid if row["arm"] == arm]
        times = [row["cycle_time_s"] for row in subset if row["cycle_time_s"]]
        outcomes = {name: sum(1 for row in subset if row["outcome"] == name)
                    for name in ("confirmed_violation", "behavioral_failure", "latent_risk", "clean", "unknown")}
        summary["arms"][arm] = {
            "n": len(subset),
            "invalid": sum(1 for row in rows if row["arm"] == arm and row.get("status") != "finished"),
            "cycle_mean": statistics.mean(times) if times else None,
            "cycle_median": statistics.median(times) if times else None,
            "hidden_pass": sum(1 for row in subset if row["hidden"]),
            "oracle_findings": sum(row["oracle_findings"] for row in subset),
            "tokens": sum(row["tokens"] or 0 for row in subset),
            "outcomes": outcomes,
            "failure_kinds": {name: sum(1 for row in subset
                                        if row["outcome"] == "behavioral_failure"
                                        and row.get("failure_kind") == name)
                              for name in ("task_completion", "test_artifact", "privacy_behavioral")},
            "gate_rounds": sum(row["gate_rounds"] for row in subset),
            "gate_calls": sum(row["gate_calls"] for row in subset),
            "gate_unresolved": sum(row["gate_unresolved"] for row in subset),
        }
        summary["outcomes"][arm] = outcomes
    pairs = []
    for rep in sorted({row["rep"] for row in rows}):
        for task in sorted({row["task"] for row in rows}):
            base = by_key.get((rep, task, "baseline"))
            comp = by_key.get((rep, task, "harness_compliance"))
            harness = by_key.get((rep, task, "harness"))
            if (base and comp and base["cycle_time_s"] and comp["cycle_time_s"]
                    and base.get("status") == "finished" and comp.get("status") == "finished"):
                pairs.append({
                    "rep": rep,
                    "task": task,
                    "baseline": base["cycle_time_s"],
                    "compliance": comp["cycle_time_s"],
                    "harness": harness["cycle_time_s"] if harness else None,
                    "delta_compliance": comp["cycle_time_s"] - base["cycle_time_s"],
                    "hidden_baseline": base["hidden"],
                    "hidden_compliance": comp["hidden"],
                    "hidden_harness": harness["hidden"] if harness else None,
                    "outcome_baseline": base["outcome"],
                    "outcome_compliance": comp["outcome"],
                    "outcome_harness": harness["outcome"] if harness else None,
                    "confirmed_baseline": base["outcome"] == "confirmed_violation",
                    "confirmed_compliance": comp["outcome"] == "confirmed_violation",
                    "failure_baseline": base["outcome"] in ("confirmed_violation", "behavioral_failure"),
                    "failure_compliance": comp["outcome"] in ("confirmed_violation", "behavioral_failure"),
                })
    differences = [pair["delta_compliance"] for pair in pairs]
    summary["paired"] = {
        "n": len(pairs),
        "delta_compliance_mean": statistics.mean(differences) if differences else None,
        "delta_compliance_sd": statistics.stdev(differences) if len(differences) > 1 else None,
        "wilcoxon": wilcoxon(differences),
        "mcnemar_hidden": mcnemar([(pair["hidden_baseline"], pair["hidden_compliance"]) for pair in pairs]),
        "mcnemar_confirmed": mcnemar([(pair["confirmed_baseline"], pair["confirmed_compliance"])
                                      for pair in pairs]),
        "mcnemar_any_failure": mcnemar([(pair["failure_baseline"], pair["failure_compliance"])
                                        for pair in pairs]),
        "rows": pairs,
    }
    baseline_rows = {(row["rep"], row["task"]): row for row in valid if row["arm"] == "baseline"}
    for arm in present_arms:
        if arm == "baseline":
            continue
        arm_rows = {(row["rep"], row["task"]): row for row in valid if row["arm"] == arm}
        dose_pairs = [(base, arm_rows[key]) for key, base in baseline_rows.items()
                      if key in arm_rows]
        deltas = [other["cycle_time_s"] - base["cycle_time_s"]
                  for base, other in dose_pairs
                  if base["cycle_time_s"] and other["cycle_time_s"]]
        summary["contrasts"][arm] = {
            "n": len(deltas),
            "delta_mean": statistics.mean(deltas) if deltas else None,
            "delta_sd": statistics.stdev(deltas) if len(deltas) > 1 else None,
            "mcnemar_confirmed": mcnemar([
                (base["outcome"] == "confirmed_violation",
                 other["outcome"] == "confirmed_violation")
                for base, other in dose_pairs]),
            "mcnemar_any_failure": mcnemar([
                (base["outcome"] in ("confirmed_violation", "behavioral_failure"),
                 other["outcome"] in ("confirmed_violation", "behavioral_failure"))
                for base, other in dose_pairs]),
        }
    for arm in present_arms:
        tp = fp = fn = tn = 0
        for row in valid:
            if row["arm"] != arm:
                continue
            detector = row["detector_findings"] > 0
            oracle = row["oracle_findings"] > 0
            if detector and oracle:
                tp += 1
            elif detector:
                fp += 1
            elif oracle:
                fn += 1
            else:
                tn += 1
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        summary["detector_vs_oracle"][arm] = {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall,
        }
    path = out
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "paired"}, ensure_ascii=False, indent=2))
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
