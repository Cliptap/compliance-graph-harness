---
name: data-modeling
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: 2
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Diseno del modelo de datos. Define entidades (ENT-xxx), atributos, tipos, relaciones, indices (IDX-xxx), esquemas de persistencia y almacenamiento cliente (DTO-xxx), invariantes de datos (INV-xxx) y datos semilla (SEED-xxx) respetando el PRD y la Arquitectura.
---

# Skill 03: Modelado y Diseño de Datos (Data Modeling)

## 1. Overview y Propósito

Esta skill traduce los requerimientos funcionales (`REQ-xxx`) y límites de alcance de `docs/PRD.md` junto con los componentes (`COMP-xxx`) y decisiones arquitectónicas (`AD-xxx`) de `docs/ARCHITECTURE.md` en una **especificación formal, coherente y tipada del modelo de datos** en `docs/DATA_MODEL.md`.

Su propósito fundamental es responder con rigor técnico:
> **¿Cuáles son las estructuras, entidades, tipos, invariantes de negocio y esquemas de persistencia necesarios para soportar los casos de uso aprobados sin inventar modelos huérfanos ni contradecir la arquitectura?**

La skill opera bajo tres principios de interoperabilidad del arnés:
1. **Regla de Oro Anti-Amnesia:** Está estrictamente prohibido modelar entidades, tablas o esquemas para conceptos sentenciados como `OUT OF SCOPE` en el PRD (cero usuarios, cuentas, credenciales, sesiones de servidor, pagos o recomendaciones).
2. **Coherencia con Decisiones Arquitectónicas (Anti-Deriva DAG):** El motor de persistencia y base de datos no se re-delibera si ya fue sellado en `docs/ARCHITECTURE.md`. Del mismo modo, si la arquitectura estableció que determinado estado o contexto de usuario reside en el almacenamiento del cliente (`AD-xxx`), la skill **no debe crear tablas relacionales de servidor para entidades delegadas al cliente**, sino modelar formalmente la estructura de datos del cliente (Web Storage / LocalStorage) mediante DTOs formales.
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
  - `REQ-xxx` e `IN SCOPE`: Requerimientos funcionales y entidades del dominio en el contexto acotado (bounded context) aprobado.
  - `OUT OF SCOPE`: Prohibiciones explícitas de entidades o capacidades excluidas.
- **Desde `docs/ARCHITECTURE.md`:**
  - `COMP-xxx`: Componentes de software y subsistemas (servicios de dominio, persistencia, clientes de datos).
  - `AD-xxx`: Decisiones arquitectónicas vinculantes que determinan:
    * El motor y tecnología de persistencia del servidor.
    * La frontera de almacenamiento entre cliente y servidor (Web Storage / LocalStorage vs. base de datos de servidor).
    * La topología y layout de módulos.

---

## 5. Taxonomía Formal de Modelado de Datos

Toda definición técnica en esta fase debe utilizar los siguientes prefijos normativos:

| Prefijo | Tipo de Elemento | Definición | Ejemplo Válido | Antipatrón Prohibido |
| :--- | :--- | :--- | :--- | :--- |
| **`ENT-xxx`** | Entidad de Persistencia | Entidad almacenada en base de datos de servidor con tabla/colección formal. | `ENT-001 [<EntidadDominio>]: Entidad de persistencia en base de datos según la arquitectura.` | `ENT-999 [User]: Tabla de usuarios y contraseñas (OUT OF SCOPE).` |
| **`DTO-xxx` / `DTO-CLIENT-xxx`** | Esquema de Cliente | Estructura de datos almacenada en cliente (Web Storage) según frontera arquitectónica (`AD-xxx`). | `DTO-001 [<ContratoDatos>]: Estructura JSON {id, timestamp, valor}.` | Crear tabla SQL en el servidor para entidades expresamente delegadas al cliente. |
| **`IDX-xxx`** | Índice de Desempeño | Índice en campo justificado por consultas frecuentes del PRD. | `IDX-001 [idx_<entidad>_<campo>]: Índice B-tree para búsqueda o filtrado REQ-xxx.` | Crear 10 índices compuestos especulativos sin justificación en requisitos. |
| **`INV-xxx`** | Invariante de Datos | Regla dura de integridad y validación a nivel de datos. | `INV-001 [<regla_valor_positivo>]: valor >= 0.0.` | Dejar campos numéricos sin validación de cota inferior o dominio. |
| **`SEED-xxx`** | Datos Semilla | Conjunto inicial de registros requeridos para inicialización MVP o pruebas deterministas. | `SEED-001: Registros iniciales para el dataset semilla demostrativo (<DatasetSemilla>).` | Depender de inserciones manuales en producción sin semilla reproducible. |

---

## 6. Regla de Oro Anti-Amnesia y No Entidades Huérfanas

> 🛑 **REGLA ESTRICTA DE ANTI-AMNESIA:**  
> Si un concepto figura en `OUT OF SCOPE` en `docs/PRD.md` (ej: usuarios, cuentas, roles, contraseñas, pagos, tarjetas, transacciones financieras, recomendaciones):
> 1. Queda **ESTRICTAMENTE PROHIBIDO** definir entidades, tablas, columnas, esquemas DTO o invariantes asociados a dichos conceptos.
> 2. Queda **ESTRICTAMENTE PROHIBIDO** volver a consultar al desarrollador si desea agregar tablas de usuario o pago.
> 3. Toda entidad `ENT-xxx` debe tener **LINAJE CONTRACTUAL DIRECTO** trazable a un componente (`COMP-xxx`) y a un requisito (`REQ-xxx`). Las entidades huérfanas serán rechazadas por el arnés de gobernanza.

---

## 7. Workflow de Elicitación Interactiva

El agente debe guiar al desarrollador respetando las decisiones previas y formulando preguntas con opciones claras ([AGENTS.md](AGENTS.md)):

### Paso 1: Entidades de Persistencia del Servidor (`ENT-xxx`)
Identificar las entidades necesarias para soportar los requisitos funcionales del contexto acotado (bounded context) aprobado en el PRD de conformidad con el motor de persistencia sellado en `docs/ARCHITECTURE.md`:
- Definir las entidades de dominio aprobadas (ej. `ENT-001 [<EntidadDominio>]` o entidades nucleares).
- Atributos requeridos: identificador, denominación, descripción, campos de valor, disponibilidad.
- Tipos de datos conceptuales y nulabilidad (`NOT NULL` / `NULL`).

### Paso 2: Esquema de Estado en Cliente (`DTO-CLIENT-xxx` / `DTO-xxx`)
Si la arquitectura estableció retención de estado en cliente (ej. Web Storage / LocalStorage conforme a las decisiones arquitectónicas):
- Definir la estructura del ítem o entidad en cliente: identificadores, atributos volátiles, cantidades y cálculos.
- Definir la estructura global de retención en almacenamiento local: lista de ítems, totales y marca temporal.
- Dejar explícito que esta estructura reside en el cliente y no genera tablas en la base de datos de servidor.

### Paso 3: Identificadores y Claves Primarias
Consultar la estrategia de claves primarias adecuada a la escala de la persistencia:
- **a) Auto-incremental (`INTEGER PRIMARY KEY`)**: Máxima simplicidad, óptimo para SQLite y MVPs. [Recomendado].
- **b) UUID v4 / String**: Identificador universal aleatorio.

### Paso 4: Índices de Desempeño (`IDX-xxx`)
Identificar índices justificados por las consultas requeridas en el PRD:
- Índices B-Tree o normalizados sobre campos de búsqueda textual o filtrado recurrente.

### Paso 5: Invariantes y Reglas de Integridad (`INV-xxx`)
Definir invariantes matemáticas y de negocio:
- Cotas numéricas no negativas (`valor >= 0.0`).
- Cantidades enteras estrictamente positivas (`cantidad > 0`).
- Longitud acotada y cadenas no vacías.

### Paso 6: Campos de Auditoría según Gobernanza
- Para `governance_level: "bajo"`: Mantener simplicidad extrema (YAGNI). Opcionalmente `created_at` timestamp. Sin soft-delete ni campos de auditoría forense.
- Para `governance_level: "alto"`: Registrar auditoría formal si fue exigida contractualmente.

### Paso 7: Estrategia de Carga Inicial / Seed Data (`SEED-xxx`)
Definir la estructura de datos semilla para precargar el entorno de desarrollo y pruebas con registros demostrativos reproducibles.

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse:
- 🚩 **Amnesia de Scope:** Proponer tablas para `User`, `Account`, `Credential`, `Role`, `Payment`, `StripeToken` o `Recommendation`.
- 🚩 **Violación del DAG Arquitectónico:** Preguntar por motores de persistencia externos no contemplados en la arquitectura aprobada.
- 🚩 **Violación de Estado de Cliente:** Proponer crear tablas de persistencia en servidor para entidades expresamente delegadas al cliente en la arquitectura.
- 🚩 **Pre-especificación de API:** Definir métodos y rutas HTTP detalladas (delegado a `04-api-design`).
- 🚩 **Aislamiento Físico Violado:** Dictar listas de rutas físicas de código (`allowed_paths`, `forbidden_paths`) antes de los TaskSpecs atómicos.
- 🚩 **Goldplating de Gobernanza:** Introducir esquemas de auditoría forense o eventos para un proyecto de gobernanza baja.

---

## 9. Contrato de Salida Formal (`docs/DATA_MODEL.md`)

El artefacto generado DEBE ubicarse en `docs/DATA_MODEL.md` y cumplir con la siguiente estructura:

```markdown
---
project_id: "<project-id>"
project_name: "<Nombre del Proyecto>"
version: 1
status: "DRAFT"
governance_level: "bajo" | "medio" | "alto"
persistence_target: "sqlite" | "<target>"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# Especificación del Modelo de Datos — [Nombre del Proyecto]

## 1. Contexto e Invariantes Heredadas
- PRD de Referencia y Nivel de Gobernanza.
- Arquitectura de Referencia (COMP-xxx, AD-xxx).
- Restricciones duras de OUT OF SCOPE.

## 2. Entidades de Persistencia del Servidor (Server Data Model)
- **ENT-001 [<EntidadDominio>]:**
  - Componente: COMP-xxx
  - Requisitos: REQ-xxx
  - Tabla / Persistencia: <tabla> (<engine>)
  - Atributos:
    - id: Integer, Primary Key, Autoincrement
    - <campo_nombre>: String(255), Not Null
    - <campo_desc>: String(1000), Nullable
    - <campo_valor>: Numeric(10, 2), Not Null
  - Índices: IDX-001 (<campo_nombre>)

## 3. Esquema de Datos del Lado Cliente (Client Storage Model)
- **DTO-001 [<ContratoDatos>]:**
  - Componente: COMP-xxx
  - Requisitos: REQ-xxx
  - Almacenamiento: Web Storage (LocalStorage) — Conforme a decisiones arquitectónicas
  - Campos: id, timestamp, valor, detalles

## 4. Índices y Optimización de Consultas
- **IDX-001 [idx_<entidad>_<campo>]:** Justificación en REQ-xxx.

## 5. Invariantes y Reglas de Integridad
- **INV-001 (<invariante_positiva>):** valor >= 0.0
- **INV-002 (<invariante_cantidad>):** cantidad > 0

## 6. Datos Semilla e Inicialización (Seed Data)
- **SEED-001:** Registros iniciales del dataset semilla demostrativo (<DatasetSemilla>).

## 7. Matriz de Linaje y Trazabilidad
- Tabla que vincula cada REQ-xxx y COMP-xxx con su respectivo ENT-xxx o DTO-xxx.
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la especificación, verificar:
- [ ] Frontmatter YAML completo con `project_id`, `version: 1`, `status: "DRAFT"`, `governance_level`, `persistence_target`.
- [ ] Todas las entidades del servidor usan prefijo `ENT-xxx` unívoco.
- [ ] No existen entidades para conceptos en `OUT OF SCOPE` (usuarios, auth, pagos).
- [ ] El estado en cliente está formalmente modelado (`DTO-xxx`) respetando las decisiones arquitectónicas.
- [ ] Todos los atributos tienen tipos conceptuales definidos y restricciones de nulabilidad.
- [ ] Índices `IDX-xxx` e invariantes `INV-xxx` explícitamente formulados.
- [ ] No se emiten rutas físicas de código (`allowed_paths`) ni endpoints HTTP detallados.

---

## 11. Criterio de Término

El diseño de datos concluye únicamente cuando el usuario aprueba formalmente `docs/DATA_MODEL.md`, momento en el cual el frontmatter se actualiza a `status: "APPROVED"` para habilitar la transición a `04-api-design`.

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian de la siguiente forma:
- **Entidades de Servidor (`ENT-xxx`):** `ENT-001 [Product]` mapeada a la tabla relacional `products` en SQLite / SQLAlchemy conforme a `AD-005`, con atributos `id` (Integer PK), `name` (String(255) Not Null), `description` (Text Nullable) y `price` (Numeric(10,2) Not Null).
- **Esquema de Cliente (`DTO-CART-xxx`):** `DTO-CART-001 [CartItem]` almacenado en Web Storage (`localStorage`) en el cliente conforme a `AD-003`, con campos `product_id`, `name`, `unit_price`, `quantity` y `subtotal`, sin tablas relacionales en servidor.
- **Índices (`IDX-xxx`):** `IDX-001 [idx_product_name]` sobre `name` para acelerar la búsqueda textual insensible a mayúsculas comprometida en `REQ-002`.
- **Invariantes (`INV-xxx`):** `INV-001` (`price >= 0.0`), `INV-002` (`quantity >= 1`), `INV-003` (`LENGTH(TRIM(name)) > 0`), `INV-004` (subtotal = precio * cantidad).
- **Datos Semilla (`SEED-001`):** Catálogo demostrativo inicial de 5 productos de papelería y librería técnica inicializados en SQLite.
