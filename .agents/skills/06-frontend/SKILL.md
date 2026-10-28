---
name: frontend-implementation
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation]
stage: 5
project_types: [web_app]
governance: all
description: Implementacion modular de interfaz de usuario. Define estructura de componentes, consumo de API, gestion del estado en cliente y manejo de estados UI respetando el PRD y la Arquitectura.
---

# Skill 06: Implementación de Frontend (Frontend Implementation)

## 1. Overview y Propósito

Esta skill gobierna la **construcción física de la interfaz de usuario** del sistema según los contratos arquitectónicos y funcionales formalmente aprobados. Traduce los requerimientos del PRD (`docs/PRD.md`), las directivas arquitectónicas (`docs/ARCHITECTURE.md`), las estructuras de estado y almacenamiento de datos (`docs/DATA_MODEL.md`) y los contratos REST (`docs/API_DESIGN.md`) en una interfaz de usuario interactiva, modular, responsiva, accesible y de alto rendimiento.

Su propósito fundamental es responder con rigor de ingeniería:
> **¿Cómo implementar la interfaz de usuario para el contexto acotado (bounded context) aprobado de forma modular, responsiva y desacoplada, garantizando el consumo estricto de los contratos de API, el manejo predecible de los estados UI y del estado en cliente según las decisiones arquitectónicas aprobadas, y la delimitación perimetral estricta sin introducir dependencias pesadas no autorizadas ni código fuera de alcance?**

La skill opera bajo principios fundamentales de gobernanza metodológica:
1. **Desacoplamiento Estricto y Estado en Cliente:** La gestión del estado en el cliente (sea Web Storage, memoria o store reactivo) se rige por las decisiones arquitectónicas aprobadas (`AD-xxx`). Queda terminantemente prohibido asumir o forzar endpoints en servidor no aprobados en `API_DESIGN.md`.
2. **Consumo Estricto de Contratos de API:** La comunicación con servicios backend se realiza exclusivamente a través de los endpoints formales y DTOs canónicos aprobados en `docs/API_DESIGN.md`.
3. **Manejo Obligatorio de los 3 Estados UI:** Toda vista o componente que consuma datos asíncronos debe implementar de forma explícita los estados de **Carga (Loading)**, **Vacío (Empty)** y **Error (Fail-Fast)**.
4. **Delimitación Perimetral Estricta mediante `TaskSpec`:** La codificación física se circunscribe a las rutas de frontend permitidas (`allowed_paths`), blindando las capas de backend y base de datos contra modificaciones no autorizadas (`forbidden_paths`).
5. **No-Goldplating de Stack Tecnológico:** Implementación apegada estrictamente al stack tecnológico normado en la arquitectura (ej. Vanilla HTML5/CSS3/JS sin dependencias innecesarias a menos que el PRD o ADRs aprueben un framework específico).

---

## 2. Cuándo Usar (Use When)

- Inmediatamente después de que `05-backend` (`backend-implementation`) haya finalizado con su suite unitaria y contratos de API aprobados.
- Cuando se requiere codificar la estructura de interfaz, hojas de estilo y lógica interactiva de usuario para el contexto acotado bajo desarrollo.
- Previo a la ejecución de las pruebas integrales de sistema en `08-testing` y a la configuración de empaquetado/despliegue en `10-deployment`.

---

## 3. Precondiciones

1. **Aprobación Formal de la Cadena Upstream:**
   - `docs/PRD.md` DEBE existir con `status: APPROVED`.
   - `docs/ARCHITECTURE.md` DEBE existir con `status: APPROVED`.
   - `docs/DATA_MODEL.md` DEBE existir con `status: APPROVED`.
   - `docs/API_DESIGN.md` DEBE existir con `status: APPROVED`.
   - La suite de pruebas de backend del contexto acotado DEBE estar 100% aprobada.
2. **Definición de `TaskSpec` Perimetral:**
   - Toda tarea de frontend debe formalizar `allowed_paths` delimitando los archivos de interfaz y tests correspondientes.
3. **Disponibilidad de Servicio Backend:**
   - El backend debe exponer los contratos de endpoints y DTOs requeridos para el contexto de interfaz.

---

## 4. Entradas (Inputs) desde Upstream

La skill extrae deterministamente:
- **Desde `docs/PRD.md`:**
  - Requerimientos funcionales (`REQ-xxx`) asignados a la interfaz.
  - Criterios de aceptación observables en interfaz (`AC-xxx`).
  - Límites de alcance (`OUT OF SCOPE`): prohibición estricta de implementar pantallas, campos o flujos excluidos.
- **Desde `docs/ARCHITECTURE.md`:**
  - Componentes de interfaz (`COMP-xxx`).
  - Decisiones técnicas estructurales (`AD-xxx`), incluyendo stack de UI, persistencia en cliente y políticas de autenticación/visitante.
- **Desde `docs/DATA_MODEL.md`:**
  - DTOs de transferencia o de estado en cliente (`DTO-xxx`).
  - Invariantes de datos (`INV-xxx`) que la interfaz debe respetar o validar.
- **Desde `docs/API_DESIGN.md`:**
  - Endpoints canónicos (`EP-xxx`), métodos HTTP y parámetros de consulta/ruta.
  - Esquemas de respuesta de éxito y DTOs de error estructurado (`DTO-ERR-xxx`).

---

## 5. Taxonomía Formal y Mecanismo `TaskSpec`

Toda tarea de implementación en frontend debe estar formalmente delimitada bajo el contrato `TaskSpec` del arnés para garantizar el aislamiento perimetral del contexto acotado (bounded context):

```python
TaskSpec(
    task_id="TS-FRONTEND-<id>",
    goal="Implementar la interfaz de usuario para el contexto acotado <bounded_context>",
    category="feature",
    allowed_paths=[
        "src/frontend/**",
        "tests/frontend/**",
    ],
    forbidden_paths=[
        "src/backend/**",            # Preservación de código de backend
        "src/database/**",           # Preservación de esquemas de datos
        "src/<bounded_context>/**",  # Preservación de módulos backend sellados
        "src/shared/**",             # Preservación de infraestructura compartida
        "package.json",              # Prohibición de manifiestos no autorizados en stack Vanilla
        "node_modules/**",           # Prohibición de dependencias pesadas no autorizadas
    ],

    constraints=[
        "Stack tecnológico alineado estrictamente con las decisiones arquitectónicas (AD-xxx)",
        "Persistencia y estado cliente alineados con el diseño arquitectónico y de datos",
        "Consumo exclusivo de endpoints y DTOs autorizados en docs/API_DESIGN.md",
        "Manejo explícito de 3 estados UI: Loading, Empty y Error",
        "Cero elementos, vistas o formularios declarados OUT OF SCOPE",
    ],
    acceptance_criteria=[
        "Cumplimiento verificable de los criterios de aceptación AC-xxx de la interfaz",
    ],
    test_targets=["tests/frontend/..."]
)
```

Cualquier archivo fuera de `allowed_paths` será clasificado como **`orphan_change`** y rechazado por el `ScopePolicy` del arnés.

---

## 6. Regla de Oro Anti-Amnesia y No-Goldplating

> 🛑 **REGLAS CONTRACTUALES DE IMPLEMENTACIÓN:**
> 1. **Anti-Amnesia Estricta:** Queda **ESTRICTAMENTE PROHIBIDO** crear vistas, modales, formularios, botones o campos asociados a requerimientos categorizados como `OUT OF SCOPE` en el PRD (tales como flujos de login, registro, passwords, JWT, checkout financiero, etc.).
> 2. **Respeto a Decisiones Arquitectónicas (`AD-xxx`):** La persistencia y el ciclo de vida del estado en cliente deben seguir rigurosamente los ADRs aprobados. Queda **ESTRICTAMENTE PROHIBIDO** inventar endpoints o persistencia en servidor para funciones asignadas al cliente.
> 3. **No-Goldplating de Stack Tecnológico:** Queda **ESTRICTAMENTE PROHIBIDO** agregar herramientas de build, bundlers o frameworks pesados no aprobados en la arquitectura.
> 4. **No-Goldplating Funcional:** Queda **ESTRICTAMENTE PROHIBIDO** añadir capacidades de mutación o administración sobre recursos definidos como de solo lectura en los contratos upstream.
> 5. **Preservación Perimetral:** Queda **ESTRICTAMENTE PROHIBIDO** modificar archivos pertenecientes a capas de backend, esquemas de persistencia o contextos acotados ajenos.

---

## 7. Workflow de Implementación Interactiva

El agente debe proceder siguiendo la secuencia de construcción modular de frontend:

### Paso 1: Estructura Semántica de la Interfaz
- Definir el marcado semántico de la vista o componente con accesibilidad (roles, etiquetas, jerarquía de encabezados).
- Establecer contenedores específicos para los tres estados UI: **Loading**, **Empty** y **Error**.

### Paso 2: Diseño y Hoja de Estilos
- Implementar maquetación responsiva con CSS moderno (Grid/Flexbox) adaptada a resoluciones móviles y desktop.
- Asegurar contraste visual accesible, tipografía clara y microinteracciones fluidas en controles interactivos.

### Paso 3: Cliente de Transporte y Consumo de API
- Modularizar las funciones de invocación HTTP encapsulando URLs base y parámetros según `docs/API_DESIGN.md`.
- Mapear respuestas exitosas a los modelos de vista requeridos y manejar fallos HTTP transformándolos en DTOs de error estructurados.

### Paso 4: Gestor de Estado en Cliente
- Encapsular la lógica de estado del contexto de usuario (por ejemplo en Web Storage o store reactivo) garantizando atomicidad y cumplimiento de invariantes (`INV-xxx`).

### Paso 5: Controlador de Interfaz y Enlace de Eventos
- Vincular eventos de usuario (búsqueda, clics, selección de cantidades) con actualización reactiva de la interfaz.
- Gobernar las transiciones entre estados UI (mostrar feedback de carga, renderizar estado vacío cuando corresponda, desplegar banner de error ante fallos).

### Paso 6: Suite de Validación de Frontend
- Desarrollar pruebas automatizadas que verifiquen marcado, selectores, lógica de estado, invariantes de datos y ausencia de llamadas a endpoints prohibidos.

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse de inmediato:
- 🚩 **Amnesia de Scope:** Crear formularios o pantallas de funciones categorizadas como `OUT OF SCOPE` en el PRD.
- 🚩 **Invasión Perimetral de Servidor:** Intentar hacer llamadas `fetch` a endpoints de servidor no autorizados en los contratos de API.
- 🚩 **Goldplating de Dependencias:** Introducir frameworks, bundlers o dependencias pesadas no aprobadas en la arquitectura.
- 🚩 **Mutación No Autorizada:** Agregar botones o formularios de mutación sobre APIs de solo lectura.
- 🚩 **Invasión Perimetral de Código:** Modificar archivos en capas de backend o esquemas de persistencia.

---

## 9. Contrato de Salida Formal

La implementación de frontend DEBE ubicarse estrictamente dentro de la estructura de archivos definida en la arquitectura para el contexto acotado:

```text
src/
└── <frontend_module>/
    ├── index.html        # Estructura semántica de la interfaz
    ├── styles.css        # Diseño responsivo y estados UI
    ├── api.js            # Cliente HTTP para contratos de API
    ├── <state_mgr>.js    # Gestor de estado en cliente
    └── app.js            # Controlador principal de eventos y renderizado
tests/
└── <frontend_module>/
    └── test_<module>.py  # Tests deterministas de marcado, estado e invariantes
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la implementación de frontend, verificar:
- [ ] Todos los archivos creados están dentro de `allowed_paths`.
- [ ] Cero archivos modificados en capas de backend o base de datos preexistentes.
- [ ] Cero dependencias añadidas en manifiestos de paquetes no autorizados.
- [ ] El estado en cliente cumple rigurosamente con las decisiones arquitectónicas e invariantes de datos.
- [ ] Se implementan visualmente los 3 estados UI (Loading, Empty, Error).
- [ ] Cero componentes o campos correspondientes a requerimientos fuera de alcance.
- [ ] Los tests deterministas de frontend pasan 100% en verde.

---

## 11. Criterio de Término

La etapa de implementación de frontend concluye cuando:
1. Todos los archivos requeridos existen en disco y cargan limpiamente en navegador sin errores de consola.
2. La suite de pruebas de frontend finaliza con código de salida 0 (100% verde).
3. El test de perímetro valida con `ScopePolicy` la ausencia de archivos huérfanos.
4. La suite completa del harness y tests unitarios permanece 100% en verde.

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En el proyecto de referencia comercial `catalogo-carrito-web`, los principios metodológicos generales de esta skill se instancian de la siguiente manera:

### 1. Entradas Específicas del Proyecto
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

### 2. TaskSpec Concreto de la Demo
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

### 3. Topología de Archivos de la Demo
- `src/frontend/index.html`: Estructura semántica de catálogo, barra de búsqueda (`#search-input`) y panel lateral de carrito (`#cart-drawer`).
- `src/frontend/styles.css`: Diseño responsivo (CSS Grid / Flexbox) y visualización de estados UI (Loading, Empty, Error).
- `src/frontend/api.js`: Cliente fetch para EP-001 y EP-002 con manejo estructurado de DTO-ERR-001.
- `src/frontend/cart.js`: Módulo CartManager (localStorage, DTO-CART-001, INV-002, INV-004).
- `src/frontend/app.js`: Controlador principal de eventos y renderizado reactivo.
- `tests/frontend/test_catalog_frontend.py`: Tests deterministas de marcado, carrito e invariantes.

```text
src/
└── frontend/
    ├── index.html        # Estructura semántica (catálogo, barra de búsqueda #search-input, panel de carrito #cart-drawer)
    ├── styles.css        # Diseño responsivo (CSS Grid / Flexbox) y visualización de estados UI (Loading, Empty, Error)
    ├── api.js            # Cliente fetch para EP-001 y EP-002 con manejo estructurado de DTO-ERR-001
    ├── cart.js           # Módulo CartManager (localStorage, DTO-CART-001, INV-002, INV-004)
    └── app.js            # Controlador principal de eventos y renderizado reactivo
tests/
└── frontend/
    └── test_catalog_frontend.py  # Tests deterministas de marcado, carrito e invariantes
```
