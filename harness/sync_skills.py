"""
Módulo de Sincronización Automatizada de Skills del Harness.

Principio Arquitectónico:
- La ÚNICA FUENTE DE VERDAD normativa reside en:
    .agents/skills/<skill-name>/SKILL.md
- El directorio 'harness/skills/' contiene el paquete de distribución portable
  y debe mantenerse 100% sincronizado (byte a byte) con las skills nativas.
"""

from __future__ import annotations

import pathlib
import shutil

SKILL_MAPPING: dict[str, str] = {
    "01-prd": "01_prd.md",
    "02-architecture": "02_architecture.md",
    "03-data-modeling": "03_data_modeling.md",
    "04-api-design": "04_api_design.md",
    "05-backend": "05_backend_implementation.md",
    "06-frontend": "06_frontend_implementation.md",
    "07-auth": "07_auth_security.md",
    "08-testing": "08_testing_strategy.md",
    "09-cicd": "09_ci_cd.md",
    "10-deployment": "10_deployment.md",
    "11-observability": "11_observability.md",
    "12-documentation": "12_documentation.md",
}


def sync_portable_skills(
    repo_root: pathlib.Path | None = None,
) -> dict[str, bool]:
    """Sincroniza deterministamente las 12 skills nativas hacia harness/skills/."""
    if repo_root is None:
        repo_root = pathlib.Path(__file__).resolve().parent.parent

    native_base = repo_root / ".agents" / "skills"
    portable_base = repo_root / "harness" / "skills"
    portable_base.mkdir(parents=True, exist_ok=True)

    results: dict[str, bool] = {}
    for skill_name, portable_filename in SKILL_MAPPING.items():
        source_file = native_base / skill_name / "SKILL.md"
        target_file = portable_base / portable_filename

        if not source_file.exists():
            raise FileNotFoundError(f"Fuente de verdad faltante: {source_file}")

        shutil.copyfile(source_file, target_file)
        # Verificar paridad byte a byte
        results[skill_name] = source_file.read_bytes() == target_file.read_bytes()

    return results


if __name__ == "__main__":
    status = sync_portable_skills()
    print("Sincronización de skills completada:")
    for skill, ok in status.items():
        print(f"  - {skill:18} -> {SKILL_MAPPING[skill]:32} [{'OK' if ok else 'FAIL'}]")
