---
name: prd-generation
version: 2.0.0
depends_on: []
stage: 1
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Workflow de especificacion de requisitos con contrato de salida formal (docs/PRD.md). Define identidad, problema, objetivos, requisitos (REQ-xxx), limites de alcance (IN/OUT SCOPE), criterios de aceptacion (AC-xxx), restricciones (CONST-xxx), supuestos (ASSUMP-xxx) y preguntas abiertas sin adelantar decisiones tecnicas prematuras ni emitir rutas fisicas.
---

# Skill 01: Especificación de Requisitos de Producto (PRD)

## 1. Overview y Propósito

Esta skill transforma la intención de negocio y la interacción inicial con el desarrollador en una **especificación de requisitos estructurada con un contrato de salida definido y versionado** en `docs/PRD.md`.

No es un cuestionario conversacional aislado ni un generador de suposiciones técnicas. Su propósito es responder con precisión:
> **¿Qué debe lograr el sistema y cuáles son sus límites explícitos?**

La skill opera bajo una regla de oro de interoperabilidad:
> **`02-architecture` y las etapas posteriores deben poder obtener de `docs/PRD.md` toda la información funcional, restricciones y criterios que necesitan sin volver a interrogar al desarrollador sobre decisiones ya resueltas.**

---

## 2. Cuándo Usar (Use When)

- Al iniciar un proyecto o repositorio desde cero.
- Al definir una nueva capacidad o producto mayor en un repositorio existente.
- Cuando no existe un `docs/PRD.md` con estado `APPROVED`.
- Cuando se requiere redefinir el alcance del producto antes de tomar decisiones de arquitectura o diseño de datos.

---

## 3. Precondiciones

1. Disponer de comunicación interactiva con el desarrollador para resolver requerimientos de negocio.
2. No asumir ninguna tecnología, patrón de arquitectura, ORM, base de datos ni endpoint que el desarrollador no haya estipulado explícitamente como restricción fija.
3. El directorio del proyecto debe permitir la persistencia del artefacto en `docs/PRD.md`.

---

## 4. Entradas (Inputs)

- **Intención inicial / Problema de negocio:** Descripción general del problema que se busca resolver.
- **Restricciones del desarrollador (si existen):** Requisitos técnicos no negociables dados de antemano (ej: "debe ejecutarse en Python 3.13", "sin dependencias de red externa").
- **Tipo de proyecto y nivel de gobernanza inicial.**

---

## 5. Distinción Fundamental: Requisito vs. Restricción vs. Decisión Técnica

Para evitar el acoplamiento prematuro y el scope creep, la skill debe clasificar con rigor cada información:

| Concepto | Prefijo | Definición | Ejemplo Válido en PRD | Ejemplo Inválido en PRD (Antipatrón) |
| :--- | :--- | :--- | :--- | :--- |
| **Requisito Funcional** | `REQ-xxx` | Capacidad observable que el sistema debe brindar al usuario. | `REQ-001: El sistema debe permitir consultar productos por categoría.` | `REQ-001: El sistema debe tener un endpoint GET /api/v1/products con FastAPI y SQLAlchemy.` |
| **Restricción** | `CONST-xxx` | Límite operativo, regulatorio o de entorno impuesto desde el exterior. | `CONST-001: El MVP no utilizará servicios externos de búsqueda ni APIs de pago de terceros.` | `CONST-001: Usaremos PostgreSQL con índices B-Tree.` *(Decisión técnica prematura)* |
| **Decisión Técnica** | *(Diferida)* | Elección de patrones, frameworks, esquemas y componentes (`AD-xxx`). | *No se toma en 01-prd ni se especulan alternativas técnicas en OPEN-*. Se indica únicamente una delegación genérica a `02-architecture` / `03-data-modeling` sin preseleccionar opciones.* | Elegir React, Docker, Postgres o Redis en esta fase, o formular preguntas como "SPA vs SSR" o "SQL vs NoSQL" en el PRD. |

---

## 6. Delimitación de Alcance: PRD Scope ≠ TaskSpec Scope

La skill debe establecer con nitidez qué entra y qué queda fuera del producto:
- **`IN SCOPE`:** Capacidades funcionales comprometidas para el MVP.
- **`OUT OF SCOPE`:** Funcionalidades, integraciones o extensiones expresamente excluidas para proteger el MVP.

### Regla Crítica de Aislamiento Físico:
> **El PRD define fronteras funcionales, NUNCA rutas físicas de archivos.**
> 
> `PRD Scope` $\to$ **NO produce** `allowed_paths`.
> 
> La derivación correcta a lo largo del arnés es:
> ```text
> PRD Scope (Funcional)
>      ↓
> Architecture (02)
>      ↓
> Technical Components (03, 04, 05)
>      ↓
> TaskSpec (Atómico) ──► allowed_paths (Físico)
> ```

---

## 7. Workflow de Elicitación Interactiva

El agente debe guiar al desarrollador a través de las siguientes etapas sin saltarse pasos y sin rellenar vacíos con suposiciones.

### Paso 0: Identidad, Tipo de Proyecto y Nivel de Gobernanza
1. Solicitar el nombre del proyecto y generar un `project_id` normalizado (slug).
2. Preguntar el tipo de proyecto:
   - `web_app`: Aplicación con interfaz gráfica web y servicios backend.
   - `api`: Servicio de backend puro sin frontend (REST, GraphQL, gRPC).
   - `data_pipeline`: Flujo de procesamiento de datos, ETL o análisis por lotes.
   - `cli_tool`: Herramienta interactiva o utilitaria de línea de comandos.
   - `mobile`: Aplicación para plataformas móviles.
3. **Preguntar obligatoriamente el nivel de gobernanza:**
   - `bajo`: Prototipo rápido, validaciones mínimas, sin auditoría obligatoria.
   - `medio`: Aplicación estándar con validaciones de datos y registro de eventos clave.
   - `alto`: Entorno regulado o crítico; trazabilidad estricta, RBAC y auditoría exhaustiva.
   - 🛑 **COMPUERTA DE BLOQUEO (Sin Asunciones Silenciosas):** Si el desarrollador no especificó el nivel de gobernanza en su solicitud inicial, el agente **DEBE PREGUNTARLO EXPLÍCITAMENTE** antes de emitir el frontmatter del PRD. Está **ESTRICTAMENTE PROHIBIDO asumir o rellenar un valor por defecto (como `medio`) sin respuesta o confirmación del usuario**.

### Paso 1: Problema, Contexto y Actores
1. **Problema:** ¿Qué dolor, ineficiencia o necesidad concreta resuelve este sistema?
2. **Contexto:** ¿Dónde y bajo qué condiciones operará?
3. **Actores / Roles:** ¿Quiénes interactúan con el sistema? (ej: Usuario Final, Administrador, Sistema Externo).

### Paso 2: Requisitos Funcionales (`REQ-xxx`)
1. Elicitar las capacidades que cada actor necesita realizar.
2. Asignar identificadores estables y secuenciales: `REQ-001`, `REQ-002`, ...
3. Redactar cada requisito de forma concreta y verificable, centrada en el comportamiento y no en la implementación.

### Paso 3: Frontera de Alcance (`IN SCOPE` vs. `OUT OF SCOPE`)
1. Listar los requisitos funcionales aprobados bajo `IN SCOPE`.
2. **Regla Estricta de OUT OF SCOPE (Frontera sin Invenciones):**
   - Registrar en `OUT OF SCOPE` **ÚNICA Y EXCLUSIVAMENTE** aquellas capacidades o requerimientos que hayan sido explícitamente mencionados y descartados o postergados durante la elicitación con el usuario.
   - 🛑 **PROHIBIDO inventar scope negativo:** No agregues capacidades no solicitadas ni mencionadas "por si acaso" o "por iniciativa propia" (ej: inventar exclusión de multi-almacén, blockchain o notificaciones push si el usuario nunca habló de ellas). Agregar elementos no discutidos a `OUT OF SCOPE` activa erróneamente la barrera de Change Request y distorsiona el ciclo de vida del producto.
3. **Regla de No Re-Interrogación y Gobierno de Frontera:** Si un elemento fue clasificado como `OUT OF SCOPE`, las skills posteriores NO deben volver a consultar al usuario si desea incluirlo por iniciativa propia. No constituye un muro físico inmutable: si durante etapas posteriores surge una necesidad legítima de incorporar un elemento excluido, el agente NO puede modificarlo silenciosamente; debe emitir un **Change Request formal** para que el desarrollador humano decida, generando un `PRD v2` (`APPROVED`) antes de autorizar el cambio en arquitectura o código.

### Paso 4: Criterios de Aceptación (`AC-xxx`)
1. Para cada `REQ-xxx`, formular al menos un criterio de aceptación medible.
2. Asignar identificador estable: `AC-001`, `AC-002`, ...
3. Cada criterio debe responder:
   > **¿Qué comportamiento observable o resultado verificable determina que el requisito se considera satisfecho?**
4. Vincular explícitamente: `AC-xxx` $\leftrightarrow$ `REQ-xxx`.
5. Los criterios deben ser aptos para que posteriormente `08-testing` los mapee a pruebas con evidencia (`T-xxx`).

### Paso 5: Restricciones, Supuestos y Preguntas Abiertas
1. **Restricciones (`CONST-xxx`):** Factores externos inmutables (legales, plazos, licencias, plataformas obligatorias). Si no hay, dejar vacío o indicar "Ninguna restricción externa declarada".
2. **Supuestos (`ASSUMP-xxx`):** Hipótesis de trabajo explícitas de carácter cualitativo (ej: "Se asume conectividad IP estándar", "Se asume codificación UTF-8", "Se asume moneda base local única para el MVP"). Evitan que las suposiciones se conviertan silenciosamente en "hechos".
   - 🛑 **PROHIBIDO introducir números mágicos o umbrales cuantitativos inventados:** Queda terminantemente prohibido introducir cotas numéricas no fundamentadas (ej: `< 200 productos`, `< 10 usuarios concurrentes`, `latencia < 100ms`) a menos que hayan sido provistas textualmente por el desarrollador o fijadas en una restricción regulatoria externa. Si la volumetría es incierta, debe preguntarse al usuario o expresarse de forma cualitativa ("volumen reducido para prototipo MVP").
3. **Preguntas Abiertas (`OPEN-xxx`):** Puntos de decisión **ESTRICTAMENTE FUNCIONALES, DE NEGOCIO O DE COMPORTAMIENTO OBSERVABLE** pendientes de clarificación con el usuario (ej: comportamiento ante expiración de sesión, reglas de validación de negocio).
   - 🛑 **PROHIBIDO redactar dilemas o disyuntivas arquitectónicas concretas:** No formules preguntas técnicas prematuras como "SPA vs SSR", "localStorage vs backend session", "PostgreSQL vs MongoDB".
   - **Tratamiento de Incertidumbres Técnicas:** Si existe una necesidad técnica que debe resolverse en etapas posteriores, se registra como una **referencia de delegación genérica** (ej: `OPEN-xxx: Delegación técnica: La selección de patrones arquitectónicos, estrategia de persistencia y contratos de API se resolverá formalmente en 02-architecture, 03-data-modeling y 04-api-design`), sin preseleccionar ni deliberar sobre alternativas técnicas específicas dentro del PRD.

### Paso 6: Aprobación y Versionado Lógico
1. El agente presenta el borrador completo en `docs/PRD.md` con `status: DRAFT` y `version: 1`.
2. Solicita confirmación explícita:
   ```text
   He redactado el PRD formal en docs/PRD.md con versión 1 (DRAFT).
   ¿Confirmas que el alcance, requisitos y criterios son correctos para proceder a la fase de Arquitectura?
   ⏳ Esperando tu confirmación.
   ```
3. Una vez confirmado por el desarrollador, se actualiza el estado a `status: APPROVED`.

---

## 8. Criterios de Aceptación: Ejemplos de Calidad

| ID | Requisito Asociado | Formulación Incorrecta (Rechazada) | Formulación Correcta (Aceptada) |
| :--- | :--- | :--- | :--- |
| `AC-001` | `REQ-001` | "El carrito debe funcionar bien y rápido." *(Vago, no testeable)* | "Al invocar la acción de agregar producto disponible con cantidad $N$, el ítem figura en el carrito con cantidad $N$ y el subtotal refleja el precio unitario multiplicado por $N$." |
| `AC-002` | `REQ-002` | "Seguridad adecuada para datos de pacientes." *(Subjetivo)* | "Ninguna respuesta o log del sistema expone el identificador nacional (RUT) en texto plano sin máscara cuando se consulta la ficha clínica." |
| `AC-003` | `REQ-003` | "Manejar errores con FastAPI HTTPExceptions." *(Prematuro / implementativo)* | "Si se solicita un recurso inexistente por su identificador, el sistema responde con una indicación estructurada de no encontrado (404) y mensaje de error descriptivo." |

---

## 9. Señales de Alerta y Antipatrones (Red Flags)

- 🚨 **Decisión de Stack Prematura:** Elegir bases de datos, ORMs, librerías o frameworks en el PRD cuando el desarrollador no los impuso como restricción.
- 🚨 **Scope a Rutas Físicas (`allowed_paths` en PRD):** Mencionar archivos, carpetas o extensiones dentro del PRD.
- 🚨 **Gobernanza Asumida en Silencio:** Fijar `governance_level` sin consulta explícita ni confirmación del desarrollador.
- 🚨 **Scope Negativo Alucinado:** Agregar en `OUT OF SCOPE` funcionalidades, módulos o tecnologías que el usuario jamás mencionó ni formaron parte de la negociación de alcance.
- 🚨 **Números Mágicos en Supuestos:** Inventar cotas, umbrales o métricas numéricas arbitrarias en `ASSUMP-xxx` sin respaldo documental o confirmación del usuario.
- 🚨 **Preselección Técnica en OPEN-*:** Plantear disyuntivas de patrones, frameworks, esquemas o librerías en las preguntas abiertas del PRD en vez de registrar dudas de negocio o una delegación genérica a `02-architecture`.
- 🚨 **Re-interrogar lo Excluido:** Preguntar en etapas posteriores si se desea agregar algo que el PRD marcó en `OUT OF SCOPE`.
- 🚨 **Preguntas Abiertas Resueltas en Silencio:** Transformar una duda técnica en un requisito sin intervención del desarrollador.
- 🚨 **Requisitos sin Criterios de Aceptación:** Dejar un `REQ-xxx` sin al menos un `AC-xxx` que permita verificar su cumplimiento.
- 🚨 **IDs Duplicados o Inestables:** Cambiar la numeración de los requisitos entre versiones del PRD.

---

## 10. Contrato de Salida Formal: `docs/PRD.md`

El artefacto producido debe residir en `docs/PRD.md` y cumplir estrictamente la siguiente estructura markdown con frontmatter YAML:

```markdown
---
project_id: "nombre-proyecto-slug"
project_name: "Nombre Formal del Proyecto"
version: 1
status: "DRAFT" # "DRAFT" durante formulación, "APPROVED" tras confirmación explícita
project_type: "web_app" # web_app | api | data_pipeline | cli_tool | mobile
governance_level: "medio" # bajo | medio | alto (Elicitado obligatoriamente, nunca asumido)
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# PRD — [Nombre Formal del Proyecto]

## 1. Identidad y Contexto
- **Project ID:** [slug]
- **Tipo de Proyecto:** [web_app | api | data_pipeline | cli_tool | mobile]
- **Nivel de Gobernanza:** [bajo | medio | alto]
- **Problema a Resolver:** [Descripción precisa del problema de negocio]
- **Contexto Operativo:** [Entorno o condiciones de uso]

## 2. Objetivos del Sistema
- **Objetivo Principal:** [Una frase clara del propósito central]
- **Objetivos Secundarios:**
  - OBJ-1: [Objetivo concreto 1]
  - OBJ-2: [Objetivo concreto 2]

## 3. Actores y Usuarios
- **ACT-01 [Rol]:** [Descripción de responsabilidades y permisos]
- **ACT-02 [Rol]:** [Descripción de responsabilidades y permisos]

## 4. Requisitos Funcionales
- **REQ-001:** [Descripción del requisito observable 1]
- **REQ-002:** [Descripción del requisito observable 2]
- **REQ-003:** [Descripción del requisito observable 3]

## 5. Delimitación de Alcance (Scope Boundary)

### IN SCOPE (Comprometido para MVP)
- [Capacidad funcional 1 respaldada por REQ-xxx]
- [Capacidad funcional 2 respaldada por REQ-xxx]

### OUT OF SCOPE (Explícitamente Excluido)
- [Capacidad mencionada y descartada 1 - Prohibida su reintroducción sin Change Request]
- [Capacidad mencionada y descartada 2 - Prohibida su reintroducción sin Change Request]

## 6. Criterios de Aceptación (Acceptance Criteria)
- **AC-001** (Vinculado a `REQ-001`): [Comportamiento observable verificable]
- **AC-002** (Vinculado a `REQ-002`): [Comportamiento observable verificable]
- **AC-003** (Vinculado a `REQ-003`): [Comportamiento observable verificable]

## 7. Restricciones del Sistema (Constraints)
- **CONST-001:** [Restricción legal, temporal o de entorno no negociable]
- **CONST-002:** [Restricción técnica externa obligatoria, si existe]

## 8. Supuestos de Trabajo (Assumptions)
- **ASSUMP-001:** [Hipótesis cualitativa explícita 1 — Sin números mágicos ni umbrales inventados]
- **ASSUMP-002:** [Hipótesis cualitativa explícita 2]

## 9. Preguntas Abiertas y Decisiones Pendientes (Open Questions)
- **OPEN-001:** [Duda funcional o de comportamiento de negocio pendiente de aclaración con el usuario]
- **OPEN-002:** Delegación técnica: La selección de patrones y arquitectura se resolverá formalmente en `02-architecture`
```

---

## 11. Verificación del Artefacto

### Verificación Automática (Determinista):
- [ ] El archivo existe en `docs/PRD.md`.
- [ ] El frontmatter YAML es válido y contiene `project_id`, `version`, `status` y `governance_level`.
- [ ] El estado es `APPROVED` (para dar paso a arquitectura).
- [ ] Existen secciones obligatorias: `Requisitos Funcionales`, `Delimitación de Alcance`, `Criterios de Aceptación`.
- [ ] Todos los requisitos siguen el patrón `REQ-\d{3}` y son únicos.
- [ ] Todos los criterios de aceptación siguen el patrón `AC-\d{3}` y son únicos.
- [ ] Cada `REQ-xxx` cuenta con al menos un `AC-xxx` asociado.
- [ ] Existen tanto la subsección `IN SCOPE` como `OUT OF SCOPE`.
- [ ] El documento **NO CONTIENE** definiciones de rutas de archivos (`allowed_paths` o patrones tipo `src/**`).
- [ ] No existen números mágicos ni cotas cuantitativas arbitrarias inventadas en `ASSUMP-xxx`.
- [ ] `OPEN-xxx` no preselecciona dilemas de implementación técnica concreta (solo dudas funcionales o delegación técnica genérica).

### Verificación Humana (Juicio de Negocio):
- [ ] Los requisitos representan fielmente la necesidad del usuario.
- [ ] El alcance `IN SCOPE` es realista para un MVP sin goldplating.
- [ ] `OUT OF SCOPE` contiene únicamente elementos mencionados y descartados o restricciones acordadas, sin scope negativo inventado.
- [ ] Los criterios `AC-xxx` describen comportamientos suficientes para aceptar el producto.
- [ ] Las restricciones `CONST-xxx` reflejan límites reales y no suposiciones inventadas.
- [ ] El `governance_level` fue confirmado explícitamente por el desarrollador.

---

## 12. Criterio de Término y Salida (Exit Criteria)

La ejecución de la Skill 01 concluye exitosamente **únicamente cuando**:
1. `docs/PRD.md` ha sido generado y cuenta con validación sintáctica completa.
2. El desarrollador humano ha confirmado explícitamente el contenido y el archivo tiene `status: APPROVED`.
3. Todos los puntos de decisión técnica no resueltos han quedado clasificados como `OPEN-xxx` o delegados a `02-architecture`.
4. El agente **SE DETIENE** y presenta el resumen al usuario antes de invocar cualquier skill posterior.
