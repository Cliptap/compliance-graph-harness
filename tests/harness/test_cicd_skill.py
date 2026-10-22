import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "09-cicd" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "09_ci_cd.md"
DOCS_CICD_PATH = ROOT_DIR / "docs" / "CICD.md"
WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "ci.yml"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de CI/CD (cicd-automation)
# ==============================================================================
def lint_cicd_contract(
    spec_or_doc: str,
    allowed_paths: list[str] | None = None,
    workflow_content: str | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para cicd-automation."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            if normalized_ap.startswith("src/") or normalized_ap.startswith("tests/"):
                violations.append(
                    f"Invasión perimetral de TaskSpec: '{ap}' modifica código fuente en src/ o tests/ (CI/CD no muta aplicación ni tests)"
                )
            elif normalized_ap not in ["docs/CICD.md", ".github/workflows/ci.yml"]:
                violations.append(f"Ruta no autorizada en TaskSpec de CI/CD: '{ap}'")

    combined_text = spec_or_doc + ("\n" + workflow_content if workflow_content else "")

    # 2. Anti-Amnesia y Detección de Goldplating de Infraestructura
    toxic_patterns = [
        (r"\b(kubernetes|k8s|helm|kubectl)\b", "Infraestructura pesada de Kubernetes no autorizada para MVP"),
        (r"\b(docker\s+swarm|swarm)\b", "Docker Swarm fuera de alcance para MVP"),
        (r"\b(terraform|pulumi|ansible)\b", "Herramientas de IaC fuera de alcance para MVP"),
        (r"\b(golangci-lint|cargo\s+test|bundle\s+exec)\b", "Herramientas de lenguajes no pertenecientes al repositorio"),
        (r"\b(aws_access_key_id|aws_secret_access_key|api_key\s*=\s*['\"][a-zA-Z0-9]+['\"])\b", "Secrets o credenciales hardcodeadas en configuración de CI/CD"),
    ]
    for pattern, reason in toxic_patterns:
        m = re.search(pattern, combined_text, re.IGNORECASE)
        if m:
            violations.append(f"Violación de No-Goldplating / Anti-Amnesia: {reason} ('{m.group(0)}')")

    # 3. Verificación de Contrato de Artefacto Documental (docs/CICD.md)
    if "# docs/CICD.md" in spec_or_doc or "Pipeline CI/CD" in spec_or_doc:
        if "---" in spec_or_doc:
            try:
                fm, _ = _extract_frontmatter_and_body(spec_or_doc)
                if not fm.get("status"):
                    violations.append("Falta campo 'status' en frontmatter de CICD.md")
                if not fm.get("governance_level"):
                    violations.append("Falta campo 'governance_level' en frontmatter de CICD.md")
                if not fm.get("pipeline_provider"):
                    violations.append("Falta campo 'pipeline_provider' en frontmatter de CICD.md")
                if not fm.get("quality_gates_count"):
                    violations.append("Falta campo 'quality_gates_count' en frontmatter de CICD.md")
            except Exception as e:
                violations.append(f"Error parseando frontmatter de CICD.md: {e}")

        # Secciones obligatorias
        required_sections = [
            "Identidad del Pipeline y Objetivos de Calidad",
            "Matriz de Quality Gates Contractuales",
            "Especificación de Etapas y Triggers",
            "Dependencias y Tiempos de Ejecución",
            "Política de Seguridad en CI/CD",
            "Matriz de Linaje con TEST_PLAN.md y PRD.md",
        ]
        for sec in required_sections:
            if sec not in spec_or_doc:
                violations.append(f"Sección obligatoria faltante en CICD.md: {sec}")

        # Quality Gates obligatorios
        required_gates = ["GATE-001", "GATE-002", "GATE-003"]
        for gate in required_gates:
            if gate not in spec_or_doc:
                violations.append(f"Quality Gate contractual faltante en CICD.md: {gate}")

    # 4. Verificación del Workflow Ejecutable (si se provee)
    if workflow_content:
        # Triggers
        if not re.search(r"\bon:\s*\n\s*(push|pull_request)", workflow_content) and "push:" not in workflow_content:
            violations.append("Faltan triggers requeridos (push / pull_request) en workflow YAML")

        # Entornos y Setup
        if "setup-python" not in workflow_content or "3.12" not in workflow_content:
            violations.append("Falta configuración explícita de Python 3.12 en workflow YAML")
        if "setup-node" not in workflow_content and "node" not in workflow_content:
            violations.append("Falta configuración requerida de Node.js en workflow YAML (necesario para tests de frontend)")

        # Inicialización de DB y Test Runner
        if "init_harness_db" not in workflow_content:
            violations.append("Falta paso explícito de inicialización de base de datos 'init_harness_db()' en workflow YAML")
        if "pytest" not in workflow_content:
            violations.append("Falta paso de ejecución de pruebas con 'pytest' en workflow YAML")

        # Seguridad y Permisos Mínimos
        if "permissions:" not in workflow_content or "contents: read" not in workflow_content:
            violations.append("Falta configuración de menores privilegios 'permissions: contents: read' en workflow YAML")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias v2.0
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 09-cicd/SKILL.md y su versión portable contienen las secciones y metadatos contractuales v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo de skill no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter normativo
        assert fm.get("name") in ["cicd-automation", "ci-cd-pipeline", "09-cicd"]
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 8

        expected_dependencies = [
            "prd-generation",
            "architecture-design",
            "data-modeling",
            "api-design",
            "backend-implementation",
            "frontend-implementation",
            "auth-governance",
            "testing-strategy",
        ]
        for dep in expected_dependencies:
            assert dep in fm.get("depends_on", []), f"Dependencia faltante en {path.name}: {dep}"

        produces = fm.get("produces_artifact", [])
        assert "docs/CICD.md" in produces or produces == "docs/CICD.md"
        assert ".github/workflows/ci.yml" in produces

        assert "description" in fm and len(fm["description"]) > 20

        # Secciones estructurales obligatorias (Contrato v2.0)
        required_headers = [
            "Overview",
            "Cuándo Usar",
            "Precondiciones",
            "Entradas",
            "Taxonomía Formal",
            "Regla de Oro Anti-Amnesia",
            "Workflow de Implementación",
            "Señales de Alerta",
            "Contrato de Salida Formal",
            "Verificación del Artefacto",
            "Criterio de Término",
        ]
        for header in required_headers:
            assert header.lower() in body.lower(), f"Sección faltante en {path.name}: {header}"


# ==============================================================================
# TEST 2: Sincronización Estricta entre Versión Nativa y Versión Portable
# ==============================================================================
def test_portable_skills_synchronized():
    """Verifica paridad byte a byte o de contenido exacto entre SKILL.md y 09_ci_cd.md."""
    assert SKILL_PATH.exists()
    assert PORTABLE_SKILL_PATH.exists()
    native_content = SKILL_PATH.read_text(encoding="utf-8").strip()
    portable_content = PORTABLE_SKILL_PATH.read_text(encoding="utf-8").strip()
    assert native_content == portable_content, "Desincronización detectada entre .agents/skills/09-cicd/SKILL.md y harness/skills/09_ci_cd.md"


# ==============================================================================
# TEST 3: Validación del Esquema de TaskSpec y Delimitación Perimetral
# ==============================================================================
def test_cicd_skill_contract_schema_and_taskspec():
    """Valida que la skill define formalmente TaskSpec con allowed_paths y forbidden_paths."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec" in content or "task_spec" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "docs/CICD.md" in content
        assert ".github/workflows/ci.yml" in content
        assert "src/**" in content
        assert "tests/**" in content


# ==============================================================================
# TEST 4: Especificación del Pipeline Reproducible y Quality Gates (GATE-001..003)
# ==============================================================================
def test_reproducible_pipeline_and_quality_gates_specification():
    """Valida que la skill prescribe el flujo reproducible y los 3 Quality Gates obligatorios."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        # Quality Gates
        assert "GATE-001" in content
        assert "GATE-002" in content
        assert "GATE-003" in content
        assert "Zero Failure" in content
        assert "Acceptance Coverage" in content
        assert "ScopePolicy" in content or "Scope Policy" in content

        # Flujo y entorno
        assert "ubuntu-latest" in content
        assert "3.12" in content
        assert "init_harness_db" in content
        assert "contents: read" in content
        assert "push" in content
        assert "pull_request" in content


# ==============================================================================
# TEST 5: Reglas Anti-Amnesia y Detección de Goldplating de Infraestructura
# ==============================================================================
def test_anti_amnesia_and_goldplating_detection_rules():
    """Verifica que el linter rechaza configuraciones de CI/CD con Kubernetes, Swarm o linters ajenos."""
    toxic_configs = [
        ("deploy to kubernetes cluster with helm", "Kubernetes"),
        ("docker swarm init and stack deploy", "Docker Swarm"),
        ("terraform apply --auto-approve", "IaC"),
        ("run golangci-lint run ./...", "Herramientas ajenas"),
    ]
    for toxic_text, label in toxic_configs:
        violations = lint_cicd_contract(toxic_text)
        assert len(violations) >= 1, f"No se detectó violación para caso: {label}"

    # Verificación de invasión de perímetro
    perimeter_violations = lint_cicd_contract(
        "Spec normal",
        allowed_paths=["src/main.py", "docs/CICD.md"],
    )
    assert any("Invasión perimetral" in v for v in perimeter_violations)


# ==============================================================================
# TEST 6: Esquema del Artefacto de Salida (docs/CICD.md)
# ==============================================================================
def test_cicd_doc_output_contract_schema():
    """Valida que la skill prescribe las 6 secciones requeridas para docs/CICD.md."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "Identidad del Pipeline y Objetivos de Calidad" in content
        assert "Matriz de Quality Gates Contractuales" in content
        assert "Especificación de Etapas y Triggers" in content
        assert "Dependencias y Tiempos de Ejecución" in content
        assert "Política de Seguridad en CI/CD" in content
        assert "Matriz de Linaje con TEST_PLAN.md y PRD.md" in content


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_cicd_spec_passes_linter():
    """Verifica que una especificación y workflow conformes pasan el linter con 0 violaciones."""
    clean_cicd_doc = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
pipeline_provider: "github-actions"
quality_gates_count: 3
last_audit: "2026-10-22"
---

# docs/CICD.md — Especificación de Pipeline CI/CD y Quality Gates

## 1. Identidad del Pipeline y Objetivos de Calidad
Automatización determinista PIPE-001 para catalogo-carrito-web.

## 2. Matriz de Quality Gates Contractuales (GATE-xxx)
- GATE-001: Zero Failure (exit_code == 0).
- GATE-002: Acceptance Coverage al 100.0%.
- GATE-003: Scope Policy Enforcement.

## 3. Especificación de Etapas y Triggers
Triggers push y pull_request hacia rama main.

## 4. Dependencias y Tiempos de Ejecución
Python 3.12, Node 20, tiempo total < 1 minuto.

## 5. Política de Seguridad en CI/CD
Principio de menor privilegio con permissions: contents: read.

## 6. Matriz de Linaje con TEST_PLAN.md y PRD.md
Trazabilidad formal con AC-001..AC-006 y TEST_PLAN.md.
"""

    clean_workflow_yaml = """
name: CI Quality Gates

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: pip install -r requirements.txt
      - run: python -c "from src.harness.db import init_harness_db; init_harness_db()"
      - run: pytest tests/harness/ tests/catalog/ tests/frontend/ -v
"""

    violations = lint_cicd_contract(
        clean_cicd_doc,
        allowed_paths=["docs/CICD.md", ".github/workflows/ci.yml"],
        workflow_content=clean_workflow_yaml,
    )
    assert len(violations) == 0, f"Violaciones inesperadas en especificación conforme: {violations}"


# ==============================================================================
# TEST 8: Validación de Artefactos de CI/CD Físicos si Existen (Condicional/Skip)
# ==============================================================================
def test_cicd_artifacts_pass_linter_if_exist():
    """Valida docs/CICD.md y .github/workflows/ci.yml si ya fueron generados físicamente en disco (esperado en Etapa C)."""
    if not DOCS_CICD_PATH.exists() or not WORKFLOW_PATH.exists():
        pytest.skip("docs/CICD.md y/o .github/workflows/ci.yml aún no generados (esperado en Etapa C)")

    doc_content = DOCS_CICD_PATH.read_text(encoding="utf-8")
    wf_content = WORKFLOW_PATH.read_text(encoding="utf-8")
    violations = lint_cicd_contract(
        doc_content,
        allowed_paths=["docs/CICD.md", ".github/workflows/ci.yml"],
        workflow_content=wf_content,
    )
    assert len(violations) == 0, f"Violaciones en artefactos de CI/CD: {violations}"
