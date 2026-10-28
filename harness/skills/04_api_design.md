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
  - `project_id`: Identificador canónico del proyecto.
  - `governance_level`: Nivel de gobernanza (`bajo`, `medio`, `alto`).
  - `REQ-xxx` e `IN SCOPE`: Requerimientos funcionales y operaciones del dominio en el contexto acotado (bounded context) aprobado.
  - `AC-xxx`: Criterios de aceptación observables asociados a las operaciones.
  - `OUT OF SCOPE`: Prohibición explícita de operaciones o conceptos excluidos.
- **Desde `docs/ARCHITECTURE.md`:**
  - `COMP-xxx`: Componentes de software y subsistemas (servicios de dominio, interfaces de usuario).
  - `AD-xxx`: Decisiones arquitectónicas vinculantes:
    * Estilo de API y transporte (`AD-002`: HTTP REST, etc.).
    * Frontera cliente-servidor (`AD-003`: retención de estado en cliente vs endpoints en servidor).
    * Estrategia de manejo de errores (`AD-006`: Fail-Fast, respuestas estructuradas).
    * Nivel de seguridad y autenticación (`AD-007`).
- **Desde `docs/DATA_MODEL.md`:**
  - `ENT-xxx`: Entidades de persistencia y sus esquemas de atributos y tipos.
  - `DTO-xxx`: Esquemas de datos y estructuras de transferencia ya formuladas.
  - `IDX-xxx` e `INV-xxx`: Índices para parámetros de consulta e invariantes de validación.

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
> 2. **No-Goldplating (Fidelidad a Requerimientos / Read-Only cuando aplique):** La API de servidor debe exponer exclusivamente las operaciones respaldadas por el PRD. Si los requisitos del actor o caso de uso definen únicamente exploración o consulta (`solo lectura`), queda **ESTRICTAMENTE PROHIBIDO** inventar métodos de mutación (`POST`, `PUT`, `PATCH` o `DELETE`) no solicitados explícitamente.
> 3. **Respeto a la Frontera Arquitectónica (`AD-003`):** Si la arquitectura estableció retención de estado en el cliente (ej. Web Storage / `localStorage`), queda **ESTRICTAMENTE PROHIBIDO** inventar endpoints de persistencia en servidor para dicho estado.
> 4. **Aislamiento Físico:** Queda **ESTRICTAMENTE PROHIBIDO** emitir listas de rutas físicas (`allowed_paths`) o código ejecutable de frameworks (`FastAPI`, `APIRouter`), delegados a `05-backend`.

---

## 7. Workflow de Elicitación Interactiva

El agente debe guiar al desarrollador respetando las decisiones previas y formulando preguntas con opciones claras ([AGENTS.md](AGENTS.md)):

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

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian en los siguientes contratos:
- **Endpoints de Catálogo (`EP-xxx`):**
  - `EP-001 [list_products]`: `GET /api/v1/products?q=termino` retornando `DTO-PROD-LIST-001` con filtrado insensible a mayúsculas y paginación básica (`REQ-001`, `REQ-002`).
  - `EP-002 [get_product_by_id]`: `GET /api/v1/products/{id}` retornando `DTO-PROD-RES-001` o error 404 estructurado.
- **Esquemas de Transferencia (`DTO-xxx`):**
  - `DTO-PROD-RES-001 [ProductResponse]`: `{ id: int, name: str, description: str | None, price: float }`.
  - `DTO-PROD-LIST-001 [ProductListResponse]`: `{ items: ProductResponse[], total: int }`.
  - `DTO-ERR-001 [ErrorEnvelope]`: `{ error_code: str, message: str, detail: str }`.
- **Catálogo de Errores (`ERR-xxx`):** `ERR-001` (404 Not Found), `ERR-002` (400 Bad Request por parámetro inválido o `q > 100`), `ERR-500` (500 Internal Server Error).
- **Frontera de Carrito (`AD-003`):** Cero endpoints de servidor para el carrito (`/carts`, `/cart-items`), ya que el estado reside en `localStorage` del cliente (`DTO-CART-001`).
- **Invariante de Solo Lectura:** La API para el MVP de catálogo es 100% de solo lectura (únicamente métodos `GET` autorizados, prohibidos `POST/PUT/PATCH/DELETE` sobre `/products`).
