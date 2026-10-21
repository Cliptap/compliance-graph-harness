---
project_id: "catalogo-carrito-web"
project_name: "Sistema Web Básico de Catálogo y Carrito de Compras"
version: 1
status: "APPROVED"
governance_level: "bajo"
api_style: "REST"
base_path: "/api/v1"
created_at: "2026-10-21"
updated_at: "2026-10-21"
---

# Especificación de Diseño de API — Sistema Web Básico de Catálogo y Carrito de Compras

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `status: APPROVED`).
- **Arquitectura de Referencia:** `docs/ARCHITECTURE.md` (Versión 1, `status: APPROVED`).
- **Modelo de Datos de Referencia:** `docs/DATA_MODEL.md` (Versión 1, `status: APPROVED`).
- **Nivel de Gobernanza:** `bajo` (MVP básico sin esquemas de credenciales ni auditoría forense pesada).
- **Límites de Alcance Heredados:**
  - `IN SCOPE:` Catálogo de productos, filtrado textual insensible a mayúsculas, operaciones de carrito en cliente y cálculo de subtotales/total.
  - `OUT OF SCOPE (Inmutable por Anti-Amnesia):` Cero pasarelas de pago ni procesamiento financiero, cero autenticación/roles/registro de cuentas de usuario, y cero motores de recomendaciones.
- **Decisiones Técnicas Vinculantes:**
  - `AD-001:` Monolito modular desacoplado.
  - `AD-002:` Comunicación cliente-servidor síncrona desacoplada mediante transporte HTTP REST básico con prefijo `/api/v1`.
  - `AD-003:` Retención del estado del carrito íntegramente en Web Storage del cliente (`localStorage`), validando precios contra el servicio backend sin tablas ni endpoints de carrito en servidor.
  - `AD-005:` Persistencia del catálogo en SQLite con SQLAlchemy precargada con datos semilla (`SEED-001`).
  - `AD-006:` Estrategia Fail-Fast con respuestas de error estructuradas y sanitización perimetral de transporte (justificación de diseño para la validación estricta de parámetros: cota máxima de 100 caracteres en 'q' para prevenir abusos de cómputo/memoria en SQLite y rechazo de caracteres nulos o valores de 'id < 1' bajo DTO-ERR-001).
  - `AD-007:` Nivel de seguridad mínimo: modo visitante anónimo sin sesiones ni tokens de acceso.

---

## 2. Catálogo de Endpoints de Servidor (Server Endpoints)

La API del servidor es **estrictamente de solo lectura** (únicamente métodos `GET`), exponiendo las capacidades de consulta comercial requeridas por el catálogo (`REQ-001`, `REQ-002`).

- **EP-001 [list_products]:**
  - **Propósito:** Retornar la colección de productos disponibles en el catálogo comercial, permitiendo filtrado textual por coincidencia sobre el nombre.
  - **Componente Asociado:** `COMP-001 [catalog_service]` (Servidor).
  - **Requisitos Soportados:** `REQ-001` (Visualización de Catálogo) y `REQ-002` (Búsqueda por Nombre).
  - **Criterios de Aceptación:** `AC-001`, `AC-002`, `AC-003`.
  - **Método HTTP:** `GET`
  - **Ruta Canónica:** `/api/v1/products`
  - **Parámetros de Consulta (Query Params):**
    - `q` (String, opcional): Cadena de texto para filtrado sobre el campo `name` de los productos. Insensible a mayúsculas y minúsculas (`case-insensitive`). Longitud máxima: 100 caracteres. Si se omite o es una cadena vacía, retorna todos los productos disponibles.
  - **Respuestas del Servidor:**
    - `200 OK`: Consulta exitosa. Retorna la colección en Envelope estructurado según `DTO-PROD-LIST-001`. Si no existen coincidencias para el término `q`, retorna `200 OK` con `items: []` y `total: 0` (`AC-003`).
    - `400 Bad Request`: Si el parámetro `q` excede los 100 caracteres o contiene caracteres de control no permitidos (`DTO-ERR-001` con `ERR-002`).
    - `500 Internal Server Error`: Fallo no previsto del servicio (`DTO-ERR-001` con `ERR-500`).

- **EP-002 [get_product_by_id]:**
  - **Propósito:** Retornar los datos comerciales unitarios de un producto identificado por su clave primaria, permitiendo al cliente web verificar precio e integridad al agregar o sincronizar ítems en el carrito.
  - **Componente Asociado:** `COMP-001 [catalog_service]` (Servidor).
  - **Requisitos Soportados:** `REQ-001` (Datos Básicos de Producto) y soporte de verificación para `REQ-003` (`AD-003`).
  - **Criterios de Aceptación:** `AC-001`, `AC-004`.
  - **Método HTTP:** `GET`
  - **Ruta Canónica:** `/api/v1/products/{id}`
  - **Parámetros de Ruta (Path Params):**
    - `id` (Integer, obligatorio): Identificador numérico único del producto. Restricción: entero estrictamente positivo ($id \ge 1$).
  - **Respuestas del Servidor:**
    - `200 OK`: Producto localizado exitosamente. Retorna `DTO-PROD-RES-001`.
    - `400 Bad Request`: Si el parámetro de ruta `id` no es un número entero válido o es menor a 1 (`DTO-ERR-001` con `ERR-002`).
    - `404 Not Found`: Si no existe ningún producto registrado con el identificador solicitado (`DTO-ERR-001` con `ERR-001`).
    - `500 Internal Server Error`: Fallo no previsto del servicio (`DTO-ERR-001` con `ERR-500`).

---

## 3. Esquemas de Transferencia de Datos (DTO Schemas)

Todos los intercambios de datos utilizan serialización JSON bajo codificación UTF-8.

- **DTO-PROD-RES-001 [ProductResponse]:**
  - **Propósito:** Representación comercial unitaria de un producto del catálogo (alineada biunívocamente con `ENT-001`).
  - **Estructura de Atributos:**
    - `id`: Integer, Not Null. Identificador numérico único del producto.
    - `name`: String, Not Null. Denominación comercial del producto.
    - `description`: String, Nullable. Resumen descriptivo de características.
    - `price`: Float / Numeric(10, 2), Not Null. Precio unitario en moneda base (`INV-001`).
  - **Ejemplo JSON:**
    ```json
    {
      "id": 1,
      "name": "Cuaderno Universitario",
      "description": "Cuaderno espiral de 100 hojas cuadriculadas",
      "price": 2500.00
    }
    ```

- **DTO-PROD-LIST-001 [ProductListResponse]:**
  - **Propósito:** Envelope estructurado para listados del catálogo que encapsula la colección y el cómputo total.
  - **Estructura de Atributos:**
    - `items`: Array de `DTO-PROD-RES-001`, Not Null. Lista de productos ordenados ascendentemente por `id`.
    - `total`: Integer, Not Null. Cantidad total de elementos contenidos en el listado.
  - **Ejemplo JSON:**
    ```json
    {
      "items": [
        {
          "id": 1,
          "name": "Cuaderno Universitario",
          "description": "Cuaderno espiral de 100 hojas cuadriculadas",
          "price": 2500.00
        },
        {
          "id": 2,
          "name": "Bolígrafo Tinta Negra",
          "description": "Bolígrafo retráctil con tinta gel de secado rápido",
          "price": 800.00
        }
      ],
      "total": 2
    }
    ```

- **DTO-ERR-001 [ErrorResponse]:**
  - **Propósito:** Envelope estructurado unificado para respuestas de error de la API conforme a la estrategia Fail-Fast (`AD-006`).
  - **Estructura de Atributos:**
    - `error_code`: String, Not Null. Código machine-readable del error (`ERR-xxx`).
    - `message`: String, Not Null. Explicación concisa y clara del motivo del rechazo.
    - `detail`: String, Nullable. Detalle complementario o parámetro causante de la falla.
  - **Ejemplo JSON:**
    ```json
    {
      "error_code": "ERR-001",
      "message": "Producto no encontrado",
      "detail": "No existe un producto con el identificador 99"
    }
    ```

---

## 4. Mapeo de Códigos de Estado y Manejo de Errores (Error Mapping)

El manejo de errores sigue la directiva Fail-Fast de `AD-006` con códigos de estado HTTP estándar:

| Código HTTP | Nombre Estándar | Código Negocio (`ERR-xxx`) | Condición de Disparo | Payload Retornado |
| :---: | :--- | :--- | :--- | :--- |
| **`200`** | OK | — | Operación exitosa de consulta (`EP-001`, `EP-002`). | `DTO-PROD-LIST-001` o `DTO-PROD-RES-001` |
| **`400`** | Bad Request | `ERR-002 [INVALID_PARAMETER]` | El parámetro de ruta `id` no es un entero positivo o `q` supera 100 caracteres. | `DTO-ERR-001` |
| **`404`** | Not Found | `ERR-001 [PRODUCT_NOT_FOUND]` | El producto con el `id` solicitado no existe en la base de datos (`EP-002`). | `DTO-ERR-001` |
| **`500`** | Internal Server Error | `ERR-500 [INTERNAL_SERVER_ERROR]` | Excepción no controlada o falla de conexión a la base de datos local SQLite. | `DTO-ERR-001` |

---

## 5. Gestión de Carrito en Cliente y Desacoplamiento de Servidor

Conforme a la decisión arquitectónica vinculante **AD-003** y al modelo de datos **DTO-CART-001**:

1. **Inexistencia de Endpoints Server-Side:** La API del servidor **no expone endpoints para carritos** (`/carts`, `/cart-items` o similares).
2. **Ciclo de Vida en el Navegador:** El estado del carrito reside íntegramente en Web Storage (`localStorage`) administrado en el frontend por `COMP-002 [cart_service]`.
3. **Operaciones Locales de Cliente:**
   - Adición de ítems (`REQ-003`, `AC-004`).
   - Modificación interactiva de cantidades y eliminación al fijar cantidad en cero (`REQ-004`, `AC-005`, `AC-006`).
   - Cómputo aritmético inmediato de subtotales y total general (`INV-002`, `INV-004`).
4. **Sincronización con Backend:** Si el cliente web requiere validar la vigencia del precio unitario de un producto almacenado en el carrito antes de renderizar la vista, invoca de forma desacoplada `EP-002` (`GET /api/v1/products/{id}`).

---

## 6. Seguridad de Transporte y Gobernanza

- **Nivel de Gobernanza:** `bajo` (`AD-007`). Acceso libre en modo visitante anónimo.
- **Sin Credenciales de Transporte:** Cero encabezados `Authorization: Bearer` o cookies de sesión requeridas.
- **Validación de Entradas:** Sanitización estricta de parámetros en la capa de transporte:
  - `id`: Coerción a entero positivo ($id \ge 1$).
  - `q`: Eliminación de espacios en blanco en los extremos (`strip`), verificación de longitud ($\le 100$) y rechazo de caracteres nulos.
  > [!NOTE]
  > **Nota de Linaje Técnico (AD-006 — Sanitización de Transporte):** La restricción de longitud máxima a 100 caracteres en el parámetro `q` y el rechazo de caracteres nulos derivan contractualmente de la decisión arquitectónica `AD-006` (Estrategia Fail-Fast). Estas cotas operativas protegen al motor de persistencia SQLite de sobrecargas de cómputo en búsquedas `contains` y previenen inyecciones o desbordamientos en la capa HTTP, garantizando respuestas deterministas inmediatas mediante el envelope estructurado `DTO-ERR-001` sin constituir goldplating huérfano.
- **Política de Encabezados (CORS):** La API admitirá orígenes locales controlados (`http://localhost:*`, `http://127.0.0.1:*`) para habilitar el consumo directo desde la interfaz web estática (`COMP-003`).

---

## 7. Matriz de Linaje Contractual y Trazabilidad

| Identificador Requisito (PRD) | Criterios de Aceptación | Componente Arquitectura | Entidad Datos | Endpoint Asociado | DTOs Asociados | Códigos Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-001** (Catálogo) | `AC-001` | `COMP-001`, `COMP-003` | `ENT-001` [Product] | `EP-001` (`GET /api/v1/products`), `EP-002` (`GET /api/v1/products/{id}`) | `DTO-PROD-LIST-001`, `DTO-PROD-RES-001` | `ERR-001`, `ERR-500` |
| **REQ-002** (Búsqueda) | `AC-002`, `AC-003` | `COMP-001`, `COMP-003` | `ENT-001`, `IDX-001` | `EP-001` (`GET /api/v1/products?q=`) | `DTO-PROD-LIST-001`, `DTO-ERR-001` | `ERR-002`, `ERR-500` |
| **REQ-003** (Agregar al Carrito) | `AC-004` | `COMP-002`, `COMP-003` | `DTO-CART-001` [CartItem] | *(Cliente: Web Storage / `AD-003`)* | `DTO-CART-001` | `INV-002` |
| **REQ-004** (Modificar Carrito y Totales) | `AC-005`, `AC-006` | `COMP-002`, `COMP-003` | `DTO-CART-001` [CartItem] | *(Cliente: Web Storage / `AD-003`)* | `DTO-CART-001` | `INV-002`, `INV-004` |
