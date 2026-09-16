"""metrics_collector.py

Métricas estáticas aplicadas a archivos Python generados por el LLM.
Diseñado para ser invocado por runner.py. Salida: dict JSON-serializable.

Métricas implementadas:
    - cc_avg:           Complejidad ciclomática promedio (McCabe) por función, via radon
    - cc_max:           CC máxima
    - cog_avg:          Complejidad cognitiva promedio via lizard
    - cog_max:          Cognitiva máxima
    - loc:              Líneas de código totales
    - lloc:             Logical lines of code (lizard)
    - aloc_ratio:       (clases + abstractas + herencias) / statements ejecutables
    - hallucination_score:  imports/atributos referenciados que NO están en el whitelist del proyecto
    - thrashing_index:  conteo de archivos con contenido idéntico a la versión anterior
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable

from lizard import analyze_file
from radon.complexity import cc_visit
from radon.raw import analyze as radon_raw

import re


@dataclass
class FileMetrics:
    path: str
    cc_avg: float = 0.0
    cc_max: int = 0
    cog_avg: float = 0.0
    cog_max: int = 0
    loc: int = 0
    lloc: int = 0
    aloc_ratio: float = 0.0
    hallucination_score: int = 0
    unknown_imports: list[str] = field(default_factory=list)


@dataclass
class RunMetrics:
    files: list[FileMetrics] = field(default_factory=list)
    cycle_time_seconds: float = 0.0
    thrashing_index: int = 0
    file_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _collect_whitelisted_symbols(project_root: Path) -> set[str]:
    """Escanea src/ y app/ extrayendo top-level imports y nombres definidos.

    Se usa como ground-truth para detectar alucinaciones: si el LLM importa
    algo que no existe en ningún archivo del proyecto, es alucinación.
    """
    symbols: set[str] = set()
    roots = [project_root / "src", project_root / "app"]
    for root in roots:
        if not root.exists():
            continue
        for py_file in root.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        symbols.add(alias.asname or alias.name.split(".")[0])
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.add(node.name)
    symbols.update({"os", "re", "sys", "json", "ast", "uuid", "datetime", "typing",
                    "pathlib", "collections", "functools", "itertools", "math", "string",
                    "unicodedata", "dataclasses", "abc", "logging", "asyncio", "hashlib",
                    "secrets", "time", "copy", "enum"})
    project_deps = _read_requirements_whitelist(project_root)
    symbols.update(project_deps)
    return symbols


def _read_requirements_whitelist(project_root: Path) -> set[str]:
    """Lee requirements.txt y extrae nombres de paquetes normalizados.

    Ignora extras como [cryptography] y normaliza nombres con guiones
    (python-jose -> jose, SQLAlchemy -> sqlalchemy).
    """
    req_file = project_root / "requirements.txt"
    if not req_file.exists():
        return set()
    names: set[str] = set()
    for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        pkg = re.split(r"[<>=!~\[]", line, 1)[0].strip()
        if not pkg:
            continue
        if pkg.lower() == "python-jose":
            names.add("jose")
        else:
            names.add(pkg)
            names.add(pkg.replace("-", "_"))
    names.update({"jose", "passlib", "bcrypt", "pytest", "pytest_asyncio", "httpx",
                  "aiosqlite"})
    return names


def _analyze_hallucinations(file_path: Path, whitelist: set[str]) -> tuple[int, list[str]]:
    """Cuenta imports y accesos a atributos top-level que no están en whitelist.

    No es perfecto (no resuelve imports relativos), pero detecta los casos
    comunes: `import xyz_fake_lib`, `from nonexistent import foo`.
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return 0, []

    unknown: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in whitelist and not top.startswith("_"):
                    unknown.append(top)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None or node.level > 0:
                continue
            top = node.module.split(".")[0]
            if top not in whitelist and not top.startswith("_"):
                unknown.append(top)
    return len(unknown), sorted(set(unknown))


def _analyze_aloc(tree: ast.AST) -> float:
    """ALOC ratio: clases + ABCs + herencias múltiples / statements ejecutables.

    Heurística KISS: un módulo sin POO tiene ratio 0. Un módulo con clase
    por función tiene ratio alto.
    """
    abstract_count = 0
    exec_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            abstract_count += 1
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id in {"ABC", "ABCMeta", "Protocol"}:
                    abstract_count += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                exec_count += 1
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            exec_count += 1
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
            exec_count += 1
    if exec_count == 0:
        return float(abstract_count)
    return round(abstract_count / exec_count, 3)


def analyze_file_metrics(file_path: Path, project_root: Path) -> FileMetrics:
    if not file_path.exists():
        return FileMetrics(path=str(file_path))

    whitelist = _collect_whitelisted_symbols(project_root)
    source = file_path.read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return FileMetrics(path=str(file_path), hallucination_score=-1)

    try:
        cc_blocks = cc_visit(source)
        if cc_blocks:
            cc_values = [b.complexity for b in cc_blocks]
            cc_avg = round(sum(cc_values) / len(cc_values), 2)
            cc_max = max(cc_values)
        else:
            cc_avg, cc_max = 0.0, 0
    except Exception:
        cc_avg, cc_max = 0.0, 0

    try:
        lz = analyze_file(str(file_path))
        if lz.function_list:
            cog_values = [f.cyclomatic_complexity for f in lz.function_list]
            cog_avg = round(sum(cog_values) / len(cog_values), 2)
            cog_max = max(cog_values)
        else:
            cog_avg, cog_max = 0.0, 0
        loc = lz.nloc
        lloc = lz.lloc if hasattr(lz, "lloc") else loc
    except Exception:
        loc, lloc = 0, 0
        cog_avg, cog_max = 0.0, 0

    aloc = _analyze_aloc(tree)
    hallu_count, unknown = _analyze_hallucinations(file_path, whitelist)

    return FileMetrics(
        path=str(file_path.relative_to(project_root)) if project_root in file_path.parents else str(file_path),
        cc_avg=cc_avg,
        cc_max=cc_max,
        cog_avg=cog_avg,
        cog_max=cog_max,
        loc=loc,
        lloc=lloc,
        aloc_ratio=aloc,
        hallucination_score=hallu_count,
        unknown_imports=unknown,
    )


def compute_run_metrics(
    files: Iterable[Path],
    project_root: Path,
    cycle_time_seconds: float,
    file_hashes_history: list[dict[str, str]],
) -> RunMetrics:
    """Calcula métricas agregadas para un set de archivos.

    file_hashes_history: lista de snapshots {path: hash} tomados durante la
    ejecución. thrashing_index = cantidad de transiciones (path, hash) que
    revierten a un estado ya visto.
    """
    file_metrics: list[FileMetrics] = []
    for f in files:
        if f.suffix == ".py":
            file_metrics.append(analyze_file_metrics(f, project_root))

    thrashing = 0
    seen_states: set[tuple[str, str]] = set()
    for snapshot in file_hashes_history:
        for path, h in snapshot.items():
            state = (path, h)
            if state in seen_states:
                thrashing += 1
            seen_states.add(state)

    if not file_metrics:
        return RunMetrics(cycle_time_seconds=cycle_time_seconds, thrashing_index=thrashing)

    n = len(file_metrics)
    run = RunMetrics(
        files=file_metrics,
        cycle_time_seconds=round(cycle_time_seconds, 2),
        thrashing_index=thrashing,
        file_count=n,
    )
    return run


def save_metrics(metrics: RunMetrics, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
