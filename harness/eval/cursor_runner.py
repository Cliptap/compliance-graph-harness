"""Runner del piloto A/B/C sobre el Cursor SDK (runtime local, plan del usuario).

Uso:
    python -m harness.eval.cursor_runner --dry-run
    $env:CURSOR_API_KEY="..."; python -m harness.eval.cursor_runner --model composer-2.5

Brazos: `baseline` (solo la app), `harness` (reglas + skills del pipeline en `.cursor/`) y
`harness_compliance` (harness + herramienta `compliance_check` + compuerta de cumplimiento).
Los workspaces se crean fuera del repositorio y el reporte se escribe en `qa_reports/pilot/`.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

from harness.eval.pilot_arms import ARMS, ArmConfig, prepare_workspace
from harness.eval.pilot_metrics import (
    changed_files,
    classify_findings,
    collect_event_stats,
    compliance_score,
    context_relevance,
    evaluate_policies,
    run_pytest,
)
from src.harness.contracts import Finding, ValidationVerdict
from src.harness.validation_engine import ValidationEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASK = "harness/eval/tasks/task_02_appointments_endpoint.md"
DEFAULT_MODEL = "composer-2.5"
TASK_SUFFIX = "\n\nImplementa la tarea directamente en los archivos de este repositorio."
CLARIFICATION_REPLY = (
    "No hay información adicional disponible. Decide con lo especificado en la tarea, "
    "documenta tus suposiciones en un comentario y completa la implementación."
)
NULL_REASONS = {
    "defects_introduced": "requiere suite de aceptación oculta por tarea (pendiente)",
    "architecture_violations": "no existe política de capas en el PolicyEngine (pendiente)",
    "symbols_retrieved": "el SDK no expone símbolos recuperados; requiere el recortador de grafo",
    "context_tokens": "el SDK no separa tokens de contexto; ver hook preCompact (pendiente)",
    "manual_changes_after": "requiere revisión humana posterior",
    "human_review_minutes": "requiere registro manual del revisor",
}


@dataclass(frozen=True)
class RunPlan:
    arm: ArmConfig
    workspace: Path
    prompt: str
    scope: dict[str, Any]


@dataclass(frozen=True)
class LiveSettings:
    model: str
    api_key: str
    max_rounds: int
    timeout_s: int


def build_prompt(task_path: Path) -> str:
    return task_path.read_text(encoding="utf-8") + TASK_SUFFIX


def load_scope(task_path: Path) -> dict[str, Any]:
    return json.loads(task_path.with_suffix(".scope.json").read_text(encoding="utf-8"))


def format_findings_feedback(task_id: str, findings: list[Finding]) -> str:
    verdict = ValidationVerdict(
        task_id=task_id, status="FAIL", findings=findings, tests_passed=True,
        files_evaluated=sorted({f.file for f in findings}),
    )
    return ValidationEngine().format_feedback(verdict)


def compliance_tool(workspace: Path, scope: dict[str, Any]) -> Any:
    from cursor_sdk import CustomTool

    def execute(args: dict[str, Any], _context: Any) -> str:
        files = args.get("files") or list(changed_files(workspace))
        return format_findings_feedback(scope["task_id"], evaluate_policies(workspace, files, scope))

    return CustomTool(
        execute=execute,
        description="Evalúa los archivos cambiados contra las políticas del harness "
                    "(alcance, Ley N° 21.719, CWE-532) y devuelve los hallazgos.",
        input_schema={
            "type": "object",
            "properties": {"files": {"type": "array", "items": {"type": "string"}}},
        },
    )


def run_live(plan: RunPlan, settings: LiveSettings) -> dict[str, Any]:
    from cursor_sdk import Agent, CursorAgentError, LocalAgentOptions

    tools = {"compliance_check": compliance_tool(plan.workspace, plan.scope)} if plan.arm.compliance_tool else None
    sources = list(plan.arm.setting_sources) if plan.arm.setting_sources else None
    local = LocalAgentOptions(cwd=str(plan.workspace), setting_sources=sources, custom_tools=tools)
    rounds: list[dict[str, Any]] = []
    messages: list[Any] = []
    started = time.perf_counter()
    try:
        with Agent.create(model=settings.model, api_key=settings.api_key, local=local) as agent:
            _drive_rounds(agent, plan, settings, rounds, messages)
    except CursorAgentError as err:
        return {"status": "startup_error", "error": f"{err} (retryable={err.is_retryable})"}
    return {"status": rounds[-1]["status"] if rounds else "no_rounds", "error": None,
            "cycle_time_s": round(time.perf_counter() - started, 2),
            "rounds": rounds, "messages": messages}


def _drive_rounds(agent: Any, plan: RunPlan, settings: LiveSettings,
                  rounds: list[dict[str, Any]], messages: list[Any]) -> None:
    message, kind = plan.prompt, "task"
    for _ in range(settings.max_rounds):
        rounds.append(_send(agent, message, kind, settings.timeout_s, messages))
        if rounds[-1]["status"] != "finished":
            return
        changes = changed_files(plan.workspace)
        if not changes:
            message, kind = CLARIFICATION_REPLY, "clarification"
            continue
        if not plan.arm.compliance_tool:
            return
        violations = [f for f in evaluate_policies(plan.workspace, changes, plan.scope)
                      if f.status == "VIOLATION"]
        if not violations:
            return
        message, kind = format_findings_feedback(plan.scope["task_id"], violations), "compliance_feedback"


def _send(agent: Any, message: str, kind: str, timeout_s: int, sink: list[Any]) -> dict[str, Any]:
    started = time.perf_counter()
    run = agent.send(message)
    print(f"    run={run.id} kind={kind}", flush=True)
    timer = threading.Timer(timeout_s, lambda: run.status == "running" and run.cancel())
    timer.start()
    try:
        sink.extend(run.messages())
        result = run.wait()
    finally:
        timer.cancel()
    return {"kind": kind, "run_id": run.id, "status": result.status,
            "duration_ms": result.duration_ms, "wall_s": round(time.perf_counter() - started, 2),
            "usage": _usage_dict(result.usage)}


def _usage_dict(usage: Any) -> dict[str, int] | None:
    if usage is None:
        return None
    return dataclasses.asdict(usage) if dataclasses.is_dataclass(usage) else dict(vars(usage))


def summarize_run(plan: RunPlan, live: dict[str, Any]) -> dict[str, Any]:
    """Calcula las métricas post-hoc del workspace y las combina con los datos del SDK."""
    rounds = live.get("rounds", [])
    changes = changed_files(plan.workspace)
    findings = evaluate_policies(plan.workspace, changes, plan.scope)
    counts = classify_findings(findings)
    stats = collect_event_stats(live.get("messages", []), plan.workspace)
    usages = [r["usage"] for r in rounds if r["usage"]]
    return {
        "status": live["status"], "error": live.get("error"),
        "efficiency": {
            "cycle_time_s": live.get("cycle_time_s"),
            "latency_ms": sum(r["duration_ms"] or 0 for r in rounds),
            "rounds": len(rounds), "tool_calls": stats.tool_calls, "turns": stats.turns,
            "usage_reported": bool(usages), "tokens": _sum_usage(usages),
        },
        "quality": {
            "tests": run_pytest(plan.workspace, plan.scope.get("test_targets", ["tests/"])),
            "files_changed": len(changes),
            "lines_added": sum(a for a, _ in changes.values()),
            "lines_deleted": sum(d for _, d in changes.values()),
            "unrequested_changes": counts["scope"], "defects_introduced": None,
        },
        "governance": {
            "policy_violations": counts["policy"], "scope_violations": counts["scope"],
            "privacy_findings": counts["privacy"], "architecture_violations": None,
            "compliance_score": compliance_score(findings),
            "findings": [f.model_dump(include={"policy_id", "severity", "file", "line"}) for f in findings],
        },
        "context": {
            "files_read": stats.files_read, "files_read_count": len(stats.files_read),
            "symbols_retrieved": None, "context_tokens": None,
            "relevance_ratio": context_relevance(stats.files_read, plan.scope.get("relevant_paths", [])),
        },
        "review": {
            "required_corrections": max(0, len(rounds) - 1),
            "manual_changes_after": None, "human_review_minutes": None,
        },
        "rounds": rounds,
        "tool_calls_by_name": stats.tool_calls_by_name,
        "changed_files": {path: list(lines) for path, lines in changes.items()},
    }


def _sum_usage(usages: list[dict[str, int]]) -> dict[str, int] | None:
    if not usages:
        return None
    keys = {k for u in usages for k in u}
    return {k: sum(u.get(k) or 0 for u in usages) for k in sorted(keys)}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task", default=DEFAULT_TASK, help="tarea .md con su sidecar .scope.json")
    parser.add_argument("--arms", default=",".join(ARMS), help="brazos separados por coma")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="id de modelo fijo (nunca 'auto')")
    parser.add_argument("--reps", type=int, default=1, help="repeticiones por brazo")
    parser.add_argument("--max-rounds", type=int, default=3, help="envíos máximos por corrida")
    parser.add_argument("--timeout", type=int, default=900, help="segundos máximos por envío")
    parser.add_argument("--workspace-root", default=None, help="raíz de workspaces (por defecto, temp del SO)")
    parser.add_argument("--out-dir", default="qa_reports/pilot", help="directorio del reporte JSON")
    parser.add_argument("--dry-run", action="store_true", help="prepara workspaces sin llamar al SDK")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not args.dry_run and not api_key:
        print("ERROR: define CURSOR_API_KEY (Cursor Dashboard -> Integrations) o usa --dry-run.",
              file=sys.stderr)
        return 1
    if args.model == "auto":
        print("ERROR: --model auto invalida la comparación; usa un id fijo.", file=sys.stderr)
        return 1
    stamp = time.strftime("%Y%m%d-%H%M%S")
    task_path = (REPO_ROOT / args.task).resolve()
    ws_root = Path(args.workspace_root or Path(tempfile.gettempdir()) / "vibecoding-pilot" / stamp)
    settings = LiveSettings(args.model, api_key, args.max_rounds, args.timeout)
    runs = []
    for rep in range(1, args.reps + 1):
        for arm in args.arms.split(","):
            runs.append(_execute(arm.strip(), rep, task_path, ws_root, settings, args.dry_run))
    report = {"metadata": _metadata(args, task_path, ws_root), "runs": runs}
    out_dir = REPO_ROOT / args.out_dir if not Path(args.out_dir).is_absolute() else Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"pilot_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"[pilot] reporte -> {out_path}")
    return 0 if all(r["status"] in ("prepared", "finished") for r in runs) else 2


def _execute(arm: str, rep: int, task_path: Path, ws_root: Path,
             settings: LiveSettings, dry_run: bool) -> dict[str, Any]:
    workspace = prepare_workspace(REPO_ROOT, arm, ws_root / f"{arm}_r{rep}")
    plan = RunPlan(ARMS[arm], workspace, build_prompt(task_path), load_scope(task_path))
    header = {"arm": arm, "rep": rep, "workspace": str(workspace)}
    print(f"[pilot] arm={arm} rep={rep} ws={workspace}", flush=True)
    if dry_run:
        return {**header, "status": "prepared"}
    live = run_live(plan, settings)
    if live["status"] == "startup_error":
        return {**header, **live}
    return {**header, **summarize_run(plan, live)}


def _metadata(args: argparse.Namespace, task_path: Path, ws_root: Path) -> dict[str, Any]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                            capture_output=True, text=True).stdout.strip()
    return {
        "dry_run": args.dry_run, "model": args.model, "task": task_path.name,
        "arms": args.arms.split(","), "reps": args.reps, "max_rounds": args.max_rounds,
        "sdk_version": _sdk_version(), "harness_commit": commit,
        "platform": platform.platform(), "python": platform.python_version(),
        "workspace_root": str(ws_root), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "null_reasons": NULL_REASONS,
    }


def _sdk_version() -> str | None:
    try:
        return metadata.version("cursor-sdk")
    except metadata.PackageNotFoundError:
        return None


if __name__ == "__main__":
    sys.exit(main())
