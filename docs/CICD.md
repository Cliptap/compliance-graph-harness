---
status: "APPROVED"
version: 1
governance_level: "bajo"
pipeline_provider: "github-actions"
quality_gates_count: 3
last_audit: "2026-10-22"
---

# docs/CICD.md — Especificación de Pipeline CI/CD y Quality Gates

## 1. Identidad del Pipeline y Objetivos de Calidad
El sistema **Catálogo Comercial y Carrito de Compras Desacoplado** (`catalogo-carrito-web`) implementa una canalización de Integración Continua (CI) automatizada, determinista y de retroalimentación inmediata denominada **`PIPE-001` (Pipeline de Verificación y Quality Gates)**.

Bajo la clasificación formal de `governance_level: "bajo"`, la estrategia de integración continua se adhiere rigurosamente a los principios de diseño KISS y YAGNI, eliminando la complejidad accidental de orquestadores pesados, despliegues multi-nube prematuros o matrices de compatibilidad innecesarias para un MVP.

### Objetivos Estratégicos del Pipeline:
- **Automatización Determinista:** Garantizar que cada commit integrado en la rama principal o propuesto en un Pull Request sea evaluado en un entorno limpio e independiente en la nube (`ubuntu-latest`), replicando fielmente las condiciones de ejecución local sin latencias no controladas.
- **Velocidad y Eficiencia:** Mantener el tiempo total de ejecución del pipeline por debajo de los 60 segundos (con la suite de pruebas corriendo en menos de 7.0 segundos), proporcionando un ciclo de retroalimentación ultrarrápido a los desarrolladores y agentes de código.
- **Bloqueo Preventivo de Regresiones:** Actuar como barrera infranqueable ante fallos en pruebas de catálogo (`tests/catalog/`), desbordamientos de contratos en frontend (`tests/frontend/`) o violaciones de gobernanza de arnés (`tests/harness/`).

---

## 2. Matriz de Quality Gates Contractuales (GATE-xxx)

El pipeline automatizado hace cumplir obligatoriamente tres compuertas de calidad deterministas (`GATE-001` a `GATE-003`), formalizadas contractualmente en la Sección 6.2 de [docs/TEST_PLAN.md](docs/TEST_PLAN.md):

| Quality Gate | Nombre de la Compuerta | Criterio Técnico de Aprobación | Mecanismo de Verificación | Política de Fallo |
| :--- | :--- | :--- | :--- | :--- |
| **`GATE-001`** | Zero Failure en Suite Completa | `exit_code == 0` (151/151 tests pasando sin errores ni omisiones inesperadas) | `pytest tests/harness/ tests/catalog/ tests/frontend/ -v` | **BLOQUEO INMEDIATO:** El pipeline falla y bloquea el merge si cualquier test unitario o de contrato reporta error. |
| **`GATE-002`** | Cobertura Formal de Aceptación (Acceptance Coverage) | $\text{Acceptance Coverage} == 100.0\%$ (Trazabilidad verificada de `AC-001` a `AC-006`) | `test_active_repository_acceptance_criteria_coverage` en `test_testing_skill.py` | **BLOQUEO INMEDIATO:** Prohíbe la presencia de criterios de aceptación sin prueba física automatizada. |
| **`GATE-003`** | Scope Policy & Security Audit | 0 invasiones de perímetro en `TaskSpec`, 0 dependencias ilícitas y 0 secrets hardcodeados | Evaluación de políticas del arnés en `test_policy_engine.py` y linters estáticos de skills (`ScopePolicy`, `CWE-532`) | **BLOQUEO INMEDIATO:** Prohíbe mutaciones a rutas no autorizadas o introducción de tokens/secrets. |

---

## 3. Especificación de Etapas y Triggers

### 3.1 Eventos Disparadores (Triggers)
El pipeline `PIPE-001` se dispara de manera automática ante los siguientes eventos en el repositorio Git:
- **`push`:** Todo commit empujado directamente a las ramas principales (`main`, `master`).
- **`pull_request`:** Toda propuesta de cambio abierta o actualizada con destino a las ramas principales (`main`, `master`).

Adicionalmente, se implementa control de concurrencia mediante `concurrency.cancel-in-progress: true` para cancelar automáticamente ejecuciones redundantes sobre el mismo ref ante commits sucesivos, optimizando el consumo de minutos de cómputo.

### 3.2 Secuenciamiento de Etapas Reproducibles (STAGE-xxx)

```text
               [ Evento Git: Push / Pull Request a main ]
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │ STAGE-001: Preparación del Entorno (Runner)    │
          │ - SO: ubuntu-latest                             │
          │ - Checkout de código (actions/checkout@v4)      │
          │ - Python 3.12 (actions/setup-python@v5)         │
          │ - Node.js LTS v24 (actions/setup-node@v4)       │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │ STAGE-002: Dependencias y Base de Datos         │
          │ - pip install -r requirements.txt               │
          │ - python -c "from src.harness.db import         │
          │              init_harness_db; init_harness_db()"│
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │ STAGE-003: Quality Gates y Evaluación           │
          │ - pytest tests/harness/ tests/catalog/          │
          │          tests/frontend/ -v                     │
          │   * GATE-001: Zero Failure (151/151 PASS)       │
          │   * GATE-002: Acceptance Coverage 100%          │
          │   * GATE-003: ScopePolicy & Cero Secrets        │
          └────────────────────────┬────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
              [ exit_code == 0 ]            [ exit_code != 0 ]
                    │                             │
                    ▼                             ▼
             STATUS: PASS                  STATUS: FAIL
          (Merge habilitado)          (Bloqueo con reporte claro)
```

1. **`STAGE-001` (Setup de Entornos Duales):**
   - Runner: `ubuntu-latest`.
   - Clonación profunda del código fuente mediante `actions/checkout@v4`.
   - Configuración de Python 3.12 (`actions/setup-python@v5`) con caché activa para gestor `pip`.
   - Configuración de Node.js v24 LTS (`actions/setup-node@v4`), indispensable para que `test_cart_invariants_and_storage_contract` evalúe el motor `CartManager` en runtime real de JavaScript con mocks de Web Storage.
2. **`STAGE-002` (Instalación de Dependencias e Inicialización):**
   - Instalación determinista de librerías listadas en `requirements.txt`.
   - Inicialización obligatoria del esquema SQLite del arnés mediante `python -c "from src.harness.db import init_harness_db; init_harness_db()"`, evitando errores de tablas inexistentes (`sqlite3.OperationalError: no such table: graph_nodes`).
3. **`STAGE-003` (Ejecución de Quality Gates):**
   - Ejecución integrada con `pytest tests/harness/ tests/catalog/ tests/frontend/ -v`.
   - Validación atómica de las tres compuertas: `GATE-001`, `GATE-002` y `GATE-003`.

---

## 4. Dependencias y Tiempos de Ejecución

### 4.1 Inventario de Dependencias en Runner
El pipeline se ejecuta de forma autosuficiente utilizando las dependencias declaradas en el manifiesto raíz:
- **Runtime Python:** `fastapi`, `pydantic`, `sqlalchemy`, `uvicorn`, `pytest`, `pytest-asyncio`, `pyyaml`.
- **Runtime JavaScript:** Entorno Node.js LTS v24 estándar provisto por la GitHub Actions virtual environment image (sin empaquetadores pesados ni dependencias externas en `node_modules`).

### 4.2 Métricas de Rendimiento y Tiempos Observados
- **Tiempo de Checkout y Configuración de Runtimes:** ~15 - 20 segundos.
- **Tiempo de Instalación de Dependencias (con pip cache):** ~10 - 15 segundos.
- **Tiempo de Inicialización de Persistencia SQLite:** < 1.0 segundo.
- **Tiempo de Ejecución de Suites de Pruebas (151 tests):** ~6.0 - 7.5 segundos.
- **Tiempo Total de Pipeline E2E:** **< 45 segundos**.

---

## 5. Política de Seguridad en CI/CD

De acuerdo con la postura sellada en [docs/SECURITY.md](docs/SECURITY.md), el pipeline de CI implementa las siguientes medidas de defensa en profundidad:

1. **Principio de Menor Privilegio (Least Privilege):**
   - Se declara taxativamente el bloque de permisos de solo lectura a nivel raíz del workflow:
     ```yaml
     permissions:
       contents: read
     ```
   - Se prohíbe la concesión de permisos de escritura (`contents: write`, `issues: write`, `pull-requests: write`), eliminando cualquier vector de ataque por inyección de código o manipulación no autorizada del repositorio desde acciones de terceros.
2. **Ausencia Absoluta de Secrets Hardcodeados:**
   - Cero tokens de acceso, API keys o contraseñas en el archivo YAML o scripts asociados.
   - El catálogo y carrito operan bajo acceso 100% público y anónimo (`SEC-DEC-001`), por lo que el pipeline no requiere ni almacena credenciales de producción.
3. **Control Estricto de Timeouts:**
   - Se fija un límite máximo de ejecución por job (`timeout-minutes: 10`) para prevenir bloqueos silenciosos o consumo infinito de minutos en caso de bucles de prueba imprevistos.

---

## 6. Matriz de Linaje con TEST_PLAN.md y PRD.md

| Elemento de CI/CD | Identificador Origen | Documento Upstream | Relación y Justificación Contractual |
| :--- | :--- | :--- | :--- |
| **`PIPE-001`** | `TP-004` | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Automatización del feedback de pruebas en menos de 3.0s de cómputo neto. |
| **`GATE-001`** | `TP-001`, Gate 1 | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Certificación de determinismo absoluto: 118/118 tests en verde en memoria. |
| **`GATE-002`** | `TP-003`, Gate 2, `AC-001`..`AC-006` | [docs/TEST_PLAN.md](docs/TEST_PLAN.md), [docs/PRD.md](docs/PRD.md) | Trazabilidad E2E: 100% de los criterios del PRD cubiertos formalmente. |
| **`GATE-003`** | `TP-002`, Gate 3, `SEC-CTRL-003` | [docs/TEST_PLAN.md](docs/TEST_PLAN.md), [docs/SECURITY.md](docs/SECURITY.md) | Cumplimiento perimetral de ScopePolicy y cero credenciales hardcodeadas. |
| **`STAGE-001`** | `AD-005` | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Configuración dual Python/Node requerida para probar el frontend Vanilla. |
| **`STAGE-002`** | `COMP-003`, `SEED-001` | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Inicialización de SQLite para dar soporte a la persistencia de catálogo y arnés. |
