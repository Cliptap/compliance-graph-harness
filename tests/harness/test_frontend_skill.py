import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "06-frontend" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "06_frontend_implementation.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Implementación de Frontend
# ==============================================================================
def lint_frontend_skill_contract(
    spec_or_code: str,
    allowed_paths: list[str] | None = None,
    out_of_scope_items: list[str] | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para frontend-implementation."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec
    forbidden_path_prefixes = [
        "src/backend/",
        "src/database/",
        "src/catalog/",
        "src/shared/",
        "src/cart/",
        "src/auth/",
        "src/users/",
        "src/payments/",
        "node_modules/",
    ]
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            for fp in forbidden_path_prefixes:
                if normalized_ap.startswith(fp) or normalized_ap == fp.rstrip("/"):
                    violations.append(
                        f"Invasión perimetral de TaskSpec: '{ap}' pertenece a una ruta prohibida (forbidden_path: '{fp}')"
                    )

    active_text = spec_or_code

    # 2. Anti-Amnesia: Violación de OUT OF SCOPE heredado
    toxic_ui_patterns = [
        (r"\b(login|iniciar_sesion|iniciar-sesion|signin|sign_in)\b", "Formulario o vista de inicio de sesión no autorizada"),
        (r"\b(password|contraseña|contrasena)\b", "Campo o referencia a contraseñas fuera de alcance"),
        (r"\b(register|registro_usuario|crear_cuenta|signup)\b", "Formulario de registro de cuentas de usuario fuera de alcance"),
        (r"\b(jwt|token|access_token|refresh_token)\b", "Manejo de tokens JWT de sesión no autorizados"),
        (r"\b(stripe|paypal|tarjeta_credito|credit_card|cvv|pasarela|payment|payments|pago|checkout)\b", "Integración o formulario de pasarela de pago o checkout fuera de alcance"),
    ]
    for pattern, reason in toxic_ui_patterns:
        m = re.search(pattern, active_text, re.IGNORECASE)
        if m:
            violations.append(f"Violación de Anti-Amnesia: {reason} ('{m.group(0)}')")

    # 3. Coherencia con AD-003: Prohibición de endpoints de servidor para carrito
    server_cart_patterns = [
        r"fetch\(\s*['\"`][^'\"`]*?/(carts|cart_items|carritos)",
        r"\b(axios|http)\.(get|post|put|delete|patch)\(\s*['\"`][^'\"`]*?/(carts|cart_items|carritos)",
        r"@router\.(get|post).*?/(carts|cart_items)",
    ]
    for cp in server_cart_patterns:
        cm = re.search(cp, active_text, re.IGNORECASE)
        if cm:
            violations.append(f"Violación de AD-003: Intento de consumo de endpoint de carrito en servidor ('{cm.group(0)}')")

    # 4. No-Goldplating de Stack Tecnológico y Funcional
    heavy_stack_patterns = [
        r"\bimport\s+React\b",
        r"\bfrom\s+['\"]react['\"]",
        r"\bfrom\s+['\"]vue['\"]",
        r"\bfrom\s+['\"]@angular/",
        r"\bpackage\.json\b",
    ]
    for hp in heavy_stack_patterns:
        hm = re.search(hp, active_text)
        if hm:
            violations.append(f"Violación de No-Goldplating: Dependencia o framework pesado no autorizado para este MVP Vanilla ('{hm.group(0)}')")

    # Prohibición de mutación sobre catálogo
    mutation_ui_patterns = [
        r"fetch\(['\"`].*?/products.*?['\"`]\s*,\s*\{\s*method:\s*['\"](POST|PUT|DELETE|PATCH)['\"]",
        r"\b(create_product_form|formulario_crear_producto|boton_eliminar_producto)\b",
    ]
    for mp in mutation_ui_patterns:
        mm = re.search(mp, active_text, re.IGNORECASE)
        if mm:
            violations.append(f"Violación de No-Goldplating: Interfaz de mutación de productos no autorizada ('{mm.group(0)}')")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 06-frontend/SKILL.md y su versión portable contienen las secciones y metadatos contractuales v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo de skill no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter normativo
        assert fm.get("name") == "frontend-implementation"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 5
        assert "prd-generation" in fm.get("depends_on", [])
        assert "architecture-design" in fm.get("depends_on", [])
        assert "data-modeling" in fm.get("depends_on", [])
        assert "api-design" in fm.get("depends_on", [])
        assert "backend-implementation" in fm.get("depends_on", [])
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
def test_frontend_skill_contract_schema_and_taskspec_rules():
    """Valida que la skill define formalmente TaskSpec con allowed_paths, forbidden_paths y prevención de orphan changes."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec(" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "src/frontend/**" in content
        assert "tests/frontend/**" in content
        assert "src/backend/**" in content   # Preservación clínica
        assert "src/database/**" in content  # Preservación clínica
        assert "src/catalog/**" in content   # Preservación de backend sellado
        assert "src/shared/**" in content    # Preservación de backend sellado
        assert "orphan_change" in content or "orphan changes" in content.lower()


# ==============================================================================
# TEST 3: Topología del Código Frontend
# ==============================================================================
def test_frontend_skill_codebase_layout_compliance():
    """Valida que la skill prescribe la topología canónica (index.html, styles.css, api.js, cart.js, app.js)."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "src/frontend/index.html" in content
        assert "src/frontend/styles.css" in content
        assert "src/frontend/api.js" in content
        assert "src/frontend/cart.js" in content
        assert "src/frontend/app.js" in content
        assert "tests/frontend/test_catalog_frontend.py" in content


# ==============================================================================
# TEST 4: Regla de Oro Anti-Amnesia y Detección de Violaciones de Scope
# ==============================================================================
def test_frontend_skill_anti_amnesia_rules():
    """Verifica que el linter rechaza código frontend que reintroduce conceptos OUT OF SCOPE."""
    toxic_frontend_code = """
function renderLoginModal() {
    return `
        <form id="login-form">
            <input type="text" name="username" placeholder="Usuario" />
            <input type="password" name="password" placeholder="Contraseña" />
            <button type="submit">Iniciar Sesión</button>
        </form>
    `;
}

function processPaymentStripe(token) {
    fetch('/api/v1/payments/checkout', { method: 'POST', body: JSON.stringify({ token }) });
}
"""
    violations = lint_frontend_skill_contract(toxic_frontend_code)
    assert len(violations) >= 3
    assert any("login" in v.lower() or "sesión" in v.lower() for v in violations)
    assert any("password" in v.lower() or "contraseña" in v.lower() for v in violations)
    assert any("stripe" in v.lower() or "pago" in v.lower() for v in violations)

    # Verificar que las directivas anti-amnesia constan en ambas skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "Anti-Amnesia" in text
        assert "OUT OF SCOPE" in text
        assert "Amnesia de Scope" in text


# ==============================================================================
# TEST 5: Coherencia con AD-003 (Carrito en Cliente, Cero Persistencia en Servidor)
# ==============================================================================
def test_frontend_skill_coherence_with_ad003_cart_in_client():
    """Verifica que el linter rechaza peticiones fetch a endpoints de servidor para el carrito."""
    toxic_cart_code = """
async function syncCartWithServer(items) {
    const response = await fetch('/api/v1/carts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
    });
    return response.json();
}
"""
    violations = lint_frontend_skill_contract(toxic_cart_code)
    assert len(violations) >= 1
    assert any("AD-003" in v or "servidor" in v.lower() for v in violations)

    # Verificar que el respeto a AD-003 y localStorage consta en ambas skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "AD-003" in text
        assert "localStorage" in text
        assert "DTO-CART-001" in text
        assert "INV-002" in text
        assert "INV-004" in text


# ==============================================================================
# TEST 6: Detección y Rechazo de Goldplating (Stack Tecnológico y Mutaciones)
# ==============================================================================
def test_frontend_skill_no_goldplating_tech_stack():
    """Verifica que el linter rechaza frameworks pesados o bundlers no autorizados para este MVP Vanilla."""
    toxic_framework_code = """
import React, { useState } from 'react';

export function ProductCatalog() {
    const [products, setProducts] = useState([]);
    return <div>React Catalog</div>;
}
"""
    violations = lint_frontend_skill_contract(toxic_framework_code)
    assert len(violations) >= 1
    assert any("No-Goldplating" in v for v in violations)

    # Verificar que la invariante de stack Vanilla consta en ambas skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "vanilla" in text.lower()
        assert "AD-005" in text


# ==============================================================================
# TEST 7: Manejo Obligatorio de Estados UI y Consumo de API
# ==============================================================================
def test_frontend_skill_ui_states_and_api_consumption():
    """Valida que la skill impone los 3 estados UI (Loading, Empty, Error) y el consumo de EP-001 / EP-002."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "Loading" in text or "Carga" in text
        assert "Empty" in text or "Vacío" in text
        assert "Error" in text
        assert "AC-003" in text
        assert "DTO-ERR-001" in text
        assert "EP-001" in text
        assert "EP-002" in text


# ==============================================================================
# TEST 8: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_frontend_spec_passes_linter():
    """Verifica que un código y módulo conforme al contrato pasa con 0 violaciones."""
    clean_frontend_code = """
class CartManager {
    constructor() {
        this.storageKey = 'shopping_cart';
    }

    getState() {
        const raw = localStorage.getItem(this.storageKey);
        if (!raw) return { items: [], total_items: 0, total_amount: 0.0 };
        try {
            return JSON.parse(raw);
        } catch {
            return { items: [], total_items: 0, total_amount: 0.0 };
        }
    }

    saveState(state) {
        localStorage.setItem(this.storageKey, JSON.stringify(state));
    }
}

async function fetchProducts(q = null) {
    const url = q ? `/api/v1/products?q=${encodeURIComponent(q)}` : '/api/v1/products';
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('Error al consultar productos');
    }
    return res.json();
}
"""
    allowed = ["src/frontend/cart.js", "src/frontend/api.js"]
    violations = lint_frontend_skill_contract(clean_frontend_code, allowed_paths=allowed)
    assert len(violations) == 0, f"Violaciones inesperadas: {violations}"


# ==============================================================================
# TEST 9: Validación de Código Frontend si ya está Implementado (Condicional/Skip)
# ==============================================================================
def test_frontend_code_compliance_if_implemented():
    """Valida que si src/frontend/ está implementado para catalogo-carrito-web, cumpla rigurosamente con los contratos."""
    frontend_dir = ROOT_DIR / "src" / "frontend"
    cart_file = frontend_dir / "cart.js"
    if not cart_file.exists():
        pytest.skip("Código frontend de catálogo (cart.js) aún no implementado (esperado en Etapa C)")

    # Archivos requeridos
    required_files = [
        "index.html",
        "styles.css",
        "api.js",
        "cart.js",
        "app.js",
    ]
    for rf in required_files:
        target = frontend_dir / rf
        assert target.exists(), f"Archivo faltante en src/frontend/: {rf}"

    # Verificación de que no se reintroducen llamadas server cart ni auth
    cart_code = (frontend_dir / "cart.js").read_text(encoding="utf-8")
    violations = lint_frontend_skill_contract(cart_code)
    assert len(violations) == 0, f"Violaciones en cart.js: {violations}"


# ==============================================================================
# TEST 10: Verificación Mecánica de Perímetro Físico (Scope Policy Enforcement)
# ==============================================================================
def test_frontend_physical_scope_enforcement():
    """Inspecciona los archivos físicos en src/ y verifica deterministamente el respeto al TaskSpec de frontend."""
    import subprocess
    from src.harness.contracts import TaskSpec
    from src.harness.policy_engine import ScopePolicy

    task_spec = TaskSpec(
        task_id="TS-FRONTEND-001",
        goal="Implementar la interfaz web interactiva de catálogo y carrito de compras en Vanilla HTML/CSS/JS",
        category="feature",
        allowed_paths=[
            "src/frontend/**",
            "tests/frontend/**",
        ],
        forbidden_paths=[
            "src/backend/**",
            "src/database/**",
            "src/catalog/**",
            "src/shared/**",
            "src/cart/**",
            "src/auth/**",
            "src/users/**",
            "src/payments/**",
            "package.json",
            "node_modules/**",
        ],
    )

    # 1. Verificación de ausencia de directorios prohibidos en disco
    forbidden_directories = [
        ROOT_DIR / "src" / "cart",
        ROOT_DIR / "src" / "auth",
        ROOT_DIR / "src" / "users",
        ROOT_DIR / "src" / "payments",
        ROOT_DIR / "src" / "carritos",
        ROOT_DIR / "node_modules",
    ]
    for fdir in forbidden_directories:
        assert not fdir.exists(), (
            f"Directorio prohibido fuera de alcance detectado en disco: '{fdir.relative_to(ROOT_DIR)}'. "
            f"Viola la delimitación perimetral de TaskSpec y la Regla Anti-Amnesia."
        )

    # 2. Verificación de ausencia de manifiestos pesados de build no autorizados
    assert not (ROOT_DIR / "package.json").exists(), (
        "package.json detectado en la raíz del proyecto. Viola AD-005 (Frontend Vanilla sin dependencias pesadas)."
    )

    # 3. Verificación reactiva del evaluador ante infracciones de frontend
    policy = ScopePolicy()
    hypothetical_violations = policy.evaluate(
        task_spec,
        {"src/cart/cart.js": "??", "package.json": "??"},
    )
    assert len(hypothetical_violations) >= 2, "ScopePolicy debe reaccionar ante violaciones de scope de frontend"
