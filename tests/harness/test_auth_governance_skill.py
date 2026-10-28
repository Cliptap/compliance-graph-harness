import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "07-auth" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "07_auth_security.md"
DOCS_SECURITY_PATH = ROOT_DIR / "docs" / "SECURITY.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Gobernanza de Autenticación y Seguridad
# ==============================================================================
def lint_auth_governance_contract(
    spec_or_doc: str,
    allowed_paths: list[str] | None = None,
    governance_level: str = "bajo",
    out_of_scope: list[str] | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para auth-governance."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec
    forbidden_path_prefixes = [
        "src/auth/",
        "src/users/",
        "src/tokens/",
        "src/cart/",
        "src/payments/",
    ]
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            for fp in forbidden_path_prefixes:
                if normalized_ap.startswith(fp) or normalized_ap == fp.rstrip("/"):
                    violations.append(
                        f"Invasión perimetral de TaskSpec: '{ap}' pertenece a una ruta prohibida (forbidden_path: '{fp}')"
                    )

    active_text = spec_or_doc

    # 2. Anti-Amnesia y No-Goldplating en Gobernanza Baja / Auth OUT OF SCOPE
    if governance_level.lower() == "bajo":
        toxic_auth_patterns = [
            (r"@router\.(post|get|put|delete).*?/(auth|login|register|signup|token)", "Endpoint activo de autenticación fuera de alcance"),
            (r"\bclass\s+(User|Usuario|Account|Cuenta|Session|Sesion|TokenAuth)\b", "Definición de modelo de usuario/cuenta fuera de alcance"),
            (r"\b(jwt\.encode|jwt\.decode|create_access_token|bcrypt\.hashpw)\b", "Implementación activa de tokens o hashing fuera de alcance"),
            (r"<form\s+id=[\"'](login-form|signin-form)[\"']", "Formulario UI de inicio de sesión fuera de alcance"),
            (r"\b(fastapi_jwt_auth|flask_login|passlib|auth0)\b", "Dependencia pesada de autenticación no autorizada"),
        ]
        for pattern, reason in toxic_auth_patterns:
            m = re.search(pattern, active_text, re.IGNORECASE)
            if m:
                violations.append(f"Violación de Anti-Amnesia / No-Goldplating: {reason} ('{m.group(0)}')")

    # 3. Verificación de Contrato de Artefacto (si es docs/SECURITY.md)
    if "# docs/SECURITY.md" in active_text or "Postura de Seguridad" in active_text:
        # Frontmatter y metadatos
        if "---" in active_text:
            try:
                fm, _ = _extract_frontmatter_and_body(active_text)
                if not fm.get("status"):
                    violations.append("Falta campo 'status' en frontmatter de SECURITY.md")
                if not fm.get("derivation_decision"):
                    violations.append("Falta campo 'derivation_decision' en frontmatter de SECURITY.md")
            except Exception as e:
                violations.append(f"Error parseando frontmatter de SECURITY.md: {e}")

        # Identificadores canónicos
        if not re.search(r"\bSEC-DEC-\d+\b", active_text):
            violations.append("Falta identificador formal de decisión (SEC-DEC-xxx)")

        required_controls = [
            "SEC-CTRL-001",
            "SEC-CTRL-002",
            "SEC-CTRL-003",
            "SEC-CTRL-004",
            "SEC-CTRL-005",
        ]
        for rc in required_controls:
            if rc not in active_text:
                violations.append(f"Control mínimo proporcional faltante en SECURITY.md: {rc}")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias v2.0
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 07-auth/SKILL.md y su versión portable contienen las secciones y metadatos contractuales v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo de skill no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter normativo
        assert fm.get("name") == "auth-governance"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 6
        assert "prd-generation" in fm.get("depends_on", [])
        assert "architecture-design" in fm.get("depends_on", [])
        assert "data-modeling" in fm.get("depends_on", [])
        assert "api-design" in fm.get("depends_on", [])
        assert "backend-implementation" in fm.get("depends_on", [])
        assert "frontend-implementation" in fm.get("depends_on", [])
        assert fm.get("produces_artifact") == "docs/SECURITY.md"
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
def test_auth_skill_contract_schema_and_taskspec():
    """Valida que la skill define TaskSpec agnóstico en el cuerpo normativo y la demo en Reference Context."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        parts = content.split("## Reference Context: Demo Implementation")
        normative = parts[0]
        ref_context = parts[1] if len(parts) > 1 else ""

        # Estándar metodológico en el cuerpo normativo:
        assert "TaskSpec" in normative or "TS-AUTH-001" in normative
        assert "allowed_paths" in normative
        assert "forbidden_paths" in normative
        assert "docs/SECURITY.md" in normative
        assert "src/auth/**" in normative
        assert "src/users/**" in normative
        assert "src/tokens/**" in normative
        assert "src/<out_of_scope_module>/**" in normative

        # Ausencia de módulos excluidos propios de la demo en el cuerpo normativo:
        assert "src/cart/**" not in normative
        assert "src/payments/**" not in normative

        # Sección Reference Context de la demo:
        assert len(ref_context) > 0
        assert "src/cart/**" in ref_context
        assert "src/payments/**" in ref_context
        assert "TS-AUTH-001" in ref_context


# ==============================================================================
# TEST 2b: Desacoplamiento del Cuerpo Normativo respecto de la Demo
# ==============================================================================
def test_auth_skill_normative_body_is_demo_agnostic():
    """Valida que el cuerpo normativo es genérico y que la instanciación demo vive en Reference Context."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "## Reference Context: Demo Implementation (catalogo-carrito-web)" in content
        parts = content.split("## Reference Context: Demo Implementation")
        assert len(parts) == 2, f"{path.name} debe tener exactamente una sección Reference Context"
        normative, ref_context = parts

        # Placeholders genéricos en el cuerpo normativo:
        assert "src/<bounded_context>/" in normative
        assert "EP-xxx" in normative
        assert "ENT-xxx" in normative
        assert "AD-xxx" in normative
        assert "COMP-xxx" in normative

        # Ausencia de acoplamiento demo en el cuerpo normativo:
        demo_strings = [
            "src/catalog",
            "tests/catalog",
            "catalogo-carrito",
            "Web Storage",
            "localStorage",
            "SEED-0",
            "NUESTRO CASO",
            "fastapi-jwt-auth",
            "Ley 21.719",
            "Vanilla",
            "carrito",
            "catálogo público",
            "AD-003",
            "AD-005",
            "EP-001",
            "ENT-001",
            "COMP-001",
        ]
        for demo in demo_strings:
            assert demo not in normative, f"Contenido demo '{demo}' filtrado al cuerpo normativo de {path.name}"
        assert not re.search(r"(?i)\b(catalog|cart|product)", normative)

        # Instanciación demo preservada en Reference Context:
        for demo in [
            "src/catalog/**",
            "src/frontend/**",
            "src/main.py",
            "AD-001",
            "AD-003",
            "AD-005",
            "Web Storage",
            "COMP-001",
            "ENT-001",
            "EP-001",
            "EP-002",
            "FastAPI",
            "fastapi-jwt-auth",
            "Ley 21.719",
            "Vanilla",
        ]:
            assert demo in ref_context, f"Instanciación demo '{demo}' ausente en Reference Context de {path.name}"


# ==============================================================================
# TEST 3: Lógica del Árbol de Derivación Condicional
# ==============================================================================
def test_conditional_derivation_logic_specification():
    """Valida que la skill prescribe el árbol de decisión formal según governance_level y PRD."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "Derivación Condicional" in content
        assert "governance_level" in content
        assert "OUT OF SCOPE" in content
        assert "Invariante Negativa" in content
        assert "SEC-DEC-001" in content


# ==============================================================================
# TEST 4: Regla de Oro Anti-Amnesia y Detección de Goldplating
# ==============================================================================
def test_anti_amnesia_and_no_goldplating_rules():
    """Verifica que el linter rechaza código o especificaciones que introduzcan login/auth innecesarios."""
    toxic_auth_code = """
@router.post("/api/v1/auth/login")
def login_user(creds: dict):
    token = jwt.encode(creds, "secret")
    return {"access_token": token}

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    password_hash = Column(String)
"""
    violations = lint_auth_governance_contract(toxic_auth_code, governance_level="bajo")
    assert len(violations) >= 3
    assert any("Endpoint activo" in v for v in violations)
    assert any("modelo de usuario" in v for v in violations)
    assert any("tokens o hashing" in v for v in violations)


# ==============================================================================
# TEST 5: Taxonomía Formal y Controles Técnicos Mínimos Proporcionales
# ==============================================================================
def test_baseline_security_controls_specification():
    """Valida que la skill impone los 5 controles técnicos mínimos de seguridad baseline."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "SEC-DEC-" in content
        assert "SEC-CTRL-001" in content  # Sanitización
        assert "SEC-CTRL-002" in content  # CORS
        assert "SEC-CTRL-003" in content  # No hardcoded secrets
        assert "SEC-CTRL-004" in content  # CWE-532 / Logs sin PII
        assert "SEC-CTRL-005" in content  # Mitigación XSS


# ==============================================================================
# TEST 6: Esquema del Artefacto de Salida (docs/SECURITY.md)
# ==============================================================================
def test_security_doc_output_contract_schema():
    """Valida que la skill define las 6 secciones obligatorias para docs/SECURITY.md."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "Identidad del Sistema y Alcance" in content
        assert "Dictamen de Derivación Condicional" in content
        assert "Matriz de Controles Técnicos Mínimos" in content
        assert "Análisis de Superficie de Ataque" in content
        assert "Auditoría de Cero Secrets" in content
        assert "Hoja de Ruta para Escalamiento" in content


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_security_spec_passes_linter():
    """Verifica que un documento conforme de seguridad pasa el linter con 0 violaciones."""
    clean_security_doc = """---
status: "APPROVED"
version: 1
governance_level: "bajo"
derivation_decision: "SEC-DEC-001"
last_audit: "2026-10-21"
---

# docs/SECURITY.md — Postura de Seguridad y Gobernanza de Identidades

## 1. Identidad del Sistema y Alcance
Sistema informativo de acceso público bajo nivel de gobernanza bajo.

## 2. Dictamen de Derivación Condicional (SEC-DEC-xxx)
- SEC-DEC-001: Autenticación formalmente excluida del alcance MVP según PRD.md (OUT OF SCOPE).

## 3. Matriz de Controles Técnicos Mínimos Proporcionales (SEC-CTRL-xxx)
- SEC-CTRL-001: Sanitización y validación estricta de parámetros en FastAPI.
- SEC-CTRL-002: Configuración de CORS restrictivo.
- SEC-CTRL-003: Ausencia total de credenciales y secrets hardcodeados.
- SEC-CTRL-004: Prevención de fuga de información y PII en logs (CWE-532).
- SEC-CTRL-005: Prevención de XSS en interfaz gráfica mediante textContent.

## 4. Análisis de Superficie de Ataque y Límites de Exposición
Solo expone EP-001 y EP-002 sin operaciones de mutación.

## 5. Auditoría de Cero Secrets y Privacidad
El escaneo determinista certifica 0 claves privadas o tokens en disco.

## 6. Hoja de Ruta para Escalamiento de Gobernanza (Futuro)
Evolución a RBAC en caso de añadir módulos transaccionales.
"""
    violations = lint_auth_governance_contract(clean_security_doc, allowed_paths=["docs/SECURITY.md"])
    assert len(violations) == 0, f"Violaciones inesperadas en spec conforme: {violations}"


# ==============================================================================
# TEST 8: Inspección Física del Repositorio Actual (Auditoría Cero Secrets y Cero Auth)
# ==============================================================================
def test_active_repository_security_compliance():
    """Inspecciona físicamente src/ y tests/ certificando 0 archivos de auth y 0 secrets hardcodeados."""
    # 1. Cero endpoints de auth en routers de backend
    router_file = ROOT_DIR / "src" / "catalog" / "router.py"
    if router_file.exists():
        router_code = router_file.read_text(encoding="utf-8")
        assert "/auth" not in router_code
        assert "/login" not in router_code
        # Validación de SEC-CTRL-001: Sanitización y límite de longitud
        assert "len(q) > 100" in router_code or "max_length" in router_code

    # 2. Cero secrets hardcodeados en archivos de código (.py, .js)
    secret_patterns = [
        r"(?i)(api_key|apikey|secret_key|private_key)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        r"(?i)(password|passwd)\s*=\s*['\"][A-Za-z0-9_\-@#]{8,}['\"]",
        r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----",
    ]
    code_extensions = (".py", ".js")
    for src_dir in [ROOT_DIR / "src", ROOT_DIR / "tests"]:
        for file_path in src_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in code_extensions:
                # Omitir archivos clínicos de demo existentes
                if "src/backend" in str(file_path).replace("\\", "/"):
                    continue
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for sp in secret_patterns:
                    assert not re.search(sp, content), (
                        f"Posible secret hardcodeado detectado en {file_path.relative_to(ROOT_DIR)}"
                    )


# ==============================================================================
# TEST 9: Validación de Documento de Seguridad Físico si Existe (Condicional/Skip)
# ==============================================================================
def test_security_doc_file_passes_linter_if_exists():
    """Valida docs/SECURITY.md si ya fue generado físicamente en disco (esperado en Etapa C)."""
    if not DOCS_SECURITY_PATH.exists():
        pytest.skip("docs/SECURITY.md aún no generado (esperado en Etapa C)")

    content = DOCS_SECURITY_PATH.read_text(encoding="utf-8")
    violations = lint_auth_governance_contract(content, allowed_paths=["docs/SECURITY.md"])
    assert len(violations) == 0, f"Violaciones en docs/SECURITY.md: {violations}"


# ==============================================================================
# TEST 10: Verificación Mecánica de Perímetro Físico con ScopePolicy
# ==============================================================================
def test_auth_physical_scope_enforcement():
    """Inspecciona disco y valida con ScopePolicy que no existan módulos prohibidos de auth."""
    from src.harness.contracts import TaskSpec
    from src.harness.policy_engine import ScopePolicy

    task_spec = TaskSpec(
        task_id="TS-AUTH-001",
        goal="Emitir la postura de seguridad y dictamen de derivación condicional en docs/SECURITY.md",
        category="compliance",
        allowed_paths=[
            "docs/SECURITY.md",
            "tests/harness/test_auth_governance_skill.py",
        ],
        forbidden_paths=[
            "src/auth/**",
            "src/users/**",
            "src/tokens/**",
            "src/cart/**",
            "src/payments/**",
        ],
    )

    # 1. Verificación en disco de ausencia de directorios prohibidos
    forbidden_dirs = [
        ROOT_DIR / "src" / "auth",
        ROOT_DIR / "src" / "users",
        ROOT_DIR / "src" / "tokens",
        ROOT_DIR / "src" / "cart",
        ROOT_DIR / "src" / "payments",
    ]
    for fdir in forbidden_dirs:
        assert not fdir.exists(), f"Directorio prohibido detectado en disco: {fdir.name}"

    # 2. Evaluación reactiva ante hipotéticas violaciones
    policy = ScopePolicy()
    findings = policy.evaluate(
        task_spec,
        {"src/auth/service.py": "??"},
    )
    assert len(findings) >= 1, "ScopePolicy debe reaccionar ante violación de perímetro en src/auth/"
