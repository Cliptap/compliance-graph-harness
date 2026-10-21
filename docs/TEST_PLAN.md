---
status: "APPROVED"
version: 1
governance_level: "bajo"
acceptance_coverage: "100.0%"
total_tests_active: 110
last_audit: "2026-10-21"
---

# docs/TEST_PLAN.md — Plan Integral y Estrategia de Testing

## 1. Identidad y Objetivos de Calidad
El sistema **Catálogo Comercial y Carrito de Compras Desacoplado** (`catalogo-carrito-web`) implementa una estrategia de aseguramiento de calidad automatizada, determinista y transversal, orientada a certificar la correspondencia exacta entre los requisitos formales de negocio y el software ejecutable.

### Objetivos Estratégicos de Calidad (TP-xxx)
- **`TP-001` (Determinismo Absoluto):** El 100% de las suites de prueba deben ser reproducibles, ejecutarse en memoria (`sqlite:///:memory:`, Web Storage simulado) y no depender de servicios externos de red ni latencias no controladas.
- **`TP-002` (Aislamiento de Perímetro y Anti-Amnesia):** Garantizar que ninguna prueba introduzca o valide funcionalidades prohibidas por la cláusula `OUT OF SCOPE` de [docs/PRD.md](file:///c:/Users/Bastian/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md) (cero pruebas de autenticación, usuarios, tokens o pasarelas de pago).
- **`TP-003` (Trazabilidad Extremo a Extremo):** Todo Criterio de Aceptación (`AC-xxx`) debe contar con al menos una prueba física verificable que impida la presencia de requisitos huérfanos.
- **`TP-004` (Velocidad de Feedback para CI/CD):** La suite completa debe ejecutarse en menos de 3.0 segundos, permitiendo su integración como Quality Gate obligatorio previo al despliegue.

---

## 2. Matriz Bidireccional de Trazabilidad (AC-xxx -> Test-xxx)

Cada Criterio de Aceptación definido en [docs/PRD.md](file:///c:/Users/Bastian/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md) se encuentra rigurosamente vinculado a pruebas automatizadas en disco:

| Criterio de Aceptación | Requisito Origen | Componente y Archivo de Prueba | Función de Prueba (Test-xxx) | Tipo de Verificación | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`AC-001`** (Carga inicial y renderizado de catálogo completo) | `REQ-001`, `CONST-001` | Backend: `tests/catalog/test_catalog_backend.py`<br>Frontend: `tests/frontend/test_catalog_frontend.py` | `test_list_all_products_returns_seed_envelope`<br>`test_html_semantic_markup_and_ids` | Integración API (`EP-001`) y Marcado Semántico DOM | **PASS** |
| **`AC-002`** (Búsqueda textual insensible a mayúsculas/minúsculas) | `REQ-002` | Backend: `tests/catalog/test_catalog_backend.py`<br>Frontend: `tests/frontend/test_catalog_frontend.py` | `test_search_products_case_insensitive_match`<br>`test_app_orchestration_and_ui_states` | Filtrado SQL (`contains`) y Debounce UI (300ms) | **PASS** |
| **`AC-003`** (Empty State y feedback amigable ante búsqueda vacía) | `REQ-002` | Backend: `tests/catalog/test_catalog_backend.py`<br>Frontend: `tests/frontend/test_catalog_frontend.py` | `test_search_products_no_match_returns_empty_list`<br>`test_app_orchestration_and_ui_states` | Contrato Envelope Vacío (`total: 0`) y Estado UI `#empty-state` | **PASS** |
| **`AC-004`** (Adición interactiva al carrito e incremento de cantidad) | `REQ-003`, `AD-003` | Frontend: `tests/frontend/test_catalog_frontend.py` | `test_cart_invariants_and_storage_contract` | Ejecución en Node.js de `CartManager` y Persistencia Web Storage | **PASS** |
| **`AC-005`** (Modificación de cantidad y remoción automática al decrementar a $< 1$) | `REQ-003`, `INV-002` | Frontend: `tests/frontend/test_catalog_frontend.py` | `test_cart_invariants_and_storage_contract` | Cumplimiento estricto de invariante `INV-002` (eliminación ante $< 1$) | **PASS** |
| **`AC-006`** (Cálculo automático consistente de subtotales y total general) | `REQ-004`, `INV-004` | Frontend: `tests/frontend/test_catalog_frontend.py` | `test_cart_invariants_and_storage_contract` | Consistencia aritmética `INV-004` (redondeo bancario a 2 decimales) | **PASS** |

---

## 3. Métricas Deterministas de Cobertura

### 3.1 Acceptance Coverage (Métrica Formal del Arnés)
La cobertura formal de criterios de aceptación se evalúa de manera determinista:

$$\text{Acceptance Coverage} = \frac{\text{Criterios de Aceptación (AC) con Test Verificado Aprobado}}{\text{Total de Criterios de Aceptación (AC) Declarados en PRD}} \times 100\%$$

$$\text{Acceptance Coverage} = \frac{6}{6} \times 100\% = 100.0\%$$

### 3.2 Distribución Cuantitativa del Inventario de Pruebas
Actualmente el sistema cuenta con **110 pruebas automatizadas activas**, todas operando al 100% en verde:

| Suite de Pruebas | Alcance Tecnológico | Ubicación Física | Total Tests | Tiempo de Ejecución |
| :--- | :--- | :--- | :--- | :--- |
| **Harness & Governance** | Contratos de Skills (01 a 08), AST, Lineage, PolicyEngine, ScopePolicy | `tests/harness/` | 95 tests | ~1.60 s |
| **Catalog Backend** | API REST FastAPI, Repositorio SQLAlchemy, SQLite, DTOs y Errores | `tests/catalog/` | 9 tests | ~0.45 s |
| **Frontend Web** | DOM HTML5, Accesibilidad ARIA, Responsive CSS, CartManager (Node.js) | `tests/frontend/` | 6 tests | ~0.35 s |
| **TOTAL GENERAL** | Cobertura integral del sistema `catalogo-carrito-web` | `tests/` | **110 tests** | **~2.40 s** |

---

## 4. Pirámide de Pruebas e Inventario de Suites

La arquitectura de pruebas está organizada en tres niveles desacoplados:

```text
               ┌────────────────────────┐
               │   Nivel 3: Frontend    │  (6 tests)
               │ DOM, ARIA, CSS, Cart   │
               ├────────────────────────┴───────┐
               │     Nivel 2: Catalog Backend   │  (9 tests)
               │ FastAPI, SQLite, EP-001/002    │
         ┌─────┴────────────────────────────────┴─────┐
         │       Nivel 1: Arnés de Gobernanza         │  (95 tests)
         │  TaskSpec, Linters, ScopePolicy, AST, ADRs │
         └────────────────────────────────────────────┘
```

1. **Nivel 1 (Gobernanza y Contratos de Skills):** Verifica que la documentación técnica, los esquemas de TaskSpec y las decisiones arquitectónicas cumplan las reglas de Anti-Amnesia, No-Goldplating y Cero Alucinación.
2. **Nivel 2 (Backend y Persistencia Liviana):** Verifica el comportamiento de la API REST de catálogo (`EP-001`, `EP-002`), garantizando aislamiento de transacciones mediante base de datos SQLite en memoria y respuestas normalizadas con `DTO-ERR-001`.
3. **Nivel 3 (Frontend e Invariantes de Carrito):** Evalúa el DOM estático mediante `HTMLParser`, analiza las reglas CSS de diseño responsivo y ejecuta el motor `CartManager` directamente en el runtime de Node.js con mocks de `localStorage` para auditar la precisión matemática.

---

## 5. Auditoría de Anomalías de Testing

La auditoría estática determinista realizada sobre el repositorio certifica la ausencia de las cuatro anomalías críticas de ingeniería:

1. **Ausencia de Criterios sin Test (Zero Uncovered AC):**
   - El 100% de los criterios del PRD (`AC-001` a `AC-006`) cuentan con verificación automatizada en tests activos.
2. **Ausencia de Tests Huérfanos (Zero Orphan Tests):**
   - No existe ninguna prueba en `tests/` que evalúe autenticación, endpoints `/auth/*`, tokens JWT, tablas de usuarios, o flujos de pago con pasarelas externas.
3. **Ausencia de Tests Tautológicos (Zero Tautological Tests):**
   - Las pruebas no evalúan mocks vacíos; verifican comportamiento observable (cálculo de subtotales, rechazo de querys $> 100$ caracteres con HTTP 400, y remoción física de ítems al decrementar).
4. **Validación Rigurosa de Invariantes de Dominio:**
   - `INV-001` (Precios estrictamente positivos): Verificado en validadores Pydantic y tests de catálogo.
   - `INV-002` (Cantidades enteras $\ge 1$ y eliminación ante $< 1$): Verificado en `test_cart_invariants_and_storage_contract`.
   - `INV-003` (Unicidad de SKU): Verificado en esquema de base de datos.
   - `INV-004` (Consistencia aritmética de totales y subtotales): Verificado con aserciones sobre cálculos con decimales (`Math.round((val + EPSILON) * 100) / 100`).

---

## 6. Guía de Ejecución Determinista y Quality Gates para CI/CD

### 6.1 Comandos de Ejecución Local
Para reproducir la totalidad de la suite sin dependencias externas:

```powershell
# Ejecución completa de la suite de pruebas
.\.venv\Scripts\pytest tests/harness/ tests/catalog/ tests/frontend/ -v

# Ejecución rápida en memoria (< 1 segundo)
.\.venv\Scripts\pytest -m "fast" -v
```

### 6.2 Quality Gates Obligatorios para la Etapa 09 (CI/CD)
El pipeline automatizado en `09-cicd` deberá hacer cumplir las siguientes tres compuertas:
1. **Gate 1 (Zero Failure):** `exit_code == 0` (110/110 tests pasando).
2. **Gate 2 (Acceptance Coverage):** `Acceptance Coverage == 100.0%` (ningún criterio de aceptación huérfano).
3. **Gate 3 (Scope Policy Enforcement):** `ScopePolicy` certificando cero alteraciones a rutas prohibidas y cero dependencias no autorizadas en manifiestos.
