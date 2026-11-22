"""Métricas post-hoc del piloto: eventos del agente, diff, políticas, cumplimiento y pruebas."""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import Finding, TaskSpec
from src.harness.policy_engine import PolicyEngine

_PACKS = Path(__file__).resolve().parents[2] / ".harness" / "packs"
CATALOG_PATH = _PACKS / "catalog.full.json"
if not CATALOG_PATH.is_file():
    CATALOG_PATH = _PACKS / "catalog.v2.json"
_CATALOG_ENGINE: CatalogEngine | None = None

READ_TOOLS = {"read", "read_file", "readfile"}
PATH_KEYS = ("path", "file_path", "filePath", "target_file", "file")
SEVERITY_WEIGHTS = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 0}
WARNING_WEIGHT = 1
PYTEST_COUNT = re.compile(r"(\d+) (passed|failed|errors?)")


@dataclass
class EventStats:
    tool_calls: int = 0
    tool_calls_by_name: dict[str, int] = field(default_factory=dict)
    files_read: list[str] = field(default_factory=list)
    turns: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def collect_event_stats(messages: Iterable[Any], workspace: Path | None = None) -> EventStats:
    """Agrega los mensajes del stream: tool calls únicas por `call_id`, archivos leídos y turnos."""
    seen_calls: dict[str, str] = {}
    files_read: list[str] = []
    turns = 0
    for message in messages:
        kind = getattr(message, "type", None)
        if kind == "usage":
            turns += 1
        elif kind == "tool_call":
            call_id = getattr(message, "call_id", None) or str(len(seen_calls))
            name = str(getattr(message, "name", "") or "unknown")
            seen_calls.setdefault(call_id, name)
            path = _tool_path(getattr(message, "args", None), workspace)
            if name.lower() in READ_TOOLS and path and path not in files_read:
                files_read.append(path)
    return EventStats(
        tool_calls=len(seen_calls),
        tool_calls_by_name=dict(Counter(seen_calls.values())),
        files_read=files_read,
        turns=turns,
    )


def _tool_path(args: Any, workspace: Path | None) -> str | None:
    if not isinstance(args, dict):
        return None
    raw = next((args[k] for k in PATH_KEYS if isinstance(args.get(k), str)), None)
    if not raw:
        return None
    path = Path(raw)
    if workspace is not None and path.is_absolute():
        try:
            path = path.resolve().relative_to(workspace.resolve())
        except ValueError:
            pass
    return path.as_posix()


def changed_files(ws: Path) -> dict[str, tuple[int, int]]:
    """Devuelve {ruta: (líneas agregadas, líneas eliminadas)} respecto del commit base."""
    subprocess.run(["git", "add", "-A"], cwd=ws, check=True, capture_output=True)
    out = subprocess.run(
        ["git", "diff", "--cached", "--numstat", "--no-renames", "-z", "HEAD"],
        cwd=ws, check=True, capture_output=True,
    ).stdout.decode("utf-8")
    changes: dict[str, tuple[int, int]] = {}
    for entry in filter(None, out.split("\0")):
        added, deleted, path = entry.split("\t", 2)
        changes[path] = (_to_int(added), _to_int(deleted))
    return changes


def _to_int(value: str) -> int:
    return int(value) if value.isdigit() else 0


def evaluate_policies(ws: Path, changed: Iterable[str], scope: dict[str, Any]) -> list[Finding]:
    """Ejecuta el PolicyEngine del harness sobre los archivos cambiados del workspace."""
    spec = TaskSpec(
        task_id=scope["task_id"],
        goal=scope["goal"],
        allowed_paths=scope.get("allowed_paths", []),
        forbidden_paths=scope.get("forbidden_paths", []),
    )
    modified = {}
    for rel in changed:
        target = ws / rel
        modified[rel] = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
    findings = PolicyEngine().evaluate_changes(spec, modified)
    engine = _catalog_engine()
    if engine is not None:
        findings = _merge_findings(findings, engine.evaluate(spec, modified))
    return findings


def _catalog_engine() -> CatalogEngine | None:
    global _CATALOG_ENGINE
    if _CATALOG_ENGINE is None:
        if not CATALOG_PATH.is_file():
            return None
        _CATALOG_ENGINE = CatalogEngine(load_catalog(CATALOG_PATH), include_legacy=False)
    return _CATALOG_ENGINE


def _merge_findings(left: list[Finding], right: list[Finding]) -> list[Finding]:
    seen = {(f.policy_id, f.file, f.line, f.message) for f in left}
    for finding in right:
        key = (finding.policy_id, finding.file, finding.line, finding.message)
        if key not in seen:
            seen.add(key)
            left.append(finding)
    return left


def compliance_score(findings: Iterable[Finding]) -> float:
    """Puntaje v2: resta la severidad de cada infraccion y un punto por riesgo potencial."""
    penalty = 0
    for f in findings:
        if f.policy_id.startswith("scope."):
            continue
        if f.status == "VIOLATION":
            penalty += SEVERITY_WEIGHTS[f.severity]
        elif f.status == "WARNING":
            penalty += WARNING_WEIGHT
    return float(max(0, 100 - penalty))


def classify_findings(findings: Iterable[Finding]) -> dict[str, int]:
    counts = {"scope": 0, "privacy": 0, "policy": 0}
    for f in findings:
        if f.status != "VIOLATION":
            continue
        prefix = f.policy_id.split(".", 1)[0]
        counts[prefix if prefix in ("scope", "privacy") else "policy"] += 1
    return counts


def count_potential_risks(findings: Iterable[Finding]) -> int:
    """Hallazgos WARNING no relativos al alcance (riesgo potencial, no violacion confirmada)."""
    return sum(1 for f in findings if f.status == "WARNING" and not f.policy_id.startswith("scope."))


def context_relevance(files_read: list[str], relevant: list[str]) -> float | None:
    """Proporción de archivos leídos que pertenecen al conjunto relevante de la tarea."""
    read = set(files_read)
    if not read:
        return None
    return len(read & set(relevant)) / len(read)


def parse_pytest_summary(text: str) -> dict[str, int]:
    counts = {"passed": 0, "failed": 0, "errors": 0}
    for number, label in PYTEST_COUNT.findall(text):
        counts["errors" if label.startswith("error") else label] = int(number)
    return counts


def run_pytest(ws: Path, targets: list[str], timeout: int = 180) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets]
    try:
        res = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": 0, "errors": 0, "exit_code": None, "timeout": True}
    summary = parse_pytest_summary(res.stdout[-2000:])
    return {**summary, "exit_code": res.returncode, "timeout": False}
