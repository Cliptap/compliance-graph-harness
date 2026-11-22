"""Autonomous detector repair for the dose pipeline.

The decision script marks a repair when a gate arm produced a confirmed
violation that the deterministic detector did not flag. This script gives the
missing cases to an OpenCode agent, lets it edit the detector and a regression
case, and accepts the change only if the harness tests stay green and the
experiment files were not touched. The diff is saved for human review.

Exit codes: 0 = fixed and green, 1 = not fixed or unsafe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

FORBIDDEN = [
    "experiments/tasks/hidden",
    "experiments/tasks/manifest.json",
    "experiments/tasks/oracle",
    "experiments/tasks/opencode_arms.py",
    "experiments/tasks/opencode_run.py",
]
MODEL = "opencode-go/deepseek-v4.1-flash"


def opencode_exe() -> str:
    override = os.environ.get("OPENCODE_BIN")
    if override:
        return override
    exe = shutil.which("opencode.exe")
    if exe:
        return exe
    for name in ("opencode.cmd", "opencode"):
        found = shutil.which(name)
        if found:
            candidate = Path(found).parent / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
            if candidate.is_file():
                return str(candidate)
    return "opencode"


def tree_hash(repo: Path) -> str:
    digest = hashlib.sha256()
    for relative in FORBIDDEN:
        path = repo / relative
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for file in files:
            digest.update(file.relative_to(repo).as_posix().encode("utf-8"))
            digest.update(file.read_bytes())
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return (result.stdout or "") + (result.stderr or "")


def build_prompt(decision: dict, pilot_dir: Path) -> str:
    misses = decision.get("detector_misses") or []
    lines = [
        "You are repairing the T7 harness detector.",
        "A compliance-gate run produced a confirmed privacy violation that the deterministic detector did not flag.",
        f"Missed cases: {', '.join(misses)}",
        "",
        "Read the pilot reports to see the workspace, the hidden output, the oracle findings and the final detector findings:",
    ]
    for miss in misses:
        task, _, arm = miss.partition("/")
        lines.append(f"- {pilot_dir}/cost_{task}_{arm}.json")
    lines += [
        "",
        "Task:",
        "1. Add a regression case that reproduces the miss (harness/eval/catalog_corpus.json or tests/harness).",
        "2. Fix the detector: src/harness/policy_families.py, src/harness/catalog_engine.py, src/harness/catalog.py or .harness/packs/catalog.full.json.",
        "3. Run `python -m pytest tests/harness -q` until it is green.",
        "",
        "Do not modify experiments/tasks/hidden, experiments/tasks/manifest.json, experiments/tasks/oracle,",
        "experiments/tasks/opencode_arms.py or experiments/tasks/opencode_run.py.",
        "Do not reset or revert any uncommitted change.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python scripts/autofix_detector.py")
    parser.add_argument("--decision", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    decision_path = Path(args.decision)
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if not decision.get("detector_misses"):
        print("no detector misses to repair")
        return 0

    before_hash = tree_hash(repo)
    before_diff = git(repo, "diff")
    (log_path.parent / "autofix-before.diff").write_text(before_diff, encoding="utf-8")
    prompt = build_prompt(decision, decision_path.parent)
    command = [opencode_exe(), "run", prompt, "--model", MODEL, "--format", "json",
               "--auto", "--pure", "--dir", str(repo)]
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=repo, capture_output=True, encoding="utf-8",
                                   errors="replace", timeout=args.timeout)
        stdout, stderr, code = completed.stdout or "", completed.stderr or "", completed.returncode
    except subprocess.TimeoutExpired as err:
        stdout = (err.stdout or "") if isinstance(err.stdout, str) else ""
        stderr = (err.stderr or "") if isinstance(err.stderr, str) else ""
        code = None
    (log_path.parent / "autofix-agent.log").write_text(stdout + "\n" + stderr, encoding="utf-8")
    after_diff = git(repo, "diff")
    (log_path.parent / "autofix-after.diff").write_text(after_diff, encoding="utf-8")
    (log_path.parent / "autofix.diff").write_text(after_diff, encoding="utf-8")

    if tree_hash(repo) != before_hash:
        message = "autofix changed a forbidden experiment file; review autofix.diff"
        log_path.write_text(message + "\n", encoding="utf-8")
        print(message)
        return 1
    if code != 0:
        message = f"autofix agent exited with {code}; review autofix-agent.log"
        log_path.write_text(message + "\n", encoding="utf-8")
        print(message)
        return 1

    tests = subprocess.run([sys.executable, "-m", "pytest", "tests/harness", "-q",
                            "-p", "no:cacheprovider"], cwd=repo, capture_output=True,
                           text=True, timeout=900)
    (log_path.parent / "autofix-tests.log").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    elapsed = round(time.perf_counter() - started, 1)
    if tests.returncode != 0:
        message = f"autofix tests failed after {elapsed}s; review autofix.diff and autofix-tests.log"
        log_path.write_text(message + "\n", encoding="utf-8")
        print(message)
        return 1
    message = f"autofix green after {elapsed}s; diff saved to autofix.diff"
    log_path.write_text(message + "\n", encoding="utf-8")
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
