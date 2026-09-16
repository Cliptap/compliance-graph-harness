"""runner.py

Orquesta el experimento A/B: para cada tarea, invoca al LLM DOS veces
(una con system prompt que incluye las skills/reglas del proyecto, otra sin)
y mide el código generado.

Salida: qa_reports/results.json con la estructura:

    {
      "metadata": {...},
      "runs": [
        {
          "task_id": "01",
          "task_name": "...",
          "mode": "with_skills" | "without_skills",
          "metrics": FileMetrics...,
          "cycle_time_seconds": float,
          "llm_tokens": {"input": N, "output": M, "cost": float},
          "files_created": [...]
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_NPM_BIN = Path(os.environ.get("APPDATA", str(Path.home()))) / "npm"
if _NPM_BIN.exists():
    _npm_bin_str = str(_NPM_BIN)
    current = os.environ.get("PATH", "")
    if _npm_bin_str not in current:
        os.environ["PATH"] = _npm_bin_str + os.pathsep + current

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from harness.eval.metrics_collector import compute_run_metrics, save_metrics, FileMetrics  # noqa: E402

DEFAULT_MODEL = "opencode-go/minimax-m3"

SKILLS_SYSTEM_PROMPT = """\
Eres un agente de desarrollo de software senior que sigue ESTRICTAMENTE estas reglas:

1. ANTES de escribir cualquier código, debes hacer preguntas de clarificación si el
   requerimiento es ambiguo. NO asumas.
2. SOLO implementa lo que está explícitamente solicitado. NO agregues features
   "por si acaso" (sin dark mode, sin admin panel, sin auth extra, sin tests extra,
   sin Docker, sin CI/CD, sin configuración innecesaria).
3. KISS: la solución más simple que funcione. Funciones < 50 líneas, < 4 parámetros.
4. NO inventes librerías, APIs, ni endpoints. Si no estás 100% seguro, pregunta.
5. Sin números mágicos, sin abstracciones prematuras, sin herencia múltiple,
   sin ABC, sin jerarquías de validadores, sin Factory pattern sin justificación.
6. Type hints en funciones públicas. NO docstrings redundantes.
7. SI la tarea incluye restricciones explícitas ("NO crear X", "SÍ usar Y"),
   las respetas al pie de la letra.

Cuando termines, lista los archivos creados/modificados con sus paths absolutos
en una línea que comience con: FILES_CREATED:
"""

LIBRE_SYSTEM_PROMPT = """\
Eres un asistente de desarrollo. Resuelve la tarea del usuario de la mejor
forma posible. Sé prolijo, agregá lo que consideres necesario para que el
código sea robusto y production-ready. Usá las prácticas que consideres
apropiadas (clases, herencia, abstracciones, factory, etc.) sin restricciones.
No preguntes, solo entregá.
"""


@dataclass
class RunResult:
    task_id: str
    task_name: str
    mode: str
    files_created: list[str] = field(default_factory=list)
    file_metrics: list[dict] = field(default_factory=list)
    cycle_time_seconds: float = 0.0
    thrashing_index: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_cost_usd: float = 0.0
    raw_events_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _build_prompt(task_path: Path) -> str:
    body = task_path.read_text(encoding="utf-8")
    return f"""\
Resolver la siguiente tarea de desarrollo. Entregar el código completo,
listo para ejecutarse.

=== TAREA ===
{body}
=== FIN TAREA ===

INSTRUCCION OPERATIVA OBLIGATORIA: para crear o modificar archivos, USA
EXCLUSIVAMENTE la tool `write` (o `edit` para archivos existentes). NO
respondas con bloques de codigo en prosa. Cada archivo que declares en
FILES_CREATED debe existir fisicamente en disco al final de la sesion,
creado via tool call. Si respondes con bloques ```python ...``` sin
invocar la tool, el archivo no sera persistido y la corrida se
considerara fallida.

Cuando termines, listá los archivos creados/modificados con paths absolutos
en una línea que comience con: FILES_CREATED: <path1>, <path2>, ...
"""


def _parse_opencode_events(stdout: str) -> tuple[str, dict[str, str], list[str], dict]:
    """Extrae de los eventos JSON:
      - el texto conversacional completo
      - dict {filePath: content} de TODAS las tool_use 'write' (fuente de verdad del codigo generado)
      - lista de FILES_CREATED declarados en el texto (solo para reporte)
      - tokens y costo agregados
    """
    text_parts: list[str] = []
    declared_files: list[str] = []
    written_files: dict[str, str] = {}
    tokens = {"input": 0, "output": 0, "cost": 0.0}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = ev.get("type")
        if etype == "text":
            part = ev.get("part", {})
            t = part.get("text", "")
            if t:
                text_parts.append(t)
                if "FILES_CREATED:" in t:
                    marker_idx = t.find("FILES_CREATED:")
                    after = t[marker_idx + len("FILES_CREATED:"):]
                    for raw in after.split("\n")[0].split(","):
                        p = raw.strip().strip("`").strip()
                        if p and (p.endswith(".py") or "/" in p):
                            declared_files.append(p)
        elif etype == "tool_use":
            part = ev.get("part", {})
            tool_name = part.get("tool", "")
            if tool_name == "write":
                state = part.get("state", {})
                inp = state.get("input", {}) if isinstance(state, dict) else {}
                fp = inp.get("filePath", "")
                content = inp.get("content", "")
                if fp and content:
                    written_files[fp] = content
        elif etype == "step_finish":
            part = ev.get("part", {})
            t = part.get("tokens", {})
            tokens["input"] += t.get("input", 0)
            tokens["output"] += t.get("output", 0)
            tokens["cost"] += part.get("cost", 0.0)
    final_text = "\n".join(text_parts)
    return final_text, written_files, declared_files, tokens


def _invoke_llm(
    project_dir: Path,
    task_prompt: str,
    system_prompt: str,
    model: str,
    timeout_seconds: int,
    agent_name: str = "build",
) -> tuple[str, list[str], dict, float, int]:
    """Llama a opencode run en subprocess. Devuelve (texto, files, tokens, cycle_time, event_count).

    El system_prompt se inyecta vía el frontmatter del agent (.opencode/agents/*.md),
    no se prepende al user prompt.
    """
    prompt_file = project_dir / f"_prompt_{int(time.time())}.txt"
    prompt_file.write_text(task_prompt, encoding="utf-8")
    cmd_str = (
        f'opencode run --model "{model}" --format json '
        f'--title "eval-{int(time.time())}" --auto '
        f'--agent "{agent_name}" "@{prompt_file.name}"'
    )
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd_str,
        cwd=str(project_dir),
        capture_output=True,
        timeout=timeout_seconds,
        shell=True,
    )
    cycle = time.perf_counter() - t0
    stdout_text = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
    stderr_text = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
    try:
        prompt_file.unlink()
    except OSError:
        pass
    if proc.returncode != 0 and not stdout_text:
        raise RuntimeError(f"opencode run falló (rc={proc.returncode}): {stderr_text[:500]}")
    text, written_files, declared_files, tokens = _parse_opencode_events(stdout_text)
    return text, written_files, declared_files, tokens, cycle, stdout_text.count("\n")


def _hash_files(files: list[Path]) -> dict[str, str]:
    h = {}
    for f in files:
        if f.exists() and f.is_file():
            h[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    return h


def _prepare_workspace(project_root: Path, mode: str, task_id: str) -> Path:
    """Crea una copia temporal del proyecto para una combinacion (mode, task_id).

    El workspace es por (mode, task_id) y no por mode, para evitar que
    corridas sucesivas de distintas tareas compartan directorio y los
    archivos de T03 contaminen a T01 (o viceversa).
    """
    ws = project_root / "qa_reports" / "_workspace" / f"{mode}_t{task_id}"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    ignore = shutil.ignore_patterns(
        "qa_reports", ".venv", "node_modules", "__pycache__",
        ".git", ".pytest_cache", "vibedb.db", "*.pyc",
    )
    shutil.copytree(project_root, ws / "project", ignore=ignore)
    if mode == "without_skills":
        oc = ws / "project" / ".opencode"
        if oc.exists():
            shutil.rmtree(oc)
        ag = ws / "project" / "AGENTS.md"
        if ag.exists():
            ag.rename(ag.with_suffix(".md.disabled"))
    return ws / "project"


def _persist_written_files(
    written_files: dict[str, str], declared_files: list[str], workspace: Path,
) -> list[Path]:
    """Escribe en disco el contenido REAL de cada tool_use 'write' que emitió el LLM.

    Args:
        written_files: dict {filePath_abs: content} extraído de eventos tool_use.
        declared_files: lista de paths que el LLM mencionó en 'FILES_CREATED:' (solo
            para reportar en metrics; no se usan para escribir).
        workspace: raíz del proyecto clonado en modo A/B.
    """
    import re
    written: list[Path] = []
    seen: set[Path] = set()
    for fp_str, content in written_files.items():
        target = Path(fp_str)
        if not target.is_absolute():
            target = workspace / fp_str
        if workspace not in target.parents and target != workspace:
            continue
        try:
            rel = target.relative_to(workspace)
        except ValueError:
            rel = Path(fp_str)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if target not in seen:
            written.append(target)
            seen.add(target)
    if not written and declared_files:
        for rel_path in declared_files:
            target = Path(rel_path)
            if not target.is_absolute():
                target = workspace / rel_path
            try:
                rel = target.relative_to(workspace)
            except ValueError:
                rel = Path(rel_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# LLM declaro FILES_CREATED pero no escribio el archivo via tool\n",
                              encoding="utf-8")
            if target not in seen:
                written.append(target)
                seen.add(target)
    return written


def run_single(
    task_path: Path,
    project_root: Path,
    mode: str,
    model: str,
    timeout_seconds: int,
) -> RunResult:
    task_id = task_path.stem.split("_")[1]
    task_name = "_".join(task_path.stem.split("_")[2:])
    system_prompt = SKILLS_SYSTEM_PROMPT if mode == "with_skills" else LIBRE_SYSTEM_PROMPT
    agent_name = "eval-con-skills" if mode == "with_skills" else "eval-libre"
    workspace = _prepare_workspace(project_root, mode, task_id)

    task_prompt = _build_prompt(task_path)
    try:
        text, written_files, declared_files, tokens, cycle, ev_count = _invoke_llm(
            workspace, task_prompt, system_prompt, model, timeout_seconds, agent_name,
        )
    except subprocess.TimeoutExpired:
        return RunResult(task_id=task_id, task_name=task_name, mode=mode, error="timeout")
    except Exception as e:
        return RunResult(task_id=task_id, task_name=task_name, mode=mode, error=str(e)[:300])

    written = _persist_written_files(written_files, declared_files, workspace)

    file_metrics = []
    for f in written:
        if f.suffix == ".py":
            from harness.eval.metrics_collector import analyze_file_metrics
            fm = analyze_file_metrics(f, workspace)
            file_metrics.append(fm.__dict__)

    hashes_now = _hash_files(written)
    files_created_rel: list[str] = []
    for w in written:
        try:
            files_created_rel.append(str(w.relative_to(workspace)))
        except ValueError:
            files_created_rel.append(str(w))
    run = RunResult(
        task_id=task_id,
        task_name=task_name,
        mode=mode,
        files_created=files_created_rel,
        file_metrics=file_metrics,
        cycle_time_seconds=cycle,
        thrashing_index=0,
        llm_input_tokens=tokens["input"],
        llm_output_tokens=tokens["output"],
        llm_cost_usd=round(tokens["cost"], 6),
        raw_events_count=ev_count,
    )
    return run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=300, help="segundos por llamada")
    parser.add_argument("--tasks-dir", default="harness/eval/tasks")
    parser.add_argument("--output", default="qa_reports/results.json")
    args = parser.parse_args()

    project_root = Path(".").resolve()
    tasks_dir = project_root / args.tasks_dir
    out_path = project_root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    task_files = sorted([p for p in tasks_dir.glob("task_*.md") if p.stem.split("_")[1].isdigit()])
    if not task_files:
        print(f"ERROR: no se encontraron tareas en {tasks_dir}")
        return 1

    print(f"[runner] modelo={args.model}  tareas={len(task_files)}  modos=2  timeout={args.timeout}s")
    results: list[RunResult] = []
    for task in task_files:
        for mode in ("without_skills", "with_skills"):
            print(f"[runner] {task.name}  modo={mode}  ...", flush=True)
            r = run_single(task, project_root, mode, args.model, args.timeout)
            tag = "OK" if not r.error else f"ERR: {r.error}"
            print(f"  -> {tag}  cycle={r.cycle_time_seconds:.1f}s  files={len(r.files_created)}  "
                  f"cost=${r.llm_cost_usd:.4f}")
            results.append(r)

    payload = {
        "metadata": {
            "model": args.model,
            "tasks": [t.name for t in task_files],
            "modes": ["without_skills", "with_skills"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "runs": [r.to_dict() for r in results],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[runner] resultados -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
