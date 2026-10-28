import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "04-api-design" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "04_api_design.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Diseño de API
# ==============================================================================
def lint_api_design_contract(body: str, out_of_scope_items: list[str] | None = None) -> list[str]:
    """Analizador determinista de cumplimiento de contrato de API_DESIGN.md."""
    violations = []

    # 1. Aislamiento físico: No emitir allowed_paths ni código ejecutable de framework
    if any(k in body for k in ["allowed_paths", "forbidden_paths"]):
        violations.append("Rutas de allowed_paths o forbidden_paths detectadas en el diseño de API")
    if re.search(r"\b(from\s+fastapi\s+import|APIRouter\(|class\s+\w+\(BaseModel\))", body):
        violations.append("Código ejecutable de framework detectado en el diseño de API: delegado a 05-backend")

    # Separar sección activa (ignorar sección 1 de contexto donde se cita el PRD / arquitectura)
    active_sections_match = re.search(r"## 2\.\s*Catálogo de Endpoints.*", body, re.DOTALL | re.IGNORECASE)
    active_text = active_sections_match.group(0) if active_sections_match else body

    # 2. Anti-Amnesia: Violación de OUT OF SCOPE heredado
    default_exclusions = [
        "usuario",
        "user",
        "password",
        "credential",
        "credencial",
        "role",
        "jwt",
        "token",
        "auth",
        "login",
        "pago",
        "payment",
        "stripe",
        "tarjeta",
        "credit_card",
        "checkout",
        "recommendation",
        "recomendación",
    ]
    active_exclusions = out_of_scope_items if out_of_scope_items is not None else default_exclusions

    for exclusion in active_exclusions:
        pattern = r"\b" + re.escape(exclusion) + r"\b"
        if re.search(pattern, active_text, re.IGNORECASE):
            violations.append(f"Violación de Anti-Amnesia: Reintroducción indebida de concepto OUT_OF_SCOPE ('{exclusion}')")

    # 3. Coherencia con AD-003: No crear endpoints server-side para el carrito
    cart_server_patterns = [
        r"\b(GET|POST|PUT|DELETE|PATCH)\s+/(api/v\d+/)?(carts|cart_items|carritos)\b",
        r"EP-\d{3}\s*\[.*?(cart|carrito).*?\]",
    ]
    for cp in cart_server_patterns:
        if re.search(cp, active_text, re.IGNORECASE):
            violations.append("Violación de AD-003: Se definió endpoint server-side para carrito (debe residir en cliente Web Storage)")

    # 4. No-Goldplating: En este MVP la API de servidor debe ser estrictamente de solo lectura (únicamente GET)
    mutation_patterns = [
        r"\b(POST|PUT|PATCH|DELETE)\s+/(api/v\d+/)?products\b",
        r"\b(POST|PUT|PATCH|DELETE)\s+/(api/v\d+/)?productos\b",
        r"-\s*Método:\s*(POST|PUT|PATCH|DELETE)\b",
        r"-\s*Method:\s*(POST|PUT|PATCH|DELETE)\b",
        r"EP-\d{3}\s*\[.*?(create|update|delete|patch|eliminar|actualizar|crear|mutar).*?\]",
    ]
    for mp in mutation_patterns:
        if re.search(mp, active_text, re.IGNORECASE):
            violations.append("Violación de No-Goldplating: Se detectó método HTTP de mutación (POST/PUT/PATCH/DELETE) no respaldado en el PRD")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 04-api-design/SKILL.md y portable contienen las secciones y metadatos contractuales."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter de la Skill
        assert fm.get("name") == "api-design"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 3
        assert "prd-generation" in fm.get("depends_on", [])
        assert "architecture-design" in fm.get("depends_on", [])
        assert "data-modeling" in fm.get("depends_on", [])
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

        # Verificación del estándar metodológico genérico y sección de contexto de referencia
        assert "bounded context" in body.lower() or "contexto acotado" in body.lower(), (
            f"Falta estándar de delimitación de bounded context en {path.name}"
        )
        assert "upstream" in body.lower(), f"Falta referencia a trazabilidad upstream en {path.name}"
        assert "Reference Context: Demo Implementation" in body, (
            f"Falta sección de contexto de referencia de demo en {path.name}"
        )


# ==============================================================================
# TEST 2: Validación del Esquema de Salida (API_DESIGN Output Contract)
# ==============================================================================
def test_api_design_output_contract_schema():
    """Valida que una especificación de API cumple el esquema formal de frontmatter y secciones."""
    sample_api_design = """---
project_id: "demo-retail-core"
project_name: "Demo Retail Core MVP"
version: 1
status: "APPROVED"
governance_level: "bajo"
api_style: "REST"
base_path: "/api/v1"
created_at: "2026-10-07"
updated_at: "2026-10-07"
---

# Especificación de Diseño de API — Demo Retail Core MVP

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `APPROVED`)
- **Arquitectura de Referencia:** `docs/ARCHITECTURE.md` (COMP-001, COMP-002, AD-002, AD-003, AD-005)
- **Modelo de Datos de Referencia:** `docs/DATA_MODEL.md` (ENT-001, DTO-CART-001)
- **Nivel de Gobernanza:** bajo
- **Restricciones:** OUT OF SCOPE sin pagos ni autenticación.

## 2. Catálogo de Endpoints de Servidor (Server Endpoints)
- **EP-001 [list_products]:**
  - Método: GET
  - Ruta: /api/v1/products
  - Query Params: q (String, opcional)
  - Respuestas: 200 OK (DTO-PROD-LIST-001), 400 Bad Request (DTO-ERR-001)
- **EP-002 [get_product_by_id]:**
  - Método: GET
  - Ruta: /api/v1/products/{id}
  - Path Params: id (Integer >= 1)
  - Respuestas: 200 OK (DTO-PROD-RES-001), 404 Not Found (DTO-ERR-001)

## 3. Esquemas de Transferencia de Datos (DTO Schemas)
- **DTO-PROD-RES-001 [ProductResponse]:** id, name, description, price
- **DTO-PROD-LIST-001 [ProductListResponse]:** Envelope { items: list, total: int }
- **DTO-ERR-001 [ErrorResponse]:** error_code, message, detail

## 4. Mapeo de Códigos de Estado y Manejo de Errores
- **ERR-001 [PRODUCT_NOT_FOUND]:** HTTP 404
- **ERR-002 [INVALID_PARAMETER]:** HTTP 400

## 5. Gestión de Carrito en Cliente y Desacoplamiento de Servidor
Conforme a AD-003, el carrito no tiene endpoints en servidor y reside en cliente.

## 6. Seguridad de Transporte y Gobernanza
Visitante anónimo sin credenciales.

## 7. Matriz de Linaje Contractual y Trazabilidad
Mapeo REQ-001 -> EP-001.
"""
    fm, body = _extract_frontmatter_and_body(sample_api_design)

    # Frontmatter obligatorio
    assert fm.get("project_id") == "demo-retail-core"
    assert isinstance(fm.get("version"), int)
    assert fm.get("status") in ["DRAFT", "APPROVED", "SUPERSEDED"]
    assert fm.get("governance_level") in ["bajo", "medio", "alto"]
    assert fm.get("api_style") == "REST"
    assert fm.get("base_path") == "/api/v1"

    # Secciones obligatorias
    required_sections = [
        "Contexto e Invariantes",
        "Catálogo de Endpoints",
        "Esquemas de Transferencia",
        "Manejo de Errores",
        "Gestión de Carrito en Cliente",
        "Matriz de Linaje",
    ]
    for sec in required_sections:
        assert sec.lower() in body.lower(), f"Sección faltante en body de API: {sec}"


# ==============================================================================
# TEST 3: Unicidad y Formato Estable de IDs (EP-xxx, DTO-xxx, ERR-xxx)
# ==============================================================================
def test_api_design_unique_stable_ids():
    """Valida que los IDs formales de API tengan formatos estables y sin duplicados."""
    sample_body = """
## 2. Catálogo de Endpoints de Servidor
- **EP-001 [list_products]:** Listar catálogo.
- **EP-002 [get_product_by_id]:** Obtener producto por ID.

## 3. Esquemas de Transferencia de Datos
- **DTO-PROD-RES-001 [ProductResponse]:** Detalle unitario.
- **DTO-PROD-LIST-001 [ProductListResponse]:** Lista en envelope.
- **DTO-ERR-001 [ErrorResponse]:** Error estructurado.

## 4. Mapeo de Códigos de Estado y Manejo de Errores
- **ERR-001 [PRODUCT_NOT_FOUND]:** Error 404.
- **ERR-002 [INVALID_PARAMETER]:** Error 400.
"""
    ep_matches = re.findall(r"-\s+\*\*(EP-\d{3})", sample_body)
    dto_matches = re.findall(r"-\s+\*\*(DTO-[A-Z0-9\-]+)", sample_body)
    err_matches = re.findall(r"-\s+\*\*(ERR-\d{3})", sample_body)

    assert len(ep_matches) >= 2, f"EP-xxx insuficientes: {ep_matches}"
    assert len(ep_matches) == len(set(ep_matches)), f"EP-xxx duplicados: {ep_matches}"

    assert len(dto_matches) >= 3, f"DTO-xxx insuficientes: {dto_matches}"
    assert len(dto_matches) == len(set(dto_matches)), f"DTO-xxx duplicados: {dto_matches}"

    assert len(err_matches) >= 2, f"ERR-xxx insuficientes: {err_matches}"
    assert len(err_matches) == len(set(err_matches)), f"ERR-xxx duplicados: {err_matches}"


# ==============================================================================
# TEST 4: Regla de Oro Anti-Amnesia y Detección de Violaciones de Scope
# ==============================================================================
def test_api_design_anti_amnesia_rules():
    """Verifica que el linter rechaza diseños de API que reintroducen endpoints OUT OF SCOPE."""
    bad_api_body = """
## 2. Catálogo de Endpoints de Servidor
- **EP-001 [list_products]:** GET /api/v1/products.
- **EP-002 [login_user]:** POST /api/v1/auth/login para autenticar usuario con password.
- **EP-003 [checkout_payment]:** POST /api/v1/payments/checkout para procesar pago con tarjeta stripe.
"""
    violations = lint_api_design_contract(bad_api_body)
    assert len(violations) >= 2
    assert any("user" in v.lower() or "usuario" in v.lower() or "auth" in v.lower() for v in violations)
    assert any("pago" in v.lower() or "payment" in v.lower() or "stripe" in v.lower() or "checkout" in v.lower() for v in violations)

    # Verificar que las reglas constan en ambos archivos de skill
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "REGLA ESTRICTA DE ANTI-AMNESIA" in text or "Anti-Amnesia" in text
        assert "OUT OF SCOPE" in text
        assert "Amnesia de Scope" in text


# ==============================================================================
# TEST 5: Coherencia con Arquitectura y Data Model (Respeto a AD-003)
# ==============================================================================
def test_api_design_coherence_with_architecture_and_data_model():
    """Verifica que el linter rechaza endpoints server-side para persistir carritos."""
    bad_cart_server_body = """
## 2. Catálogo de Endpoints de Servidor
- **EP-001 [list_products]:** GET /api/v1/products.
- **EP-002 [create_cart]:** POST /api/v1/carts para inicializar carrito en base de datos.
- **EP-003 [add_cart_item]:** POST /api/v1/carts/{id}/items para agregar producto.
"""
    violations = lint_api_design_contract(bad_cart_server_body)
    assert len(violations) >= 1
    assert any("AD-003" in v for v in violations)

    # Verificar que el respeto a AD-003 y Web Storage consta en las skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "AD-003" in text
        assert "LocalStorage" in text or "Web Storage" in text


# ==============================================================================
# TEST 6: Detección y Rechazo de Goldplating (Endpoints de Mutación no Respaldados)
# ==============================================================================
def test_api_design_no_goldplating_mutation_endpoints():
    """Verifica que el linter rechaza métodos HTTP de mutación (POST/PUT/PATCH/DELETE) para el catálogo MVP."""
    bad_mutation_body = """
## 2. Catálogo de Endpoints de Servidor
- **EP-001 [list_products]:** GET /api/v1/products.
- **EP-002 [create_product]:** POST /api/v1/products para registrar nuevo ítem.
- **EP-003 [delete_product]:** DELETE /api/v1/products/{id} para dar de baja.
"""
    violations = lint_api_design_contract(bad_mutation_body)
    assert len(violations) >= 1
    assert any("No-Goldplating" in v or "mutación" in v for v in violations)

    # Verificar que la prohibición de mutación consta en las Red Flags de la skill
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "Goldplating de Mutación" in text or "solo lectura" in text.lower()


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_api_design_passes_linter():
    """Verifica que una especificación canónica y conforme al contrato pasa con 0 violaciones."""
    good_api_body = """
## 2. Catálogo de Endpoints de Servidor (Server Endpoints)
- **EP-001 [list_products]:**
  - Método: GET
  - Ruta: /api/v1/products
  - Query Params: q (String, opcional)
  - Respuestas: 200 OK (DTO-PROD-LIST-001), 400 Bad Request (DTO-ERR-001)
- **EP-002 [get_product_by_id]:**
  - Método: GET
  - Ruta: /api/v1/products/{id}
  - Path Params: id (Integer >= 1)
  - Respuestas: 200 OK (DTO-PROD-RES-001), 404 Not Found (DTO-ERR-001)

## 3. Esquemas de Transferencia de Datos (DTO Schemas)
- **DTO-PROD-RES-001 [ProductResponse]:** id, name, description, price
- **DTO-PROD-LIST-001 [ProductListResponse]:** Envelope { items: list, total: int }
- **DTO-ERR-001 [ErrorResponse]:** error_code, message, detail

## 4. Mapeo de Códigos de Estado y Manejo de Errores
- **ERR-001 [PRODUCT_NOT_FOUND]:** HTTP 404
- **ERR-002 [INVALID_PARAMETER]:** HTTP 400

## 5. Gestión de Carrito en Cliente y Desacoplamiento de Servidor
Conforme a AD-003, el estado del carrito reside íntegramente en el cliente (LocalStorage).
"""
    violations = lint_api_design_contract(good_api_body)
    assert len(violations) == 0, f"Violaciones inesperadas: {violations}"


def test_docs_api_design_file_passes_linter_if_exists():
    """Valida que si docs/API_DESIGN.md existe en disco, cumpla 100% las reglas del contrato."""
    api_file = ROOT_DIR / "docs" / "API_DESIGN.md"
    if not api_file.exists():
        pytest.skip("docs/API_DESIGN.md aún no generado (esperado en Etapa C)")

    content = api_file.read_text(encoding="utf-8")
    fm, body = _extract_frontmatter_and_body(content)

    assert fm.get("project_id") == "catalogo-carrito-web"
    assert fm.get("status") in ["DRAFT", "APPROVED"]
    assert fm.get("governance_level") == "bajo"
    assert fm.get("api_style") == "REST"
    assert fm.get("base_path") == "/api/v1"

    violations = lint_api_design_contract(body)
    assert len(violations) == 0, f"Violaciones detectadas en docs/API_DESIGN.md: {violations}"
