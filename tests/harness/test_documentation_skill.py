import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "12-documentation" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "12_documentation.md"
README_PATH = ROOT_DIR / "README.md"
SYSTEM_GUIDE_PATH = ROOT_DIR / "docs" / "SYSTEM_GUIDE.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


def _is_out_of_scope_context(text: str, match_start: int, match_end: int) -> bool:
    """Verifica si la coincidencia ocurre dentro de una sección o cláusula de exclusión / out of scope."""
    # 1. Verificar la línea en la que ocurre
    line_start = text.rfind("\n", 0, match_start)
    line_start = 0 if line_start == -1 else line_start + 1
    line_end = text.find("\n", match_end)
    line_end = len(text) if line_end == -1 else line_end
    line = text[line_start:line_end]

    exclusion_pattern = r"(out\s+of\s+scope|fuera\s+de\s+alcance|exclusi[oó]n(es)?|alternativas?\s+descartadas?|descartad[ao]s?|no\s+(se\s+)?incluye|no\s+soportad[ao]s?)"
    if re.search(exclusion_pattern, line, re.IGNORECASE):
        return True

    # 2. Verificar la sección (último encabezado markdown antes del match)
    text_before = text[:match_start]
    headers = re.findall(r"(?m)^#{1,6}\s+(.+)$", text_before)
    if headers:
        last_header = headers[-1]
        if re.search(exclusion_pattern, last_header, re.IGNORECASE):
            return True

    return False


# ==============================================================================
# Linter Determinista de Contrato de Documentación (documentation-generation)
# ==============================================================================
def lint_documentation_contract(
    readme_content: str | None = None,
    system_guide_content: str | None = None,
    allowed_paths: list[str] | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para documentation-generation."""
    violations = []

    # 1. Delimitación Perimetral de TaskSpec
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            if (
                normalized_ap.startswith("src/")
                or normalized_ap.startswith("tests/")
                or normalized_ap.startswith(".github/")
                or normalized_ap in ["Dockerfile", ".dockerignore"]
            ):
                violations.append(
                    f"Invasión perimetral de TaskSpec: '{ap}' modifica rutas protegidas en src/, tests/, .github/ o Dockerfile "
                    "(Documentation no muta código ni infraestructura)"
                )
            elif normalized_ap not in ["README.md", "docs/SYSTEM_GUIDE.md"]:
                violations.append(f"Ruta no autorizada en TaskSpec de Documentación: '{ap}'")

    combined_text = (readme_content or "") + "\n" + (system_guide_content or "")


    # 2. Anti-Amnesia y Detección de Tecnologías Descartadas / Deuda Legacy
    toxic_patterns = [
        (r"\b(postgresql|postgres|mysql|mongodb|redis|dynamodb)\b", "Base de datos externa no autorizada (contradicción con SQLite embebido AD-005)"),
        (r"\b(vue(\.js)?|react|angular|svelte)\b", "Framework de frontend no autorizado (contradicción con Vanilla JS AD-005)"),
        (r"\b(docusaurus|mkdocs|gitbook|confluence)\b", "Generador de sitios pesados o SaaS no autorizado para MVP"),
        (r"\b(jwt|oauth2?|bearer\s+token|rbac|roles?)\b", "Esquema de autenticación ajeno (contradicción con visitante anónimo AD-007)"),
        (r"\b(stripe|paypal|webpay|gateway)\b", "Pasarela financiera fuera de alcance"),
        (r"\b(admin@clinic\.com|admin123|super_secret_hipaa_key)\b", "Deuda técnica de aplicación clínica legacy en documentación"),
    ]
    for pattern, reason in toxic_patterns:
        if pattern == r"\b(stripe|paypal|webpay|gateway)\b":
            # Para pasarelas financieras, ignorar menciones legítimas en secciones o cláusulas de OUT OF SCOPE / Exclusiones / Alternativas Descartadas
            for m in re.finditer(pattern, combined_text, re.IGNORECASE):
                if not _is_out_of_scope_context(combined_text, m.start(), m.end()):
                    violations.append(f"Violación de No-Goldplating / Anti-Amnesia: {reason} ('{m.group(0)}')")
        else:
            m = re.search(pattern, combined_text, re.IGNORECASE)
            if m:
                violations.append(f"Violación de No-Goldplating / Anti-Amnesia: {reason} ('{m.group(0)}')")

    # 3. Verificación de Contrato de README.md
    if readme_content:
        required_readme_sections = [
            "Identidad del Sistema",
            "Stack Tecnológico",
            "Requisitos de Entorno",
            "Despliegue con Contenedor Docker",
            "Desarrollo y Ejecución Local",
            "Ejecución de la Suite Completa de Pruebas",
            "Referencia de Endpoints",
            "Observabilidad",
            "Especificaciones Formales",
        ]
        for sec in required_readme_sections:
            if not re.search(sec, readme_content, re.IGNORECASE):
                violations.append(f"Sección requerida faltante en README.md: '{sec}'")

        required_readme_tokens = ["EP-001", "EP-002", "HC-001", "DEP-001", "uvicorn src.main:app"]
        for tok in required_readme_tokens:
            if tok not in readme_content:
                violations.append(f"Token o directiva requerida faltante en README.md: '{tok}'")

    # 4. Verificación de Contrato de docs/SYSTEM_GUIDE.md
    if system_guide_content:
        if "---" in system_guide_content:
            try:
                fm, _ = _extract_frontmatter_and_body(system_guide_content)
                if not fm.get("status"):
                    violations.append("Falta campo 'status' en frontmatter de SYSTEM_GUIDE.md")
                if not fm.get("governance_level"):
                    violations.append("Falta campo 'governance_level' en frontmatter de SYSTEM_GUIDE.md")
                if not fm.get("project_id"):
                    violations.append("Falta campo 'project_id' en frontmatter de SYSTEM_GUIDE.md")
                if not fm.get("total_stages"):
                    violations.append("Falta campo 'total_stages' en frontmatter de SYSTEM_GUIDE.md")
            except Exception as e:
                violations.append(f"Error parseando frontmatter de SYSTEM_GUIDE.md: {e}")

        required_guide_sections = [
            "Propósito y Alcance Consolidado del Sistema",
            "Topología Arquitectónica y Componentes",
            "Modelo de Dominio y Persistencia",
            "Contrato de Integración REST y Manejo de Errores",
            "Postura de Seguridad Defensiva y Privacidad",
            "Matriz Consolidada de Trazabilidad End-to-End",
        ]
        for sec in required_guide_sections:
            if sec not in system_guide_content:
                violations.append(f"Sección obligatoria faltante en SYSTEM_GUIDE.md: '{sec}'")

        # Verificación de la Matriz de Trazabilidad E2E (etapas 01 a 12)
        required_stages = [
            "01-prd",
            "02-architecture",
            "03-data-modeling",
            "04-api-design",
            "05-backend",
            "06-frontend",
            "07-auth",
            "08-testing",
            "09-cicd",
            "10-deployment",
            "11-observability",
            "12-documentation",
        ]
        for stg in required_stages:
            if stg.lower() not in system_guide_content.lower():
                violations.append(f"Etapa faltante en la Matriz de Trazabilidad E2E de SYSTEM_GUIDE.md: '{stg}'")

    return violations


# ==============================================================================
# TEST 1: Sincronización Estricta entre Versión Nativa y Versión Portable
# ==============================================================================
def test_documentation_skills_files_synchronized():
    """Verifica paridad byte a byte o de contenido exacto entre SKILL.md y 12_documentation.md."""
    assert SKILL_PATH.exists(), f"No existe {SKILL_PATH}"
    assert PORTABLE_SKILL_PATH.exists(), f"No existe {PORTABLE_SKILL_PATH}"
    native_content = SKILL_PATH.read_text(encoding="utf-8").strip()
    portable_content = PORTABLE_SKILL_PATH.read_text(encoding="utf-8").strip()
    assert native_content == portable_content, (
        "Desincronización detectada entre .agents/skills/12-documentation/SKILL.md "
        "y harness/skills/12_documentation.md"
    )


# ==============================================================================
# TEST 2: Validación de Frontmatter y Metadatos Normativos v2.0
# ==============================================================================
def test_documentation_skill_frontmatter_metadata():
    """Valida que 12-documentation/SKILL.md y su versión portable contienen metadatos normativos v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        fm, _ = _extract_frontmatter_and_body(content)

        assert fm.get("name") in ["documentation-generation", "12-documentation", "documentation"]
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 11
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
            "observability-setup",
        ]
        for dep in expected_dependencies:
            assert dep in fm.get("depends_on", []), f"Dependencia faltante en {path.name}: {dep}"

        produces = fm.get("produces_artifact", [])
        assert "README.md" in produces
        assert "docs/SYSTEM_GUIDE.md" in produces

        assert "description" in fm and len(fm["description"]) > 20


# ==============================================================================
# TEST 3: Secciones Contractuales Obligatorias v2.0 (11 Secciones)
# ==============================================================================
def test_documentation_skill_canonical_sections():
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
# TEST 4: Reglas Anti-Amnesia y Prohibición de Tecnologías Descartadas
# ==============================================================================
def test_documentation_skill_anti_amnesia_rules():
    """Verifica que la skill prohíbe revivir tecnologías descartadas o inventar requisitos."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        # Prohibición explícita de amnesia sobre BD externas, auth, Vue y Stripe
        assert "PostgreSQL" in content or "postgresql" in content
        assert "AD-005" in content or "SQLite" in content
        assert "AD-007" in content or "anónimo" in content
        assert "EP-001" in content
        assert "EP-002" in content
        assert "CWE-532" in content


# ==============================================================================
# TEST 5: Detección y Rechazo de Goldplating en Documentación
# ==============================================================================
def test_documentation_skill_anti_goldplating():
    """Verifica que el linter rechaza generadores pesados externos o tecnologías ajenas."""
    toxic_cases = [
        ("setup documentation with docusaurus website", "Docusaurus"),
        ("build static docs using mkdocs serve", "MkDocs"),
        ("host docs on gitbook platform", "GitBook"),
        ("sync documentation to confluence wiki", "Confluence"),
        ("use postgresql database connection for docs", "PostgreSQL ajeno"),
        ("user login with jwt tokens and rbac roles", "JWT / RBAC ajeno"),
    ]
    for toxic_text, label in toxic_cases:
        violations = lint_documentation_contract(readme_content=toxic_text)
        assert len(violations) >= 1, f"No se detectó violación de goldplating para caso: {label}"


# ==============================================================================
# TEST 6: Delimitación de Perímetro y Control de TaskSpec
# ==============================================================================
def test_documentation_task_spec_boundary_control():
    """Valida la delimitación perimetral de TaskSpec en la skill y en el linter."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec" in content or "task_spec" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "README.md" in content
        assert "docs/SYSTEM_GUIDE.md" in content
        assert "src/**" in content
        assert "tests/**" in content

    # Verificación en el linter: invasión perimetral debe ser detectada
    perimeter_violations = lint_documentation_contract(
        allowed_paths=["src/main.py", "README.md"],
    )
    assert any("Invasión perimetral" in v for v in perimeter_violations)

    dockerfile_violations = lint_documentation_contract(
        allowed_paths=["Dockerfile", "README.md"],
    )
    assert any("Invasión perimetral" in v for v in dockerfile_violations)


# ==============================================================================
# TEST 7: Especificación de la Matriz Consolidada de Trazabilidad E2E
# ==============================================================================
def test_documentation_e2e_lineage_matrix():
    """Verifica que la skill exige la Matriz de Trazabilidad E2E cubriendo las 12 etapas."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "Matriz Consolidada de Trazabilidad End-to-End" in content or "Trazabilidad E2E" in content
        assert "01" in content and "12" in content


# ==============================================================================
# TEST 8: Validación de Especificación Conforme y Artefactos en Disco (Condicional)
# ==============================================================================
def test_conforming_documentation_spec_passes_linter():
    """Verifica que especificaciones conformes de README.md y docs/SYSTEM_GUIDE.md pasan con 0 violaciones."""
    clean_readme = """# Sistema Web Básico de Catálogo Comercial y Carrito de Compras

## Identidad del Sistema y Arquitectura Monolítica Liviana
Monolito modular liviano para catalogo-carrito-web.

## Stack Tecnológico Oficial
Python 3.12, FastAPI, SQLite con SQLAlchemy, Vanilla HTML5/CSS/JS y Docker.

## Requisitos de Entorno y Prerrequisitos
Python 3.12, Node.js LTS, Docker.

## Guía Rápida de Despliegue con Contenedor Docker
Ejecución con DEP-001 y sondeo de salud HC-001.

## Guía de Desarrollo y Ejecución Local Reproducible
Ejecución local con uvicorn src.main:app --port 8000.

## Ejecución de la Suite Completa de Pruebas
pytest tests/harness/ tests/catalog/ tests/frontend/ -v

## Referencia de Endpoints de Servidor
Consulta mediante EP-001 y EP-002; salud mediante HC-001.

## Observabilidad, Logging JSON y Trazabilidad por Request-ID
Formato LOG-001 y encabezado X-Request-ID (OBS-001).

## Índice y Navegación hacia las Especificaciones Formales
Enlaces a docs/PRD.md, docs/ARCHITECTURE.md, docs/DEPLOYMENT.md.
"""

    clean_system_guide = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
project_id: "catalogo-carrito-web"
total_stages: 12
last_audit: "2026-10-22"
---

# docs/SYSTEM_GUIDE.md — Guía Integral del Sistema y Gobernanza de Arquitectura

## 1. Propósito y Alcance Consolidado del Sistema (PRD)
Síntesis de REQ-001, REQ-002 y REQ-003.

## 2. Topología Arquitectónica y Componentes (Monolito Liviano)
Decisiones AD-001 a AD-007.

## 3. Modelo de Dominio y Persistencia (SQLite + Web Storage)
ENT-001, INV-001 a INV-004 y SEED-001.

## 4. Contrato de Integración REST y Manejo de Errores
EP-001, EP-002, DTO-ERR-001, ERR-001, ERR-002, ERR-500.

## 5. Postura de Seguridad Defensiva y Privacidad (CWE-532)
SEC-CTRL-001 a SEC-CTRL-005 y prevención CWE-532.

## 6. Matriz Consolidada de Trazabilidad End-to-End (Etapas 01 a 12)
| Etapa | Nombre | Contrato | Salida |
| :---: | :--- | :--- | :--- |
| 01 | 01-prd | PRD | docs/PRD.md |
| 02 | 02-architecture | Architecture | docs/ARCHITECTURE.md |
| 03 | 03-data-modeling | Model | docs/DATA_MODEL.md |
| 04 | 04-api-design | API | docs/API_DESIGN.md |
| 05 | 05-backend | Backend | src/main.py |
| 06 | 06-frontend | Frontend | src/frontend/ |
| 07 | 07-auth | Security | docs/SECURITY.md |
| 08 | 08-testing | Tests | docs/TEST_PLAN.md |
| 09 | 09-cicd | CI/CD | docs/CICD.md |
| 10 | 10-deployment | Docker | docs/DEPLOYMENT.md |
| 11 | 11-observability | Telemetría | docs/OBSERVABILITY.md |
| 12 | 12-documentation | Guía | docs/SYSTEM_GUIDE.md |
"""

    violations = lint_documentation_contract(
        readme_content=clean_readme,
        system_guide_content=clean_system_guide,
        allowed_paths=["README.md", "docs/SYSTEM_GUIDE.md"],
    )
    assert len(violations) == 0, f"Violaciones inesperadas en especificación conforme: {violations}"


def test_documentation_artifacts_pass_linter_if_exist():
    """Valida README.md y docs/SYSTEM_GUIDE.md cuando ya hayan sido formalmente generados en disco en Etapa C."""
    if not SYSTEM_GUIDE_PATH.exists():
        pytest.skip("docs/SYSTEM_GUIDE.md aún no generado en disco (esperado en Etapa C)")

    readme_content = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else None
    system_guide_content = SYSTEM_GUIDE_PATH.read_text(encoding="utf-8")
    violations = lint_documentation_contract(
        readme_content=readme_content,
        system_guide_content=system_guide_content,
        allowed_paths=["README.md", "docs/SYSTEM_GUIDE.md"],
    )
    assert len(violations) == 0, f"Violaciones en artefactos de documentación: {violations}"


def test_documentation_linter_permits_out_of_scope_payment_gateway_exclusions():
    """Certifica que menciones a pasarelas (Stripe, PayPal, WebPay) en cláusulas de OUT OF SCOPE o Exclusiones pasan el linter con 0 violaciones."""
    doc_with_exclusions = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
project_id: "catalogo-carrito-web"
total_stages: 12
last_audit: "2026-10-22"
---

# docs/SYSTEM_GUIDE.md — Guía Integral del Sistema y Gobernanza de Arquitectura

## 1. Propósito y Alcance Consolidado del Sistema (PRD)
REQ-001, REQ-002, REQ-003, REQ-004 y AC-001 a AC-006.

### Exclusiones y Cláusulas OUT OF SCOPE
- Pasarelas de pago externas (Stripe, PayPal, WebPay) quedan fuera del alcance del MVP por directiva de visitante anónimo.

## 2. Topología Arquitectónica y Componentes (Monolito Liviano)
Decisiones AD-001 a AD-007.

### Alternativas Descartadas
Se descartaron gateways financieros comerciales (Stripe, PayPal) para priorizar simplicidad sin cuentas bancarias.

## 3. Modelo de Dominio y Persistencia (SQLite + Web Storage)
ENT-001, INV-001 a INV-004 y SEED-001.

## 4. Contrato de Integración REST y Manejo de Errores
EP-001, EP-002, DTO-ERR-001, ERR-001, ERR-002, ERR-500.

## 5. Postura de Seguridad Defensiva y Privacidad (CWE-532)
SEC-CTRL-001 a SEC-CTRL-005 y prevención CWE-532.

## 6. Matriz Consolidada de Trazabilidad End-to-End (Etapas 01 a 12)
| Etapa | Nombre | Contrato | Salida |
| :---: | :--- | :--- | :--- |
| 01 | 01-prd | PRD | docs/PRD.md |
| 02 | 02-architecture | Architecture | docs/ARCHITECTURE.md |
| 03 | 03-data-modeling | Model | docs/DATA_MODEL.md |
| 04 | 04-api-design | API | docs/API_DESIGN.md |
| 05 | 05-backend | Backend | src/main.py |
| 06 | 06-frontend | Frontend | src/frontend/ |
| 07 | 07-auth | Security | docs/SECURITY.md |
| 08 | 08-testing | Tests | docs/TEST_PLAN.md |
| 09 | 09-cicd | CI/CD | docs/CICD.md |
| 10 | 10-deployment | Docker | docs/DEPLOYMENT.md |
| 11 | 11-observability | Telemetría | docs/OBSERVABILITY.md |
| 12 | 12-documentation | Guía | docs/SYSTEM_GUIDE.md |
"""

    violations = lint_documentation_contract(
        system_guide_content=doc_with_exclusions,
        allowed_paths=["docs/SYSTEM_GUIDE.md"],
    )
    assert len(violations) == 0, f"Violaciones inesperadas en especificación con exclusiones: {violations}"
