"""Run one task in one arm with the OpenCode headless CLI and evaluate it with the oracle.

Usage:
    python experiments/tasks/opencode_run.py --task T01-payment-method --arm baseline
    python experiments/tasks/opencode_run.py --task T01-payment-method --arm harness --dry-run

The fixed model is never ``auto``. Global OpenCode config, persona and skills are
isolated with a temporary ``XDG_CONFIG_HOME``/``XDG_DATA_HOME`` sandbox; the real
``auth.json`` is copied into the sandbox data dir so no credential is written to
the workspace.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for path in (str(ROOT), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from evaluate import evaluate, load_manifest, task_by_id  # noqa: E402
from evidence_check import run_evidence  # noqa: E402
from opencode_arms import (  # noqa: E402
    ARMS, prepare_harness_bundle, prepare_sandbox, prepare_workspace, skill_permissions,
    write_arm_config,
)
from harness.eval.pilot_metrics import (  # noqa: E402
    changed_files, classify_findings, compliance_score, context_relevance,
    count_potential_risks, evaluate_policies, run_pytest,
)

DEFAULT_MODEL = "opencode-go/deepseek-v4.1-flash"
DEFAULT_AUTH = Path.home() / ".local" / "share" / "opencode" / "auth.json"
DEFAULT_WORKSPACE_ROOT = Path(tempfile.gettempdir()) / "t7-opencode" / "workspaces"
READ_TOOLS = {"read", "read_file"}


def opencode_binary() -> str:
    """Resolve the real OpenCode executable (never the .cmd/.ps1 npm shim).

    The shims re-parse ``%*`` through cmd.exe, which mangles prompts that contain
    newlines and drops trailing flags such as ``--dir`` and ``--format json``.
    """
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
            if found.lower().endswith(".exe"):
                return found
    return "opencode"


def scope_for(task: dict) -> dict:
    return {
        "task_id": task["id"],
        "goal": task["prompt"],
        "allowed_paths": task["allowed_paths"],
        "forbidden_paths": ["oracle/", "hidden/", ".harness/"],
        "relevant_paths": ["app/main.py", "schema.sql", "app/templates/", "app/db.py"],
        "test_targets": ["tests/"],
    }


def parse_events(lines: list[str]) -> tuple[list[dict], dict | None]:
    events = []
    error = None
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "error":
            error = ((event.get("error") or {}).get("data") or {}).get("message") or str(event.get("error"))
            continue
        events.append(event)
    return events, error


def summarize_events(events: list[dict], workspace: Path, gate_enabled: bool = False) -> dict:
    steps = []
    tool_calls: Counter[str] = Counter()
    files_read: list[str] = []
    gate_calls = 0
    tokens = Counter()
    cost = 0.0
    for event in events:
        kind = event.get("type")
        part = event.get("part") or {}
        if kind == "step_finish":
            step_tokens = part.get("tokens") or {}
            steps.append({
                "kind": "step",
                "reason": part.get("reason"),
                "tokens": step_tokens,
                "cost": part.get("cost"),
            })
            for key in ("total", "input", "output", "reasoning"):
                tokens[key] += int(step_tokens.get(key) or 0)
            cache = step_tokens.get("cache") or {}
            tokens["cache_read"] += int(cache.get("read") or 0)
            tokens["cache_write"] += int(cache.get("write") or 0)
            cost += float(part.get("cost") or 0.0)
        elif kind == "tool_use":
            tool = str(part.get("tool") or "unknown")
            tool_calls[tool] += 1
            state = part.get("state") or {}
            payload = state.get("input") or {}
            raw_path = payload.get("filePath") or payload.get("path")
            if tool in READ_TOOLS and isinstance(raw_path, str):
                try:
                    relative = Path(raw_path).resolve().relative_to(workspace.resolve()).as_posix()
                except (ValueError, OSError):
                    relative = Path(raw_path).as_posix()
                if relative not in files_read:
                    files_read.append(relative)
            command = payload.get("command")
            if (gate_enabled and tool == "bash" and isinstance(command, str)
                    and "compliance_check.py" in command):
                gate_calls += 1
    return {
        "steps": steps,
        "tool_calls": tool_calls,
        "files_read": files_read,
        "gate_calls": gate_calls,
        "tokens": {
            "total_tokens": tokens["total"],
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "reasoning_tokens": tokens["reasoning"],
            "cache_read_tokens": tokens["cache_read"],
            "cache_write_tokens": tokens["cache_write"],
        } if tokens["total"] else None,
        "cost": round(cost, 6),
    }


def build_environment(sandbox: Path, scope: dict, workspace: Path, auth_file: Path,
                      model: str, arm: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(prepare_sandbox(sandbox, model, auth_file))
    write_arm_config(sandbox, arm, model)
    # The gate CLI imports the engine from a bundle that carries src/harness and the
    # pack only. Exporting the repository root let the agent read the hidden tests
    # and the oracle rules with a shell.
    if ARMS[arm].gate:
        bundle = prepare_harness_bundle(sandbox / "harness-bundle")
        env["VIBECODING_HARNESS_ROOT"] = str(bundle)
    else:
        env.pop("VIBECODING_HARNESS_ROOT", None)
    env["VIBECODING_WORKSPACE"] = str(workspace)
    env["VIBECODING_SCOPE"] = json.dumps(scope, ensure_ascii=False)
    env.pop("OPENCODE_CONFIG", None)
    return env


def _status(events: list[dict], code: int | None, error: str | None, timed_out: bool) -> str:
    reasons = [(event.get("part") or {}).get("reason") for event in events
               if event.get("type") == "step_finish"]
    if timed_out:
        return "timeout"
    if error or (code not in (0, None)):
        return "error"
    if reasons and reasons[-1] in ("stop", "end_turn"):
        return "finished"
    if reasons:
        return "incomplete"
    return "no_steps"


PROVIDER_FATAL_MARKERS = (
    "usage limit reached",
    "invalid credential",
    "AI_APICallError",
    "AI_RetryError",
    "401 Unauthorized",
)


def _kill_tree(process: subprocess.Popen) -> None:
    """Kill the CLI and the server it spawns so no orphan keeps the socket open."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)],
                           capture_output=True, timeout=15)
        else:
            process.kill()
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def _fatal_provider_line(stderr_tail: str) -> str | None:
    lowered = stderr_tail.lower()
    for marker in PROVIDER_FATAL_MARKERS:
        if marker.lower() in lowered:
            for line in reversed(stderr_tail.splitlines()):
                if marker.lower() in line.lower():
                    return line.strip()[:500]
    return None


def _run_watched(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict:
    """Run the CLI while watching stderr for fatal provider errors.

    A dead provider (quota exhausted, invalid credential) makes the OpenCode CLI retry and hang
    without emitting any JSON event, which used to surface as a clean 900s timeout with zero
    signal. Aborting on the first fatal provider line keeps the failure attributable.
    """
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace", env=env,
                               cwd=str(cwd))
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def pump(pipe, sink: list[str]) -> None:
        try:
            for line in pipe:
                sink.append(line)
        finally:
            pipe.close()

    readers = [
        threading.Thread(target=pump, args=(process.stdout, stdout_lines), daemon=True),
        threading.Thread(target=pump, args=(process.stderr, stderr_lines), daemon=True),
    ]
    for reader in readers:
        reader.start()
    started = time.perf_counter()
    timed_out = False
    fatal = None
    while True:
        if process.poll() is not None:
            break
        fatal = _fatal_provider_line("".join(stderr_lines[-40:]))
        if fatal:
            _kill_tree(process)
            break
        if time.perf_counter() - started >= timeout:
            timed_out = True
            _kill_tree(process)
            break
        time.sleep(0.25)
    for reader in readers:
        reader.join(timeout=5)
    return {
        "stdout": "".join(stdout_lines),
        "stderr": "".join(stderr_lines),
        "exit_code": None if (timed_out or fatal) else process.returncode,
        "timed_out": timed_out,
        "fatal": fatal,
    }


def _invoke(workspace: Path, prompt: str, model: str, timeout: int, env: dict[str, str],
            session_id: str | None = None) -> dict:
    command = [
        opencode_binary(), "run", prompt,
        "--model", model, "--format", "json", "--auto", "--pure", "--print-logs",
        "--dir", str(workspace), "--title", workspace.name,
    ]
    if session_id:
        command += ["--session", session_id]
    started = time.perf_counter()
    result = _run_watched(command, workspace, env, timeout)
    elapsed = round(time.perf_counter() - started, 2)
    events, error = parse_events(result["stdout"].splitlines())
    if result["fatal"]:
        error = result["fatal"]
    found_id = next((event.get("sessionID") for event in events if event.get("sessionID")), None)
    return {"events": events, "error": error, "exit_code": result["exit_code"],
            "timed_out": result["timed_out"], "elapsed": elapsed,
            "session_id": found_id or session_id, "stderr": result["stderr"],
            "stdout": result["stdout"],
            "status": _status(events, result["exit_code"], error, result["timed_out"])}



FEEDBACK_CONTROLS = {
    "privacy.cwe_532": ("CORE-CHECK-002", "CL-DATAPROT-001"),
    "privacy.api_exposure": ("CORE-CHECK-002",),
    "privacy.payment_data_storage": ("ECOM-CHECK-003",),
    "privacy.customer_hard_delete": ("CORE-CHECK-006", "CORE-CHECK-013"),
}


def _catalog_label(policy_id: str) -> str | None:
    try:
        from src.harness.catalog import load_catalog
        control = load_catalog(ROOT / ".harness" / "packs" / "catalog.v2.json").control(policy_id)
    except Exception:
        return None
    return f"control {control.id}: {control.title} | " + "; ".join(control.framework_labels())


def format_gate_feedback(findings: list) -> str:
    from src.harness.catalog import load_catalog
    from src.harness.precommit import DEFAULT_PACK

    controls = {control.id: control for control in load_catalog(DEFAULT_PACK).controls}
    lines = ["La compuerta de cumplimiento encontró violaciones en el cambio actual:", ""]
    for finding in findings:
        if finding.status != "VIOLATION":
            continue
        lines.append(f"- [{finding.severity}] {finding.policy_id} en {finding.file}:{finding.line}: "
                     f"{finding.message}")
        if finding.evidence:
            lines.append(f"  evidencia: {finding.evidence}")
        if finding.remediation_advice:
            lines.append(f"  corrección: {finding.remediation_advice}")
        for control_id in FEEDBACK_CONTROLS.get(finding.policy_id, ()):
            control = controls.get(control_id)
            if control:
                lines.append(f"  control {control_id}: {control.title}")
        catalog_label = _catalog_label(finding.policy_id)
        if catalog_label:
            lines.append(f"  {catalog_label}")
    lines += ["", "Corregí estas violaciones y volvé a ejecutar `python compliance_check.py`. "
                  "No termines mientras queden violaciones."]
    return "\n".join(lines)


def run_opencode(workspace: Path, prompt: str, model: str, timeout: int,
                 env: dict[str, str], gate_enabled: bool = False,
                 gate_check=None, max_rounds: int = 3, enforce: bool = True) -> dict:
    started = time.perf_counter()
    first = _invoke(workspace, prompt, model, timeout, env)
    all_events = list(first["events"])
    last = first
    gate_rounds = 0
    gate_unresolved = 0
    feedback_messages: list[str] = []
    if gate_enabled and enforce and gate_check is not None and first["status"] == "finished":
        for _ in range(max_rounds):
            feedback, violations = gate_check()
            gate_unresolved = violations
            if not feedback:
                break
            feedback_messages.append(feedback)
            follow = _invoke(workspace, feedback, model, timeout, env, first["session_id"])
            all_events.extend(follow["events"])
            last = follow
            gate_rounds += 1
            if follow["status"] != "finished":
                break
        _, gate_unresolved = gate_check()
    stats = summarize_events(all_events, workspace, gate_enabled)
    status = last["status"]
    return {
        "status": status,
        "error": last["error"],
        "exit_code": last["exit_code"],
        "timed_out": last["timed_out"],
        "cycle_time_s": round(time.perf_counter() - started, 2),
        "steps": stats["steps"],
        "tool_calls_by_name": dict(stats["tool_calls"]),
        "files_read": stats["files_read"],
        "gate_calls": stats["gate_calls"],
        "gate_rounds": gate_rounds,
        "gate_unresolved": gate_unresolved,
        "feedback_messages": feedback_messages,
        "tokens": stats["tokens"],
        "cost": stats["cost"],
        "stderr_tail": "" if status in ("finished", "incomplete") else (last["stderr"] or "")[-2000:],
    }


def summarize_run(workspace: Path, scope: dict, live: dict) -> dict:
    changes = changed_files(workspace)
    findings = evaluate_policies(workspace, list(changes), scope)
    counts = classify_findings(findings)
    return {
        "status": live["status"], "error": live.get("error"),
        "efficiency": {
            "cycle_time_s": live.get("cycle_time_s"),
            "latency_ms": round((live.get("cycle_time_s") or 0) * 1000),
            "rounds": len(live.get("steps") or []),
            "tool_calls": sum((live.get("tool_calls_by_name") or {}).values()),
            "turns": len(live.get("steps") or []),
            "usage_reported": bool(live.get("tokens")),
            "tokens": live.get("tokens"),
            "cost_usd": live.get("cost"),
        },
        "quality": {
            "tests": run_pytest(workspace, scope.get("test_targets", ["tests/"])),
            "files_changed": len(changes),
            "lines_added": sum(added for added, _ in changes.values()),
            "lines_deleted": sum(deleted for _, deleted in changes.values()),
            "unrequested_changes": counts["scope"], "defects_introduced": None,
        },
        "governance": {
            "policy_violations": counts["policy"], "scope_violations": counts["scope"],
            "privacy_findings": counts["privacy"],
            "potential_risks_detected": count_potential_risks(findings),
            "architecture_violations": None,
            "compliance_score": compliance_score(findings),
            "gate_rounds": live.get("gate_rounds", 0),
            "gate_calls": live.get("gate_calls", 0),
            "gate_unresolved": live.get("gate_unresolved", 0),
            "findings": [f.model_dump(include={"policy_id", "severity", "status", "file", "line"})
                         for f in findings],
        },
        "context": {
            "files_read": live.get("files_read") or [],
            "files_read_count": len(live.get("files_read") or []),
            "symbols_retrieved": None, "context_tokens": None,
            "relevance_ratio": context_relevance(live.get("files_read") or [],
                                                 scope.get("relevant_paths", [])),
        },
        "review": {
            "required_corrections": None,
            "manual_changes_after": None, "human_review_minutes": None,
        },
        "rounds": live.get("steps") or [],
        "tool_calls_by_name": live.get("tool_calls_by_name") or {},
        "changed_files": {path: list(lines) for path, lines in changes.items()},
    }


def run(args) -> dict:
    task = task_by_id(load_manifest(), args.task)
    workspace = Path(args.workspace_root) / f"{args.task}-{args.arm}"
    prepare_workspace(args.arm, task, workspace)
    scope = scope_for(task)
    if args.dry_run:
        allowed = [name for name, value in skill_permissions(args.arm).items() if value == "allow"]
        return {"task": task["id"], "arm": args.arm, "workspace": str(workspace),
                "dry_run": True, "scope": scope, "skills": sorted(allowed)}
    sandbox = Path(args.sandbox_root) / f"{args.task}-{args.arm}"
    if sandbox.exists():
        shutil.rmtree(sandbox, ignore_errors=True)
    sandbox.mkdir(parents=True, exist_ok=True)
    env = build_environment(sandbox, scope, workspace, Path(args.auth_file), args.model, args.arm)
    prompt = (workspace / "TASK.md").read_text(encoding="utf-8")

    def gate_check() -> tuple[str, int]:
        findings = evaluate_policies(workspace, list(changed_files(workspace)), scope)
        violations = [finding for finding in findings if finding.status == "VIOLATION"]
        return (format_gate_feedback(violations) if violations else "", len(violations))

    live = run_opencode(workspace, prompt, args.model, args.timeout, env,
                        gate_enabled=ARMS[args.arm].gate,
                        gate_check=gate_check, max_rounds=args.max_rounds,
                        enforce=ARMS[args.arm].enforce)
    report = {"task": task["id"], "arm": args.arm, "workspace": str(workspace),
              "model": args.model, "runner": "opencode",
              "live": {k: v for k, v in live.items() if k not in ("steps", "feedback_messages")},
              "summary": summarize_run(workspace, scope, live),
              "hidden_and_oracle": evaluate(workspace, task),
              "evidence": run_evidence(workspace, task)}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.keep_sandbox:
        shutil.rmtree(sandbox, ignore_errors=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/tasks/opencode_run.py")
    parser.add_argument("--task", required=True)
    parser.add_argument("--arm", choices=sorted(ARMS), required=True)
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--sandbox-root",
                        default=str(Path(tempfile.gettempdir()) / "t7-opencode-sandbox"))
    parser.add_argument("--auth-file", default=str(DEFAULT_AUTH))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--out", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-sandbox", action="store_true")
    args = parser.parse_args()
    if args.model.strip().lower() == "auto":
        raise SystemExit("'auto' invalidates the comparison; use a fixed model id")
    if not args.out:
        args.out = f"qa_reports/pilot-opencode/{args.task}_{args.arm}.json"
    report = run(args)
    print(json.dumps({k: report[k] for k in report if k not in ("live", "summary")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
