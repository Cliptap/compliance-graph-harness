---
name: api-design
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling]
stage: 3
project_types: [web_app, api, mobile]
governance: all
description: Diseno de API REST. Define contratos de endpoints (EP-xxx), metodos HTTP de solo lectura, DTOs de transferencia (DTO-xxx), mapeo de errores (ERR-xxx) y linaje de requerimientos respetando el PRD, la Arquitectura y el Modelo de Datos.
---

# Skill 04: Diseño de Contratos de API (API Design)

## 1. Overview y Propósito

Esta skill traduce los requerimientos funcionales (`REQ-xxx`) y criterios de aceptación (`AC-xxx`) de `docs/PRD.md`, los componentes (`COMP-xxx`) y decisiones de `docs/ARCHITECTURE.md` (`AD-001`, `AD-002`, `AD-003`, `AD-005`, `AD-006`, `AD-007`) y el modelo de datos de `docs/DATA_MODEL.md` (`ENT-001`, `DTO-CART-001`, `IDX-001`, `INV-xxx`) en una **especificación formal de contratos de interfaz pública y transporte** en `docs/API_DESIGN.md`.

Su propósito fundamental es responder con rigor técnico:
> **¿Cuáles son los endpoints, métodos HTTP, esquemas de transferencia (DTOs), códigos de estado y formatos de error requeridos para satisfacer los casos de uso aprobados sin inventar endpoints no solicitados ni contradecir la arquitectura?**

La skill opera bajo cuatro principios de interoperabilidad del arnés:
1. **Regla de Oro Anti-Amnesia:** Está estrictamente prohibido definir endpoints, DTOs o esquemas para conceptos sentenciados como `OUT OF SCOPE` en el PRD (cero autenticación, roles, sesiones de servidor, pagos, pasarelas o recomendaciones).
2. **Coherencia con Decisiones Previas (Anti-Deriva DAG):**
   - El estilo de transporte **HTTP REST** síncrono desacoplado viene formalmente sellado desde `AD-002`: queda terminantemente prohibido re-deliberar o preguntar al usuario si prefiere GraphQL, gRPC o RPC.
   - La estrategia de seguridad sin credenciales para visitante anónimo viene sellada desde `AD-007` y `governance_level: bajo`: queda prohibido consultar por tokens JWT o roles RBAC.
   - La persistencia del carrito reside íntegramente en Web Storage del cliente (`AD-003` y `DTO-CART-001`): **queda estrictamente prohibido crear endpoints server-side para persistir o mutar carritos (`/carts`, `/cart-items`)**.
3. **Regla Estricta de No-Goldplating (API de Solo Lectura para MVP):**
   - El PRD define un catálogo comercial básico de exploración y búsqueda para un visitante anónimo (`ACT-01`, `REQ-001`, `REQ-002`). No existen casos de uso administrativos de creación, edición o baja de productos.
   - En consecuencia, la API del servidor para este MVP es **100% de solo lectura (únicamente métodos GET autorizados)**. Queda prohibido definir métodos de mutación (`POST`, `PUT`, `PATCH`, `DELETE`) para el catálogo sin un requerimiento de negocio explícito.
4. **Principio de Desacoplamiento y Progresión:** La skill define contratos HTTP formales, schemas DTO, códigos de error y respuestas, pero **no genera código ejecutable de backend** (routers FastAPI, controladores, handlers) ni listas de rutas físicas de archivos (`allowed_paths`), delegadas a `05-backend`.

---

## 2. Cuándo Usar (Use When)

- Inmediatamente después de que `docs/DATA_MODEL.md` haya alcanzado el estado `status: APPROVED`.
- Cuando se requiere definir los contratos formales de comunicación cliente-servidor (endpoints, query parameters, esquemas DTO de request/response y manejo estructurado de errores).
- Previo a la implementación de código en `05-backend` y `06-frontend` y a la formulación de pruebas de integración de endpoints en `08-testing`.

---

## 3. Precondiciones

1. **Aprobación de Artefactos Upstream:**
   - `docs/PRD.md` DEBE existir con `status: APPROVED`.
   - `docs/ARCHITECTURE.md` DEBE existir con `status: APPROVED`.
   - `docs/DATA_MODEL.md` DEBE existir con `status: APPROVED`.
   - Queda terminantemente prohibido diseñar contratos de API si los artefactos previos están en estado `DRAFT` o ausentes.
2. **Respeto a las Invariantes Heredadas:**
   - Adoptar `governance_level: "bajo"` (sin sesiones con credenciales ni auditoría pesada).
   - Adoptar `api_style: "REST"` y prefijo canónico `base_path: "/api/v1"`.
3. **Persistencia Garantizada:** El entorno debe permitir generar y versionar `docs/API_DESIGN.md`.

---

## 4. Entradas (Inputs) desde Upstream

La skill extrae deterministamente:
- **Desde `docs/PRD.md`:**
  - `project_id`: Identificador canónico del proyecto (`catalogo-carrito-web`).
  - `governance_level`: Nivel de gobernanza (`bajo`).
  - `REQ-001` (Catálogo de productos con datos comerciales básicos) y `REQ-002` (Búsqueda textual insensible a mayúsculas).
  - `AC-001`, `AC-002`, `AC-003`: Criterios de aceptación observables del catálogo y búsqueda.
  - `OUT OF SCOPE`: Prohibición explícita de pasarelas de pago, autenticación/cuentas y recomendaciones.
- **Desde `docs/ARCHITECTURE.md`:**
  - `COMP-001 [catalog_service]`: Servicio de catálogo en backend.
  - `COMP-002 [cart_service]`: Operaciones de carrito en cliente.
  - `COMP-003 [web_ui]`: Interfaz gráfica visitante.
  - `AD-001`: Monolito modular desacoplado.
  - `AD-002`: Transporte HTTP REST síncrono desacoplado.
  - `AD-003`: **Carrito en Web Storage (`localStorage`) en cliente** (sin tablas ni endpoints en servidor).
  - `AD-005`: Backend en Python 3.12+ con persistencia en SQLite / SQLAlchemy.
  - `AD-006`: Fail Fast con respuestas estructuradas ante operaciones inválidas.
  - `AD-007`: Nivel de seguridad mínimo: modo visitante anónimo sin tokens.
- **Desde `docs/DATA_MODEL.md`:**
  - `ENT-001 [Product]`: Entidad de persistencia en SQLite con atributos `id`, `name`, `description`, `price`.
  - `DTO-CART-001 [CartItem]`: Estructura en Web Storage del cliente (`product_id`, `name`, `unit_price`, `quantity`, `subtotal`).
  - `IDX-001 [idx_product_name]`: Índice para optimización de búsqueda textual.
  - `INV-001` (`price >= 0.0`), `INV-003` (`name` no vacío ni nulo).

---

## 5. Taxonomía Formal de Diseño de API

Toda definición en esta fase debe utilizar los siguientes prefijos normativos:

| Prefijo | Tipo de Elemento | Definición | Ejemplo Válido | Antipatrón Prohibido |
| :--- | :--- | :--- | :--- | :--- |
| **`EP-xxx`** | Endpoint de API | Contrato de operación HTTP expuesto por el backend. | `EP-001 [list_products]: GET /api/v1/products?q=termino` | `EP-999: POST /api/v1/checkout (OUT OF SCOPE)` o `POST /api/v1/products (Goldplating)` |
| **`DTO-xxx`** | Objeto de Transferencia | Estructura JSON tipada para request o response. | `DTO-PROD-RES-001 [ProductResponse]: { id, name, description, price }` | `DTO-USER-001: Schema de credenciales/usuarios (OUT OF SCOPE)` |
| **`ERR-xxx`** | Error Estructurado | Código unívoco y máquina-legible para fallos y validaciones. | `ERR-001 [PRODUCT_NOT_FOUND]: 404 al consultar ID inexistente.` | Mensajes de error en texto plano sin código estructurado o exposición de stack traces. |

---

## 6. Regla de Oro Anti-Amnesia y No-Goldplating

> 🛑 **REGLAS CONTRACTUALES DETERMINISTAS:**
> 1. **Anti-Amnesia Estricta:** Si un concepto figura en `OUT OF SCOPE` en `docs/PRD.md` (usuarios, autenticación, contraseñas, tokens JWT, roles, pagos, tarjetas, pasarelas, transacciones financieras o recomendaciones), queda **ESTRICTAMENTE PROHIBIDO** definir endpoints, DTOs, headers de autorización o códigos de error asociados.
> 2. **No-Goldplating (Read-Only API para MVP):** Dado que el actor es visitante anónimo (`ACT-01`) y el sistema solo contempla consulta y búsqueda (`REQ-001`, `REQ-002`), la API del servidor debe ser **estrictamente de solo lectura (únicamente métodos GET)**. Queda **ESTRICTAMENTE PROHIBIDO** definir métodos `POST`, `PUT`, `PATCH` o `DELETE` sobre el catálogo sin un requerimiento de negocio explícito.
> 3. **Respeto a AD-003 (Carrito en Cliente):** El estado del carrito reside en el navegador (`localStorage`, `DTO-CART-001`). Queda **ESTRICTAMENTE PROHIBIDO** definir endpoints de persistencia de carritos en el servidor (`/carts`, `/cart-items`).
> 4. **Aislamiento Físico:** Queda **ESTRICTAMENTE PROHIBIDO** emitir listas de rutas físicas (`allowed_paths`) o código ejecutable de frameworks (`FastAPI`, `APIRouter`).

---

## 7. Workflow de Elicitación Interactiva

El agente debe guiar al desarrollador respetando las decisiones previas y formulando preguntas con opciones claras ([AGENTS.md](file:///c:/Users/Bastian/OneDrive/Documentos/GitHub/compliance-graph-harness/AGENTS.md)):

### Paso 1: Confirmación de Convenciones Base y Base Path
- Validar prefijo unificado `base_path: "/api/v1"`.
- Convención REST: Recursos en plural, kebab-case, respuestas JSON UTF-8.

### Paso 2: Especificación del Endpoint de Catálogo y Búsqueda (`EP-001`)
- **Método y Ruta:** `GET /api/v1/products`
- **Parámetro de Búsqueda:** Sellar de forma unívoca el parámetro como `q` (query param opcional: `GET /api/v1/products?q=termino`), eliminando ambigüedades.
- **Códigos HTTP:**
  - `200 OK`: Retorna colección estructurada en Envelope `DTO-PROD-LIST-001`.
  - `400 Bad Request`: Si el término de búsqueda excede la longitud permitida o contiene caracteres de control (`ERR-002`).

### Paso 3: Especificación del Endpoint de Consulta Unitaria (`EP-002`)
- **Método y Ruta:** `GET /api/v1/products/{id}`
- **Parámetro de Ruta:** `id`: Entero estrictamente positivo ($id \ge 1$).
- **Códigos HTTP:**
  - `200 OK`: Retorna `DTO-PROD-RES-001` con los datos comerciales del producto.
  - `404 Not Found`: Si no existe un producto con dicho identificador (`ERR-001`).
  - `400 Bad Request`: Si el identificador provisto no es un entero positivo (`ERR-002`).

### Paso 4: Esquemas DTO de Transferencia de Datos (`DTO-xxx`)
- **`DTO-PROD-RES-001 [ProductResponse]`:**
  - `id`: Integer, Not Null.
  - `name`: String, Not Null.
  - `description`: String, Nullable.
  - `price`: Numeric(10, 2) / Float, Not Null.
  *(Alineado biunívocamente con ENT-001 podada).*
- **`DTO-PROD-LIST-001 [ProductListResponse]` (Envelope Estructurado):**
  - `items`: List[`DTO-PROD-RES-001`], Not Null.
  - `total`: Integer, Not Null.
- **`DTO-ERR-001 [ErrorResponse]`:**
  - `error_code`: String, Not Null (`ERR-001`, `ERR-002`, etc.).
  - `message`: String, Not Null (mensaje legible).
  - `detail`: String, Nullable (detalle técnico de validación).

### Paso 5: Mapeo de Códigos de Estado y Manejo de Errores (`ERR-xxx`)
- `ERR-001 [PRODUCT_NOT_FOUND]`: HTTP 404. Producto no encontrado para el ID provisto.
- `ERR-002 [INVALID_PARAMETER]`: HTTP 400. Parámetro de ruta o query malformado o fuera de límites.
- `ERR-500 [INTERNAL_SERVER_ERROR]`: HTTP 500. Falla no controlada del servidor.

### Paso 6: Sello de Operaciones de Carrito en Cliente (`AD-003`)
- Documentar formalmente que las operaciones de carrito (`REQ-003`, `REQ-004`) no generan endpoints en el servidor, sino que son ejecutadas en el navegador por `COMP-002 [cart_service]` manipulando `DTO-CART-001` en `localStorage`.

### Paso 7: Seguridad de Transporte y Gobernanza
- Nivel de gobernanza bajo: modo visitante anónimo sin autenticación (`AD-007`).
- Sanitización básica de parámetros query contra ataques de inyección.
- Cabeceras de control CORS restrictivas orientadas a la interfaz web local.

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse de inmediato:
- 🚩 **Amnesia de Scope:** Proponer endpoints tipo `/api/v1/auth/**`, `/api/v1/users/**`, `/api/v1/payments/**` o `/api/v1/recommendations/**`.
- 🚩 **Violación del DAG Arquitectónico:** Preguntar si usar GraphQL o gRPC cuando `AD-002` ya selló REST.
- 🚩 **Violación de Carrito en Cliente:** Diseñar endpoints server-side para carritos (`/carts`, `/cart-items`) cuando `AD-003` selló almacenamiento en cliente.
- 🚩 **Goldplating de Mutación:** Definir métodos `POST`, `PUT`, `PATCH`, `DELETE` sobre productos sin respaldo en el PRD.
- 🚩 **Ambigüedad de Parámetros:** Usar `search` en vez del parámetro unívoco sellado `q`.
- 🚩 **Aislamiento Físico Violado:** Dictar listas `allowed_paths` o emitir código ejecutable de framework.

---

## 9. Contrato de Salida Formal (`docs/API_DESIGN.md`)

El artefacto generado DEBE ubicarse en `docs/API_DESIGN.md` y cumplir con la siguiente estructura:

```markdown
---
project_id: "catalogo-carrito-web"
project_name: "Sistema Web Básico de Catálogo y Carrito de Compras"
version: 1
status: "DRAFT"
governance_level: "bajo"
api_style: "REST"
base_path: "/api/v1"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# Especificación de Diseño de API — [Nombre del Proyecto]

## 1. Contexto e Invariantes Heredadas
- PRD de Referencia y Nivel de Gobernanza.
- Arquitectura de Referencia (COMP-001, COMP-002, AD-002, AD-003, AD-006, AD-007).
- Modelo de Datos de Referencia (ENT-001, DTO-CART-001).
- Restricciones de OUT OF SCOPE (cero auth, cero pagos).

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
  - Respuestas: 200 OK (DTO-PROD-RES-001), 404 Not Found (DTO-ERR-001), 400 Bad Request

## 3. Esquemas de Transferencia de Datos (DTO Schemas)
- **DTO-PROD-RES-001 [ProductResponse]:** id, name, description, price
- **DTO-PROD-LIST-001 [ProductListResponse]:** Envelope { items: list, total: int }
- **DTO-ERR-001 [ErrorResponse]:** error_code, message, detail

## 4. Mapeo de Códigos de Estado y Manejo de Errores
- **ERR-001 [PRODUCT_NOT_FOUND]:** HTTP 404
- **ERR-002 [INVALID_PARAMETER]:** HTTP 400
- **ERR-500 [INTERNAL_SERVER_ERROR]:** HTTP 500

## 5. Gestión de Carrito en Cliente y Desacoplamiento de Servidor
- Explicación formal de por qué no existen endpoints server-side para el carrito en respeto a AD-003 y DTO-CART-001.

## 6. Seguridad de Transporte y Gobernanza
- Modo visitante anónimo sin credenciales (AD-007). Sanitización de parámetros query y CORS.

## 7. Matriz de Linaje Contractual y Trazabilidad
- Mapeo bidireccional entre REQ-xxx / AC-xxx <-> COMP-xxx <-> ENT-xxx <-> EP-xxx <-> DTO-xxx.
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la especificación, verificar:
- [ ] Frontmatter YAML completo con `project_id`, `version: 1`, `status: "DRAFT"`, `governance_level`, `api_style: "REST"`, `base_path: "/api/v1"`.
- [ ] Todos los endpoints del servidor usan prefijo `EP-xxx` unívoco.
- [ ] La API es 100% de solo lectura (`GET` únicamente). Cero métodos `POST/PUT/PATCH/DELETE` no autorizados.
- [ ] El parámetro de búsqueda en `EP-001` está sellado unívocamente como `q`.
- [ ] `DTO-PROD-LIST-001` implementa Envelope estructurado (`items` y `total`).
- [ ] Cero endpoints para conceptos en `OUT OF SCOPE` (usuarios, auth, pagos, recomendaciones).
- [ ] Cero endpoints de persistencia de carrito en servidor (`AD-003`).
- [ ] Códigos de error `ERR-xxx` y DTOs formalmente definidos.
- [ ] No se emiten rutas físicas de código (`allowed_paths`) ni código ejecutable de frameworks.

---

## 11. Criterio de Término

El diseño de API concluye únicamente cuando el usuario aprueba formalmente `docs/API_DESIGN.md`, momento en el cual el frontmatter se actualiza a `status: "APPROVED"` para habilitar la transición a `05-backend` y `06-frontend`.
