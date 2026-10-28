import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "10-deployment" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "10_deployment.md"
DOCS_DEPLOYMENT_PATH = ROOT_DIR / "docs" / "DEPLOYMENT.md"
DOCKERFILE_PATH = ROOT_DIR / "Dockerfile"
DOCKERIGNORE_PATH = ROOT_DIR / ".dockerignore"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Despliegue (deployment-automation)
# ==============================================================================
def lint_deployment_contract(
    spec_or_doc: str,
    allowed_paths: list[str] | None = None,
    dockerfile_content: str | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para deployment-automation."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            if normalized_ap.startswith("src/") or normalized_ap.startswith("tests/") or normalized_ap.startswith(".github/"):
                violations.append(
                    f"Invasión perimetral de TaskSpec: '{ap}' modifica rutas protegidas en src/, tests/ o .github/ (Deployment no muta código ni pipelines)"
                )
            elif normalized_ap not in ["docs/DEPLOYMENT.md", "Dockerfile", ".dockerignore"]:
                violations.append(f"Ruta no autorizada en TaskSpec de Deployment: '{ap}'")

    combined_text = spec_or_doc + ("\n" + dockerfile_content if dockerfile_content else "")

    # 2. Anti-Amnesia y Detección de Goldplating de Infraestructura
    toxic_patterns = [
        (r"\b(kubernetes|k8s|helm|kubectl)\b", "Infraestructura pesada de Kubernetes no autorizada para MVP"),
        (r"\b(docker\s+swarm|swarm)\b", "Docker Swarm fuera de alcance para MVP"),
        (r"\b(terraform|pulumi|ansible|cloudformation)\b", "Herramientas de IaC fuera de alcance para MVP"),
        (r"\b(postgres(ql)?|mysql|redis|dynamodb)\b", "Base de datos externa no autorizada (contradicción con SQLite embebido AD-005)"),
        (r"\b(aws_access_key_id|aws_secret_access_key|jwt_secret|secret_key\s*=\s*['\"][a-zA-Z0-9]+['\"])\b", "Secrets o credenciales hardcodeadas en configuración de despliegue"),
    ]
    for pattern, reason in toxic_patterns:
        m = re.search(pattern, combined_text, re.IGNORECASE)
        if m:
            violations.append(f"Violación de No-Goldplating / Anti-Amnesia: {reason} ('{m.group(0)}')")

    # 3. Verificación de Contrato de Artefacto Documental (docs/DEPLOYMENT.md)
    if "# docs/DEPLOYMENT.md" in spec_or_doc or "Especificación de Despliegue" in spec_or_doc:
        if "---" in spec_or_doc:
            try:
                fm, _ = _extract_frontmatter_and_body(spec_or_doc)
                if not fm.get("status"):
                    violations.append("Falta campo 'status' en frontmatter de DEPLOYMENT.md")
                if not fm.get("governance_level"):
                    violations.append("Falta campo 'governance_level' en frontmatter de DEPLOYMENT.md")
                if not fm.get("deployment_target"):
                    violations.append("Falta campo 'deployment_target' en frontmatter de DEPLOYMENT.md")
                if not fm.get("exposed_port"):
                    violations.append("Falta campo 'exposed_port' en frontmatter de DEPLOYMENT.md")
                if not fm.get("healthcheck_endpoint"):
                    violations.append("Falta campo 'healthcheck_endpoint' en frontmatter de DEPLOYMENT.md")
            except Exception as e:
                violations.append(f"Error parseando frontmatter de DEPLOYMENT.md: {e}")

        # Secciones obligatorias
        required_sections = [
            "Identidad de Despliegue y Arquitectura de la Unidad Desplegable",
            "Estrategia de Empaquetado en Contenedor",
            "Gestión de Persistencia y Datos Semilla",
            "Variables de Entorno y Política de Secrets",
            "Health Checks y Procedimiento Operativo de Verificación",
            "Matriz de Linaje con ARCHITECTURE.md, SECURITY.md y CICD.md",
        ]
        for sec in required_sections:
            if sec not in spec_or_doc:
                violations.append(f"Sección obligatoria faltante en DEPLOYMENT.md: {sec}")

        # Identificadores de despliegue requeridos
        if "DEP-001" not in spec_or_doc:
            violations.append("Falta identificador formal de despliegue (DEP-001) en DEPLOYMENT.md")
        if "HC-001" not in spec_or_doc:
            violations.append("Falta identificador formal de health check (HC-001) en DEPLOYMENT.md")

    # 4. Verificación del Manifiesto de Contenedor (Dockerfile si se provee)
    if dockerfile_content:
        # Multi-stage y runtime ligero
        if "AS builder" not in dockerfile_content and "as builder" not in dockerfile_content:
            violations.append("Dockerfile debe implementar Multi-Stage Build con etapa builder")
        if "python:3.12-slim" not in dockerfile_content:
            violations.append("Dockerfile debe utilizar imagen base oficial 'python:3.12-slim'")

        # Usuario no-root por seguridad
        if "useradd" not in dockerfile_content or "USER" not in dockerfile_content:
            violations.append("Dockerfile debe configurar y ejecutar bajo un usuario sin privilegios (non-root user)")

        # Entrypoint canónico
        if "src.backend.main:app" in dockerfile_content:
            violations.append("Dockerfile apunta a ruta legacy 'src.backend.main:app' en lugar de 'src.main:app'")
        if "src.main:app" not in dockerfile_content:
            violations.append("Dockerfile debe ejecutar el entrypoint canónico 'uvicorn src.main:app'")

        # Exposición de puerto y Healthcheck
        if "EXPOSE 8000" not in dockerfile_content and "EXPOSE" not in dockerfile_content:
            violations.append("Dockerfile debe exponer puerto 8000 (EXPOSE 8000)")
        if "HEALTHCHECK" not in dockerfile_content or "/health" not in dockerfile_content:
            violations.append("Dockerfile debe configurar HEALTHCHECK sondeando '/health'")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias v2.0
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 10-deployment/SKILL.md y su versión portable contienen las secciones y metadatos contractuales v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo de skill no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter normativo
        assert fm.get("name") in ["deployment-automation", "deployment", "10-deployment"]
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 9

        expected_dependencies = [
            "prd-generation",
            "architecture-design",
            "data-modeling",
            "api-design",
            "backend-implementation",
            "frontend-implementation",
            "auth-governance",
            "testing-strategy",
            "cicd-automation",
        ]
        for dep in expected_dependencies:
            assert dep in fm.get("depends_on", []), f"Dependencia faltante en {path.name}: {dep}"

        produces = fm.get("produces_artifact", [])
        assert "docs/DEPLOYMENT.md" in produces
        assert "Dockerfile" in produces
        assert ".dockerignore" in produces

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

        # Verificación del estándar metodológico genérico y sección de contexto de referencia
        assert "upstream" in body.lower(), f"Falta referencia a trazabilidad upstream en {path.name}"
        assert "Reference Context: Demo Implementation" in body, (
            f"Falta sección de contexto de referencia de demo en {path.name}"
        )


# ==============================================================================
# TEST 2: Sincronización Estricta entre Versión Nativa y Versión Portable
# ==============================================================================
def test_portable_skills_synchronized():
    """Verifica paridad byte a byte o de contenido exacto entre SKILL.md y 10_deployment.md."""
    assert SKILL_PATH.exists()
    assert PORTABLE_SKILL_PATH.exists()
    native_content = SKILL_PATH.read_text(encoding="utf-8").strip()
    portable_content = PORTABLE_SKILL_PATH.read_text(encoding="utf-8").strip()
    assert native_content == portable_content, "Desincronización detectada entre .agents/skills/10-deployment/SKILL.md y harness/skills/10_deployment.md"


# ==============================================================================
# TEST 3: Validación del Esquema de TaskSpec y Delimitación Perimetral
# ==============================================================================
def test_deployment_skill_contract_schema_and_taskspec():
    """Valida que la skill define formalmente TaskSpec con allowed_paths y forbidden_paths."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec" in content or "task_spec" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "docs/DEPLOYMENT.md" in content
        assert "Dockerfile" in content
        assert ".dockerignore" in content
        assert "src/**" in content
        assert "tests/**" in content
        assert ".github/**" in content

        # Coexistencia de la sección de contexto de referencia de la demo
        assert "Reference Context: Demo Implementation" in content


# ==============================================================================
# TEST 4: Coherencia con la Arquitectura Monolítica y Liviana (AD-001, AD-005)
# ==============================================================================
def test_deployable_unit_specification_coherence_with_ad001_and_ad005():
    """Valida que la skill prescribe monolito liviano, Python 3.12, non-root, src.main:app y SQLite embebido."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        # Stack y Arquitectura
        assert "python:3.12-slim" in content
        assert "src.main:app" in content
        assert "appuser" in content or "non-root" in content
        assert "/health" in content
        assert "SQLite" in content or "sqlite" in content
        assert "Multi-Stage" in content or "multi-stage" in content
        assert "DEP-001" in content
        assert "HC-001" in content


# ==============================================================================
# TEST 5: Reglas Anti-Amnesia y Detección de Goldplating de Infraestructura
# ==============================================================================
def test_anti_amnesia_and_goldplating_detection_rules():
    """Verifica que el linter rechaza orquestadores pesados, bases de datos externas o invasiones perimetrales."""
    toxic_configs = [
        ("deploy to kubernetes with helm chart", "Kubernetes"),
        ("docker swarm init and deploy stack", "Docker Swarm"),
        ("terraform apply --auto-approve for aws infra", "IaC"),
        ("connect to postgresql database on port 5432", "PostgreSQL ajeno"),
    ]
    for toxic_text, label in toxic_configs:
        violations = lint_deployment_contract(toxic_text)
        assert len(violations) >= 1, f"No se detectó violación para caso: {label}"

    # Verificación de invasión de perímetro
    perimeter_violations = lint_deployment_contract(
        "Spec normal",
        allowed_paths=["src/main.py", "docs/DEPLOYMENT.md"],
    )
    assert any("Invasión perimetral" in v for v in perimeter_violations)


# ==============================================================================
# TEST 6: Esquema del Artefacto de Salida (docs/DEPLOYMENT.md)
# ==============================================================================
def test_deployment_doc_output_contract_schema():
    """Valida que la skill prescribe las 6 secciones requeridas para docs/DEPLOYMENT.md."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "Identidad de Despliegue y Arquitectura de la Unidad Desplegable" in content
        assert "Estrategia de Empaquetado en Contenedor" in content
        assert "Gestión de Persistencia y Datos Semilla" in content
        assert "Variables de Entorno y Política de Secrets" in content
        assert "Health Checks y Procedimiento Operativo de Verificación" in content
        assert "Matriz de Linaje con ARCHITECTURE.md, SECURITY.md y CICD.md" in content


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_deployment_spec_passes_linter():
    """Verifica que una especificación y Dockerfile conformes pasan el linter con 0 violaciones."""
    clean_deployment_doc = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
deployment_target: "docker"
container_engine: "docker"
exposed_port: 8000
healthcheck_endpoint: "/health"
last_audit: "2026-10-22"
---

# docs/DEPLOYMENT.md — Especificación de Despliegue y Empaquetado

## 1. Identidad de Despliegue y Arquitectura de la Unidad Desplegable (DEP-001)
Unidad desplegable monolítica liviana DEP-001 para catalogo-carrito-web.

## 2. Estrategia de Empaquetado en Contenedor
Multi-stage build sobre python:3.12-slim con usuario non-root.

## 3. Gestión de Persistencia y Datos Semilla
Persistencia relacional SQLite embebida y precarga de SEED-001.

## 4. Variables de Entorno y Política de Secrets
Modo anónimo sin secrets requeridos conforme a AD-007 y SEC-DEC-001.

## 5. Health Checks y Procedimiento Operativo de Verificación
HC-001 sondea /health. Procedimiento reproducible con docker run.

## 6. Matriz de Linaje con ARCHITECTURE.md, SECURITY.md y CICD.md
Trazabilidad formal con AD-001, AD-005, SEC-DEC-001 y PIPE-001.
"""

    clean_dockerfile = """
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY src/ ./src/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    violations = lint_deployment_contract(
        clean_deployment_doc,
        allowed_paths=["docs/DEPLOYMENT.md", "Dockerfile", ".dockerignore"],
        dockerfile_content=clean_dockerfile,
    )
    assert len(violations) == 0, f"Violaciones inesperadas en especificación conforme: {violations}"


# ==============================================================================
# TEST 8: Validación de Artefactos de Despliegue Físicos si Existen (Condicional/Skip)
# ==============================================================================
def test_deployment_artifacts_pass_linter_if_exist():
    """Valida docs/DEPLOYMENT.md y Dockerfile si ya fueron generados formalmente en disco (esperado en Etapa C)."""
    if not DOCS_DEPLOYMENT_PATH.exists():
        pytest.skip("docs/DEPLOYMENT.md aún no generado (esperado en Etapa C)")

    doc_content = DOCS_DEPLOYMENT_PATH.read_text(encoding="utf-8")
    dockerfile_content = DOCKERFILE_PATH.read_text(encoding="utf-8") if DOCKERFILE_PATH.exists() else None
    violations = lint_deployment_contract(
        doc_content,
        allowed_paths=["docs/DEPLOYMENT.md", "Dockerfile", ".dockerignore"],
        dockerfile_content=dockerfile_content,
    )
    assert len(violations) == 0, f"Violaciones en artefactos de despliegue: {violations}"
