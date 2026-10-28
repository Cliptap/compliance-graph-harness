---
name: testing-strategy
version: 2.0.0
stage: 7
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance]
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
produces_artifact: docs/TEST_PLAN.md
description: Estrategia de testing y aseguramiento de calidad transversal. Formaliza la matriz bidireccional AC-xxx -> Test-xxx, el cálculo de Acceptance Coverage y la auditoría contra tests huérfanos y tautológicos.
---

# Skill: Estrategia de Testing y Aseguramiento de Calidad (testing-strategy)

## 1. Overview
Esta skill define, audita y formaliza la estrategia integral de testing y aseguramiento de calidad del sistema.
A diferencia de enfoques tradicionales que reducen el testing a la mera instalación de librerías o a la generación aislada de archivos de prueba, esta skill cumple una **función transversal de control y gobernanza**:
- Conecta directamente los requisitos del negocio y Criterios de Aceptación (`AC-xxx`) definidos en `docs/PRD.md` con las pruebas físicas automatizadas en `tests/`.
- Construye la **Matriz Bidireccional de Trazabilidad Contractual**: cada criterio de aceptación debe poseer una o más pruebas automatizadas verificables.
- Calcula de manera determinista la métrica formal de **Acceptance Coverage**.
- Audita el repositorio para detectar patologías de testing comunes en coding agents: **criterios sin test**, **tests huérfanos** (pruebas de funcionalidades fuera de alcance) y **tests tautológicos** (pruebas vacías que solo prueban mocks).
- Emite el artefacto formal canónico: `docs/TEST_PLAN.md`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 7** del pipeline de desarrollo, inmediatamente después de haber consolidado el backend (`05-backend`), frontend (`06-frontend`) y la gobernanza de seguridad (`07-auth-governance`).
- Se utiliza para certificar la cobertura de aceptación antes de automatizar los pipelines de despliegue en `09-cicd`.
- Opera de forma continua y acumulativa sobre la totalidad del código y las suites de pruebas del repositorio.

---

## 3. Precondiciones
1. **Artefactos Previos Sellados:**
   - `docs/PRD.md` en estado `APPROVED`, con Criterios de Aceptación formales (`AC-xxx`) y frontera de alcance (`OUT OF SCOPE`).
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, con componentes (`COMP-xxx`) y decisiones estructurales (`AD-xxx`).
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con invariantes de dominio (`INV-xxx`) y, cuando existan, datos semilla (`SEED-xxx`).
   - `docs/API_DESIGN.md` en estado `APPROVED`, con contratos de endpoints (`EP-xxx`) y mapeo de errores (`DTO-ERR-xxx`).
   - `docs/SECURITY.md` en estado `APPROVED`, con dictamen de derivación condicional (`SEC-DEC-xxx`) y controles mínimos (`SEC-CTRL-xxx`).
   - Si una etapa upstream no aplica al `project_type` (por ejemplo, un pipeline de datos sin API HTTP), su exención debe constar formalmente en el artefacto correspondiente; la ausencia no justificada bloquea la skill.
2. **Código Físico y Pruebas Implementadas:**
   - Existencia de suites físicas de prueba por contexto acotado (`tests/<bounded_context>/`) y, cuando el sistema tenga capa de interfaz, de la suite de UI (`tests/frontend/` o la ruta equivalente declarada en la arquitectura).

---

## 4. Entradas
La skill consume de forma estricta y exhaustiva:
- **Desde `docs/PRD.md`:**
  - Lista canónica completa de Criterios de Aceptación (`AC-xxx`): todos y cada uno de los declarados, sin omisiones.
  - Requisitos funcionales (`REQ-xxx`) y cláusula `OUT OF SCOPE`.
- **Desde `docs/ARCHITECTURE.md`:**
  - Decisiones `AD-xxx` que condicionan la estrategia de pruebas: estilo macro y modularidad, localización del estado (cliente vs servidor), motor de persistencia y stack de interfaz. Cada una determina en qué suite y con qué tipo de prueba se verifica el comportamiento (por ejemplo, el estado delegado al cliente se verifica en la suite de cliente, nunca con tests de servidor).
- **Desde `docs/DATA_MODEL.md`:**
  - Todas las invariantes de datos `INV-xxx` declaradas, con su regla verificable (rangos, unicidad, cardinalidad, consistencia aritmética, etc.).
- **Desde `docs/API_DESIGN.md`:**
  - Endpoints `EP-xxx` y los códigos de estado esperados para cada uno (éxito, validación, recurso inexistente, etc.).
- **Desde `docs/SECURITY.md`:**
  - Dictamen `SEC-DEC-xxx` (inclusión o exclusión de autenticación) y controles `SEC-CTRL-xxx`.
- **Desde las Suites Físicas en Disco:**
  - Archivos ejecutables de prueba en `tests/<bounded_context>/` y, si aplica, en la suite de interfaz.

---

## 5. Taxonomía Formal
Toda directiva, caso de prueba o métrica emitida por esta skill debe utilizar identificadores estables y trazables:
- **`TP-xxx` (Test Plan):** Objetivos y directivas estratégicas de aseguramiento de calidad (ej. `TP-001`: "Verificación determinista de contratos y reglas del dominio").
- **`TC-xxx` (Test Case):** Casos de prueba específicos y ejecutables vinculados a requisitos (ej. genérico `TC-001`: "Rechazo de entrada inválida con error estructurado").
- **`AC-xxx` (Acceptance Criterion):** Criterio de aceptación formal consumido del PRD.
- **`AC-COV` (Acceptance Coverage):** Métrica porcentual determinista de cobertura de criterios de aceptación.

---

## 6. Regla de Oro Anti-Amnesia y Prevención de Patologías de Testing
1. **Prohibición de Tests Huérfanos (Orphan Tests):**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** escribir o validar tests para funcionalidades sentenciadas en `OUT OF SCOPE` (por ejemplo, si el PRD excluye autenticación o pagos: tests de endpoints `/auth/login`, creación de usuarios, tokens JWT, checkout o pasarelas de pago).
   - Todo test en el repositorio debe responder a un `REQ-xxx` o `AC-xxx` autorizado.
2. **Prohibición de Tests Tautológicos (Tautological Tests):**
   - Se prohíben tests triviales que solo afirmen el retorno de mocks pre-programados (ej. mockear un servicio para devolver `True` y asertar `is True`), sin validar la semántica real del dominio ni los datos.
3. **Validación Obligatoria de Invariantes del Dominio:**
   - Toda prueba sobre una entidad, agregado o flujo sujeto a reglas de negocio debe verificar explícitamente cada `INV-xxx` declarado en `docs/DATA_MODEL.md` que le aplique, incluyendo sus casos límite (valores frontera, rechazo o eliminación ante valores inválidos, consistencia aritmética y redondeo cuando la invariante lo exija).
   - Toda invariante `INV-xxx` declarada debe figurar en la matriz de trazabilidad con al menos una prueba que la ejercite.
4. **Delimitación de Perímetro (TaskSpec):**
   - `allowed_paths`: `["docs/TEST_PLAN.md"]`
   - `forbidden_paths`: `["src/**"]` (la skill de testing documenta y audita la calidad; no muta el código de producción).

---

## 7. Workflow de Implementación (Función Transversal y Trazabilidad)

```text
INICIO: Cargar PRD.md (todos los AC-xxx), ARCHITECTURE.md, DATA_MODEL.md, API_DESIGN.md, SECURITY.md
  │
  ▼
Paso 1: Extracción de Criterios de Aceptación (AC-xxx)
  Identificar exhaustivamente cada criterio declarado en docs/PRD.md.
  │
  ▼
Paso 2: Construcción de la Matriz Bidireccional de Trazabilidad
  Mapear cada AC-xxx con su respectiva función de prueba física en tests/
  (ejemplo genérico de forma, no de contenido):
  - AC-xxx ──► test_<comportamiento_observable> [+ test_<verificacion_ui> si hay interfaz]
  - AC-yyy ──► test_<regla_de_dominio> (INV-xxx)
  Verificar también el sentido inverso: cada test activo apunta a un AC-xxx o REQ-xxx.
  │
  ▼
Paso 3: Cálculo Determinista de Acceptance Coverage
  Calcular: Acceptance Coverage = (AC con test aprobado / AC totales) * 100%
  Verificar que Acceptance Coverage == 100.0%.
  │
  ▼
Paso 4: Auditoría de Patologías de Testing
  - Verificar ausencia de AC sin test.
  - Verificar ausencia de tests huérfanos (cero pruebas de conceptos declarados OUT OF SCOPE).
  - Verificar ausencia de tests tautológicos.
  │
  ▼
Paso 5: Emisión del Artefacto Formal
  Generar docs/TEST_PLAN.md en estado DRAFT / APPROVED.
```

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir:
- Proponer "crear tests para el endpoint de login" en un sistema donde auth está en `OUT OF SCOPE`.
- Afirmar que "el sistema tiene 100% de cobertura" basándose solo en cobertura de líneas (line coverage) sin demostrar trazabilidad con los criterios de aceptación (`AC-COV`).
- Reducir o relajar aserciones para que un test pase en verde sin probar la invariante de negocio.
- Modificar archivos en `src/` bajo el pretexto de "hacer pasar los tests".

---

## 9. Contrato de Salida Formal: `docs/TEST_PLAN.md`
La skill produce obligatoriamente el artefacto canónico `docs/TEST_PLAN.md`.

### Estructura y Esquema Obligatorio
El archivo debe contener el siguiente frontmatter y secciones normalizadas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "<nivel declarado en docs/PRD.md>"
acceptance_coverage: "100.0%"
total_tests_active: <N>
last_audit: "YYYY-MM-DD"
---

# docs/TEST_PLAN.md — Plan Integral y Estrategia de Testing

## 1. Identidad y Objetivos de Calidad
Resumen del sistema, nivel de gobernanza y directivas estratégicas de testing (determinismo, aislamiento de datos, ejecución rápida en CI/CD).

## 2. Matriz Bidireccional de Trazabilidad (AC-xxx -> Test-xxx)
Tabla completa vinculando:
- Criterio de Aceptación (AC-xxx)
- Requisito de Origen (REQ-xxx)
- Archivo de Test y Función de Prueba (Test-xxx)
- Tipo de Verificación (Unitaria, Integración, Contrato, UI)

## 3. Métricas Deterministas de Cobertura
- Acceptance Coverage: (<AC cubiertos> / <AC totales>) = 100.0%.
- Inventario cuantitativo de tests por suite.

## 4. Pirámide de Pruebas e Inventario de Suites
Niveles según los `project_types` y la arquitectura aprobada, por ejemplo:
1. Nivel 1: Pruebas de Gobernanza y Contratos de Skills (`tests/harness/`).
2. Nivel 2: Pruebas de dominio, contratos de API y persistencia por contexto acotado (`tests/<bounded_context>/`).
3. Nivel 3: Pruebas de interfaz e invariantes ejecutadas en el cliente, cuando exista capa de UI (`tests/frontend/` o ruta equivalente).

## 5. Auditoría de Anomalías de Testing
- Certificación de Cero AC sin test.
- Certificación de Cero Tests huérfanos (ausencia de tests para funcionalidades OUT OF SCOPE).
- Certificación de Cero Tests tautológicos.
- Cumplimiento de todas las Invariantes del Dominio (INV-xxx) declaradas en docs/DATA_MODEL.md.

## 6. Guía de Ejecución Determinista y Quality Gates para CI/CD
Instrucciones reproducibles para ejecución en terminal local (`pytest` o el runner del stack) y compuertas de calidad requeridas para avanzar a `09-cicd`.
```

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_testing_skill.py`:
1. **Verificación Estructural:** `docs/TEST_PLAN.md` existe, tiene frontmatter válido y contiene las 6 secciones canónicas.
2. **Validación de Métricas:** Contiene la métrica `acceptance_coverage: "100.0%"` y mapea formalmente cada `AC-xxx` declarado en `docs/PRD.md`.
3. **Auditoría de Tests Huérfanos:** Verifica deterministamente que no existan tests para conceptos declarados `OUT OF SCOPE` (por ejemplo, cuando auth y pagos están excluidos: `login`, `password`, `jwt` ni `pagos`).
4. **Verificación de ScopePolicy:**
   - El 100% de los cambios pertenecen a `allowed_paths = ["docs/TEST_PLAN.md"]`.
   - Cero modificaciones no autorizadas en `src/**`.

---

## 11. Criterio de Término
La etapa de `testing-strategy` se considera concluida satisfactoriamente cuando:
- [ ] La skill `testing-strategy` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/08-testing/SKILL.md` y `harness/skills/08_testing_strategy.md`.
- [ ] La suite determinista `tests/harness/test_testing_skill.py` está implementada y pasa 100% en verde.
- [ ] El artefacto canónico `docs/TEST_PLAN.md` ha sido validado sin violaciones de linter ni de TaskSpec.
- [ ] La suite completa de pruebas acumula el 100% de tests en verde sin regresiones.

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian de la siguiente forma:

### 1. Artefactos Upstream Concretos de la Demo
- `docs/PRD.md`: Criterios de Aceptación `AC-001` a `AC-006`, requisitos funcionales `REQ-001` a `REQ-004` y cláusula `OUT OF SCOPE` (autenticación, usuarios, checkout y pagos).
- `docs/ARCHITECTURE.md`: componentes `COMP-001`, `COMP-002` y decisiones `AD-001` (Monolito modular liviano), `AD-003` (Persistencia del carrito en Web Storage / localStorage del cliente), `AD-005` (Frontend Vanilla).
- `docs/DATA_MODEL.md`: invariantes `INV-001` (precio $> 0$), `INV-002` (cantidades $\ge 1$), `INV-003` (unicidad SKU), `INV-004` (consistencia aritmética de subtotales y total general) y datos semilla `SEED-001`.
- `docs/API_DESIGN.md`: endpoints `EP-001`, `EP-002` (`/api/v1/products`) con códigos HTTP 200, 400 y 404, y mapeo de errores `DTO-ERR-001`.
- `docs/SECURITY.md`: `SEC-DEC-001` (exclusión de auth) y controles `SEC-CTRL-001` a `SEC-CTRL-005`.

### 2. Suites Físicas de la Demo
- `tests/catalog/test_catalog_backend.py`: backend de catálogo, API REST y persistencia SQLite.
- `tests/frontend/test_catalog_frontend.py`: DOM semántico e invariantes del carrito en el cliente.

### 3. Invariantes Obligatorias del Carrito
Toda prueba sobre el carrito debe verificar explícitamente `INV-002` (eliminación automática ante cantidad $< 1$) e `INV-004` (consistencia matemática de redondeo a 2 decimales).

### 4. Matriz Bidireccional de Trazabilidad de la Demo
```text
- AC-001 ──► test_list_all_products_returns_seed_envelope + test_html_semantic_markup_and_ids
- AC-002 ──► test_search_products_case_insensitive_match + test_app_orchestration_and_ui_states
- AC-003 ──► test_search_products_no_match_returns_empty_list + test_app_orchestration_and_ui_states
- AC-004 ──► test_cart_invariants_and_storage_contract
- AC-005 ──► test_cart_invariants_and_storage_contract (INV-002)
- AC-006 ──► test_cart_invariants_and_storage_contract (INV-004)
```
Ejemplo de caso de prueba de la demo: `TC-001`: "Búsqueda textual insensible a mayúsculas".

### 5. Instanciación de `docs/TEST_PLAN.md` en la Demo
- Frontmatter: `governance_level: "bajo"`, `acceptance_coverage: "100.0%"`, `total_tests_active: 100`.
- Métricas: Acceptance Coverage: (6 / 6) = 100.0%; inventario por suite (Harness, Catalog Backend, Frontend UI).
- Pirámide de pruebas:
  1. Nivel 1: Pruebas de Gobernanza y Contratos de Skills (`tests/harness/`).
  2. Nivel 2: Pruebas de Backend, API REST y Persistencia SQLite (`tests/catalog/`).
  3. Nivel 3: Pruebas de Frontend, DOM Semántico e Invariantes de Carrito (`tests/frontend/`).
- Auditoría: cumplimiento de Invariantes del Dominio (`INV-001` a `INV-004`).
- Verificación: el plan mapea formalmente `AC-001` a `AC-006`.
- Ejecución determinista: `pytest tests/harness/ tests/catalog/ tests/frontend/ -v`.
