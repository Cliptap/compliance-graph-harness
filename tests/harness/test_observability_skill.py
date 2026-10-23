import pathlib
import re
import pytest
import yaml

from src.harness.contracts import TaskSpec
from src.harness.policy_engine import SensitiveLoggingPolicy

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "11-observability" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "11_observability.md"
DOCS_OBSERVABILITY_PATH = ROOT_DIR / "docs" / "OBSERVABILITY.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Observabilidad (observability-setup)
# ==============================================================================
def lint_observability_contract(
    spec_or_doc: str,
    allowed_paths: list[str] | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para observability-setup."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            if (
                normalized_ap.startswith("src/backend/")
                or normalized_ap.startswith("src/database/")
                or normalized_ap.startswith("src/frontend/")
                or normalized_ap.startswith(".github/")
                or normalized_ap == "Dockerfile"
            ):
                violations.append(
                    f"Invasión perimetral de TaskSpec: '{ap}' modifica rutas protegidas en src/backend/, src/database/, src/frontend/, .github/ o Dockerfile"
                )
            elif (
                normalized_ap not in ["docs/OBSERVABILITY.md", "src/main.py", "tests/catalog/**"]
                and not normalized_ap.startswith("tests/catalog/")
            ):
                violations.append(f"Ruta no autorizada en TaskSpec de Observability: '{ap}'")

    # 2. Anti-Amnesia y Detección de Goldplating de Telemetría
    toxic_patterns = [
        (r"\b(prometheus|prom_client|prometheus_client)\b", "Servidor o cliente Prometheus no autorizado para MVP"),
        (r"\b(grafana|kibana|chronograf)\b", "Plataforma de visualización externa no autorizada para MVP"),
        (r"\b(jaeger|zipkin)\b", "Herramienta de tracing distribuido no autorizada para monolito autónomo"),
        (r"\b(opentelemetry|open_telemetry|\botel\b)\b", "Framework OpenTelemetry no autorizado para MVP"),
        (r"\b(datadog|newrelic|dynatrace|splunk|sentry)\b", "APM o SaaS externo no autorizado para MVP"),
        (r"\b(pagerduty|opsgenie)\b", "Sistema de alerta on-call no autorizado para MVP"),
        (r"\b(slack|discord)\b.*(webhook|alert|notif)", "Webhooks de canales de alerta externos no autorizados"),
    ]
    for pattern, reason in toxic_patterns:
        m = re.search(pattern, spec_or_doc, re.IGNORECASE)
        if m:
            violations.append(f"Violación de No-Goldplating / Anti-Amnesia: {reason} ('{m.group(0)}')")

    # 3. Verificación de Contrato de Artefacto Documental (docs/OBSERVABILITY.md)
    if "# docs/OBSERVABILITY.md" in spec_or_doc or "Especificación de Observabilidad" in spec_or_doc:
        if "---" in spec_or_doc:
            try:
                fm, _ = _extract_frontmatter_and_body(spec_or_doc)
                if not fm.get("status"):
                    violations.append("Falta campo 'status' en frontmatter de OBSERVABILITY.md")
                if not fm.get("governance_level"):
                    violations.append("Falta campo 'governance_level' en frontmatter de OBSERVABILITY.md")
                if not fm.get("logging_format"):
                    violations.append("Falta campo 'logging_format' en frontmatter de OBSERVABILITY.md")
                if not fm.get("log_sink"):
                    violations.append("Falta campo 'log_sink' en frontmatter de OBSERVABILITY.md")
                if not fm.get("request_id_header"):
                    violations.append("Falta campo 'request_id_header' en frontmatter de OBSERVABILITY.md")
                if not fm.get("healthcheck_endpoint"):
                    violations.append("Falta campo 'healthcheck_endpoint' en frontmatter de OBSERVABILITY.md")
            except Exception as e:
                violations.append(f"Error parseando frontmatter de OBSERVABILITY.md: {e}")

        # Secciones obligatorias
        required_sections = [
            "Identidad de Observabilidad y Principios de Evidencia",
            "Arquitectura de Logging Estructurado JSON",
            "Trazabilidad y Correlación de Peticiones por Request-ID",
            "Auditoría de Seguridad y Cero Fuga de Datos Sensibles",
            "Métricas Operacionales Mínimas y Health Checks",
            "Matriz de Linaje con PRD, Arquitectura, Seguridad, API y Despliegue",
        ]
        for sec in required_sections:
            if sec not in spec_or_doc:
                violations.append(f"Sección obligatoria faltante en OBSERVABILITY.md: {sec}")

        # Identificadores formales requeridos
        required_ids = ["OBS-001", "OBS-002", "LOG-001", "MET-001", "HC-001"]
        for fid in required_ids:
            if fid not in spec_or_doc:
                violations.append(f"Falta identificador formal requerido ({fid}) en OBSERVABILITY.md")

    return violations


# ==============================================================================
# TEST 1: Sincronización Estricta entre Versión Nativa y Versión Portable
# ==============================================================================
def test_observability_skills_files_synchronized():
    """Verifica paridad byte a byte o de contenido exacto entre SKILL.md y 11_observability.md."""
    assert SKILL_PATH.exists(), f"No existe {SKILL_PATH}"
    assert PORTABLE_SKILL_PATH.exists(), f"No existe {PORTABLE_SKILL_PATH}"
    native_content = SKILL_PATH.read_text(encoding="utf-8").strip()
    portable_content = PORTABLE_SKILL_PATH.read_text(encoding="utf-8").strip()
    assert native_content == portable_content, (
        "Desincronización detectada entre .agents/skills/11-observability/SKILL.md "
        "y harness/skills/11_observability.md"
    )


# ==============================================================================
# TEST 2: Validación de Frontmatter y Metadatos Normativos v2.0
# ==============================================================================
def test_observability_skill_frontmatter_metadata():
    """Valida que 11-observability/SKILL.md y su versión portable contienen metadatos normativos v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        fm, _ = _extract_frontmatter_and_body(content)

        assert fm.get("name") in ["observability-setup", "11-observability", "observability"]
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 10
        assert fm.get("governance") == "all"

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
            "deployment-automation",
        ]
        for dep in expected_dependencies:
            assert dep in fm.get("depends_on", []), f"Dependencia faltante en {path.name}: {dep}"

        produces = fm.get("produces_artifact", [])
        assert "docs/OBSERVABILITY.md" in produces

        assert "description" in fm and len(fm["description"]) > 20


# ==============================================================================
# TEST 3: Secciones Contractuales Obligatorias v2.0 (11 Secciones)
# ==============================================================================
def test_observability_skill_canonical_sections():
    """Valida la presencia obligatoria de las 11 secciones canónicas en la skill."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        _, body = _extract_frontmatter_and_body(content)

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
            assert header.lower() in body.lower(), f"Sección canónica faltante en {path.name}: {header}"


# ==============================================================================
# TEST 4: Reglas Anti-Amnesia Contractuales
# ==============================================================================
def test_observability_skill_anti_amnesia_rules():
    """Verifica que la skill prohíbe re-preguntar decisiones ya cerradas aguas arriba."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        # Prohibición explícita de amnesia sobre SQLite, /health, modo anónimo y gobernanza
        assert "AD-005" in content or "SQLite" in content
        assert "HC-001" in content or "/health" in content
        assert "AD-007" in content or "anónimo" in content
        assert "EP-001" in content
        assert "EP-002" in content
        assert "SEC-CTRL-004" in content or "CWE-532" in content


# ==============================================================================
# TEST 5: Detección y Rechazo de Goldplating de Telemetría Externa
# ==============================================================================
def test_observability_skill_anti_goldplating():
    """Verifica que el linter rechaza plataformas pesadas ajenas (Prometheus, Grafana, Jaeger, etc.)."""
    toxic_cases = [
        ("export metrics using prometheus_client library", "Prometheus"),
        ("setup grafana dashboard on port 3000", "Grafana"),
        ("configure jaeger tracer exporter", "Jaeger"),
        ("use opentelemetry sdk with otel collector", "OpenTelemetry"),
        ("send traces to datadog apm agent", "Datadog"),
        ("alerting via pagerduty on-call schedule", "PagerDuty"),
        ("send notification to slack webhook https://hooks.slack.com", "Slack Webhook"),
    ]
    for toxic_text, label in toxic_cases:
        violations = lint_observability_contract(toxic_text)
        assert len(violations) >= 1, f"No se detectó violación de goldplating para caso: {label}"


# ==============================================================================
# TEST 6: Delimitación de Perímetro y Control de TaskSpec
# ==============================================================================
def test_observability_task_spec_boundary_control():
    """Valida la delimitación perimetral de TaskSpec en la skill y en el linter."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec" in content or "task_spec" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "docs/OBSERVABILITY.md" in content
        assert "src/main.py" in content
        assert "tests/catalog/**" in content
        assert "src/backend/**" in content
        assert "src/frontend/**" in content

    # Verificación en el linter: invasión perimetral debe ser detectada ante rutas prohibidas
    perimeter_violations = lint_observability_contract(
        "Spec normal",
        allowed_paths=["src/backend/api/patients.py", "docs/OBSERVABILITY.md"],
    )
    assert any("Invasión perimetral" in v for v in perimeter_violations)

    forbidden_dockerfile_violations = lint_observability_contract(
        "Spec normal",
        allowed_paths=["Dockerfile", "docs/OBSERVABILITY.md"],
    )
    assert any("Invasión perimetral" in v for v in forbidden_dockerfile_violations)

    forbidden_frontend_violations = lint_observability_contract(
        "Spec normal",
        allowed_paths=["src/frontend/app.js", "docs/OBSERVABILITY.md"],
    )
    assert any("Invasión perimetral" in v for v in forbidden_frontend_violations)

    # Rutas autorizadas legítimas deben pasar sin violaciones perimetrales
    clean_violations = lint_observability_contract(
        "Spec normal",
        allowed_paths=["docs/OBSERVABILITY.md", "src/main.py", "tests/catalog/**"],
    )
    assert len(clean_violations) == 0


# ==============================================================================
# TEST 7: Cumplimiento de Política de Privacidad y Cero Fuga CWE-532
# ==============================================================================
def test_observability_security_policy_cwe532_compliance():
    """Valida que la skill y el arnés certifican cero fugas CWE-532 mediante SensitiveLoggingPolicy."""
    policy = SensitiveLoggingPolicy()
    mock_spec = TaskSpec(
        task_id="OBS-TASK-001",
        goal="Verificación de observabilidad",
        allowed_paths=["docs/OBSERVABILITY.md"],
    )

    # 1. Código con fuga directa sin enmascaramiento -> VIOLACIÓN
    bad_code = {
        "src/observability/bad_logger.py": 'logger.info(f"User login attempt with token: {token} and rut: {rut}")'
    }
    findings = policy.evaluate(mock_spec, bad_code)
    assert len(findings) >= 1
    assert any(f.policy_id == "privacy.cwe_532" for f in findings)

    # 2. Código con enmascaramiento explícito -> PASS
    good_code = {
        "src/observability/good_logger.py": 'logger.info(f"User event processed: [redacted]")'
    }
    findings_good = policy.evaluate(mock_spec, good_code)
    assert len(findings_good) == 0

    # 3. La skill prescribe expresamente OBS-002 y CWE-532
    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    assert "OBS-002" in skill_content
    assert "CWE-532" in skill_content
    assert "SensitiveLoggingPolicy" in skill_content


# ==============================================================================
# TEST 8: Validación de Especificación Conforme y Artefacto en Disco
# ==============================================================================
def test_conforming_observability_spec_passes_linter():
    """Verifica que una especificación de observabilidad conforme pasa el linter con 0 violaciones."""
    clean_observability_doc = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
logging_format: "json"
log_sink: "stdout"
request_id_header: "X-Request-ID"
healthcheck_endpoint: "/health"
last_audit: "2026-10-22"
---

# docs/OBSERVABILITY.md — Especificación de Observabilidad y Captura de Evidencia

## 1. Identidad de Observabilidad y Principios de Evidencia
Definición conforme a Sección 18 de plan.md respondiendo a qué ocurrió, qué lo provocó y cómo reproducirlo bajo OBS-003.

## 2. Arquitectura de Logging Estructurado JSON
Esquema canónico LOG-001 hacia stdout con severidades INFO, WARNING, ERROR.

## 3. Trazabilidad y Correlación de Peticiones por Request-ID
Directiva OBS-001 propagando header X-Request-ID para correlación determinista reproducible con curl.

## 4. Auditoría de Seguridad y Cero Fuga de Datos Sensibles (CWE-532)
Directiva OBS-002 asegurando cero fugas bajo CWE-532 y SensitiveLoggingPolicy.

## 5. Métricas Operacionales Mínimas y Health Checks
Métrica MET-001 (duration_ms), MET-002 (códigos de error ERR-xxx) y sondeo de salud HC-001 en /health.

## 6. Matriz de Linaje con PRD, Arquitectura, Seguridad, API y Despliegue
Trazabilidad de OBS-001, OBS-002, LOG-001, MET-001 y HC-001 con upstream.
"""

    violations = lint_observability_contract(
        clean_observability_doc,
        allowed_paths=["docs/OBSERVABILITY.md"],
    )
    assert len(violations) == 0, f"Violaciones inesperadas en especificación conforme: {violations}"


def test_observability_artifact_passes_linter_if_exists():
    """Valida docs/OBSERVABILITY.md si ya fue generado físicamente en disco (esperado en Etapa C)."""
    if not DOCS_OBSERVABILITY_PATH.exists():
        pytest.skip("docs/OBSERVABILITY.md aún no generado en disco (esperado en Etapa C)")

    doc_content = DOCS_OBSERVABILITY_PATH.read_text(encoding="utf-8")
    violations = lint_observability_contract(
        doc_content,
        allowed_paths=["docs/OBSERVABILITY.md"],
    )
    assert len(violations) == 0, f"Violaciones en artefacto de observabilidad: {violations}"
