---
name: data-modeling
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: 2
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Diseno del modelo de datos. Define entidades (ENT-xxx), atributos, tipos, relaciones, indices (IDX-xxx), esquemas de persistencia y almacenamiento cliente (DTO-CART-xxx), invariantes de datos (INV-xxx) y datos semilla (SEED-xxx) respetando el PRD y la Arquitectura.
---

# Skill 03: Modelado y Diseño de Datos (Data Modeling)

## 1. Overview y Propósito

Esta skill traduce los requerimientos funcionales (`REQ-xxx`) y límites de alcance de `docs/PRD.md` junto con los componentes (`COMP-xxx`) y decisiones arquitectónicas (`AD-xxx`) de `docs/ARCHITECTURE.md` en una **especificación formal, coherente y tipada del modelo de datos** en `docs/DATA_MODEL.md`.

Su propósito fundamental es responder con rigor técnico:
> **¿Cuáles son las estructuras, entidades, tipos, invariantes de negocio y esquemas de persistencia necesarios para soportar los casos de uso aprobados sin inventar modelos huérfanos ni contradecir la arquitectura?**

La skill opera bajo tres principios de interoperabilidad del arnés:
1. **Regla de Oro Anti-Amnesia:** Está estrictamente prohibido modelar entidades, tablas o esquemas para conceptos sentenciados como `OUT OF SCOPE` en el PRD (cero usuarios, cuentas, credenciales, sesiones de servidor, pagos o recomendaciones).
2. **Coherencia con Decisiones Arquitectónicas (Anti-Deriva DAG):** El motor de base de datos no se re-delibera si ya fue sellado en `docs/ARCHITECTURE.md` (ej: persistencia relacional SQLite/SQLAlchemy en `AD-005`). Del mismo modo, si la arquitectura estableció que el carrito reside en el almacenamiento del cliente (`AD-003`), la skill **no debe crear tablas relacionales de servidor para el carrito**, sino modelar formalmente la estructura de datos del cliente (LocalStorage).
3. **Principio de Desacoplamiento y Progresión:** La skill define entidades lógicas/físicas, tipos conceptuales, índices e invariantes, pero no adelanta contratos HTTP detallados (delegado a `04-api-design`), ni código de implementación ORM/migraciones o rutas físicas de archivos (`allowed_paths`, delegado a `05-backend`).

---

## 2. Cuándo Usar (Use When)

- Inmediatamente después de que `docs/ARCHITECTURE.md` haya alcanzado el estado `status: APPROVED`.
- Cuando se requiere definir entidades del sistema, atributos, restricciones de nulabilidad, tipos de datos, índices o invariantes de negocio.
- Previo a la especificación de contratos de endpoints HTTP en `04-api-design` y a la implementación de código en `05-backend`.

---

## 3. Precondiciones

1. **Aprobación de Artefactos Upstream:**
   - `docs/PRD.md` DEBE existir con `status: APPROVED`.
   - `docs/ARCHITECTURE.md` DEBE existir con `status: APPROVED`.
   - Queda terminantemente prohibido modelar datos si los artefactos previos están en estado `DRAFT` o ausentes.
2. **Respeto a las Invariantes de Gobernanza:**
   - Adoptar el `governance_level` fijado en el PRD. Para gobernanza `bajo`, no exigir campos de auditoría forense pesados (`created_by`, `updated_by`, `deleted_at`) ni esquemas de event sourcing.
3. **Persistencia Garantizada:** El entorno debe permitir generar y versionar `docs/DATA_MODEL.md`.

---

## 4. Entradas (Inputs) desde Upstream

La skill extrae deterministamente:
- **Desde `docs/PRD.md`:**
  - `project_id`: Identificador canónico del proyecto.
  - `governance_level`: Nivel de gobernanza del sistema (`bajo`, `medio`, `alto`).
  - `REQ-xxx` e `IN SCOPE`: Casos de uso de catálogo (`REQ-001`, `REQ-002`) y carrito (`REQ-003`, `REQ-004`).
  - `OUT OF SCOPE`: Prohibición explícita de pasarelas de pago, autenticación/cuentas y recomendaciones.
- **Desde `docs/ARCHITECTURE.md`:**
  - `COMP-001`: Componente de Catálogo (servidor).
  - `COMP-002`: Componente de Carrito (cliente interactivo).
  - `COMP-003`: Capa de Persistencia Ligera.
  - `AD-001`: Runtime y arquitectura (Monolito modular en Python 3.12+).
  - `AD-003`: **Carrito en Web Storage (LocalStorage) en el cliente** (sin tablas relacionales de servidor).
  - `AD-005`: **Persistencia de Catálogo mediante SQLite / SQLAlchemy** con seed inicial.

---

## 5. Taxonomía Formal de Modelado de Datos

Toda definición técnica en esta fase debe utilizar los siguientes prefijos normativos:

| Prefijo | Tipo de Elemento | Definición | Ejemplo Válido | Antipatrón Prohibido |
| :--- | :--- | :--- | :--- | :--- |
| **`ENT-xxx`** | Entidad de Persistencia | Entidad almacenada en base de datos de servidor con tabla/colección formal. | `ENT-001 [Product]: Entidad de catálogo en SQLite.` | `ENT-999 [User]: Tabla de usuarios y contraseñas (OUT OF SCOPE).` |
| **`DTO-CART-xxx`** | Esquema de Cliente | Estructura de datos almacenada en cliente (Web Storage) según `AD-003`. | `DTO-CART-001 [CartItem]: Estructura JSON {product_id, quantity, unit_price}.` | Crear tabla SQL `cart_sessions` en el servidor contradiciendo `AD-003`. |
| **`IDX-xxx`** | Índice de Desempeño | Índice en campo justificado por consultas frecuentes del PRD. | `IDX-001 [idx_product_name]: Índice B-tree para búsqueda textual REQ-002.` | Crear 10 índices compuestos especulativos sin justificación en requisitos. |
| **`INV-xxx`** | Invariante de Datos | Regla dura de integridad y validación a nivel de datos. | `INV-001 [price_non_negative]: price >= 0.0.` | Dejar campos monetarios como Float impreciso sin validación de cota inferior. |
| **`SEED-xxx`** | Datos Semilla | Conjunto inicial de registros requeridos para el catálogo MVP. | `SEED-001: 5 a 10 productos de catálogo inicial.` | Depender de inserciones manuales en producción sin semilla reproducible. |

---

## 6. Regla de Oro Anti-Amnesia y No Entidades Huérfanas

> 🛑 **REGLA ESTRICTA DE ANTI-AMNESIA:**  
> Si un concepto figura en `OUT OF SCOPE` en `docs/PRD.md` (ej: usuarios, cuentas, roles, contraseñas, pagos, tarjetas, transacciones financieras, recomendaciones):
> 1. Queda **ESTRICTAMENTE PROHIBIDO** definir entidades, tablas, columnas, esquemas DTO o invariantes asociados a dichos conceptos.
> 2. Queda **ESTRICTAMENTE PROHIBIDO** volver a consultar al desarrollador si desea agregar tablas de usuario o pago.
> 3. Toda entidad `ENT-xxx` debe tener **LINAJE CONTRACTUAL DIRECTO** trazable a un componente (`COMP-xxx`) y a un requisito (`REQ-xxx`). Las entidades huérfanas serán rechazadas por el arnés de gobernanza.

---

## 7. Workflow de Elicitación Interactiva

El agente debe guiar al desarrollador respetando las decisiones previas y formulando preguntas con opciones claras ([AGENTS.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/AGENTS.md)):

### Paso 1: Entidades de Persistencia del Servidor (`ENT-xxx`)
Identificar las entidades necesarias para el catálogo (`COMP-001`) soportado por SQLite (`AD-005`):
- Definir `ENT-001 [Product]` (o `CatalogItem`).
- Atributos requeridos: identificador, nombre, descripción, precio unitario, stock/disponibilidad.
- Tipos de datos conceptuales y nulabilidad (`NOT NULL` / `NULL`).

### Paso 2: Esquema de Estado del Carrito en Cliente (`DTO-CART-xxx`)
Conforme a `AD-003` (almacenamiento en cliente Web Storage):
- Definir la estructura del ítem de carrito: `product_id`, `name`, `unit_price`, `quantity`, `subtotal`.
- Definir la estructura global del carrito en `localStorage`: lista de ítems, `total_amount`, `updated_at`.
- Dejar explícito que esta estructura no genera tablas en la base de datos de servidor.

### Paso 3: Identificadores y Claves Primarias
Consultar la estrategia de claves primarias adecuada a la escala de catálogo simple:
- **a) Auto-incremental (`INTEGER PRIMARY KEY`)**: Máxima simplicidad, óptimo para SQLite y catálogo MVP. [Recomendado].
- **b) UUID v4 / String**: Identificador universal aleatorio.

### Paso 4: Índices de Desempeño (`IDX-xxx`)
Identificar índices justificados por las consultas requeridas en el PRD:
- Búsqueda textual por nombre (`REQ-002`): Índice B-Tree o normalizado sobre `name`.

### Paso 5: Invariantes y Reglas de Integridad (`INV-xxx`)
Definir invariantes matemáticas y de negocio:
- Precios no negativos (`price >= 0.0`).
- Cantidades enteras estrictamente positivas (`quantity > 0`).
- Nombre de producto no vacío y de longitud acotada.

### Paso 6: Campos de Auditoría según Gobernanza
- Para `governance_level: "bajo"`: Mantener simplicidad extrema (YAGNI). Opcionalmente `created_at` timestamp. Sin soft-delete ni campos de auditoría forense.

### Paso 7: Estrategia de Carga Inicial / Seed Data (`SEED-xxx`)
Definir la estructura de datos semilla para precargar el catálogo con productos demostrativos.

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse:
- 🚩 **Amnesia de Scope:** Proponer tablas para `User`, `Account`, `Credential`, `Role`, `Payment`, `StripeToken` o `Recommendation`.
- 🚩 **Violación del DAG Arquitectónico:** Preguntar si usar Postgres o MongoDB cuando `AD-005` ya selló SQLite/SQLAlchemy.
- 🚩 **Violación de Estado de Cliente:** Proponer crear una tabla de base de datos relacional para el carrito en servidor cuando `AD-003` selló almacenamiento en cliente.
- 🚩 **Pre-especificación de API:** Definir métodos y rutas HTTP tipo `GET /api/v1/products` (delegado a `04-api-design`).
- 🚩 **Aislamiento Físico Violado:** Dictar listas de rutas físicas de código (`allowed_paths`, `forbidden_paths`) antes de los TaskSpecs atómicos.
- 🚩 **Goldplating de Gobernanza:** Introducir esquemas de auditoría forense o eventos para un proyecto de gobernanza baja.

---

## 9. Contrato de Salida Formal (`docs/DATA_MODEL.md`)

El artefacto generado DEBE ubicarse en `docs/DATA_MODEL.md` y cumplir con la siguiente estructura:

```markdown
---
project_id: "catalogo-carrito-web"
project_name: "Sistema Web Básico de Catálogo y Carrito de Compras"
version: 1
status: "DRAFT"
governance_level: "bajo"
persistence_target: "sqlite"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# Especificación del Modelo de Datos — [Nombre del Proyecto]

## 1. Contexto e Invariantes Heredadas
- PRD de Referencia y Nivel de Gobernanza.
- Arquitectura de Referencia (COMP-001, COMP-002, AD-003, AD-005).
- Restricciones duras de OUT OF SCOPE (cero usuarios, cero pagos).

## 2. Entidades de Persistencia del Servidor (Server Data Model)
- **ENT-001 [Product]:**
  - Componente: COMP-001 / COMP-003
  - Requisitos: REQ-001, REQ-002
  - Tabla / Persistencia: products (SQLite)
  - Atributos:
    - id: Integer, Primary Key, Autoincrement
    - name: String(255), Not Null
    - description: String(1000), Nullable
    - price: Numeric(10, 2), Not Null
  - Índices: IDX-001 (name)

## 3. Esquema de Datos del Lado Cliente (Client Storage Model)
- **DTO-CART-001 [CartItem]:**
  - Componente: COMP-002
  - Requisitos: REQ-003, REQ-004
  - Almacenamiento: Web Storage (LocalStorage) — Conforme a AD-003
  - Campos: product_id, name, unit_price, quantity, subtotal

## 4. Índices y Optimización de Consultas
- **IDX-001 [idx_product_name]:** Justificación en REQ-002.

## 5. Invariantes y Reglas de Integridad
- **INV-001 (price_positive):** price >= 0.0
- **INV-002 (quantity_positive):** quantity > 0

## 6. Datos Semilla e Inicialización (Seed Data)
- **SEED-001:** Catálogo inicial de productos demostrativos.

## 7. Matriz de Linaje y Trazabilidad
- Tabla que vincula cada REQ-xxx y COMP-xxx con su respectivo ENT-xxx o DTO-xxx.
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la especificación, verificar:
- [ ] Frontmatter YAML completo con `project_id`, `version: 1`, `status: "DRAFT"`, `governance_level`, `persistence_target`.
- [ ] Todas las entidades del servidor usan prefijo `ENT-xxx` unívoco.
- [ ] No existen entidades para conceptos en `OUT OF SCOPE` (usuarios, auth, pagos).
- [ ] El carrito está modelado en cliente (`DTO-CART-xxx`) respetando `AD-003`.
- [ ] Todos los atributos tienen tipos conceptuales definidos y restricciones de nulabilidad.
- [ ] Índices `IDX-xxx` e invariantes `INV-xxx` explícitamente formulados.
- [ ] No se emiten rutas físicas de código (`allowed_paths`) ni endpoints HTTP detallados.

---

## 11. Criterio de Término

El diseño de datos concluye únicamente cuando el usuario aprueba formalmente `docs/DATA_MODEL.md`, momento en el cual el frontmatter se actualiza a `status: "APPROVED"` para habilitar la transición a `04-api-design`.
