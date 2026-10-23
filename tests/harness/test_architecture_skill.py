import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "02-architecture" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "02_architecture.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato Arquitectónico
# ==============================================================================
def lint_architecture_contract(body: str, out_of_scope_items: list[str] | None = None) -> list[str]:
    """Analizador determinista de cumplimiento de contrato de ARCHITECTURE.md."""
    violations = []

    # 1. Aislamiento físico: No emitir allowed_paths ni rutas de archivos físicas
    if any(k in body for k in ["allowed_paths", "forbidden_paths"]):
        violations.append("Rutas de allowed_paths o forbidden_paths detectadas en el documento de arquitectura")

    # 2. No DDL prematuro (delegado a 03-data-modeling)
    ddl_keywords = [r"\bCREATE\s+TABLE\b", r"\bALTER\s+TABLE\b", r"\bPRIMARY\s+KEY\b", r"\bFOREIGN\s+KEY\b"]
    for kw in ddl_keywords:
        if re.search(kw, body, re.IGNORECASE):
            violations.append(f"Sentencia o definición DDL prematura detectada ({kw}): delegada a 03-data-modeling")

    # 3. No endpoints HTTP detallados (delegado a 04-api-design)
    http_endpoint_pattern = r"\b(GET|POST|PUT|DELETE|PATCH)\s+/(api|v\d+)/"
    if re.search(http_endpoint_pattern, body, re.IGNORECASE):
        violations.append("Definición de rutas de endpoints HTTP detallada detectada: delegada a 04-api-design")

    # 4. Anti-Amnesia: Violación de OUT OF SCOPE heredado
    default_exclusions = ["pasarela de pago", "stripe", "autenticación jwt", "registro de usuarios", "motor de recomendación"]
    active_exclusions = out_of_scope_items if out_of_scope_items is not None else default_exclusions

    # Inspeccionar secciones activas (componentes y decisiones), ignorando la sección de contexto donde se cita el PRD
    active_sections_match = re.search(r"## 2\.\s*Catálogo de Componentes.*", body, re.DOTALL | re.IGNORECASE)
    active_text = active_sections_match.group(0) if active_sections_match else body

    for exclusion in active_exclusions:
        if re.search(r"\b" + re.escape(exclusion) + r"\b", active_text, re.IGNORECASE):
            violations.append(f"Violación de Anti-Amnesia: Reintroducción indebida de elemento OUT_OF_SCOPE ('{exclusion}')")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 02-architecture/SKILL.md y portable contienen las secciones y metadatos contractuales."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter de la Skill
        assert fm.get("name") == "architecture-design"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 2
        assert "prd-generation" in fm.get("depends_on", [])
        assert "description" in fm and len(fm["description"]) > 20

        # Secciones estructurales obligatorias (Contrato v2.0)
        required_headers = [
            "Overview",
            "Cuándo Usar",
            "Precondiciones",
            "Entradas",
            "Taxonomía de Decisiones",
            "Regla de Oro Anti-Amnesia",
            "Workflow de Elicitación",
            "Ejemplos de Calidad",
            "Señales de Alerta",
            "Contrato de Salida Formal",
            "Verificación del Artefacto",
            "Criterio de Término",
        ]
        for header in required_headers:
            assert header.lower() in body.lower(), f"Sección faltante en {path.name}: {header}"


# ==============================================================================
# TEST 2: Validación del Esquema de Salida (ARCHITECTURE Output Contract)
# ==============================================================================
def test_architecture_output_contract_schema():
    """Valida que una especificación de arquitectura cumple el esquema formal de frontmatter y secciones."""
    sample_arch = """---
project_id: "demo-retail-core"
project_name: "Demo Retail Core MVP"
version: 1
status: "APPROVED"
architecture_style: "monolith"
governance_level: "bajo"
created_at: "2026-10-07"
updated_at: "2026-10-07"
---

# Especificación de Arquitectura — Demo Retail Core MVP

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `APPROVED`)
- **Tipo de Proyecto:** web_app
- **Nivel de Gobernanza:** bajo

## 2. Catálogo de Componentes de Software (Components)
- **COMP-001 [catalog_service]:**
  - **Propósito:** Gestión de catálogo y búsqueda por texto.
  - **Responsabilidades:** Listar productos disponibles y filtrar por nombre.
  - **Requisitos Soportados:** REQ-001, REQ-002
- **COMP-002 [cart_service]:**
  - **Propósito:** Gestión de carrito en sesión.
  - **Responsabilidades:** Agregar ítems, modificar cantidades y calcular totales.
  - **Requisitos Soportados:** REQ-003, REQ-004

## 3. Registro de Decisiones Arquitectónicas (Architectural Decisions)
- **AD-001 (architecture.pattern):**
  - **Decisión:** Monolito simple.
  - **Justificación:** Máxima simplicidad operativa acorde a escala MVP (KISS).
- **AD-002 (communication.style):**
  - **Decisión:** In-process calls síncronas.
  - **Justificación:** Sin sobrecarga de red en proceso local.

## 4. Comunicación e Interacción entre Componentes
Los componentes interactúan mediante llamadas directas en memoria.

## 5. Estructura y Organización Lógica del Código
src/catalog/ y src/cart/.

## 6. Seguridad y Cumplimiento Normativo
Gobernanza baja: validación básica de inputs sin auth.

## 7. Decisiones Técnicas Delegadas (Downstream Scope)
- **Delegado a 03-data-modeling:** Modelos de persistencia y esquemas.
- **Delegado a 04-api-design:** Especificación formal de contratos de transporte.
"""
    fm, body = _extract_frontmatter_and_body(sample_arch)

    # Frontmatter obligatorio
    assert fm.get("project_id") == "demo-retail-core"
    assert isinstance(fm.get("version"), int)
    assert fm.get("status") in ["DRAFT", "APPROVED", "SUPERSEDED"]
    assert fm.get("architecture_style") in ["monolith", "modular_monolith", "microservices", "serverless"]
    assert fm.get("governance_level") in ["bajo", "medio", "alto"]

    # Secciones obligatorias
    required_sections = [
        "Contexto e Invariantes",
        "Catálogo de Componentes",
        "Registro de Decisiones Arquitectónicas",
        "Decisiones Técnicas Delegadas",
    ]
    for sec in required_sections:
        assert sec.lower() in body.lower(), f"Sección faltante en body de arquitectura: {sec}"


# ==============================================================================
# TEST 3: Unicidad y Formato Estable de IDs (COMP-xxx y AD-xxx)
# ==============================================================================
def test_architecture_unique_stable_ids():
    """Valida que los componentes COMP-xxx y las decisiones AD-xxx tengan IDs estables y sin duplicados."""
    sample_body = """
## 2. Catálogo de Componentes de Software
- **COMP-001 [catalog_service]:** Catálogo.
- **COMP-002 [cart_service]:** Carrito.

## 3. Registro de Decisiones Arquitectónicas
- **AD-001 (architecture.pattern):** Monolito.
- **AD-002 (communication.style):** In-process.
- **AD-003 (codebase.layout):** Por feature.
"""
    comp_matches = re.findall(r"-\s+\*\*(COMP-\d{3})", sample_body)
    ad_matches = re.findall(r"-\s+\*\*(AD-\d{3})", sample_body)

    assert len(comp_matches) >= 2, "Deben existir al menos 2 componentes definidos"
    assert len(comp_matches) == len(set(comp_matches)), f"COMP-xxx duplicados: {comp_matches}"

    assert len(ad_matches) >= 3, "Deben existir al menos 3 decisiones arquitectónicas AD-xxx"
    assert len(ad_matches) == len(set(ad_matches)), f"AD-xxx duplicadas: {ad_matches}"


# ==============================================================================
# TEST 4: Regla de Oro Anti-Amnesia y Detección de Violaciones de Scope
# ==============================================================================
def test_architecture_anti_amnesia_rules():
    """Verifica que el linter rechaza arquitecturas que intentan reintroducir elementos de OUT OF SCOPE."""
    bad_arch_body = """
## 2. Catálogo de Componentes de Software
- **COMP-001 [catalog_service]:** Catálogo.
- **COMP-002 [payment_service]:** Integración con pasarela de pago Stripe para checkout.

## 3. Registro de Decisiones Arquitectónicas
- **AD-001 (auth.strategy):** Autenticación JWT con tokens de sesión.
"""
    violations = lint_architecture_contract(bad_arch_body)
    assert len(violations) >= 2
    assert any("pasarela de pago" in v.lower() or "stripe" in v.lower() for v in violations)
    assert any("autenticación" in v.lower() for v in violations)

    # Verificar que las reglas anti-amnesia están explícitas en ambos archivos de skill
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "REGLA ESTRICTA DE ANTI-AMNESIA" in text or "Anti-Amnesia" in text
        assert "OUT OF SCOPE" in text
        assert "Amnesia de Scope" in text


# ==============================================================================
# TEST 5: Reglas de Delegación (Prohibición de DDL y Rutas HTTP Prematuras)
# ==============================================================================
def test_architecture_delegation_rules():
    """Verifica que el linter rechaza DDL SQL prematuro y rutas HTTP detalladas en arquitectura."""
    bad_premature_body = """
## 2. Catálogo de Componentes de Software
- **COMP-001 [catalog_service]:** Catálogo.

## 3. Registro de Decisiones Arquitectónicas
- **AD-001 (data.schema):**
  CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(255));
- **AD-002 (api.routes):**
  POST /api/v1/products para registrar ítems.
"""
    violations = lint_architecture_contract(bad_premature_body)
    assert len(violations) >= 2
    assert any("DDL prematura" in v for v in violations)
    assert any("rutas de endpoints HTTP" in v for v in violations)

    # Verificar que las prohibiciones constan en las Red Flags de la skill
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "Pre-especificación de Datos" in text
        assert "Pre-especificación de API" in text
        assert "03-data-modeling" in text
        assert "04-api-design" in text


def test_conforming_architecture_passes_linter():
    """Verifica que una arquitectura conforme al contrato pasa con 0 violaciones."""
    good_arch_body = """
## 2. Catálogo de Componentes de Software (Components)
- **COMP-001 [catalog_service]:** Encapsula el listado y búsqueda textual de productos.
- **COMP-002 [cart_service]:** Encapsula el cálculo de totales y estado del carrito en sesión.
- **COMP-003 [web_ui]:** Interfaz de usuario interactiva y presentación.

## 3. Registro de Decisiones Arquitectónicas (Architectural Decisions)
- **AD-001 (architecture.pattern):** Monolito modular.
- **AD-002 (communication.style):** In-process.
- **AD-003 (codebase.layout):** Por feature.
- **AD-004 (tech_stack):** Runtime ligero sin dependencias externas complejas.

## 7. Decisiones Técnicas Delegadas (Downstream Scope)
- **Delegado a 03-data-modeling:** Definición detallada de esquemas de datos.
- **Delegado a 04-api-design:** Contratos formales de API.
"""
    violations = lint_architecture_contract(good_arch_body)
    assert len(violations) == 0, f"Violaciones inesperadas: {violations}"


def test_docs_architecture_file_passes_linter():
    """Valida que el archivo docs/ARCHITECTURE.md generado en disco cumple 100% las reglas del contrato."""
    arch_file = ROOT_DIR / "docs" / "ARCHITECTURE.md"
    if not arch_file.exists():
        pytest.skip("docs/ARCHITECTURE.md aún no generado")

    content = arch_file.read_text(encoding="utf-8")
    fm, body = _extract_frontmatter_and_body(content)

    assert fm.get("project_id") == "catalogo-carrito-web"
    assert fm.get("status") in ["DRAFT", "APPROVED"]
    assert fm.get("governance_level") == "bajo"
    assert "architecture_style" in fm

    # Linter determinista
    out_of_scope = ["pasarelas de pago", "stripe", "autenticación", "registro de cuentas", "motores de recomendaciones"]
    violations = lint_architecture_contract(body, out_of_scope_items=out_of_scope)
    assert len(violations) == 0, f"Violaciones detectadas en docs/ARCHITECTURE.md: {violations}"

    # Unicidad de IDs
    comp_matches = re.findall(r"-\s+\*\*(COMP-\d{3})", body)
    ad_matches = re.findall(r"-\s+\*\*(AD-\d{3})", body)
    assert len(comp_matches) >= 2
    assert len(comp_matches) == len(set(comp_matches))
    assert len(ad_matches) >= 3
    assert len(ad_matches) == len(set(ad_matches))

