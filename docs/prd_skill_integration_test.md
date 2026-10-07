# Prueba de Integración Conceptual: Handoff de `01-prd` hacia `02-architecture`

> **Fecha:** 30 de septiembre de 2026  
> **Artefacto Evaluado:** `.agents/skills/01-prd/SKILL.md` (versión 2.0.0)  
> **Contrato de Referencia:** `docs/SKILL_INTEROPERABILITY_CONTRACT.md` v2.0  
> **Estado:** CONCEPTUAL / ESPECIFICACIÓN DE INTERFAZ

---

## 1. Objetivo de la Prueba

Demostrar conceptualmente cómo la siguiente fase del workflow (`02-architecture`) debe consumir el artefacto generado por la Skill 01 (`docs/PRD.md`) **sin sufrir de amnesia conversacional ni re-interrogar al desarrollador sobre decisiones ya zanjadas**.

---

## 2. Artefacto de Entrada Simulado: `docs/PRD.md` (Aprobado)

A continuación se presenta un `docs/PRD.md` canónico resultante de la ejecución de `01-prd`:

```markdown
---
project_id: "demo-retail-core"
project_name: "Demo Retail Core MVP"
version: 1
status: "APPROVED"
project_type: "web_app"
governance_level: "medio"
created_at: "2026-09-30"
updated_at: "2026-09-30"
---

# PRD — Demo Retail Core MVP

## 1. Identidad y Contexto
- **Project ID:** demo-retail-core
- **Tipo de Proyecto:** web_app
- **Nivel de Gobernanza:** medio
- **Problema a Resolver:** Los clientes necesitan consultar productos disponibles y armar un pedido de compra sin fricción.
- **Contexto Operativo:** Entorno web interno de demostración con baja concurrencia inicial.

## 2. Objetivos del Sistema
- **Objetivo Principal:** Permitir a usuarios explorar un catálogo de ítems y gestionar un carrito de compras local.
- **Objetivos Secundarios:**
  - OBJ-1: Búsqueda y filtrado básico de catálogo en memoria o almacenamiento simple.
  - OBJ-2: Persistencia del estado del carrito durante la sesión del usuario.

## 3. Actores y Usuarios
- **ACT-01 [Cliente]:** Consulta catálogo y administra los ítems de su carrito de compras.
- **ACT-02 [Operador]:** Consulta el listado de carritos confirmados.

## 4. Requisitos Funcionales
- **REQ-001:** El sistema debe permitir consultar productos disponibles con su precio unitario y stock.
- **REQ-002:** El sistema debe permitir agregar productos disponibles al carrito de compras, actualizando la cantidad y el subtotal.
- **REQ-003:** El sistema debe permitir eliminar o modificar la cantidad de un ítem ya presente en el carrito.

## 5. Delimitación de Alcance (Scope Boundary)

### IN SCOPE (Comprometido para MVP)
- Consulta de catálogo de productos.
- Gestión interactiva de carrito de compras (agregar, actualizar cantidad, remover).
- Cálculo en tiempo real de subtotales y total del carrito.

### OUT OF SCOPE (Explícitamente Excluido)
- Autenticación OAuth / SSO federado (se usará sesión básica o usuario anónimo).
- Pasarela de pago externa (Stripe, Transbank, PayPal, etc.).
- Motor externo de búsqueda (Elasticsearch, Algolia).
- Arquitectura de microservicios o colas distribuidas asíncronas (Kafka, RabbitMQ).

## 6. Criterios de Aceptación (Acceptance Criteria)
- **AC-001** (Vinculado a `REQ-001`): Cuando un cliente solicita el catálogo, el sistema retorna únicamente los ítems marcados como disponibles con ID, nombre, precio unitario y stock > 0.
- **AC-002** (Vinculado a `REQ-002`): Cuando un cliente agrega $N$ unidades de un producto disponible, el carrito contiene dicho ítem con cantidad $N$ y el subtotal refleja $N \times \text{precio unitario}$.
- **AC-003** (Vinculado a `REQ-003`): Cuando un cliente remueve un producto del carrito, el total se recalcula inmediatamente excluyendo dicho producto.

## 7. Restricciones del Sistema (Constraints)
- **CONST-001:** El MVP debe implementarse en Python 3.13 con ejecución local autocontenida (sin servicios cloud obligatorios).
- **CONST-002:** No se permiten llamadas salientes a internet durante la ejecución normal del carrito.

## 8. Supuestos de Trabajo (Assumptions)
- **ASSUMP-001:** El catálogo inicial cabe holgadamente en memoria o en un archivo local (< 1.000 productos).
- **ASSUMP-002:** La concurrencia inicial no excederá 10 usuarios simultáneos.

## 9. Preguntas Abiertas y Decisiones Pendientes (Open Questions)
- **OPEN-001:** ¿Qué patrón de arquitectura conviene para el backend (modular monolith vs script único estructurado)? (Delegado a `02-architecture`).
- **OPEN-002:** ¿Qué mecanismo de almacenamiento local se utilizará (SQLite vs JSON en disco)? (Delegado a `03-data-modeling`).
```

---

## 3. Prueba Conceptual 1: No Re-Interrogación de Decisiones Excluidas (Anti-Amnesia)

> [!NOTE]
> **Nota Metodológica:** Esta es una **prueba conceptual de Anti-Amnesia**. Demuestra que el artefacto contiene formalmente toda la información requerida para que `02-architecture` no re-pregunte. La **validación experimental permanece pendiente mediante la ejecución real del workflow con un coding agent** en una sesión en vivo. (La aprobación de los tests unitarios automatizados comprueba invariantes y estructura del artefacto, no la conducta empírica de un LLM).

### Escenario:
`02-architecture` inicia su ejecución consumiendo `docs/PRD.md`.

### Comportamiento Defectuoso (Amnésico / Sin Contrato):
```text
[Agente en 02-architecture sin contrato]:
"Hola, para la arquitectura de seguridad y usuarios:
¿Qué método de autenticación prefieres?
a) OAuth2 con Google/GitHub
b) JWT con base de datos local
c) Sin autenticación"
```
**Violación:** El agente gasta tokens y tiempo del desarrollador preguntando sobre OAuth, ignorando que el PRD ya lo sentenció como `OUT OF SCOPE`.

### Comportamiento Gobernable (Con Contrato de Salida v2.0):
Al cargar `docs/PRD.md`, `02-architecture` parsea la sección `OUT OF SCOPE`:
- `OUT OF SCOPE: Autenticación OAuth / SSO federado`.

`02-architecture` ejecuta la regla de no-reinterrogación:
```text
[Agente en 02-architecture gobernado]:
"Detectado en PRD (OUT OF SCOPE): 'Autenticación OAuth / SSO federado'.
Por tanto, la arquitectura omite proveedores externos de identidad y selecciona 
sesión local minimalista según la gobernanza de nivel medio estipulada en el PRD.
No se requiere consulta al desarrollador."
```

### Dinámica de Modificación de Frontera: `OUT OF SCOPE` no es un muro inmutable, sino una frontera gobernada:
`OUT OF SCOPE` no prohíbe que el proyecto evolucione en el futuro, sino que **impide el drift silencioso o la alteración arbitraria por parte del agente**. Si en una etapa posterior se requiere incorporar una capacidad excluida, el flujo gobernado es:

```text
Capacidad en OUT OF SCOPE (ej: OAuth)
                 ↓
El agente o usuario requiere incorporarla
                 ↓
PROHIBIDO modificar arquitectura o código silenciosamente
                 ↓
Emisión formal de Change Request
                 ↓
Decisión y aprobación explícita humana
                 ↓
Actualización a PRD v2 (status: APPROVED)
                 ↓
Revalidación de dependencias arquitectónicas impactadas
```

---

## 4. Prueba de Fuego 2: Desacoplamiento de Alcance (`PRD Scope ≠ TaskSpec Scope`)

### Escenario:
El PRD establece:
```markdown
IN SCOPE:
- Gestión interactiva de carrito de compras (agregar, actualizar cantidad, remover).
```

### Comportamiento Defectuoso (Acoplamiento Prematuro):
Un arnés o agente ingenuo intentaría generar inmediatamente restricciones físicas:
```yaml
# ERROR CONCEPTUAL: Derivar allowed_paths directamente del PRD
TaskSpec:
  id: "TS-CART-ALL"
  allowed_paths:
    - "src/cart/**"
    - "src/frontend/components/Cart.vue"
    - "src/backend/routes/cart.py"
```
**Por qué es un fallo grave:**
1. En la fase de PRD **no se ha decidido** si el frontend usará Vue, React o Vanilla JS.
2. No se ha decidido la estructura de directorios (`src/cart/` vs `src/domain/cart/` vs `src/api/routers/`).
3. Intentar adivinar paths físicos en el PRD obliga a inventar la arquitectura antes de tiempo.

### Cadena Correcta de Refinamiento Progresivo:
```text
1. PRD (01-prd):
   Capacidad Funcional: "Gestión interactiva de carrito de compras" (REQ-002, REQ-003)
   Criterios: AC-002, AC-003.

2. Architecture (02-architecture):
   Decisión de Patrón: Monolito modular (AD-001).
   Descomposición de Componentes: 
     - Componente A: `cart_service` (Lógica de dominio de carrito)
     - Componente B: `cart_api` (Capa de transporte HTTP)
     - Componente C: `cart_ui` (Vista web)

3. Data Modeling & API Design (03 & 04):
   Estructuras: `CartItemDTO`, `CartState`.
   Endpoints: `POST /api/cart/items`, `DELETE /api/cart/items/{id}`.

4. Formulación de TaskSpec Atómico (05-backend):
   TaskSpec TS-014: "Implementar lógica de cálculo de subtotal en cart_service"
   • allowed_paths: ["src/backend/domain/cart.py"]
   • forbidden_paths: ["src/backend/api/**", "src/frontend/**"]
   • criteria_addressed: ["AC-002"]
```

**Resultado:** El PRD declara **qué** debe poder hacerse (capacidades y criterios observables) sin hipotecar prematuramente la topología del código fuente.

---

## 5. Mapeo de Consumo por `02-architecture`

La siguiente tabla resume exactamente cómo `02-architecture` extrae sus datos de `docs/PRD.md` sin requerir contexto conversacional previo:

| Sección en `docs/PRD.md` | Campo Extraído | Uso en `02-architecture` | ¿Requiere Preguntar al Usuario? |
| :--- | :--- | :--- | :--- |
| `Frontmatter` | `project_type: "web_app"` | Selecciona topología cliente-servidor o frontend/backend integrado. | **NO.** Ya está resuelto. |
| `Frontmatter` | `governance_level: "medio"` | Configura requisitos de logging y auditoría estructural. | **NO.** Ya está resuelto. |
| `4. Requisitos` | `REQ-001..003` | Identifica dominios funcionales (Catálogo, Carrito). | **NO.** Son las capacidades base. |
| `5. Scope Boundary` | `IN SCOPE` | Delimita qué subsistemas diseñar (Catálogo + Carrito). | **NO.** Ya está acotado. |
| `5. Scope Boundary` | `OUT OF SCOPE` | Descarta OAuth, pasarelas de pago, microservicios, Elasticsearch. | **NO.** Prohibido re-preguntar. |
| `6. Criterios AC` | `AC-001..003` | Se transmiten intactos hacia el plan de pruebas (`08-testing`). | **NO.** Trazabilidad directa. |
| `7. Restricciones` | `CONST-001` (Python 3.13, local) | Limita las opciones técnicas a ecosistema Python estándar. | **NO.** Es una restricción dura. |
| `9. Open Questions` | `OPEN-001` (Patrón backend) | **SÍ.** Aquí es donde `02-architecture` debe enfocar sus preguntas de diseño al desarrollador. | **SÍ.** Es el único espacio legítimo de deliberación técnica. |

---

## 6. Estado de la Validación y Limitaciones

Para mantener el rigor del proyecto de título y evitar declaraciones exageradas, separamos taxativamente lo comprobado de lo pendiente:

### Lo que esta prueba y la suite de tests demuestran (Demostrado):
1. **Completitud e Invariantes Estructurales:** La suite automatizada de tests (`tests/harness/test_prd_skill.py`) comprueba deterministamente que `01-prd` genera un artefacto que cumple el esquema de metadatos, unicidad de IDs (`REQ`, `AC`, `CONST`, `ASSUMP`, `OPEN`) y la ausencia total de rutas físicas prematuras (`allowed_paths`).
2. **Suficiencia de Información para `02-architecture`:** El formato de `docs/PRD.md` estipulado contiene analíticamente toda la información funcional necesaria para que la fase de arquitectura pueda alimentarse sin recurrir a memoria conversacional no estructurada.
3. **Desacoplamiento Funcional-Físico:** Se comprueba analíticamente que el PRD delimita capacidades observables sin hipotecar prematuramente la topología física de archivos.

### Lo que NO está demostrado todavía (Pendiente de Validación Experimental):
1. **Comportamiento Empírico de un Coding Agent Real:** Los tests de software verifican estructura e invariantes del texto, pero **no garantizan** que un modelo de lenguaje real (Gemini, Claude, GPT) ejecutando `01-prd` o `02-architecture` en una sesión viva respete consistentemente el `OUT OF SCOPE` o no vuelva a formular preguntas ya resueltas.
2. **Validación en Ejecución Real:** Queda pendiente la prueba exploratoria en vivo: desplegar la Skill 01 con un agente real en un caso concreto (ej: e-commerce retail), emitir el PRD formal, y alimentar con dicho artefacto a una nueva sesión para observar si la fase de arquitectura hereda efectivamente las decisiones sin fricción.
3. **Bloqueo Determinista de Contradicciones en Tiempo de Ejecución:** Actualmente las reglas de gobernanza validan contratos en memoria/código (`policy_engine.py`), pero aún no existe un parser dinámico de markdown conectado al hook de inicio de `02-architecture` que aborte mecánicamente una sesión si el agente propone algo explícitamente excluido.
4. **Impacto en Métricas de Desarrollo:** No se ha cuantificado empíricamente la reducción en consumo de tokens ni la tasa de defectos frente a un flujo conversacional libre en un benchmark formal.

---
*Fin del informe de integración conceptual de la Skill 01.*
