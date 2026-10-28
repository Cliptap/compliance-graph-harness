import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "08-testing" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "08_testing_strategy.md"
DOCS_TEST_PLAN_PATH = ROOT_DIR / "docs" / "TEST_PLAN.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Estrategia de Testing (testing-strategy)
# ==============================================================================
def lint_testing_strategy_contract(
    spec_or_doc: str,
    allowed_paths: list[str] | None = None,
    out_of_scope_patterns: list[str] | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para testing-strategy."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            if normalized_ap.startswith("src/"):
                violations.append(
                    f"Invasión perimetral de TaskSpec: '{ap}' modifica código fuente en src/ (testing-strategy no muta producción)"
                )

    active_text = spec_or_doc

    # 2. Anti-Amnesia y Detección de Tests Huérfanos (Orphan Tests)
    orphan_test_patterns = [
        (r"\bdef\s+test_[a-zA-Z0-9_]*(login|iniciar_sesion|signin)", "Test huérfano de login/inicio de sesión fuera de alcance"),
        (r"\bdef\s+test_[a-zA-Z0-9_]*(password|contraseña|contrasena)", "Test huérfano de contraseñas fuera de alcance"),
        (r"\bdef\s+test_[a-zA-Z0-9_]*(jwt|token_auth|access_token)", "Test huérfano de tokens de sesión fuera de alcance"),
        (r"\bdef\s+test_[a-zA-Z0-9_]*(stripe|paypal|checkout|payment|pago)", "Test huérfano de pagos o checkout fuera de alcance"),
        (r"\b(test_user_registration|test_crear_usuario)\b", "Test huérfano de registro de usuarios fuera de alcance"),
    ]
    for pattern, reason in orphan_test_patterns:
        m = re.search(pattern, active_text, re.IGNORECASE)
        if m:
            violations.append(f"Violación de Anti-Amnesia / Test Huérfano: {reason} ('{m.group(0)}')")

    # 3. Verificación de Contrato de Artefacto (si es docs/TEST_PLAN.md)
    if "# docs/TEST_PLAN.md" in active_text or "Plan Integral y Estrategia de Testing" in active_text:
        # Frontmatter y metadatos
        if "---" in active_text:
            try:
                fm, _ = _extract_frontmatter_and_body(active_text)
                if not fm.get("status"):
                    violations.append("Falta campo 'status' en frontmatter de TEST_PLAN.md")
                if not fm.get("acceptance_coverage"):
                    violations.append("Falta campo 'acceptance_coverage' en frontmatter de TEST_PLAN.md")
                if not fm.get("total_tests_active"):
                    violations.append("Falta campo 'total_tests_active' en frontmatter de TEST_PLAN.md")
            except Exception as e:
                violations.append(f"Error parseando frontmatter de TEST_PLAN.md: {e}")

        # Mapeo exhaustivo de criterios de aceptación del PRD
        required_criteria = ["AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"]
        for ac in required_criteria:
            if ac not in active_text:
                violations.append(f"Criterio de aceptación no cubierto en matriz de TEST_PLAN.md: {ac}")

        # Secciones obligatorias
        required_sections = [
            "Identidad y Objetivos de Calidad",
            "Matriz Bidireccional de Trazabilidad",
            "Métricas Deterministas de Cobertura",
            "Pirámide de Pruebas e Inventario de Suites",
            "Auditoría de Anomalías de Testing",
            "Guía de Ejecución Determinista",
        ]
        for sec in required_sections:
            if sec not in active_text:
                violations.append(f"Sección obligatoria faltante en TEST_PLAN.md: {sec}")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias v2.0
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 08-testing/SKILL.md y su versión portable contienen las secciones y metadatos contractuales v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo de skill no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter normativo
        assert fm.get("name") == "testing-strategy"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 7
        assert "prd-generation" in fm.get("depends_on", [])
        assert "architecture-design" in fm.get("depends_on", [])
        assert "data-modeling" in fm.get("depends_on", [])
        assert "api-design" in fm.get("depends_on", [])
        assert "backend-implementation" in fm.get("depends_on", [])
        assert "frontend-implementation" in fm.get("depends_on", [])
        assert "auth-governance" in fm.get("depends_on", [])
        assert fm.get("produces_artifact") == "docs/TEST_PLAN.md"
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
# TEST 2: Validación del Esquema de TaskSpec y Delimitación Perimetral
# ==============================================================================
def test_testing_skill_contract_schema_and_taskspec():
    """Valida que la skill define formalmente TaskSpec con allowed_paths y forbidden_paths."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "docs/TEST_PLAN.md" in content
        assert "src/**" in content


# ==============================================================================
# TEST 3: Especificación de Acceptance Coverage y Función Transversal
# ==============================================================================
def test_transversal_acceptance_coverage_specification():
    """Valida que la skill define la fórmula matemática y la función transversal de testing."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        parts = content.split("## Reference Context: Demo Implementation")
        normative = parts[0]
        ref_context = parts[1] if len(parts) > 1 else ""

        # Estándar metodológico en el cuerpo normativo:
        assert "Acceptance Coverage" in normative
        assert "(AC con test aprobado / AC totales)" in normative
        assert "transversal" in normative.lower()
        assert "Matriz Bidireccional de Trazabilidad" in normative
        assert "AC-xxx" in normative

        # La lista concreta de criterios de la demo solo vive en Reference Context:
        assert "AC-006" not in normative
        assert "AC-001" in ref_context
        assert "AC-006" in ref_context


# ==============================================================================
# TEST 4: Reglas Anti-Amnesia y Detección de Tests Huérfanos
# ==============================================================================
def test_anti_amnesia_and_orphan_test_detection_rules():
    """Verifica que el linter rechaza planes o código con tests para login, passwords o pagos."""
    toxic_test_plan = """
def test_login_user_with_jwt():
    assert True

def test_stripe_payment_processing():
    assert True
"""
    violations = lint_testing_strategy_contract(toxic_test_plan)
    assert len(violations) >= 2
    assert any("login" in v.lower() for v in violations)
    assert any("pago" in v.lower() or "payment" in v.lower() for v in violations)


# ==============================================================================
# TEST 5: Detección de Tests Tautológicos y Criterios sin Test
# ==============================================================================
def test_tautological_and_uncovered_ac_detection_rules():
    """Valida que la skill prescribe la prevención de tests tautológicos y AC huérfanos."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        parts = content.split("## Reference Context: Demo Implementation")
        normative = parts[0]
        ref_context = parts[1] if len(parts) > 1 else ""

        assert "tautológico" in normative.lower() or "tautologicos" in normative.lower()
        assert "huérfano" in normative.lower() or "huerfano" in normative.lower()

        # Regla genérica de invariantes en el cuerpo normativo:
        assert "INV-xxx" in normative
        assert "docs/DATA_MODEL.md" in normative

        # Invariantes concretas del carrito de la demo solo en Reference Context:
        assert "INV-002" not in normative
        assert "INV-004" not in normative
        assert "INV-002" in ref_context
        assert "INV-004" in ref_context


# ==============================================================================
# TEST 5b: Separación entre Cuerpo Normativo Genérico y Reference Context Demo
# ==============================================================================
def test_normative_body_is_decoupled_from_demo():
    """Valida que el cuerpo normativo es agnóstico y la instanciación demo vive en Reference Context."""
    demo_strings = [
        "catalogo-carrito-web",
        "tests/catalog",
        "carrito",
        "SEED-001",
        "localStorage",
        "AD-003",
        "test_catalog_backend.py",
        "test_cart_invariants_and_storage_contract",
    ]
    normative_only_forbidden = ["src/catalog"]
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "## Reference Context: Demo Implementation (catalogo-carrito-web)" in content
        parts = content.split("## Reference Context: Demo Implementation")
        assert len(parts) == 2, f"Se esperaba exactamente una sección Reference Context en {path.name}"
        normative, ref_context = parts

        # Placeholders genéricos en el cuerpo normativo:
        assert "tests/<bounded_context>/" in normative

        for demo in demo_strings:
            assert demo not in normative, f"Acoplamiento demo '{demo}' en el cuerpo normativo de {path.name}"
            assert demo in ref_context, f"Hecho demo '{demo}' perdido en Reference Context de {path.name}"
        for demo in normative_only_forbidden:
            assert demo not in normative, f"Acoplamiento demo '{demo}' en el cuerpo normativo de {path.name}"


# ==============================================================================
# TEST 6: Esquema del Artefacto de Salida (docs/TEST_PLAN.md)
# ==============================================================================
def test_test_plan_output_contract_schema():
    """Valida que la skill prescribe las 6 secciones requeridas para docs/TEST_PLAN.md."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "Identidad y Objetivos de Calidad" in content
        assert "Matriz Bidireccional de Trazabilidad" in content
        assert "Métricas Deterministas de Cobertura" in content
        assert "Pirámide de Pruebas e Inventario de Suites" in content
        assert "Auditoría de Anomalías de Testing" in content
        assert "Guía de Ejecución Determinista" in content


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_test_plan_passes_linter():
    """Verifica que un documento conforme de Test Plan pasa el linter con 0 violaciones."""
    clean_test_plan = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
acceptance_coverage: "100.0%"
total_tests_active: 100
last_audit: "2026-10-21"
---

# docs/TEST_PLAN.md — Plan Integral y Estrategia de Testing

## 1. Identidad y Objetivos de Calidad
Aseguramiento de calidad determinista para catalogo-carrito-web.

## 2. Matriz Bidireccional de Trazabilidad (AC-xxx -> Test-xxx)
- AC-001 -> test_list_all_products_returns_seed_envelope
- AC-002 -> test_search_products_case_insensitive_match
- AC-003 -> test_search_products_no_match_returns_empty_list
- AC-004 -> test_cart_invariants_and_storage_contract
- AC-005 -> test_cart_invariants_and_storage_contract
- AC-006 -> test_cart_invariants_and_storage_contract

## 3. Métricas Deterministas de Cobertura
Acceptance Coverage: (6 / 6) = 100.0%.

## 4. Pirámide de Pruebas e Inventario de Suites
Suites activas: tests/harness, tests/catalog, tests/frontend.

## 5. Auditoría de Anomalías de Testing
0 AC sin test, 0 tests huérfanos, 0 tests tautológicos.

## 6. Guía de Ejecución Determinista y Quality Gates para CI/CD
Comando: pytest tests/harness/ tests/catalog/ tests/frontend/ -v
"""
    violations = lint_testing_strategy_contract(clean_test_plan, allowed_paths=["docs/TEST_PLAN.md"])
    assert len(violations) == 0, f"Violaciones inesperadas en test plan conforme: {violations}"


# ==============================================================================
# TEST 8: Cobertura Física Actual de Criterios de Aceptación (AC-001..AC-006)
# ==============================================================================
def test_active_repository_acceptance_criteria_coverage():
    """Inspecciona tests/ y verifica deterministamente que AC-001 a AC-006 tienen al menos un test activo."""
    backend_tests_path = ROOT_DIR / "tests" / "catalog" / "test_catalog_backend.py"
    frontend_tests_path = ROOT_DIR / "tests" / "frontend" / "test_catalog_frontend.py"

    assert backend_tests_path.exists(), "Falta suite de backend en tests/catalog/"
    assert frontend_tests_path.exists(), "Falta suite de frontend en tests/frontend/"

    backend_code = backend_tests_path.read_text(encoding="utf-8")
    frontend_code = frontend_tests_path.read_text(encoding="utf-8")
    combined_tests = backend_code + "\n" + frontend_code

    # 1. AC-001: Listado completo y renderizado
    assert "test_list_all_products_returns_seed_envelope" in backend_code
    assert "test_html_semantic_markup_and_ids" in frontend_code

    # 2. AC-002: Búsqueda textual insensible
    assert "test_search_products_case_insensitive_match" in backend_code

    # 3. AC-003: Empty state ante búsqueda sin resultados
    assert "test_search_products_no_match_returns_empty_list" in backend_code

    # 4. AC-004: Adición al carrito
    assert "test_cart_invariants_and_storage_contract" in frontend_code

    # 5. AC-005: Modificación de cantidad y remoción ante < 1
    assert "INV-002" in frontend_code

    # 6. AC-006: Cálculo automático de subtotales y total
    assert "INV-004" in frontend_code


# ==============================================================================
# TEST 9: Ausencia Física de Tests Huérfanos para Funcionalidades OUT OF SCOPE
# ==============================================================================
def test_active_repository_no_orphan_tests_for_out_of_scope():
    """Inspecciona tests/catalog/ y tests/frontend/ certificando 0 tests para login, passwords o pagos."""
    toxic_test_names = [
        r"def\s+test_.*?(login|signin)",
        r"def\s+test_.*?(password|contraseña)",
        r"def\s+test_.*?(jwt|token)",
        r"def\s+test_.*?(stripe|paypal|checkout|payment|pago)",
    ]
    target_dirs = [ROOT_DIR / "tests" / "catalog", ROOT_DIR / "tests" / "frontend"]
    for tdir in target_dirs:
        for tfile in tdir.glob("*.py"):
            content = tfile.read_text(encoding="utf-8")
            for pattern in toxic_test_names:
                m = re.search(pattern, content, re.IGNORECASE)
                assert not m, f"Test huérfano detectado en {tfile.name}: {m.group(0)}"


# ==============================================================================
# TEST 10: Validación de Documento de Test Plan Físico si Existe (Condicional/Skip)
# ==============================================================================
def test_test_plan_file_passes_linter_if_exists():
    """Valida docs/TEST_PLAN.md si ya fue generado físicamente en disco (esperado en Etapa C)."""
    if not DOCS_TEST_PLAN_PATH.exists():
        pytest.skip("docs/TEST_PLAN.md aún no generado (esperado en Etapa C)")

    content = DOCS_TEST_PLAN_PATH.read_text(encoding="utf-8")
    violations = lint_testing_strategy_contract(content, allowed_paths=["docs/TEST_PLAN.md"])
    assert len(violations) == 0, f"Violaciones en docs/TEST_PLAN.md: {violations}"
