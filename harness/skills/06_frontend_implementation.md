---
name: frontend-implementation
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation]
stage: 5
project_types: [web_app]
governance: all
description: Implementacion de la interfaz de usuario en Vanilla HTML/CSS/JS. Define estructura modular de componentes, consumo de API de solo lectura (EP-001, EP-002), gestion reactiva del carrito en Web Storage (DTO-CART-001) y manejo de estados UI respetando el PRD y la Arquitectura.
---

# Skill 06: Implementación de Frontend (Frontend Implementation)

## 1. Overview y Propósito

Esta skill gobierna la **construcción física de la interfaz de usuario web** del sistema en `src/frontend/`. Traduce los requerimientos funcionales de `docs/PRD.md` (`REQ-001` a `REQ-004`, `AC-001` a `AC-006`), las directivas arquitectónicas de `docs/ARCHITECTURE.md` (`COMP-002`, `COMP-003`, `AD-001` a `AD-007`), las estructuras del modelo de datos de cliente de `docs/DATA_MODEL.md` (`DTO-CART-001`, `INV-001` a `INV-004`) y los contratos REST de `docs/API_DESIGN.md` (`EP-001`, `EP-002`, `DTO-PROD-LIST-001`, `DTO-ERR-001`) en una aplicación web interactiva, responsiva, accesible y de alto rendimiento.

Su propósito fundamental es responder con rigor de ingeniería:
> **¿Cómo implementar la interfaz web comercial y el carrito de compras del sistema de forma modular, responsiva y desacoplada, garantizando que el carrito opere íntegramente en Web Storage del cliente conforme a AD-003, consumiendo la API de solo lectura y respetando los límites perimetrales sin introducir dependencias externas ni código fuera de alcance?**

La skill opera bajo cuatro principios fundamentales de gobernanza:
1. **Desacoplamiento Estricto y Carrito en Cliente (`AD-003` / `DTO-CART-001`):** El estado del carrito de compras reside de forma exclusiva e íntegra en Web Storage (`localStorage`) en el navegador del cliente. Queda terminantemente prohibido invocar o definir endpoints de mutación o persistencia de carrito en el servidor.
2. **Consumo de API de Solo Lectura:** La comunicación con el backend se realiza exclusivamente mediante peticiones HTTP `GET` sobre los endpoints canónicos `/api/v1/products` (`EP-001`) y `/api/v1/products/{id}` (`EP-002`).
3. **Manejo Obligatorio de los 3 Estados UI:** Toda vista o componente que consuma datos asíncronos debe implementar de forma explícita los estados de **Carga (Loading)**, **Vacío (Empty - `AC-003`)** y **Error (Fail-Fast con `DTO-ERR-001`)**.
4. **Delimitación Perimetral Estricta mediante `TaskSpec`:** La codificación física se circunscribe a `src/frontend/**` y `tests/frontend/**`, blindando el código clínico preexistente (`src/backend/**`, `src/database/**`) y preservando inalterado el backend ya implementado (`src/catalog/**`, `src/shared/**`).
5. **No-Goldplating de Stack Tecnológico (`AD-005`):** Implementación en HTML5 semántico, CSS3 moderno (Flexbox/Grid) y JavaScript estándar (ES6+) sin toolchains pesados, compiladores ni dependencias de `package.json` no autorizadas para este MVP.

---

## 2. Cuándo Usar (Use When)

- Inmediatamente después de que `05-backend` (`backend-implementation`) haya finalizado con su suite unitaria 100% en verde.
- Cuando se requiere codificar la estructura de marcado HTML, las hojas de estilo CSS y la lógica interactiva en JavaScript para el catálogo de productos y el carrito de compras.
- Previo a la ejecución de las pruebas integrales de sistema en `08-testing` y a la configuración de empaquetado/despliegue en `10-deployment`.

---

## 3. Precondiciones

1. **Aprobación Formal de la Cadena Upstream:**
   - `docs/PRD.md` DEBE existir con `status: APPROVED`.
   - `docs/ARCHITECTURE.md` DEBE existir con `status: APPROVED`.
   - `docs/DATA_MODEL.md` DEBE existir con `status: APPROVED`.
   - `docs/API_DESIGN.md` DEBE existir con `status: APPROVED`.
   - La suite de pruebas de backend (`tests/catalog/test_catalog_backend.py`) DEBE estar 100% aprobada.
2. **Definición de `TaskSpec` Perimetral:**
   - Toda tarea de frontend debe formalizar `allowed_paths = ["src/frontend/**", "tests/frontend/**"]`.
3. **Disponibilidad de Servicio Backend:**
   - El backend de catálogo debe exponer los endpoints `GET /api/v1/products` y `GET /api/v1/products/{id}`.

---

## 4. Entradas (Inputs) desde Upstream

La skill extrae deterministamente:
- **Desde `docs/PRD.md`:**
  - `REQ-001` (Catálogo de productos: nombre, descripción, precio unitario formateado).
  - `REQ-002` (Búsqueda textual insensible a mayúsculas con actualización reactiva).
  - `REQ-003` (Carrito de compras interactivo: adición, incremento/decremento de cantidades, eliminación).
  - `REQ-004` (Cálculo automático de subtotales por producto y total general acumulado).
  - `AC-001` a `AC-006`: Criterios de aceptación observables en interfaz.
  - `OUT OF SCOPE`: Cero pantallas de login, registro, perfiles, tarjetas de crédito, pasarelas o formularios de creación/edición de productos.
- **Desde `docs/ARCHITECTURE.md`:**
  - `COMP-002 [cart_service]`: Lógica de carrito encapsulada en cliente.
  - `COMP-003 [catalog_frontend]`: Componente de interfaz web estática/SPA.
  - `AD-002`: Transporte HTTP REST síncrono con base `/api/v1`.
  - `AD-003`: Carrito 100% en Web Storage (`localStorage`), sin tablas ni sesiones en servidor.
  - `AD-005`: Stack liviano en Vanilla HTML5 / CSS3 / JS (ES6+) desacoplado sin bundlers complejos.
  - `AD-006`: Fail-Fast con visualización estructurada de errores.
  - `AD-007`: Modo visitante anónimo sin tokens ni credenciales.
- **Desde `docs/DATA_MODEL.md`:**
  - `DTO-CART-001 [CartItem]`: `{ product_id: int, name: str, unit_price: float, quantity: int, subtotal: float }`.
  - `CartState`: `{ items: list[CartItem], total_items: int, total_amount: float, updated_at: str }`.
  - Invariantes: `INV-001` (`unit_price >= 0.0`), `INV-002` (`quantity >= 1`), `INV-004` (`subtotal == unit_price * quantity`, `total_amount == sum(subtotals)`).
- **Desde `docs/API_DESIGN.md`:**
  - `EP-001`: `GET /api/v1/products?q=termino` retornando Envelope `{ items: list[ProductResponse], total: int }`.
  - `EP-002`: `GET /api/v1/products/{id}` retornando `DTO-PROD-RES-001`.
  - `DTO-ERR-001`: Envelope de error `{ error_code, message, detail }`.

---

## 5. Taxonomía Formal y Mecanismo `TaskSpec`

Toda tarea de implementación en frontend debe estar formalmente delimitada bajo el contrato `TaskSpec` del arnés:

```python
TaskSpec(
    task_id="TS-FRONTEND-001",
    goal="Implementar la interfaz web interactiva de catálogo y carrito de compras en Vanilla HTML/CSS/JS",
    category="feature",
    allowed_paths=[
        "src/frontend/**",
        "tests/frontend/**",
    ],
    forbidden_paths=[
        "src/backend/**",      # Preserva código clínico preexistente
        "src/database/**",     # Preserva esquemas clínicos preexistentes
        "src/catalog/**",      # Backend sellado (solo lectura)
        "src/shared/**",       # Infraestructura backend sellada
        "src/cart/**",         # Blindaje AD-003: cero servidor para carrito
        "src/auth/**",         # Blindaje Anti-Amnesia: sin autenticación
        "src/users/**",        # Blindaje Anti-Amnesia: sin usuarios
        "src/payments/**",     # Blindaje Anti-Amnesia: sin pasarelas de pago
        "package.json",        # Prohibición de frameworks/bundlers pesados no autorizados
        "node_modules/**",     # Prohibición de dependencias pesadas para este MVP
    ],
    constraints=[
        "Vanilla HTML5 semántico, CSS3 moderno y JavaScript ES6+ sin bundlers externos (AD-005)",
        "Persistencia de carrito exclusivamente en Web Storage (localStorage) (AD-003)",
        "Consumo exclusivo de endpoints GET (/api/v1/products, /api/v1/products/{id})",
        "Manejo explícito de 3 estados UI: Loading, Empty y Error (AC-001..AC-003)",
        "Cero pantallas de autenticación, login, usuarios o pasarelas de pago (OUT OF SCOPE)",
    ],
    acceptance_criteria=[
        "Renderizado de catálogo con nombre, descripción y precio unitario formateado (AC-001)",
        "Búsqueda textual reactiva insensible a mayúsculas con mensaje de vacío si total=0 (AC-002, AC-003)",
        "Adición, selector de cantidad y eliminación en carrito persistido en localStorage (AC-004, AC-005)",
        "Cálculo exacto e inmediato de subtotales y total acumulado (AC-006, INV-004)",
    ],
    test_targets=["tests/frontend/test_catalog_frontend.py"]
)
```

Cualquier archivo fuera de `allowed_paths` será clasificado como **`orphan_change`** y rechazado por el `ScopePolicy` del arnés.

---

## 6. Regla de Oro Anti-Amnesia y No-Goldplating

> 🛑 **REGLAS CONTRACTUALES DE IMPLEMENTACIÓN:**
> 1. **Anti-Amnesia Estricta:** Queda **ESTRICTAMENTE PROHIBIDO** crear vistas, modales, formularios, botones o campos de login, contraseña, registro de usuario, tokens JWT, roles, perfil de usuario, tarjetas de crédito, pasarelas de pago (Stripe, PayPal) o checkout financiero.
> 2. **Respeto a AD-003 (Carrito en Cliente):** El carrito reside 100% en `localStorage`. Queda **ESTRICTAMENTE PROHIBIDO** realizar llamadas `fetch` a rutas de servidor como `/api/v1/carts` o `/api/v1/cart-items`.
> 3. **No-Goldplating de Stack Tecnológico:** Queda **ESTRICTAMENTE PROHIBIDO** agregar `package.json`, `node_modules/`, bundlers (Webpack, Vite) o frameworks pesados (React, Angular, Vue) no autorizados. La solución debe basarse en Vanilla HTML/CSS/JS nativo.
> 4. **No-Goldplating Funcional:** Queda **ESTRICTAMENTE PROHIBIDO** crear formularios o interfaces para crear, editar o eliminar productos en el catálogo comercial (el backend es de solo lectura).
> 5. **Preservación Perimetral:** Queda **ESTRICTAMENTE PROHIBIDO** modificar archivos en `src/catalog/`, `src/shared/`, `src/backend/` o `src/database/`.

---

## 7. Workflow de Implementación Interactiva

El agente debe proceder siguiendo la secuencia de construcción modular de frontend:

### Paso 1: Estructura Semántica (`src/frontend/index.html`)
- Header con marca/título comercial y botón/icono de carrito con badge indicador de `total_items`.
- Sección de búsqueda con input de texto reactivo (`#search-input`) para el parámetro `q` (`REQ-002`).
- Contenedor principal de catálogo (`#catalog-container`) con zonas para los estados Loading (spinner), Empty (`#empty-state` con mensaje amigable `AC-003`) y Error (`#error-state`).
- Panel lateral o modal accesible de Carrito de Compras (`#cart-drawer`) que renderiza la lista de ítems (`DTO-CART-001`), controles de cantidad (+ / -), botón eliminar, subtotal por ítem y total acumulado (`#cart-total`).

### Paso 2: Diseño y Hoja de Estilos (`src/frontend/styles.css`)
- Estructura limpia y responsiva basada en CSS Grid para tarjetas de catálogo y Flexbox para cabeceras y panel de carrito.
- Paleta sobria y profesional, contraste accesible (WCAG 2.1 AA), tipografía de sistema legible y microinteracciones en botones y badges.

### Paso 3: Cliente de Transporte API (`src/frontend/api.js`)
- Módulo cliente `api.js` configurando `API_BASE_URL = "http://127.0.0.1:8000/api/v1"`.
- `fetchProducts(searchTerm)`: Invoca `GET /api/v1/products?q=...` y extrae `{ items, total }`.
- `fetchProductById(productId)`: Invoca `GET /api/v1/products/{id}`.
- Manejo estructurado de fallos transformando respuestas HTTP no exitosas en el formato `DTO-ERR-001`.

### Paso 4: Gestor de Carrito en Cliente (`src/frontend/cart.js`)
- Módulo `CartManager` (`COMP-002`):
  - Carga y guarda atómicamente el estado en `localStorage.getItem("shopping_cart")` y `localStorage.setItem(...)`.
  - `addItem(product)`: Añade un producto con `quantity = 1` o incrementa `quantity` si ya existe (`AC-004`).
  - `updateQuantity(productId, delta)`: Modifica la cantidad. Si la cantidad resultante es menor a 1, remueve el ítem (`AC-005`, `INV-002`).
  - `removeItem(productId)`: Elimina el ítem del array (`AC-005`).
  - `calculateTotals()`: Recalcula subtotales (`unit_price * quantity`) y `total_amount = sum(subtotals)` (`AC-006`, `INV-004`).
  - `getState()`: Retorna `CartState`.

### Paso 5: Controlador de Interfaz y Enlace de Eventos (`src/frontend/app.js`)
- Inicialización al cargar el DOM (`DOMContentLoaded`): renderizado inicial del catálogo y recuperación del carrito desde `localStorage`.
- Escucha de eventos de teclado en input de búsqueda con debouncing ligero para filtrar catálogo (`AC-002`).
- Gestión de transiciones entre estados UI: visualización de spinner mientras carga, renderizado de tarjetas, estado vacío si `total === 0` o banner de error.
- Interacción con el carrito: toggle de apertura/cierre de drawer, eventos de botones de adición, incremento, decremento y eliminación con actualización reactiva inmediata de subtotales y total general.

### Paso 6: Suite de Validación de Frontend (`tests/frontend/`)
- `tests/frontend/test_catalog_frontend.py`: Pruebas automatizadas de marcado HTML, presencia de selectores requeridos, estructura de datos en `cart.js`, invariantes de cálculo aritmético y ausencia de endpoints de servidor prohibidos.

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse de inmediato:
- 🚩 **Amnesia de Scope:** Crear formularios de login, registro, pantallas de autenticación o pasarelas de pago.
- 🚩 **Invasión de Carrito en Servidor (`AD-003`):** Intentar hacer `fetch` a `/api/v1/carts` o `/api/v1/cart-items`.
- 🚩 **Goldplating de Dependencias:** Crear `package.json`, instalar `node_modules` o configurar React/Vue/Vite no autorizados.
- 🚩 **Mutación de Catálogo:** Agregar botones o formularios para "Crear Producto", "Editar Producto" o "Eliminar Producto".
- 🚩 **Invasión Perimetral:** Modificar archivos en `src/catalog/`, `src/shared/`, `src/backend/` o `src/database/`.

---

## 9. Contrato de Salida Formal

La implementación de frontend DEBE ubicarse estrictamente dentro de los siguientes archivos:

```text
src/
└── frontend/
    ├── index.html        # Estructura semántica (catálogo, barra de búsqueda, panel de carrito)
    ├── styles.css        # Diseño responsivo y visualización de estados UI
    ├── api.js            # Cliente fetch para EP-001 y EP-002 con DTO-ERR-001
    ├── cart.js           # Módulo CartManager (localStorage, DTO-CART-001, INV-002, INV-004)
    └── app.js            # Controlador principal de eventos y renderizado reactivo
tests/
└── frontend/
    └── test_catalog_frontend.py  # Tests deterministas de marcado, carrito e invariantes
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la implementación de frontend, verificar:
- [ ] Todos los archivos creados están dentro de `allowed_paths` (`src/frontend/**`, `tests/frontend/**`).
- [ ] Cero archivos modificados en `src/catalog/`, `src/shared/`, `src/backend/` o `src/database/`.
- [ ] Cero dependencias añadidas en `package.json` o carpetas `node_modules`.
- [ ] El carrito funciona 100% sobre `localStorage` y respeta `INV-002` e `INV-004`.
- [ ] Se implementan visualmente los 3 estados UI (Loading, Empty, Error).
- [ ] Cero pantallas o campos de login, usuarios, roles, passwords, JWT o pasarelas de pago.
- [ ] Los tests deterministas en `tests/frontend/` pasan 100% en verde.

---

## 11. Criterio de Término

La etapa de implementación de frontend concluye cuando:
1. Todos los archivos requeridos existen en disco y cargan limpiamente en navegador sin errores de consola.
2. La suite `pytest tests/frontend/test_catalog_frontend.py` finaliza con código de salida 0 (100% verde).
3. El test de perímetro `test_frontend_physical_scope_enforcement` valida con `ScopePolicy` la ausencia de archivos huérfanos.
4. La suite completa del harness y tests unitarios permanece 100% en verde.
