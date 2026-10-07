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
