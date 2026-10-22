"""Brazos del piloto con Cursor SDK y preparación de sus workspaces aislados.

Cada brazo recibe una copia de la aplicación clínica fuera del repositorio. El motor de
cumplimiento (`src/harness`) nunca se copia: en el brazo `harness_compliance` se expone
como herramienta del runner, de modo que ningún brazo puede leer sus reglas.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

APP_PATHS = ("src/backend", "src/database", "tests/demo", "pytest.ini", "requirements.txt")
PIPELINE_SKILLS = (
    "01-prd", "02-architecture", "03-data-modeling", "04-api-design", "05-backend",
    "06-frontend", "07-auth", "08-testing", "09-cicd", "10-deployment",
    "11-observability", "12-documentation",
)
COMPLIANCE_SKILLS = ("compliance-dev", "compliance-audit", "compliance-patch")
PACK_REL = ".harness/packs/cl-ley-21719.json"
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.db", ".pytest_cache")
WORKSPACE_GITIGNORE = "__pycache__/\n*.pyc\n.pytest_cache/\n*.db\n"
# Normaliza EOL en el index para que reescrituras CRLF/LF no cuenten como líneas modificadas.
WORKSPACE_GITATTRIBUTES = "* text=auto\n"

HARNESS_RULE_HEADER = """---
description: VibeCoding harness always-on rules
alwaysApply: true
---

"""

COMPLIANCE_GATE_RULE = """---
description: Compuerta de cumplimiento normativo (Ley N° 21.719 / CWE-532)
alwaysApply: true
---

# Compuerta de cumplimiento

Antes de terminar cualquier tarea que modifique código, llama a la herramienta
`compliance_check` con la lista de archivos que cambiaste (rutas relativas a la raíz).
Si informa infracciones, corrígelas y vuelve a llamarla. No termines mientras
`compliance_check` reporte infracciones.
"""


@dataclass(frozen=True)
class ArmConfig:
    name: str
    harness_files: bool
    compliance_tool: bool
    setting_sources: tuple[str, ...] | None


ARMS: dict[str, ArmConfig] = {
    "baseline": ArmConfig("baseline", harness_files=False, compliance_tool=False, setting_sources=None),
    "harness": ArmConfig("harness", harness_files=True, compliance_tool=False, setting_sources=("project",)),
    "harness_compliance": ArmConfig(
        "harness_compliance", harness_files=True, compliance_tool=True, setting_sources=("project",)
    ),
}


def prepare_workspace(repo_root: Path, arm: str, dest: Path) -> Path:
    """Crea el workspace del brazo en `dest` con un commit base limpio y devuelve su ruta."""
    config = ARMS[arm]
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for rel in APP_PATHS:
        _copy(repo_root / rel, dest / rel)
    if config.harness_files:
        _write_harness_files(repo_root, dest)
    if config.compliance_tool:
        for skill in COMPLIANCE_SKILLS:
            _copy(repo_root / ".agents/skills" / skill, dest / ".cursor/skills" / skill)
        _copy(repo_root / PACK_REL, dest / PACK_REL)
        _write_text(dest / ".cursor/rules/compliance-gate.mdc", COMPLIANCE_GATE_RULE)
    _write_text(dest / ".gitignore", WORKSPACE_GITIGNORE)
    _write_text(dest / ".gitattributes", WORKSPACE_GITATTRIBUTES)
    _commit_baseline(dest)
    return dest


def _copy(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, ignore=COPY_IGNORE)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _write_harness_files(repo_root: Path, dest: Path) -> None:
    rules = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    _write_text(dest / ".cursor/rules/vibecoding-harness.mdc", HARNESS_RULE_HEADER + rules)
    for skill in PIPELINE_SKILLS:
        _copy(repo_root / ".agents/skills" / skill, dest / ".cursor/skills" / skill)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit_baseline(ws: Path) -> None:
    for args in (
        ["init", "-q"],
        ["config", "core.autocrlf", "false"],
        ["add", "-A"],
        ["-c", "user.name=pilot", "-c", "user.email=pilot@local", "commit", "-qm", "baseline"],
    ):
        subprocess.run(["git", *args], cwd=ws, check=True, capture_output=True)
