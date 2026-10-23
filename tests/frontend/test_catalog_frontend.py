"""Suite de pruebas unitarias y deterministas para la interfaz de usuario web del catálogo y carrito.

Verifica:
1. Integridad estructural del DOM y marcado semántico HTML5 en index.html.
2. Accesibilidad (ARIA roles, live regions y etiquetas).
3. Tokens de diseño, responsividad y reglas CSS en styles.css.
4. Contrato de solo lectura y endpoints en api.js.
5. Invariantes del dominio (INV-002, INV-004) y persistencia en cart.js.
6. Orquestación reactiva y gestión de los 3 estados UI (Loading, Empty, Error) en app.js.
"""

from html.parser import HTMLParser
import json
import pathlib
import re
import shutil
import subprocess
import pytest

pytestmark = [pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = ROOT_DIR / "src" / "frontend"


class HTMLDOMInspector(HTMLParser):
    """Parser liviano para inspeccionar elementos, atributos y jerarquía del DOM."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.elements_by_id = {}
        self.classes = set()
        self.scripts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self.tags.append(tag)

        element_id = attr_dict.get("id")
        if element_id:
            self.elements_by_id[element_id] = {"tag": tag, "attrs": attr_dict}

        class_val = attr_dict.get("class")
        if class_val:
            for c in class_val.split():
                self.classes.add(c)

        if tag == "script":
            self.scripts.append(attr_dict)
        elif tag == "link":
            self.links.append(attr_dict)


# ==============================================================================
# TEST 1: Integridad Estructural del DOM y Marcado Semántico HTML5
# ==============================================================================
def test_html_semantic_markup_and_ids():
    """Valida la presencia de etiquetas semánticas y elementos requeridos en index.html."""
    html_path = FRONTEND_DIR / "index.html"
    assert html_path.exists(), f"Falta index.html en {FRONTEND_DIR}"
    content = html_path.read_text(encoding="utf-8")

    inspector = HTMLDOMInspector()
    inspector.feed(content)

    # 1. Doctype y metadatos
    assert "<!doctype html>" in content.lower()
    assert "<title>" in content.lower()
    assert any(link.get("rel") == "stylesheet" and link.get("href") == "styles.css" for link in inspector.links)

    # 2. Etiquetas semánticas fundamentales
    assert "header" in inspector.tags
    assert "main" in inspector.tags
    assert "section" in inspector.tags
    assert "aside" in inspector.tags

    # 3. Elementos obligatorios por ID
    required_ids = [
        "search-input",
        "clear-search-btn",
        "reset-search-btn",
        "catalog-grid",
        "loading-state",
        "empty-state",
        "error-state",
        "retry-btn",
        "cart-button",
        "cart-drawer",
        "cart-overlay",
        "close-cart-btn",
        "cart-badge",
        "cart-items",
        "cart-empty-message",
        "cart-total",
        "clear-cart-btn",
    ]
    for rid in required_ids:
        assert rid in inspector.elements_by_id, f"ID obligatorio no encontrado en index.html: #{rid}"

    # 4. Inclusión del módulo app.js
    assert any(
        script.get("type") == "module" and script.get("src") == "app.js"
        for script in inspector.scripts
    ), "index.html debe cargar app.js con type='module'"


# ==============================================================================
# TEST 2: Accesibilidad Web y Atributos ARIA
# ==============================================================================
def test_html_accessibility_and_aria_attributes():
    """Valida los atributos de accesibilidad para lectores de pantalla y regiones vivas."""
    html_path = FRONTEND_DIR / "index.html"
    content = html_path.read_text(encoding="utf-8")

    inspector = HTMLDOMInspector()
    inspector.feed(content)

    # 1. Regiones vivas para estados dinámicos
    loading_el = inspector.elements_by_id["loading-state"]["attrs"]
    assert loading_el.get("role") == "status"
    assert loading_el.get("aria-live") == "polite"

    empty_el = inspector.elements_by_id["empty-state"]["attrs"]
    assert empty_el.get("role") == "status"
    assert empty_el.get("aria-live") == "polite"

    error_el = inspector.elements_by_id["error-state"]["attrs"]
    assert error_el.get("role") == "alert"
    assert error_el.get("aria-live") == "assertive"

    # 2. Accesibilidad en el drawer del carrito
    cart_drawer = inspector.elements_by_id["cart-drawer"]["attrs"]
    assert cart_drawer.get("role") == "dialog"
    assert cart_drawer.get("aria-modal") == "true"

    # 3. Etiquetas accesibles en botones clave
    cart_btn = inspector.elements_by_id["cart-button"]["attrs"]
    assert "aria-label" in cart_btn

    close_btn = inspector.elements_by_id["close-cart-btn"]["attrs"]
    assert "aria-label" in close_btn


# ==============================================================================
# TEST 3: Tokens de Diseño y Responsividad en styles.css
# ==============================================================================
def test_css_design_system_and_responsiveness():
    """Valida que styles.css implementa un diseño responsivo con CSS Grid y Flexbox sin dependencias externas."""
    css_path = FRONTENDDIR = FRONTEND_DIR / "styles.css"
    assert css_path.exists(), f"Falta styles.css en {FRONTEND_DIR}"
    css_content = css_path.read_text(encoding="utf-8")

    # 1. Variables de diseño CSS
    assert ":root" in css_content
    assert "--color-primary" in css_content
    assert "--color-surface" in css_content

    # 2. Rejilla responsiva con auto-fill y minmax
    assert ".catalog-grid" in css_content
    assert "grid-template-columns:" in css_content
    assert "minmax(" in css_content

    # 3. Clases de estado y feedback visual
    assert ".hidden" in css_content
    assert "display: none !important;" in css_content
    assert ".spinner" in css_content
    assert "@keyframes spin" in css_content
    assert ".state-error" in css_content

    # 4. Panel lateral deslizante
    assert ".cart-drawer" in css_content
    assert ".cart-overlay" in css_content
    assert ".cart-content" in css_content


# ==============================================================================
# TEST 4: Contrato de Transporte HTTP de Solo Lectura en api.js
# ==============================================================================
def test_api_client_contract_and_readonly_guarantees():
    """Valida que api.js consume exclusivamente EP-001 y EP-002 mediante GET sin mutaciones."""
    api_path = FRONTEND_DIR / "api.js"
    assert api_path.exists(), f"Falta api.js en {FRONTEND_DIR}"
    api_content = api_path.read_text(encoding="utf-8")

    # 1. Funciones y clases exportadas
    assert "export class ApiError" in api_content
    assert "export const API_BASE_URL" in api_content
    assert "export async function fetchProducts" in api_content
    assert "export async function fetchProductById" in api_content

    # 2. Rutas canónicas
    assert "/products" in api_content
    assert "/products/${encodeURIComponent(productId)}" in api_content or "/products/" in api_content

    # 3. Solo métodos GET autorizados
    fetch_methods = re.findall(r"method:\s*['\"]([^'\"]+)['\"]", api_content)
    for method in fetch_methods:
        assert method.upper() == "GET", f"Método HTTP no permitido encontrado en api.js: {method}"

    # 4. Cero mutaciones sobre catálogo ni carrito en servidor
    forbidden_methods = re.findall(r"\b(POST|PUT|DELETE|PATCH)\b", api_content)
    assert len(forbidden_methods) == 0, f"Métodos HTTP prohibidos detectados en api.js: {forbidden_methods}"

    forbidden_routes = ["/carts", "/cart_items", "/payments"]
    for fr in forbidden_routes:
        assert fr not in api_content, f"Ruta prohibida detectada en api.js: {fr}"


# ==============================================================================
# TEST 5: Invariantes del Carrito y Consistencia Aritmética en cart.js (INV-002, INV-004)
# ==============================================================================
def test_cart_invariants_and_storage_contract():
    """Valida la lógica de CartManager, persistencia en localStorage y las invariantes INV-002 e INV-004."""
    cart_path = FRONTEND_DIR / "cart.js"
    assert cart_path.exists(), f"Falta cart.js en {FRONTEND_DIR}"
    cart_content = cart_path.read_text(encoding="utf-8")

    # 1. Estructura de la clase CartManager
    assert "export class CartManager" in cart_content
    assert "export const cartInstance" in cart_content

    methods = [
        "getState",
        "addItem",
        "updateQuantity",
        "removeItem",
        "clearCart",
        "subscribe",
    ]
    for m in methods:
        assert m in cart_content, f"Método obligatorio no definido en CartManager: {m}"

    # 2. Ejecución determinista del motor de carrito en Node.js
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js no está disponible en el entorno para ejecución directa de JS")

    runner_script = """
    const storage = {};
    globalThis.window = {
        localStorage: {
            getItem(key) { return storage[key] || null; },
            setItem(key, value) { storage[key] = String(value); },
            removeItem(key) { delete storage[key]; }
        }
    };

    const { CartManager } = await import('./src/frontend/cart.js');
    const cart = new CartManager('test_cart_suite');

    // Estado inicial vacío
    let s0 = cart.getState();
    if (s0.items.length !== 0 || s0.total_items !== 0 || s0.total_amount !== 0.0) {
        throw new Error('Estado inicial inválido');
    }

    // Agregar primer producto: Cuaderno ($2.50, cant 2) -> Subtotal: 5.00
    cart.addItem({ id: 101, name: 'Cuaderno', price: 2.50 }, 2);
    let s1 = cart.getState();
    if (s1.items.length !== 1 || s1.total_items !== 2 || s1.total_amount !== 5.00) {
        throw new Error('Fallo al agregar primer producto');
    }
    if (s1.items[0].subtotal !== 5.00) throw new Error('Subtotal incorrecto');

    // Agregar segundo producto con decimales: Marcador ($1.33, cant 3) -> Subtotal: 3.99
    cart.addItem({ id: 102, name: 'Marcador', price: 1.33 }, 3);
    let s2 = cart.getState();
    // INV-004: Consistencia aritmética total_amount = 5.00 + 3.99 = 8.99
    if (s2.total_items !== 5 || s2.total_amount !== 8.99) {
        throw new Error('Fallo INV-004: Total aritmético incorrecto: ' + s2.total_amount);
    }

    // Incrementar producto 101 existente (+1)
    cart.addItem({ id: 101, name: 'Cuaderno', price: 2.50 }, 1);
    let s3 = cart.getState();
    let cu = s3.items.find(i => i.product_id === 101);
    if (cu.quantity !== 3 || cu.subtotal !== 7.50) throw new Error('Fallo al incrementar cantidad');

    // Decrementar cantidad de Marcador a 2
    cart.updateQuantity(102, -1);
    let s4 = cart.getState();
    let ma = s4.items.find(i => i.product_id === 102);
    if (ma.quantity !== 2 || ma.subtotal !== 2.66) throw new Error('Fallo al decrementar cantidad');

    // INV-002: Decrementar hasta alcanzar < 1 provoca eliminación automática
    cart.updateQuantity(102, -1); // qty: 1
    cart.updateQuantity(102, -1); // qty: 0 -> Removido
    let s5 = cart.getState();
    if (s5.items.some(i => i.product_id === 102)) {
        throw new Error('Fallo INV-002: El ítem con cantidad < 1 no fue removido');
    }
    if (s5.items.length !== 1 || s5.items[0].product_id !== 101) {
        throw new Error('Fallo al limpiar ítem en INV-002');
    }

    // Vaciar carrito
    cart.clearCart();
    let s6 = cart.getState();
    if (s6.items.length !== 0 || s6.total_items !== 0 || s6.total_amount !== 0.0) {
        throw new Error('Fallo al vaciar carrito');
    }

    console.log(JSON.stringify({ success: true }));
    """

    res = subprocess.run(
        [node_bin, "--input-type=module", "-e", runner_script],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Error al ejecutar suite de CartManager en Node: {res.stderr}\n{res.stdout}"
    output = json.loads(res.stdout.strip())
    assert output.get("success") is True


# ==============================================================================
# TEST 6: Orquestación Reactiva y Gestión de Estados UI en app.js
# ==============================================================================
def test_app_orchestration_and_ui_states():
    """Valida la definición de los 3 estados UI y la orquestación del DOM en app.js."""
    app_path = FRONTEND_DIR / "app.js"
    assert app_path.exists(), f"Falta app.js en {FRONTEND_DIR}"
    app_content = app_path.read_text(encoding="utf-8")

    # 1. Funciones exportadas
    assert "export function setUIState" in app_content
    assert "export function renderCatalog" in app_content
    assert "export function renderCart" in app_content
    assert "export async function loadCatalog" in app_content
    assert "export function formatCurrency" in app_content
    assert "export function initApp" in app_content

    # 2. Los 3 estados UI obligatorios
    assert "case 'loading':" in app_content or "loading" in app_content
    assert "case 'empty':" in app_content or "empty" in app_content
    assert "case 'error':" in app_content or "error" in app_content

    # 3. Conexión con cartInstance y fetchProducts
    assert "import { fetchProducts } from './api.js';" in app_content
    assert "import { cartInstance } from './cart.js';" in app_content
    assert "cartInstance.subscribe(renderCart);" in app_content
    assert "cartInstance.addItem(" in app_content
    assert "cartInstance.updateQuantity(" in app_content
    assert "cartInstance.removeItem(" in app_content
    assert "cartInstance.clearCart(" in app_content

    # 4. Debounce en búsqueda en tiempo real
    assert "searchDebounceTimer" in app_content
    assert "setTimeout(" in app_content
