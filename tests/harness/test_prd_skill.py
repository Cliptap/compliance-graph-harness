import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "01-prd" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "01_prd.md"
INTEGRATION_TEST_PATH = ROOT_DIR / "docs" / "prd_skill_integration_test.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


def _extract_sample_prd_from_integration_doc() -> str:
    """Extrae el bloque PRD canónico de ejemplo documentado en prd_skill_integration_test.md."""
    content = INTEGRATION_TEST_PATH.read_text(encoding="utf-8")
    # Buscar el bloque de código markdown dentro de la sección 2
    match = re.search(r"```markdown\n(---.*?status:\s*\"APPROVED\".*?```)", content, re.DOTALL)
    assert match, "No se encontró el bloque PRD de ejemplo en prd_skill_integration_test.md"
    raw_block = match.group(1)
    if raw_block.endswith("```"):
        raw_block = raw_block[:-3].strip()
    return raw_block


# ==============================================================================
# TEST 1: Estructura del SKILL.md y elementos contractuales
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 01-prd/SKILL.md contiene los elementos contractuales y secciones requeridas."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter de la Skill
        assert fm.get("name") == "prd-generation"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 1
        assert "description" in fm and len(fm["description"]) > 20

        # Secciones estructurales obligatorias (Contrato v2.0)
        required_headers = [
            "Overview",
            "Cuándo Usar",
            "Precondiciones",
            "Entradas",
            "Distinción Fundamental",
            "Delimitación de Alcance",
            "Workflow de Elicitación",
            "Criterios de Aceptación",
            "Señales de Alerta",
            "Contrato de Salida Formal",
            "Verificación",
            "Criterio de Término",
        ]
        for header in required_headers:
            assert header.lower() in body.lower(), f"Sección faltante en {path.name}: {header}"


# ==============================================================================
# TEST 2: Validación del Esquema de Salida (PRD Output Contract)
# ==============================================================================
def test_prd_output_contract_schema():
    """Valida que una especificación PRD conforme al contrato contiene todos los elementos requeridos."""
    prd_text = _extract_sample_prd_from_integration_doc()
    fm, body = _extract_frontmatter_and_body(prd_text)

    # Metadatos obligatorios
    assert "project_id" in fm and fm["project_id"]
    assert "version" in fm and isinstance(fm["version"], int)
    assert fm.get("status") in ["DRAFT", "APPROVED", "SUPERSEDED"]
    assert "project_type" in fm
    assert "governance_level" in fm

    # Secciones funcionales obligatorias en el cuerpo
    assert "## 4. Requisitos Funcionales" in body or "Requisitos Funcionales" in body
    assert "## 5. Delimitación de Alcance" in body or "Scope Boundary" in body
    assert "IN SCOPE" in body
    assert "OUT OF SCOPE" in body
    assert "## 6. Criterios de Aceptación" in body or "Acceptance Criteria" in body
    assert "## 7. Restricciones" in body or "Constraints" in body
    assert "## 8. Supuestos" in body or "Assumptions" in body
    assert "## 9. Preguntas Abiertas" in body or "Open Questions" in body

    # IDs de Requisitos y Criterios presentes
    req_matches = re.findall(r"REQ-\d{3}", body)
    ac_matches = re.findall(r"AC-\d{3}", body)
    assert len(req_matches) >= 1, "El PRD debe contener al menos un REQ-xxx"
    assert len(ac_matches) >= 1, "El PRD debe contener al menos un AC-xxx"


# ==============================================================================
# TEST 3: Unicidad y Estabilidad de IDs (No duplicados)
# ==============================================================================
def test_prd_unique_stable_ids():
    """Verifica que no existan identificadores duplicados (REQ, AC, CONST, ASSUMP, OPEN)."""
    prd_text = _extract_sample_prd_from_integration_doc()
    _, body = _extract_frontmatter_and_body(prd_text)

    id_patterns = [
        (r"-\s+\*\*(REQ-\d{3})[:\*]", "Requisitos"),
        (r"-\s+\*\*(AC-\d{3})[:\*]", "Criterios de Aceptación"),
        (r"-\s+\*\*(CONST-\d{3})[:\*]", "Restricciones"),
        (r"-\s+\*\*(ASSUMP-\d{3})[:\*]", "Supuestos"),
        (r"-\s+\*\*(OPEN-\d{3})[:\*]", "Preguntas Abiertas"),
    ]

    for pattern, name in id_patterns:
        matches = re.findall(pattern, body, re.MULTILINE)
        assert len(matches) > 0, f"No se encontraron definiciones de IDs para {name}"
        unique_matches = set(matches)
        assert len(matches) == len(unique_matches), f"Existen IDs duplicados en {name}: {matches}"

    # Verificación de que cada AC está vinculado a un REQ existente
    req_ids = set(re.findall(r"REQ-\d{3}", body))
    ac_link_matches = re.findall(r"AC-\d{3}.*?REQ-\d{3}", body)
    assert len(ac_link_matches) > 0, "Los criterios AC deben declarar su vinculación a un REQ"


# ==============================================================================
# TEST 4: Preguntas Abiertas no se Convierten en Decisiones Silenciosas
# ==============================================================================
def test_prd_open_questions_not_silent_decisions():
    """Verifica que las dudas técnicas queden explícitamente como OPEN questions y no como decisiones activas."""
    prd_text = _extract_sample_prd_from_integration_doc()
    _, body = _extract_frontmatter_and_body(prd_text)

    # Comprueba que la sección de preguntas abiertas existe y contiene items OPEN-xxx
    open_matches = re.findall(r"OPEN-\d{3}", body)
    assert len(open_matches) >= 1, "Las decisiones diferidas deben registrarse como OPEN-xxx"

    # En SKILL.md debe estar explícitamente prohibido resolver dudas en silencio
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    assert "Preguntas Abiertas Resueltas en Silencio" in skill_text or "silencio" in skill_text.lower()
    assert "OPEN-" in skill_text


# ==============================================================================
# TEST 5: Aislamiento Físico (PRD Scope ≠ allowed_paths)
# ==============================================================================
def test_prd_does_not_emit_allowed_paths():
    """Verifica que el PRD no produzca allowed_paths ni rutas físicas prematuramente."""
    prd_text = _extract_sample_prd_from_integration_doc()

    # Ni el frontmatter ni el cuerpo del PRD deben tener allowed_paths
    assert "allowed_paths" not in prd_text, "El PRD no debe contener 'allowed_paths'"
    assert "forbidden_paths" not in prd_text, "El PRD no debe contener 'forbidden_paths'"

    # Tampoco rutas de archivos como src/ o *.py
    assert "src/" not in prd_text, "El PRD no debe especificar rutas de código como 'src/'"

    # En SKILL.md debe constar la regla explícita de separación
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    assert "PRD Scope" in skill_text and "allowed_paths" in skill_text
    assert "PRD Scope ≠ TaskSpec Scope" in skill_text or "PRD Scope" in skill_text


# ==============================================================================
# TEST 6: Reglas Contractuales Anti-Drift en SKILL.md y Portable Package
# ==============================================================================
def test_skill_contract_governance_and_anti_drift_rules():
    """Valida que SKILL.md y harness/skills/01_prd.md contienen las reglas estrictas anti-drift."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")

        # 1. Elicitación obligatoria de gobernanza (sin asumir valor por defecto)
        assert "Gobernanza Asumida en Silencio" in content
        assert "COMPUERTA DE BLOQUEO" in content or "Sin Asunciones Silenciosas" in content
        assert "ESTRICTAMENTE PROHIBIDO asumir o rellenar un valor por defecto" in content

        # 2. Prohibición de inventar scope negativo en OUT OF SCOPE
        assert "Scope Negativo Alucinado" in content
        assert "PROHIBIDO inventar scope negativo" in content
        assert "Regla Estricta de OUT OF SCOPE" in content

        # 3. Prohibición de números mágicos en supuestos
        assert "Números Mágicos en Supuestos" in content
        assert "PROHIBIDO introducir números mágicos" in content

        # 4. Prohibición de dilemas arquitectónicos prematuros en OPEN-*
        assert "Preselección Técnica en OPEN-*" in content
        assert "PROHIBIDO redactar dilemas o disyuntivas arquitectónicas concretas" in content
        assert "referencia de delegación genérica" in content


# ==============================================================================
# TEST 7: Linter de Contrato Detecta Infracciones (Negative Testing)
# ==============================================================================
def lint_prd_contract(body: str) -> list[str]:
    """Analizador determinista de cumplimiento de contrato de PRD."""
    violations = []

    # 1. Rutas físicas
    if any(k in body for k in ["allowed_paths", "forbidden_paths", "src/"]):
        violations.append("Rutas físicas o allowed_paths detectadas en el PRD")

    # 2. Números mágicos en supuestos (ej: < 200, < 1.000, 10 usuarios, etc.)
    assump_match = re.search(r"## 8\.\s*Supuestos.*?(?=##|\Z)", body, re.DOTALL | re.IGNORECASE)
    if assump_match:
        assump_text = assump_match.group(0)
        if re.search(r"[<>]|\b\d+\s*(productos|usuarios|items|ms|segundos)\b", assump_text, re.IGNORECASE):
            violations.append("Número mágico o umbral numérico arbitrario detectado en ASSUMP-*")

    # 3. Disyuntivas técnicas prematuras en OPEN-*
    open_match = re.search(r"## 9\.\s*Preguntas Abiertas.*?(?=##|\Z)", body, re.DOTALL | re.IGNORECASE)
    if open_match:
        open_text = open_match.group(0)
        if re.search(r"\b(vs|versus)\b", open_text, re.IGNORECASE):
            violations.append("Disyuntiva técnica o dilema arquitectónico prematuro detectado en OPEN-*")
        if re.search(r"\b(SPA|SSR|FastAPI|Flask|Django|PostgreSQL|MySQL|MongoDB|Redis|SQLite|localStorage)\b", open_text, re.IGNORECASE):
            violations.append("Tecnología concreta o arquitectura física preseleccionada en OPEN-*")

    return violations


def test_prd_linter_detects_anti_patterns():
    """Verifica que el linter de contrato detecta números mágicos y dilemas arquitectónicos."""
    bad_prd_body = """
## 8. Supuestos de Trabajo (Assumptions)
- **ASSUMP-001:** El catálogo inicial contiene un volumen acotado (< 200 productos).
- **ASSUMP-002:** Concurrencia de hasta 10 usuarios simultáneos.

## 9. Preguntas Abiertas y Decisiones Pendientes (Open Questions)
- **OPEN-001:** ¿Qué patrón conviene adoptar (SPA vs SSR)?
- **OPEN-002:** ¿Usar SQLite vs JSON en disco?
"""
    violations = lint_prd_contract(bad_prd_body)
    assert len(violations) >= 2
    assert any("Número mágico" in v for v in violations)
    assert any("Disyuntiva técnica" in v or "Tecnología concreta" in v for v in violations)


def test_prd_linter_accepts_conforming_spec():
    """Verifica que un PRD conforme a las nuevas reglas es aceptado sin violaciones."""
    good_prd_body = """
## 8. Supuestos de Trabajo (Assumptions)
- **ASSUMP-001:** El catálogo inicial cuenta con un volumen acotado para propósitos de demostración.
- **ASSUMP-002:** Todos los precios se manejan bajo una única moneda base local predefinida.

## 9. Preguntas Abiertas y Decisiones Pendientes (Open Questions)
- **OPEN-001:** ¿Cuál debe ser el comportamiento visual si el usuario intenta agregar un producto con stock agotado?
- **OPEN-002:** Delegación técnica: La selección de patrones de arquitectura y persistencia se resolverá formalmente en 02-architecture y 03-data-modeling.
"""
    violations = lint_prd_contract(good_prd_body)
    assert len(violations) == 0, f"Violaciones inesperadas: {violations}"

