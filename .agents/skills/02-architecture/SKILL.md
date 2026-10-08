---
name: architecture-design
version: 2.0.0
depends_on: [prd-generation]
stage: 2
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Diseno de arquitectura del sistema. Define patron, estructura de componentes (COMP-xxx), comunicacion y decisiones tecnicas estructurales (AD-xxx) respetando las restricciones e invariantes del PRD.
---

# Skill 02: Diseño de Arquitectura del Sistema (Architecture Design)

## 1. Overview y Propósito

Esta skill transforma los requerimientos funcionales (`REQ-xxx`), criterios de aceptación (`AC-xxx`), límites de alcance (`IN/OUT SCOPE`) y restricciones operativas (`CONST-xxx`) de un `docs/PRD.md` aprobado en una **especificación arquitectónica estructurada, modular y formalmente gobernada** en `docs/ARCHITECTURE.md`.

Su propósito fundamental es responder con rigor:
> **¿Cómo se estructuran y comunican los componentes del software para cumplir el PRD sin introducir complejidad prematura ni violar sus límites?**

La skill opera bajo dos principios de interoperabilidad del arnés:
1. **Regla de Anti-Amnesia y No Re-Interrogación:** La arquitectura no puede volver a preguntar ni proponer capacidades o tecnologías que el PRD ya sentenció como `OUT OF SCOPE`.
2. **Principio de Desacoplamiento y Progresión:** La arquitectura define componentes lógicos (`COMP-xxx`) y decisiones estructurales (`AD-xxx`), sin adelantar esquemas DDL de base de datos (delegado a `03-data-modeling`), sin fijar endpoints HTTP detallados (delegado a `04-api-design`) y sin restringir prematuramente rutas físicas de archivos (`allowed_paths`).

---

## 2. Cuándo Usar (Use When)

- Inmediatamente después de que `docs/PRD.md` haya alcanzado el estado `status: APPROVED`.
- Cuando se requiere definir o modificar la estructura de subsistemas, comunicación y stack base de una solución.
- Previo a cualquier diseño de base de datos (`03-data-modeling`), especificación de API (`04-api-design`) o implementación de código (`05-backend`).

---

## 3. Precondiciones

1. **Existencia y Aprobación del PRD:** El archivo `docs/PRD.md` DEBE existir físicamente y tener `status: APPROVED`. Queda terminantemente prohibido iniciar el diseño si el PRD se encuentra en estado `DRAFT` o ausente.
2. **Respeto a las Invariantes de Producto:** No cuestionar ni volver a deliberar el `project_type`, `governance_level` o las capacidades funcionales ya aprobadas en el PRD.
3. **Persistencia Garantizada:** El entorno debe permitir generar y versionar `docs/ARCHITECTURE.md`.

---

## 4. Entradas (Inputs) desde `docs/PRD.md`

La skill extrae deterministamente desde `docs/PRD.md`:
- **`project_id` y `project_type`:** Define el contexto y la topología macro (ej: `web_app`, `api`, `cli_tool`).
- **`governance_level`:** Condiciona el rigor de seguridad y observabilidad (bajo, medio, alto).
- **`REQ-xxx` e `IN SCOPE`:** Determina qué subsistemas y componentes de negocio deben diseñarse.
- **`OUT OF SCOPE`:** Delimita barreras duras inmutables. Lo excluido en el PRD está taxativamente prohibido en la arquitectura.
- **`CONST-xxx` y `ASSUMP-xxx`:** Restricciones duras y supuestos de escala que fundamentan el patrón técnico.
- **`OPEN-xxx`:** Puntos de incertidumbre técnica expresamente delegados desde la fase de PRD.

---

## 5. Taxonomía de Decisiones: Inherited vs. Active vs. Delegated

Para evitar el acoplamiento prematuro y la pérdida de foco de gobernanza, toda definición en esta fase se clasifica en una de tres categorías:

| Categoría | Prefijo / Estado | Definición | Ejemplo Válido en Arquitectura | Ejemplo Inválido (Antipatrón) |
| :--- | :--- | :--- | :--- | :--- |
| **Decisión Heredada (Inherited)** | *PRD Invariant* | Decisión de negocio, límite de alcance o restricción ya sellada en `docs/PRD.md`. Inmutable sin Change Request. | `Inherited: governance_level = "bajo", auth = OUT_OF_SCOPE`. | Preguntar al usuario: *"¿Quieres agregar autenticación JWT o pasarela de pago?"* |
| **Decisión Arquitectónica Activa** | `AD-xxx` | Elección estructural tomada en esta fase tras deliberación con el usuario. | `AD-001 (architecture.pattern): "monolith"`. `AD-002 (communication.style): "in_process"`. | Adoptar microservicios o colas Kafka silenciosamente sin consultar al usuario. |
| **Decisión Delegada (Downstream)** | *Delegated* | Detalle técnico que compete exclusivamente a etapas posteriores. | `Delegated: El esquema DDL de persistencia se resolverá en 03-data-modeling`. | Definir sentencias `CREATE TABLE` o endpoints `POST /api/v1/items` en el documento de arquitectura. |

---

## 6. Regla de Oro Anti-Amnesia y Bloqueo de Frontera

> 🛑 **REGLA ESTRICTA DE ANTI-AMNESIA:**  
> Si un elemento figura en `OUT OF SCOPE` en `docs/PRD.md` (ej: pasarelas de pago, autenticación de usuarios, motores de recomendación, microservicios):
> 1. El arquitecto **TIENE ESTRICTAMENTE PROHIBIDO** proponer componentes, librerías, dependencias o patrones diseñados para dicha capacidad.
> 2. El arquitecto **TIENE ESTRICTAMENTE PROHIBIDO** volver a preguntar al desarrollador si desea incorporar o reconsiderar dicha capacidad.
> 3. La reincorporación de una capacidad excluida solo es admisible si el usuario solicita un **Change Request formal**, lo que exige retroceder a `01-prd`, aprobar un `PRD v2` y reiniciar el ciclo.

---

## 7. Workflow de Elicitación Interactiva

El agente debe guiar al desarrollador a través de las siguientes etapas consultando paso a paso mediante opciones estructuradas (según [AGENTS.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/AGENTS.md)), recomendando la alternativa más simple (KISS/YAGNI) y esperando la respuesta antes de avanzar.

### Paso 1: Patrón Arquitectónico Principal (`AD-001`)
Elicitar el estilo macro del sistema según `project_type` y la escala definida en los supuestos del PRD:
- **a) Monolito simple:** Toda la lógica en un solo runtime/despliegue. [Recomendado para MVP / escala básica].
- **b) Monolito modular:** Un solo despliegue con módulos de dominio desacoplados por interfaces internas.
- **c) Microservicios / Distribuido:** Múltiples servicios comunicados por red (solo si la escala o el PRD lo exige).
- **d) Serverless / Event-driven:** Funciones bajo demanda.

### Paso 2: Descomposición de Componentes de Software (`COMP-xxx`)
Identificar los componentes necesarios para cubrir los `REQ-xxx` comprometidos en `IN SCOPE`, asignando un ID formal y responsabilidades precisas:
- Cada componente debe identificarse como `COMP-001`, `COMP-002`, etc.
- Definir responsabilidades observables y fronteras lógicas claras (ej: componente de catálogo, componente de carrito, interfaz web).
- No inventar componentes para funcionalidades fuera de alcance.

### Paso 3: Estilo de Comunicación entre Componentes (`AD-002`)
Determinar cómo interactúan los componentes definidos:
- **En proceso (In-Process Calls):** Llamadas a funciones/métodos directos entre módulos (típico de monolito).
- **HTTP REST síncrono:** Comunicación cliente-servidor tradicional desacoplada.
- **Mensajería asíncrona / Eventos:** Event bus o broker (solo si fue justificado).

### Paso 4: Layout y Organización del Código (`AD-003`)
Definir la organización lógica de directorios que adoptará el proyecto:
- **a) Por feature / dominio:** Módulos autónomos (`catalog/`, `cart/`). [Recomendado para mantenibilidad].
- **b) Por tipo técnico / capas clásicas:** `services/`, `models/`, `views/`.
- **c) Hexagonal / Clean Architecture:** Puertos y adaptadores (solo si la complejidad del dominio lo amerita).
- 🛑 **Aislamiento Físico:** Esta definición es un lineamiento estructural conceptual; **no genera ni fija `allowed_paths`** para tareas individuales de codificación.

### Paso 5: Stack Tecnológico Base (`AD-004`)
Preguntar y definir el runtime y librerías fundamentales sin goldplating:
- Backend / Runtime (ej: Python con framework ligero vs Node/TypeScript).
- Frontend / Vista (ej: Vanilla HTML/JS interactivo vs SPA ligero).
- Persistencia macro (ej: Almacenamiento local en cliente vs persistencia relacional ligera).

### Paso 6: Estrategia de Manejo de Errores y Resiliencia (`AD-005`)
- **Fail Fast:** Fallar inmediatamente con indicación clara estructurada. [Recomendado para APIs y prototipos].
- **Graceful Degradation:** Continuar con funcionalidad básica ante fallos parciales.

### Paso 7: Seguridad y Gobernanza Heredada
Verificar que las directivas de seguridad se ajusten estrictamente al `governance_level` heredado del PRD:
- `bajo`: Validación básica de entradas, sin tokens JWT innecesarios, sin auditoría compleja forzada.
- `medio`: Validación robusta, registro estructurado de eventos clave.
- `alto`: Cifrado en reposo/tránsito, RBAC estricto, auditoría forense inmutable.
- 🛑 **PROHIBIDO:** Sobredimensionar la seguridad agregando capas de autenticación si el PRD estableció `governance_level: bajo` y `OUT OF SCOPE: Autenticación`.

### Paso 8: Aprobación y Versionado Lógico
1. El agente consolida las decisiones y emite `docs/ARCHITECTURE.md` con `status: DRAFT` y `version: 1`.
2. Solicita confirmación explícita al desarrollador.
3. Tras la confirmación, se actualiza a `status: APPROVED`.

---

## 8. Ejemplos de Calidad de Componentes y Decisiones

| ID | Tipo | Formulación Incorrecta (Rechazada) | Formulación Correcta (Aceptada) |
| :--- | :--- | :--- | :--- |
| `COMP-001` | Componente | "Módulo de compras con tabla SQL `orders` y Stripe." *(Acoplado y con scope inventado)* | `COMP-001 [cart_service]`: Encapsula la gestión de ítems en el carrito, cálculo de subtotales y total general para la sesión activa del usuario. |
| `AD-001` | Decisión | "Usaremos React y Docker porque es moderno." *(Goldplating / no justificado)* | `AD-001 (architecture.pattern)`: Monolito modular simple. *Rationale:* Maximiza la simplicidad operativa para un MVP de catálogo básico sin incurrir en costos de red ni orquestación de servicios independientes. |
| `AD-002` | Decisión | "Endpoints `GET /items` y `POST /items` con FastAPI." *(Prematuro / delegado a 04)* | `AD-002 (communication.style)`: Comunicación cliente-servidor síncrona vía HTTP REST básico. Los contratos de payload y códigos de estado específicos se delegan a `04-api-design`. |

---

## 9. Señales de Alerta y Antipatrones (Red Flags)

- 🚨 **Amnesia de Scope (Reintroducción de Excluidos):** Diseñar o proponer componentes de autenticación, pagos o recomendaciones cuando el PRD los declaró `OUT OF SCOPE`.
- 🚨 **Pre-especificación de Datos (DDL Prematuro):** Escribir sentencias `CREATE TABLE`, tipos de columnas SQL o índices en el documento de arquitectura (competencia exclusiva de `03-data-modeling`).
- 🚨 **Pre-especificación de API (Rutas Prematuras):** Detallar endpoints tipo `POST /api/v1/resource` o esquemas OpenAPI en el documento de arquitectura (competencia exclusiva de `04-api-design`).
- 🚨 **Fijación Física Prematura (`allowed_paths` en Arquitectura):** Definir o emitir restricciones de archivos de codificación física en esta fase.
- 🚨 **Goldplating Arquitectónico:** Proponer microservicios, brokers de eventos (Kafka/RabbitMQ) o caché distribuida (Redis) para aplicaciones simples que no lo requieren.
- 🚨 **Inconsistencia de Seguridad:** Introducir esquemas de autenticación complejos cuando el PRD fijó `governance_level: bajo`.

---

## 10. Contrato de Salida Formal: `docs/ARCHITECTURE.md`

El artefacto producido debe residir en `docs/ARCHITECTURE.md` y cumplir estrictamente la siguiente estructura markdown con frontmatter YAML:

```markdown
---
project_id: "nombre-proyecto-slug"
project_name: "Nombre Formal del Proyecto"
version: 1
status: "DRAFT" # "DRAFT" durante deliberación, "APPROVED" tras confirmación explícita
architecture_style: "monolith" # monolith | modular_monolith | microservices | serverless
governance_level: "bajo" # Heredado estrictamente de docs/PRD.md (bajo | medio | alto)
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# Especificación de Arquitectura — [Nombre Formal del Proyecto]

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `APPROVED`)
- **Tipo de Proyecto:** [web_app | api | data_pipeline | cli_tool | mobile]
- **Nivel de Gobernanza:** [bajo | medio | alto]
- **Frontera de Alcance Heredada:**
  - `IN SCOPE:` [Capacidades funcionales confirmadas a soportar]
  - `OUT OF SCOPE (Inmutable):` [Capacidades explícitamente excluidas que la arquitectura no soporta]

## 2. Catálogo de Componentes de Software (Components)
- **COMP-001 [Nombre del Componente]:**
  - **Propósito:** [Misión del componente]
  - **Responsabilidades:** [Qué hace]
  - **Requisitos Soportados:** [Trazabilidad hacia REQ-xxx]
- **COMP-002 [Nombre del Componente]:**
  - **Propósito:** [Misión del componente]
  - **Responsabilidades:** [Qué hace]
  - **Requisitos Soportados:** [Trazabilidad hacia REQ-xxx]

## 3. Registro de Decisiones Arquitectónicas (Architectural Decisions)
- **AD-001 (architecture.pattern):**
  - **Decisión:** [Patrón seleccionado, ej: Monolito simple / Monolito modular]
  - **Justificación:** [Por qué es la solución óptima según KISS/YAGNI y la escala del PRD]
- **AD-002 (communication.style):**
  - **Decisión:** [Estilo de comunicación, ej: In-process calls / HTTP REST síncrono]
  - **Justificación:** [Fundamento técnico]
- **AD-003 (codebase.layout):**
  - **Decisión:** [Organización de código, ej: Por feature / Por capas técnicas]
  - **Justificación:** [Fundamento técnico]
- **AD-004 (tech_stack):**
  - **Decisión:** [Runtime, framework y librerías base]
  - **Justificación:** [Fundamento técnico]
- **AD-005 (error_handling.strategy):**
  - **Decisión:** [Estrategia de errores, ej: Fail Fast estructurado]
  - **Justificación:** [Fundamento técnico]

## 4. Comunicación e Interacción entre Componentes
- [Descripción de cómo interactúan COMP-xxx entre sí sin especificar rutas HTTP detalladas]

## 5. Estructura y Organización Lógica del Código
- [Diagrama de directorios o árbol conceptual de organización de módulos]

## 6. Seguridad y Cumplimiento Normativo
- [Lineamientos de seguridad estrictamente proporcionales al governance_level heredado]

## 7. Decisiones Técnicas Delegadas (Downstream Scope)
- **Delegado a `03-data-modeling`:** Modelos de persistencia detallados, esquemas de tablas, tipos de datos y estrategias de almacenamiento granular.
- **Delegado a `04-api-design`:** Especificación formal de endpoints, métodos HTTP, esquemas de request/response DTO y códigos de retorno.
- **Delegado a `05-backend` / `06-frontend`:** Implementación concreta y formulación de TaskSpecs atómicos con `allowed_paths`.
```

---

## 11. Verificación del Artefacto

### Verificación Automática (Determinista):
- [ ] El archivo existe en `docs/ARCHITECTURE.md`.
- [ ] El frontmatter YAML es válido y contiene `project_id`, `version`, `status`, `architecture_style` y `governance_level`.
- [ ] Todos los componentes siguen el patrón `COMP-\d{3}` y son únicos.
- [ ] Todas las decisiones siguen el patrón `AD-\d{3}` y son únicas.
- [ ] Existen secciones obligatorias: `Contexto e Invariantes Heredadas`, `Catálogo de Componentes`, `Registro de Decisiones Arquitectónicas`, `Decisiones Técnicas Delegadas`.
- [ ] El documento **NO CONTIENE** definiciones DDL de base de datos (`CREATE TABLE`, claves foráneas).
- [ ] El documento **NO CONTIENE** rutas de endpoints HTTP detalladas (`POST /api/`, `GET /api/`).
- [ ] El documento **NO CONTIENE** definiciones de `allowed_paths` ni `forbidden_paths`.
- [ ] El documento **NO INTRODUCE** elementos que figuren en `OUT OF SCOPE` en `docs/PRD.md`.

### Verificación Humana (Juicio de Negocio):
- [ ] El patrón arquitectónico es el más simple posible para el requerimiento (KISS / YAGNI).
- [ ] Cada decisión `AD-xxx` tiene una justificación técnica trazable a la interacción con el usuario.
- [ ] No se asumieron tecnologías ni frameworks no solicitados ni deliberados.

---

## 12. Criterio de Término y Salida (Exit Criteria)

La ejecución de la Skill 02 concluye exitosamente **únicamente cuando**:
1. `docs/ARCHITECTURE.md` ha sido generado y cumple con toda la validación sintáctica y de contrato.
2. El desarrollador humano ha confirmado explícitamente el diseño y el archivo tiene `status: APPROVED`.
3. Todos los aspectos de modelado de datos y diseño de API han quedado formalmente delegados a las etapas 03 y 04.
4. El agente **SE DETIENE** antes de iniciar `03-data-modeling`.
