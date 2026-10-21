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
   - `docs/PRD.md` en estado `APPROVED`, con Criterios de Aceptación formales (`AC-001` a `AC-006`) y frontera de alcance (`OUT OF SCOPE`).
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, con componentes (`COMP-001`, `COMP-002`) y decisiones estructurales (`AD-xxx`).
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con invariantes de dominio (`INV-001` a `INV-004`) y datos semilla (`SEED-001`).
   - `docs/API_DESIGN.md` en estado `APPROVED`, con contratos de endpoints (`EP-001`, `EP-002`) y mapeo de errores (`DTO-ERR-001`).
   - `docs/SECURITY.md` en estado `APPROVED`, con dictamen de derivación condicional (`SEC-DEC-001`) y controles mínimos (`SEC-CTRL-001` a `SEC-CTRL-005`).
2. **Código Físico y Pruebas Implementadas:**
   - Existencia de suites físicas de prueba en `tests/catalog/` y `tests/frontend/`.

---

## 4. Entradas
La skill consume de forma estricta y exhaustiva:
- **Desde `docs/PRD.md`:**
  - Lista canónica de Criterios de Aceptación: `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`.
  - Requisitos funcionales (`REQ-001` a `REQ-004`) y cláusula `OUT OF SCOPE`.
- **Desde `docs/ARCHITECTURE.md`:**
  - `AD-001` (Monolito modular liviano), `AD-003` (Persistencia del carrito en Web Storage), `AD-005` (Frontend Vanilla).
- **Desde `docs/DATA_MODEL.md`:**
  - Invariantes de datos: `INV-001` (precio $> 0$), `INV-002` (cantidades $\ge 1$), `INV-003` (unicidad SKU), `INV-004` (consistencia aritmética de subtotales y total general).
- **Desde `docs/API_DESIGN.md`:**
  - Endpoints `EP-001`, `EP-002` y códigos de estado esperados (HTTP 200, 400, 404).
- **Desde `docs/SECURITY.md`:**
  - `SEC-DEC-001` (exclusión de auth), `SEC-CTRL-001` a `SEC-CTRL-005`.
- **Desde las Suites Físicas en Disco:**
  - Archivos ejecutables en `tests/catalog/test_catalog_backend.py` y `tests/frontend/test_catalog_frontend.py`.

---

## 5. Taxonomía Formal
Toda directiva, caso de prueba o métrica emitida por esta skill debe utilizar identificadores estables y trazables:
- **`TP-xxx` (Test Plan):** Objetivos y directivas estratégicas de aseguramiento de calidad (ej. `TP-001`: "Verificación determinista de contratos y reglas del dominio").
- **`TC-xxx` (Test Case):** Casos de prueba específicos y ejecutables vinculados a requisitos (ej. `TC-001`: "Búsqueda textual insensible a mayúsculas").
- **`AC-xxx` (Acceptance Criterion):** Criterio de aceptación formal consumido del PRD.
- **`AC-COV` (Acceptance Coverage):** Métrica porcentual determinista de cobertura de criterios de aceptación.

---

## 6. Regla de Oro Anti-Amnesia y Prevención de Patologías de Testing
1. **Prohibición de Tests Huérfanos (Orphan Tests):**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** escribir o validar tests para funcionalidades sentenciadas en `OUT OF SCOPE` (por ejemplo, tests de endpoints `/auth/login`, creación de usuarios, tokens JWT, checkout o pasarelas de pago).
   - Todo test en el repositorio debe responder a un `REQ-xxx` o `AC-xxx` autorizado.
2. **Prohibición de Tests Tautológicos (Tautological Tests):**
   - Se prohíben tests triviales que solo afirmen el retorno de mocks pre-programados (ej. mockear un servicio para devolver `True` y asertar `is True`), sin validar la semántica real del dominio ni los datos.
3. **Validación Obligatoria de Invariantes del Dominio:**
   - Toda prueba sobre el carrito debe verificar explícitamente `INV-002` (eliminación automática ante cantidad $< 1$) e `INV-004` (consistencia matemática de redondeo a 2 decimales).
4. **Delimitación de Perímetro (TaskSpec):**
   - `allowed_paths`: `["docs/TEST_PLAN.md"]`
   - `forbidden_paths`: `["src/**"]` (la skill de testing documenta y audita la calidad; no muta el código de producción).

---

## 7. Workflow de Implementación (Función Transversal y Trazabilidad)

```text
INICIO: Cargar PRD.md (AC-001..006), ARCHITECTURE.md, DATA_MODEL.md, API_DESIGN.md, SECURITY.md
  │
  ▼
Paso 1: Extracción de Criterios de Aceptación (AC-xxx)
  Identificar exhaustivamente cada criterio declarado en docs/PRD.md.
  │
  ▼
Paso 2: Construcción de la Matriz Bidireccional de Trazabilidad
  Mapear cada AC-xxx con su respectiva función de prueba física en tests/:
  - AC-001 ──► test_list_all_products_returns_seed_envelope + test_html_semantic_markup_and_ids
  - AC-002 ──► test_search_products_case_insensitive_match + test_app_orchestration_and_ui_states
  - AC-003 ──► test_search_products_no_match_returns_empty_list + test_app_orchestration_and_ui_states
  - AC-004 ──► test_cart_invariants_and_storage_contract
  - AC-005 ──► test_cart_invariants_and_storage_contract (INV-002)
  - AC-006 ──► test_cart_invariants_and_storage_contract (INV-004)
  │
  ▼
Paso 3: Cálculo Determinista de Acceptance Coverage
  Calcular: Acceptance Coverage = (AC con test aprobado / AC totales) * 100%
  Verificar que Acceptance Coverage == 100.0%.
  │
  ▼
Paso 4: Auditoría de Patologías de Testing
  - Verificar ausencia de AC sin test.
  - Verificar ausencia de tests huérfanos (cero pruebas de auth o pagos).
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
governance_level: "bajo"
acceptance_coverage: "100.0%"
total_tests_active: 100
last_audit: "YYYY-MM-DD"
---

# docs/TEST_PLAN.md — Plan Integral y Estrategia de Testing

## 1. Identidad y Objetivos de Calidad
Resumen del sistema, nivel de gobernanza y directivas estratégicas de testing (determinismo, aislamiento en memoria, ejecución ultra-rápida en CI/CD).

## 2. Matriz Bidireccional de Trazabilidad (AC-xxx -> Test-xxx)
Tabla completa vinculando:
- Criterio de Aceptación (AC-xxx)
- Requisito de Origen (REQ-xxx)
- Archivo de Test y Función de Prueba (Test-xxx)
- Tipo de Verificación (Unitaria, Integración, Contrato, DOM)

## 3. Métricas Deterministas de Cobertura
- Acceptance Coverage: (6 / 6) = 100.0%.
- Inventario cuantitativo de tests por suite (Harness, Catalog Backend, Frontend UI).

## 4. Pirámide de Pruebas e Inventario de Suites
1. Nivel 1: Pruebas de Gobernanza y Contratos de Skills (`tests/harness/`).
2. Nivel 2: Pruebas de Backend, API REST y Persistencia SQLite (`tests/catalog/`).
3. Nivel 3: Pruebas de Frontend, DOM Semántico e Invariantes de Carrito (`tests/frontend/`).

## 5. Auditoría de Anomalías de Testing
- Certificación de Cero AC sin test.
- Certificación de Cero Tests huérfanos (ausencia de tests para funcionalidades OUT OF SCOPE).
- Certificación de Cero Tests tautológicos.
- Cumplimiento de Invariantes del Dominio (INV-001 a INV-004).

## 6. Guía de Ejecución Determinista y Quality Gates para CI/CD
Instrucciones reproducibles para ejecución en terminal local (`pytest`) y compuertas de calidad requeridas para avanzar a `09-cicd`.
```

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_testing_skill.py`:
1. **Verificación Estructural:** `docs/TEST_PLAN.md` existe, tiene frontmatter válido y contiene las 6 secciones canónicas.
2. **Validación de Métricas:** Contiene la métrica `acceptance_coverage: "100.0%"` y mapea formalmente `AC-001` a `AC-006`.
3. **Auditoría de Tests Huérfanos:** Verifica deterministamente que no existan tests para `login`, `password`, `jwt` ni `pagos`.
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
