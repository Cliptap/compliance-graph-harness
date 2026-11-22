"""Workspace and sandbox preparation for the OpenCode arms of the T7 task pack.

The OpenCode runner replaces the Cursor SDK runner. The dose arms isolate the
components of the harness:

- ``baseline``: application only.
- ``rules``: application plus ``AGENTS.md``, no skills.
- ``rules_skills``: rules plus the 12 pipeline skills in ``.agents/skills``.
- ``rules_skills_gate``: plus the compliance skills, the normative pack and the
  ``compliance_check.py`` CLI, without the runner forcing a feedback round.
- ``rules_skills_gate_enforced``: plus the external feedback rounds.

``harness`` and ``harness_compliance`` are kept as aliases of
``rules_skills`` and ``rules_skills_gate_enforced`` so the 3-arm reports keep
their meaning.

Global skills under the real home directory are hidden with an explicit
permission config so they cannot leak into any arm.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.eval.pilot_arms import (  # noqa: E402
    COMPLIANCE_SKILLS, PACK_REL, PIPELINE_SKILLS,
)

BASE = ROOT / "experiments" / "supermercado"
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.db", ".pytest_cache", "photos", "data")
GITIGNORE = "__pycache__/\n*.pyc\n.pytest_cache/\n*.db\n"
GITATTRIBUTES = "* text=auto\n"

COMPLIANCE_GATE_INSTRUCTIONS = """
## Compuerta de cumplimiento (OpenCode)

## Protocolo de ejecución obligatorio

Trabajá en este orden y no abras una exploración indefinida:

1. Inspeccioná sólo los archivos necesarios para la tarea y escribí un plan breve.
2. Implementá el camino mínimo solicitado; no agregues UI, abstracciones ni documentación fuera del alcance.
3. Ejecutá una prueba dirigida apenas exista el endpoint o comportamiento principal.
4. Corregí esa prueba, ejecutá la suite completa, luego corré la compuerta.

Si una prueba falla por una razón ajena a la tarea, documentala y terminá con el estado real. No
reescribas la aplicación completa ni sigas explorando después de tener evidencia suficiente.

Antes de terminar cualquier tarea que modifique código, ejecutá en la raíz del repositorio:

```
python compliance_check.py
```

Evalúa los archivos cambiados contra las políticas del harness (Ley N° 21.719, CWE-532, CWE-200,
retención y credenciales) y devuelve los hallazgos. Si informa infracciones, corregilas y volvé a
ejecutarlo. No termines mientras `compliance_check.py` reporte infracciones.

El hook de pre-commit instalado en este repositorio rechaza el commit si queda una fuga con
severidad bloqueante. No uses `git commit --no-verify` para saltarte la compuerta.

Un gate limpio no es prueba de cumplimiento: la compuerta es una red de seguridad, no la política
completa. Aunque no reporte hallazgos, verificá los controles del pack: solicitud de supresión y
conservación antes de borrar, minimización y retención, y enmascaramiento de RUT, correo y teléfono
en respuestas de administración.

## Definición de terminado

Además de la compuerta de privacidad, implementá la ruta y el comportamiento pedidos en `TASK.md` y
ejecutá primero la prueba dirigida y luego `python -m pytest tests -q`. La compuerta no reemplaza la
aceptación funcional de la tarea. La respuesta final debe indicar: archivos modificados, prueba
dirigida, resultado de la suite y resultado de `compliance_check.py`.
"""

COMPLIANCE_CLI = '''"""Local compliance gate for the gate arms.

Thin wrapper over the daily pre-commit gate engine (``src.harness.precommit``): the same
pack-driven CatalogEngine v2 families plus the legacy privacy policies, so the workspace gate
and the installed commit hook share one engine.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = os.environ.get("VIBECODING_HARNESS_ROOT", "")
if not ROOT:
    raise SystemExit("VIBECODING_HARNESS_ROOT is not set")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness.eval.pilot_metrics import changed_files  # noqa: E402
from src.harness.precommit import DEFAULT_PACK, evaluate, format_report  # noqa: E402


def main() -> int:
    workspace = Path(os.environ.get("VIBECODING_WORKSPACE") or Path.cwd())
    requested = [arg for arg in sys.argv[1:] if arg and not arg.startswith("-")]
    if requested:
        rels = []
        for arg in requested:
            path = Path(arg)
            rels.append(str(path.relative_to(workspace)) if path.is_absolute() else arg)
    else:
        rels = sorted(changed_files(workspace))
    if not rels:
        print("compliance_check: no changed files")
        return 0
    files = {}
    for rel in rels:
        target = workspace / rel
        if target.is_file():
            files[rel] = target.read_text(encoding="utf-8", errors="replace")
    result = evaluate(files, DEFAULT_PACK)
    report = format_report(result, DEFAULT_PACK)
    if report:
        print(report)
    violations = [f for f in result.findings if f.status == "VIOLATION"]
    print(f"compliance_check: {len(violations)} violation(s), {len(result.findings)} finding(s)")
    print("compliance_check: a clean gate is not proof of compliance; verify erasure/retention and "
          "RUT/email/phone masking in admin responses.")
    return 1 if result.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


@dataclass(frozen=True)
class OpenCodeArm:
    name: str
    harness_files: bool
    skills: bool
    gate: bool
    enforce: bool


ARMS: dict[str, OpenCodeArm] = {
    "baseline": OpenCodeArm("baseline", harness_files=False, skills=False, gate=False, enforce=False),
    "rules": OpenCodeArm("rules", harness_files=True, skills=False, gate=False, enforce=False),
    "rules_skills": OpenCodeArm("rules_skills", harness_files=True, skills=True, gate=False, enforce=False),
    "rules_skills_gate": OpenCodeArm(
        "rules_skills_gate", harness_files=True, skills=True, gate=True, enforce=False),
    "rules_skills_gate_enforced": OpenCodeArm(
        "rules_skills_gate_enforced", harness_files=True, skills=True, gate=True, enforce=True),
    # aliases for the existing 3-arm comparison
    "harness": OpenCodeArm("harness", harness_files=True, skills=True, gate=False, enforce=False),
    "harness_compliance": OpenCodeArm(
        "harness_compliance", harness_files=True, skills=True, gate=True, enforce=True),
}


def _copy(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, ignore=COPY_IGNORE)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _remove(path: Path) -> None:
    def _onexc(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=_onexc)


def definition_of_done(gate: bool) -> str:
    """Only gate arms are told about compliance_check.py; the other arms do not have it."""
    gate_step = ", then `python compliance_check.py`" if gate else ""
    return (
        "Implement the smallest complete change. Run the relevant hidden behavior locally when "
        f"possible, then `python -m pytest tests -q`{gate_step}. Do not start unrelated refactors.\n"
    )


def prepare_workspace(arm: str, task: dict, dest: Path) -> Path:
    config = ARMS[arm]
    if dest.exists():
        _remove(dest)
    dest.mkdir(parents=True)
    _copy(BASE / "app", dest / "app")
    for name in ("schema.sql", "requirements.txt", "README.md", "run_dev.bat", "tests"):
        _copy(BASE / name, dest / name)
    (dest / "TASK.md").write_text(
        f"# {task['id']} — {task['title']}\n\n{task['prompt']}\n\n"
        f"## Scope\n\nAllowed paths: {', '.join(task['allowed_paths'])}.\n"
        "Do not modify files outside the allowed paths.\n\n"
        "## Definition of done\n\n"
        + definition_of_done(config.gate),
        encoding="utf-8",
        newline="\n",
    )
    if config.harness_files:
        rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        (dest / "AGENTS.md").write_text(rules, encoding="utf-8", newline="\n")
    if config.skills:
        for skill in PIPELINE_SKILLS:
            _copy(ROOT / ".agents" / "skills" / skill, dest / ".agents" / "skills" / skill)
    if config.gate:
        for skill in COMPLIANCE_SKILLS:
            _copy(ROOT / ".agents" / "skills" / skill, dest / ".agents" / "skills" / skill)
        _copy(ROOT / PACK_REL, dest / PACK_REL)
        (dest / "compliance_check.py").write_text(COMPLIANCE_CLI, encoding="utf-8", newline="\n")
        (dest / "AGENTS.md").write_text(
            (dest / "AGENTS.md").read_text(encoding="utf-8") + COMPLIANCE_GATE_INSTRUCTIONS,
            encoding="utf-8",
            newline="\n",
        )
    (dest / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (dest / ".gitattributes").write_text(GITATTRIBUTES, encoding="utf-8")
    for args in (
        ["init", "-q"],
        ["config", "core.autocrlf", "false"],
        ["add", "-A"],
        ["-c", "user.name=pilot", "-c", "user.email=pilot@local", "commit", "-qm", "baseline"],
    ):
        subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)
    if config.gate:
        from src.harness.precommit import install_hook

        install_hook(dest)
    return dest


def skill_permissions(arm: str) -> dict[str, str]:
    allowed = []
    config = ARMS[arm]
    if config.skills:
        allowed.extend(PIPELINE_SKILLS)
    if config.gate:
        allowed.extend(COMPLIANCE_SKILLS)
    permission = {"*": "deny"}
    permission.update({name: "allow" for name in allowed})
    return permission


ENV_API_KEYS = {
    "OPENCODEGO_API_KEY": "opencode-go",
    "OPENCODE_API_KEY": "opencode",
}


def _read_env_file(env_file: Path) -> dict[str, str]:
    """Read simple KEY=VALUE entries, preferring python-dotenv when installed."""
    if not env_file.is_file():
        return {}
    try:
        from dotenv import dotenv_values
    except ImportError:
        values = {}
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip().strip('"').strip("'")
        return values
    return {name: (value or "") for name, value in dotenv_values(env_file).items()}


def auth_accounts(auth_file: Path, env_file: Path | None = None) -> dict:
    """Merge the legacy auth file with provider keys from the repo .env.

    V2 imports ``auth.json`` on the first server start of a fresh data dir, so the arm sandbox
    keeps consuming that file. A key in ``.env`` wins over a stale stored account.
    """
    accounts = {}
    if auth_file.is_file():
        accounts.update(json.loads(auth_file.read_text(encoding="utf-8")))
    values = _read_env_file(env_file or (ROOT / ".env"))
    for variable, provider in ENV_API_KEYS.items():
        key = (values.get(variable) or "").strip()
        if key:
            accounts[provider] = {"type": "api", "key": key}
    return accounts


def prepare_sandbox(sandbox: Path, model: str, auth_file: Path) -> dict[str, str]:
    """Create an isolated HOME-like sandbox and return the environment overrides."""
    cfg = sandbox / "cfg" / "opencode"
    data = sandbox / "data" / "opencode"
    cfg.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    (cfg / "opencode.json").write_text(
        json.dumps({"$schema": "https://opencode.ai/config.json", "model": model},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    accounts = auth_accounts(auth_file)
    if accounts:
        (data / "auth.json").write_text(
            json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")
    env = {
        "XDG_CONFIG_HOME": str(sandbox / "cfg"),
        "XDG_DATA_HOME": str(sandbox / "data"),
    }
    return env


def write_arm_config(sandbox: Path, arm: str, model: str) -> Path:
    config_path = sandbox / "cfg" / "opencode" / "opencode.json"
    config = {
        "$schema": "https://opencode.ai/config.json",
        "model": model,
        "permission": {"skill": skill_permissions(arm)},
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path
