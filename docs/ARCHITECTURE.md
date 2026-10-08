---
project_id: "catalogo-carrito-web"
project_name: "Sistema Web Básico de Catálogo y Carrito de Compras"
version: 1
status: "APPROVED"
architecture_style: "modular_monolith"
governance_level: "bajo"
created_at: "2026-10-07"
updated_at: "2026-10-07"
---

# Especificación de Arquitectura — Sistema Web Básico de Catálogo y Carrito de Compras

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `status: APPROVED`).
- **Tipo de Proyecto:** `web_app` (Aplicación web interactiva cliente-servidor).
- **Nivel de Gobernanza:** `bajo` (Enfoque MVP: validaciones de entrada indispensables, sin sesiones con credenciales ni auditoría forense obligatoria).
- **Frontera de Alcance Heredada:**
  - `IN SCOPE:` Catálogo de productos, búsqueda textual por nombre, carrito de compras interactivo con modificación de cantidades y cálculo de subtotales/total.
  - `OUT OF SCOPE (Inmutable por Anti-Amnesia):`
    - Cero pasarelas de pago y procesamiento financiero.
    - Cero autenticación, roles y registro de cuentas de usuario.
    - Cero motores de recomendaciones y algoritmos predictivos.

---

## 2. Catálogo de Componentes de Software (Components)
- **COMP-001 [catalog_service]:**
  - **Propósito:** Encapsular la lógica de dominio para exploración y filtrado del catálogo de productos.
  - **Responsabilidades:**
    - Proporcionar la consulta de productos disponibles con sus datos comerciales básicos (identificador, nombre, descripción básica, precio unitario).
    - Ejecutar el filtrado insensible a mayúsculas y minúsculas por término de búsqueda sobre el nombre del producto.
    - Gestionar el estado de catálogo sin coincidencias para informar a la vista.
  - **Requisitos Soportados:** `REQ-001`, `REQ-002`.
  - **Criterios de Aceptación Vinculados:** `AC-001`, `AC-002`, `AC-003`.
- **COMP-002 [cart_service]:**
  - **Propósito:** Encapsular las operaciones de negocio y cálculo financiero básico de la selección de compra.
  - **Responsabilidades:**
    - Gestionar la adición de productos disponibles con una cantidad inicial especificada.
    - Actualizar cantidades de ítems existentes (incremento, reducción y remoción del ítem al fijar cantidad en cero).
    - Calcular en tiempo de ejecución los subtotales por ítem ($N \times \text{precio unitario}$) y el total consolidado.
    - Administrar el estado de carrito vacío.
  - **Requisitos Soportados:** `REQ-003`, `REQ-004`.
  - **Criterios de Aceptación Vinculados:** `AC-004`, `AC-005`, `AC-006`.
- **COMP-003 [web_ui]:**
  - **Propósito:** Proveer la interfaz gráfica web y orquestar las interacciones del usuario visitante anónimo.
  - **Responsabilidades:**
    - Renderizar visualmente el catálogo de productos y el campo de búsqueda dinámica.
    - Renderizar el carrito de compras con controles directos de modificación de cantidades y visualización de totales.
    - Capturar las acciones del usuario y sincronizar el estado visual con los servicios del sistema.
  - **Requisitos Soportados:** `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`.

---

## 3. Registro de Decisiones Arquitectónicas (Architectural Decisions)
- **AD-001 (architecture.pattern):**
  - **Decisión:** Monolito modular desacoplado.
  - **Justificación:** Cumple estrictamente los principios KISS y YAGNI. Un solo artefacto de ejecución y despliegue minimiza la fricción operativa y elimina la sobrecarga de red y orquestación de microservicios, manteniendo al mismo tiempo una separación lógica clara entre el catálogo y el carrito.
- **AD-002 (communication.style):**
  - **Decisión:** Comunicación cliente-servidor síncrona desacoplada mediante transporte HTTP REST básico.
  - **Justificación:** Desacopla la interfaz de usuario (`COMP-003`) de la lógica de procesamiento (`COMP-001`, `COMP-002`), facilitando la verificación aislada mediante pruebas automatizadas y permitiendo una evolución independiente de la vista sin acoplamiento a motores de plantillas monolíticos. Los detalles de contratos se delegan formalmente a `04-api-design`.
- **AD-003 (cart.state_strategy):**
  - **Decisión:** Retención de estado del carrito en almacenamiento local del cliente web (Web Storage) con validación de precios por servicio backend (Resuelve `OPEN-001` del PRD).
  - **Justificación:** Resuelve `OPEN-001` del PRD garantizando que el usuario visitante preserve los productos seleccionados si refresca la pestaña o reanuda su visita, sin requerir base de datos de usuarios ni gestión compleja de sesiones en servidor, en total consonancia con `governance_level: bajo` y `CONST-003`.
- **AD-004 (codebase.layout):**
  - **Decisión:** Organización del código fuente orientada a módulos de dominio (`catalog/`, `cart/`, `shared/`).
  - **Justificación:** Agrupa la lógica, modelos conceptuales y pruebas de cada capacidad de negocio en directorios cohesivos, mejorando la mantenibilidad y preparando el código para la formulación de unidades de trabajo atómicas en etapas posteriores.
- **AD-005 (tech_stack.runtime):**
  - **Decisión:** Backend ligero en Python 3.12+ con framework de servicios web liviano y Frontend web estándar (HTML5 / Vanilla CSS / JavaScript moderno sin frameworks pesados).
  - **Justificación:** Maximiza la compatibilidad con el entorno de pruebas del repositorio (`pytest`), garantiza un arranque inmediato sin procesos de compilación o bundling innecesarios y elimina dependencias de terceros pesadas.
- **AD-006 (error_handling.strategy):**
  - **Decisión:** Fail Fast en servicios de backend y notificación visual no intrusiva en interfaz de usuario.
  - **Justificación:** Los servicios rechazan inmediatamente operaciones inválidas (ej: cantidades negativas) con respuestas estructuradas, mientras que `web_ui` presenta mensajes claros al usuario sin degradar la disponibilidad de la aplicación.
- **AD-007 (security.governance_baseline):**
  - **Decisión:** Nivel de seguridad mínimo y estricto proporcional a `governance_level: bajo`.
  - **Justificación:** Modo visitante anónimo sin credenciales ni tokens de sesión. La seguridad se enfoca en validación de entradas en capa de transporte y verificación de cantidades numéricas.

---

## 4. Comunicación e Interacción entre Componentes
1. El usuario interactúa con `COMP-003 [web_ui]` ingresando texto de búsqueda o navegando productos.
2. `COMP-003` solicita a `COMP-001 [catalog_service]` los productos filtrados, renderizando el listado en pantalla.
3. Al agregar o modificar productos, `COMP-003` actualiza el estado mediante `COMP-002 [cart_service]`, recalculando subtotales y total acumulado.
4. El estado del carrito se preserva en el cliente web según `AD-003`, permaneciendo disponible ante recargas de página.

---

## 5. Estructura y Organización Lógica del Código

```text
src/
├── catalog/       # Módulo de catálogo (COMP-001): modelos de producto, búsqueda y servicios
├── cart/          # Módulo de carrito (COMP-002): lógica de cálculo, gestión de ítems y total
├── web/           # Módulo de presentación (COMP-003): vistas web estáticas y scripts cliente
└── shared/        # Constantes compartidas, utilitarios comunes de validación y configuración
```

*(Nota de gobierno: Este árbol define la topología conceptual de módulos para guiar la estructura del código).*

---

## 6. Seguridad y Cumplimiento Normativo
- **Cumplimiento de exclusiones:** No se incorporan pasarelas financieras, gestión de sesiones con credenciales ni componentes prescriptivos.
- **Validaciones mínimas:** Sanitización básica de cadenas de búsqueda y restricción estricta de cantidades a enteros positivos ($N \ge 1$).
- **Privacidad:** No se capturan ni almacenan datos personales sensibles ni PII (CWE-532 no aplicable a este MVP).

---

## 7. Decisiones Técnicas Delegadas (Downstream Scope)
Para preservar la pureza del pipeline y el principio de desacoplamiento:
- **Delegado a `03-data-modeling`:**
  - Especificación formal del catálogo de datos (definición de entidades `Product`, atributos, tipos y estrategia de almacenamiento en memoria o archivo ligero).
  - Estructura formal de datos para el ítem de carrito (`CartItem`).
  - *Prohibición respetada:* No se incluyen sentencias ni esquemas de persistencia DDL en este documento.
- **Delegado a `04-api-design`:**
  - Contratos formales de interfaz (nombres de operaciones, métodos de transporte, esquemas de transferencia y códigos de retorno).
  - *Prohibición respetada:* No se detallan rutas HTTP específicas en este documento.
- **Delegado a `05-backend` / `06-frontend`:**
  - Implementación concreta y codificación de los módulos.
