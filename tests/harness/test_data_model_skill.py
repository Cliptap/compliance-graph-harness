import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "03-data-modeling" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "03_data_modeling.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Modelo de Datos
# ==============================================================================
def lint_data_model_contract(body: str, out_of_scope_items: list[str] | None = None) -> list[str]:
    """Analizador determinista de cumplimiento de contrato de DATA_MODEL.md."""
    violations = []

    # 1. Aislamiento físico: No emitir allowed_paths ni rutas físicas de código
    if any(k in body for k in ["allowed_paths", "forbidden_paths"]):
        violations.append("Rutas de allowed_paths o forbidden_paths detectadas en el modelo de datos")

    # 2. No endpoints HTTP prematuros (delegado a 04-api-design)
    http_endpoint_pattern = r"\b(GET|POST|PUT|DELETE|PATCH)\s+/(api|v\d+)/"
    if re.search(http_endpoint_pattern, body, re.IGNORECASE):
        violations.append("Definición de rutas de endpoints HTTP detallada detectada: delegada a 04-api-design")

    # Separar sección activa (ignorar sección 1 de contexto donde se cita el PRD)
    active_sections_match = re.search(r"## 2\.\s*Entidades de Persistencia.*", body, re.DOTALL | re.IGNORECASE)
    active_text = active_sections_match.group(0) if active_sections_match else body

    # 3. Anti-Amnesia: Violación de OUT OF SCOPE heredado
    default_exclusions = [
        "usuario",
        "user",
        "password",
        "credential",
        "credencial",
        "role",
        "pago",
        "payment",
        "stripe",
        "tarjeta",
        "credit_card",
        "recommendation",
        "recomendación",
    ]
    active_exclusions = out_of_scope_items if out_of_scope_items is not None else default_exclusions

    for exclusion in active_exclusions:
        # Buscar como palabra completa
        pattern = r"\b" + re.escape(exclusion) + r"\b"
        if re.search(pattern, active_text, re.IGNORECASE):
            violations.append(f"Violación de Anti-Amnesia: Reintroducción indebida de concepto OUT_OF_SCOPE ('{exclusion}')")

    # 4. Coherencia con AD-003: No crear tablas relacionales server-side para el carrito
    server_section_match = re.search(
        r"## 2\.\s*Entidades de Persistencia del Servidor(.*?)(?=## 3\.|\Z)",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if server_section_match:
        server_content = server_section_match.group(1)
        cart_server_patterns = [
            r"ENT-\d{3}\s*\[.*?(cart|carrito).*?\]",
            r"\btable\s*:\s*(carts|cart_items|carritos)\b",
            r"\bpersistencia\s*:\s*(carts|cart_items|carritos)\b",
        ]
        for cp in cart_server_patterns:
            if re.search(cp, server_content, re.IGNORECASE):
                violations.append("Violación de AD-003: Se definió tabla relacional en servidor para carrito (debe residir en cliente Web Storage)")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 03-data-modeling/SKILL.md y portable contienen las secciones y metadatos contractuales."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter de la Skill
        assert fm.get("name") == "data-modeling"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 2
        assert "prd-generation" in fm.get("depends_on", [])
        assert "architecture-design" in fm.get("depends_on", [])
        assert "description" in fm and len(fm["description"]) > 20

        # Secciones estructurales obligatorias (Contrato v2.0)
        required_headers = [
            "Overview",
            "Cuándo Usar",
            "Precondiciones",
            "Entradas",
            "Taxonomía Formal",
            "Regla de Oro Anti-Amnesia",
            "Workflow de Elicitación",
            "Señales de Alerta",
            "Contrato de Salida Formal",
            "Verificación del Artefacto",
            "Criterio de Término",
        ]
        for header in required_headers:
            assert header.lower() in body.lower(), f"Sección faltante en {path.name}: {header}"


# ==============================================================================
# TEST 2: Validación del Esquema de Salida (DATA_MODEL Output Contract)
# ==============================================================================
def test_data_model_output_contract_schema():
    """Valida que una especificación de datos cumple el esquema formal de frontmatter y secciones."""
    sample_data_model = """---
project_id: "demo-retail-core"
project_name: "Demo Retail Core MVP"
version: 1
status: "APPROVED"
governance_level: "bajo"
persistence_target: "sqlite"
created_at: "2026-10-07"
updated_at: "2026-10-07"
---

# Especificación del Modelo de Datos — Demo Retail Core MVP

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `APPROVED`)
- **Arquitectura de Referencia:** `docs/ARCHITECTURE.md` (COMP-001, COMP-002, AD-003, AD-005)
- **Nivel de Gobernanza:** bajo
- **Restricciones:** OUT OF SCOPE sin pagos ni autenticación.

## 2. Entidades de Persistencia del Servidor (Server Data Model)
- **ENT-001 [Product]:**
  - Componente: COMP-001
  - Requisitos: REQ-001, REQ-002
  - Tabla: products (SQLite)
  - Atributos:
    - id: Integer, Primary Key, Autoincrement
    - name: String(255), Not Null
    - description: String(1000), Nullable
    - price: Numeric(10, 2), Not Null
  - Índices: IDX-001 (name)

## 3. Esquema de Datos del Lado Cliente (Client Storage Model)
- **DTO-CART-001 [CartItem]:**
  - Componente: COMP-002
  - Requisitos: REQ-003, REQ-004
  - Almacenamiento: Web Storage (LocalStorage) — Conforme a AD-003
  - Campos: product_id, name, unit_price, quantity, subtotal

## 4. Índices y Optimización de Consultas
- **IDX-001 [idx_product_name]:** Búsqueda textual sobre name para REQ-002.

## 5. Invariantes y Reglas de Integridad
- **INV-001 (price_positive):** price >= 0.0
- **INV-002 (quantity_positive):** quantity > 0

## 6. Datos Semilla e Inicialización (Seed Data)
- **SEED-001:** Catálogo inicial de 5 productos demostrativos.
"""
    fm, body = _extract_frontmatter_and_body(sample_data_model)

    # Frontmatter obligatorio
    assert fm.get("project_id") == "demo-retail-core"
    assert isinstance(fm.get("version"), int)
    assert fm.get("status") in ["DRAFT", "APPROVED", "SUPERSEDED"]
    assert fm.get("governance_level") in ["bajo", "medio", "alto"]
    assert fm.get("persistence_target") == "sqlite"

    # Secciones obligatorias
    required_sections = [
        "Contexto e Invariantes",
        "Entidades de Persistencia del Servidor",
        "Esquema de Datos del Lado Cliente",
        "Índices y Optimización",
        "Invariantes y Reglas de Integridad",
        "Datos Semilla",
    ]
    for sec in required_sections:
        assert sec.lower() in body.lower(), f"Sección faltante en body de datos: {sec}"


# ==============================================================================
# TEST 3: Unicidad y Formato Estable de IDs (ENT-xxx, DTO-CART-xxx, INV-xxx, etc.)
# ==============================================================================
def test_data_model_unique_stable_ids():
    """Valida que los IDs formales tengan formatos estables y sin duplicados."""
    sample_body = """
## 2. Entidades de Persistencia del Servidor
- **ENT-001 [Product]:** Catálogo.
- **ENT-002 [Category]:** Categorías opcionales.

## 3. Esquema de Datos del Lado Cliente
- **DTO-CART-001 [CartItem]:** Ítem de carrito.

## 4. Índices y Optimización
- **IDX-001 [idx_product_name]:** Índice para búsqueda.

## 5. Invariantes y Reglas de Integridad
- **INV-001 (price_positive):** price >= 0.0.
- **INV-002 (quantity_positive):** quantity > 0.
"""
    ent_matches = re.findall(r"-\s+\*\*(ENT-\d{3})", sample_body)
    dto_matches = re.findall(r"-\s+\*\*(DTO-CART-\d{3})", sample_body)
    idx_matches = re.findall(r"-\s+\*\*(IDX-\d{3})", sample_body)
    inv_matches = re.findall(r"-\s+\*\*(INV-\d{3})", sample_body)

    assert len(ent_matches) >= 1
    assert len(ent_matches) == len(set(ent_matches)), f"ENT-xxx duplicados: {ent_matches}"

    assert len(dto_matches) >= 1
    assert len(dto_matches) == len(set(dto_matches)), f"DTO-CART-xxx duplicados: {dto_matches}"

    assert len(idx_matches) >= 1
    assert len(idx_matches) == len(set(idx_matches)), f"IDX-xxx duplicados: {idx_matches}"

    assert len(inv_matches) >= 2
    assert len(inv_matches) == len(set(inv_matches)), f"INV-xxx duplicados: {inv_matches}"


# ==============================================================================
# TEST 4: Regla de Oro Anti-Amnesia y Detección de Violaciones de Scope
# ==============================================================================
def test_data_model_anti_amnesia_rules():
    """Verifica que el linter rechaza modelos de datos que reintroducen entidades OUT OF SCOPE."""
    bad_data_body = """
## 2. Entidades de Persistencia del Servidor
- **ENT-001 [Product]:** Catálogo.
- **ENT-002 [User]:** Tabla de usuarios para inicio de sesión con password hash.
- **ENT-003 [Payment]:** Registro de pagos y cobros procesados.
"""
    violations = lint_data_model_contract(bad_data_body)
    assert len(violations) >= 2
    assert any("user" in v.lower() or "usuario" in v.lower() for v in violations)
    assert any("pago" in v.lower() or "payment" in v.lower() for v in violations)

    # Verificar que las reglas constan en ambos archivos de skill
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "REGLA ESTRICTA DE ANTI-AMNESIA" in text or "Anti-Amnesia" in text
        assert "OUT OF SCOPE" in text
        assert "Amnesia de Scope" in text


# ==============================================================================
# TEST 5: Coherencia con Arquitectura (Respeto a AD-003 de Carrito en Cliente)
# ==============================================================================
def test_data_model_coherence_with_architecture():
    """Verifica que el linter rechaza crear tablas de base de datos de servidor para el carrito."""
    bad_cart_server_body = """
## 2. Entidades de Persistencia del Servidor
- **ENT-001 [Product]:** Catálogo.
- **ENT-002 [Cart]:**
  - Componente: COMP-002
  - Tabla: carts (SQLite)
  - Atributos: id, total

## 3. Esquema de Datos del Lado Cliente
- **DTO-CART-001 [CartItem]:** Ítem.
"""
    violations = lint_data_model_contract(bad_cart_server_body)
    assert len(violations) >= 1
    assert any("AD-003" in v for v in violations)

    # Verificar que el respeto a AD-003 y AD-005 consta en las skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "AD-003" in text
        assert "AD-005" in text
        assert "LocalStorage" in text or "Web Storage" in text


# ==============================================================================
# TEST 6: Detección de Antipatrones (Aislamiento Físico y Endpoints HTTP)
# ==============================================================================
def test_data_model_linter_detects_anti_patterns():
    """Verifica que el linter rechaza allowed_paths físicas y endpoints HTTP prematuros."""
    bad_premature_body = """
## 2. Entidades de Persistencia del Servidor
- **ENT-001 [Product]:** Catálogo.
  - allowed_paths: ["src/models/product.py"]
  - API: GET /api/v1/products para consultar
"""
    violations = lint_data_model_contract(bad_premature_body)
    assert len(violations) >= 2
    assert any("allowed_paths" in v for v in violations)
    assert any("endpoints HTTP" in v for v in violations)


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_data_model_passes_linter():
    """Verifica que un modelo conforme al contrato pasa con 0 violaciones."""
    good_data_body = """
## 2. Entidades de Persistencia del Servidor (Server Data Model)
- **ENT-001 [Product]:**
  - Componente: COMP-001
  - Requisitos: REQ-001, REQ-002
  - Tabla: products (SQLite)
  - Atributos:
    - id: Integer, Primary Key, Autoincrement
    - name: String(255), Not Null
    - description: String(1000), Nullable
    - price: Numeric(10, 2), Not Null
  - Índices: IDX-001 (name)

## 3. Esquema de Datos del Lado Cliente (Client Storage Model)
- **DTO-CART-001 [CartItem]:**
  - Componente: COMP-002
  - Requisitos: REQ-003, REQ-004
  - Almacenamiento: Web Storage (LocalStorage) — Conforme a AD-003
  - Campos: product_id, name, unit_price, quantity, subtotal

## 4. Índices y Optimización de Consultas
- **IDX-001 [idx_product_name]:** Búsqueda por nombre (REQ-002).

## 5. Invariantes y Reglas de Integridad
- **INV-001 (price_positive):** price >= 0.0
- **INV-002 (quantity_positive):** quantity > 0

## 6. Datos Semilla e Inicialización (Seed Data)
- **SEED-001:** Catálogo inicial de productos demostrativos.
"""
    violations = lint_data_model_contract(good_data_body)
    assert len(violations) == 0, f"Violaciones inesperadas: {violations}"


def test_docs_data_model_file_passes_linter_if_exists():
    """Valida que si docs/DATA_MODEL.md existe en disco, cumpla 100% las reglas del contrato."""
    data_file = ROOT_DIR / "docs" / "DATA_MODEL.md"
    if not data_file.exists():
        pytest.skip("docs/DATA_MODEL.md aún no generado (esperado en Etapa B)")

    content = data_file.read_text(encoding="utf-8")
    fm, body = _extract_frontmatter_and_body(content)

    assert fm.get("project_id") == "catalogo-carrito-web"
    assert fm.get("status") in ["DRAFT", "APPROVED"]
    assert fm.get("governance_level") == "bajo"
    assert fm.get("persistence_target") == "sqlite"

    violations = lint_data_model_contract(body)
    assert len(violations) == 0, f"Violaciones detectadas en docs/DATA_MODEL.md: {violations}"
