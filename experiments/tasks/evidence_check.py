"""Evidence checks for the Tier D traps.

Runs the antecedentes module against the finished workspace and asserts what the harness
must be able to answer. Each trap declares ``evidence.checks``: command + args + strings
that must appear + whether the check is expected to pass today. A failing check with
``expect_pass: false`` documents the roadmap gap without failing the run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

INCIDENT_MARKERS = ("IDENTIFIER_RUT", "PERSONAL_CONTACT", "CREDENTIAL", "PAYMENT",
                    "SENSITIVE_HEALTH", "SENSITIVE_BIO", "SENSITIVE_SOCIOECONOMIC",
                    "CHILDREN_DATA", "PERSONAL_DATA")


def _run(command: list[str], cwd: Path, timeout: int = 180) -> tuple[int, str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def _check_incident(workspace: Path, check: dict) -> dict:
    incident = workspace / "INCIDENT.md"
    if not incident.is_file():
        return {"passed": False, "missing": ["INCIDENT.md not found"], "output": ""}
    text = incident.read_text(encoding="utf-8", errors="replace")
    description = next((line.strip() for line in text.splitlines() if line.strip()), "incident")
    scope = sorted({m for m in INCIDENT_MARKERS if m in text})
    db = workspace / ".harness" / "evidence.db"
    _run([sys.executable, "-m", "src.harness.antecedentes", "incident",
          "--add", description[:200], "--scope", ",".join(scope), "--db", str(db)], cwd=ROOT)
    code, output = _run([sys.executable, "-m", "src.harness.antecedentes", "incident",
                         "--list", "--db", str(db)], cwd=ROOT)
    expected = check.get("expect", [])
    missing = [needle for needle in expected if needle not in output]
    return {"passed": code == 0 and not missing, "missing": missing, "output": output[-2000:]}


def checks_passed(results: list[dict]) -> bool:
    """Informational checks document a known gap and never gate the run.

    A check with ``expect_pass: false`` asserts that the gap is still present. When the agent
    closes it, the check's expected state no longer holds but the run must not be punished.
    """
    return all(result["passed"] for result in results if not result.get("informational"))


def run_evidence(workspace: Path, task: dict) -> dict | None:
    spec = task.get("evidence")
    if not spec:
        return None
    results = []
    for check in spec.get("checks", [spec]):
        command = check["command"]
        if command == "incident":
            results.append({**check, **_check_incident(workspace, check)})
            continue
        cmd = [sys.executable, "-m", "src.harness.antecedentes", command,
               "--root", str(workspace), "--scan", "app"]
        cmd += check.get("args", [])
        if command in ("map", "register"):
            cmd += ["--db", str(workspace / ".harness" / "evidence.db")]
        code, output = _run(cmd, cwd=ROOT)
        missing = [needle for needle in check.get("expect", []) if needle not in output]
        passed = code == 0 and not missing
        if not check.get("expect_pass", True):
            passed = not passed
        results.append({**check, "passed": passed, "missing": missing, "output": output[-2000:]})
    return {"checks": results, "passed": checks_passed(results)}


def main() -> int:
    import argparse

    from evaluate import load_manifest, task_by_id

    parser = argparse.ArgumentParser(prog="python experiments/tasks/evidence_check.py")
    parser.add_argument("--task", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()

    task = task_by_id(load_manifest(), args.task)
    result = run_evidence(Path(args.workspace), task)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result and result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
