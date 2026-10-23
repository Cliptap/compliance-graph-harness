---
name: cicd-automation
version: 2.0.0
stage: 8
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance, testing-strategy]
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
produces_artifact: [docs/CICD.md, .github/workflows/ci.yml]
description: Automatización de integración continua (CI) y compuertas de calidad deterministas (Quality Gates). Define el flujo reproducible de verificación para PRs y push a main con aislamiento de entorno, inicialización de BD y aseguramiento de contratos sin goldplating.
---

# Skill: Automatización de CI/CD y Compuertas de Calidad (cicd-automation)

## 1. Overview
Esta skill diseña, formaliza y automatiza el pipeline de Integración Continua (CI) del sistema.
A diferencia de enfoques empíricos que saturan el repositorio con configuraciones pesadas de DevOps, multi-plataformas o despliegues complejos antes de tiempo, esta skill se enfoca en la **automatización estricta de las compuertas de calidad (Quality Gates)** consolidadas en `docs/TEST_PLAN.md`:
- Traduce las directivas de aseguramiento de calidad local a un entorno de ejecución continuo y determinista en la nube (GitHub Actions).
- Implementa un flujo reproducible de cuatro fases: **Change -> Setup -> Init DB -> Tests & Gates -> PASS/FAIL**.
- Automatiza las tres compuertas de bloqueo obligatorias:
  1. `GATE-001` (Zero Failure): Ejecución exitosa del 100% de la suite de pruebas (`pytest`, exit code 0).
  2. `GATE-002` (Acceptance Coverage): Certificación de cobertura total de requisitos sin criterios huérfanos.
  3. `GATE-003` (ScopePolicy Enforcement): Verificación de límites perimetrales y ausencia de dependencias o rutas no autorizadas.
- Opera bajo el principio de menor privilegio (`permissions: contents: read`) y máxima sobriedad técnica (KISS / YAGNI).
- Emite dos artefactos canónicos: la especificación de gobernanza `docs/CICD.md` y el flujo ejecutable `.github/workflows/ci.yml`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 8** del pipeline de desarrollo, inmediatamente después de haber validado y sellado la estrategia de pruebas transversal en `08-testing` (`docs/TEST_PLAN.md`).
- Se utiliza para blindar el repositorio contra regresiones antes de abordar la etapa de empaquetado y despliegue en `10-deployment`.
- Aplica a todo cambio de código propuesto mediante pull requests o pushes directos a la rama principal (`main` o `master`).

---

## 3. Precondiciones
1. **Artefactos Previos Sellados:**
   - `docs/PRD.md` en estado `APPROVED`, con `governance_level: "bajo"` y límites de alcance claros.
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, especificando arquitectura monolítica modular (`AD-001`), almacenamiento cliente (`AD-003`) y frontend Vanilla (`AD-005`).
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con invariantes de dominio (`INV-001` a `INV-004`).
   - `docs/API_DESIGN.md` en estado `APPROVED`, con contratos de endpoints (`EP-001`, `EP-002`).
   - `docs/SECURITY.md` en estado `APPROVED`, con postura de seguridad pública anónima (`SEC-DEC-001`) y controles mínimos (`SEC-CTRL-001` a `SEC-CTRL-005`).
   - `docs/TEST_PLAN.md` en estado `APPROVED`, definiendo formalmente los Quality Gates de CI/CD (Sección 6.2).
2. **Suite Física de Pruebas Determinista:**
   - Existencia de suites completas en `tests/harness/`, `tests/catalog/` y `tests/frontend/` ejecutándose 100% en verde.
3. **Manifiestos y Entorno:**
   - Archivo `requirements.txt` actualizado y script de inicialización de base de datos `src.harness.db.init_harness_db`.

---

## 4. Entradas
La skill consume de manera estricta y exhaustiva:
- **Desde `docs/TEST_PLAN.md`:**
  - Sección 6.2 (Quality Gates Obligatorios para CI/CD):
    * `GATE-001` (Zero Failure): 100% de tests pasando en memoria (`exit_code == 0`).
    * `GATE-002` (Acceptance Coverage): Métrica al 100.0% (`6/6` criterios cubiertos).
    * `GATE-003` (Scope Policy Enforcement): Cero alteraciones perimetrales y cero dependencias ilícitas.
  - Inventario de suites: `tests/harness/`, `tests/catalog/`, `tests/frontend/`.
- **Desde `docs/PRD.md`:**
  - Nivel de gobernanza: `governance_level: "bajo"` (determina ausencia de pipelines complejos de auditoría forense o escaneos DAST pesados).
  - Cláusula `OUT OF SCOPE`: Prohíbe agregar stages de despliegue a producción, testing en dispositivos móviles o integración con servicios de terceros.
- **Desde `docs/ARCHITECTURE.md`:**
  - `AD-001` (Monolito modular Python + FastAPI + SQLite en memoria).
  - `AD-005` (Frontend Vanilla HTML5/CSS3/JS sin empaquetadores complejos como Webpack o Vite).
- **Desde el Repositorio Físico:**
  - `requirements.txt`: Dependencias del sistema y del arnés de testing.
  - Módulo de base de datos: `src/harness/db.py` con función `init_harness_db()`.
  - Runtime dual: Python 3.12 y Node.js (necesario para la ejecución del motor `CartManager` en `tests/frontend/test_catalog_frontend.py`).

---

## 5. Taxonomía Formal
Toda directiva, etapa o compuerta configurada por esta skill debe emplear identificadores estables y normalizados:
- **`PIPE-xxx` (Pipeline Definition):** Identificador del flujo de automatización (ej. `PIPE-001`: "Pipeline de Verificación Determinista de Integración Continua").
- **`STAGE-xxx` (Pipeline Stage):** Fases secuenciales de ejecución en el runner de CI:
  * `STAGE-001`: Setup de Entornos (Checkout + Python 3.12 + Node.js LTS).
  * `STAGE-002`: Instalación de Dependencias e Inicialización de Persistencia (`requirements.txt` + `init_harness_db()`).
  * `STAGE-003`: Ejecución de Quality Gates y Evaluación de Políticas (`pytest`, linters y ScopePolicy).
- **`GATE-xxx` (Quality Gate):** Compuertas de bloqueo y criterios de paso/rechazo:
  * `GATE-001`: Zero Failure (`exit_code == 0` sobre la suite completa de pruebas).
  * `GATE-002`: Acceptance Coverage Formal (`Acceptance Coverage == 100.0%`).
  * `GATE-003`: Scope Policy & Security Audit (Verificación estricta de `allowed_paths`, cero secrets y controles `SEC-CTRL-xxx`).

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición de Infraestructura Pesada o Innecesaria:**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** introducir:
     * Orquestadores de contenedores (Kubernetes, k8s, Docker Swarm, Nomad, Helm).
     * Herramientas de aprovisionamiento de infraestructura en la nube (Terraform, Pulumi, CloudFormation, Ansible).
     * Registros remotos de contenedores (Docker Hub, AWS ECR, GCP Artifact Registry) o publicación de paquetes en npm/PyPI.
     * Pipelines multi-nube o integraciones con nubes comerciales (AWS, Azure, GCP) en esta etapa.
2. **Prohibición de Herramientas y Runtimes Ajenos:**
   - No se deben configurar linters ni pasos para lenguajes ausentes en el proyecto (prohibido `golangci-lint`, `cargo`, `rustc`, `bundle exec`, `composer`).
3. **Principio de Menor Privilegio (Least Privilege):**
   - El workflow debe declarar explícitamente permisos mínimos de solo lectura:
     ```yaml
     permissions:
       contents: read
     ```
   - Prohibido solicitar permisos de escritura sobre el repositorio (`contents: write`, `issues: write`, `pull-requests: write`) si el pipeline no realiza mutaciones.
4. **Timeouts Obligatorios:**
   - Todo trabajo en CI debe definir un límite máximo de ejecución para evitar consumos infinitos de minutos de cómputo (`timeout-minutes: 10`).
5. **Delimitación de Perímetro (TaskSpec):**
   ```yaml
   task_spec:
     allowed_paths:
       - "docs/CICD.md"
       - ".github/workflows/ci.yml"
     forbidden_paths:
       - "src/**"
       - "tests/**"
   ```

---

## 7. Workflow de Implementación (Flujo Reproducible)

El flujo de integración continua debe ser 100% determinista, reproducible localmente y en el runner:

```text
               [ Evento Git: Push / Pull Request a main ]
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │ STAGE-001: Preparación del Entorno (Runner)    │
          │ - SO: ubuntu-latest                             │
          │ - Checkout de código (actions/checkout@v4)      │
          │ - Python 3.12 (actions/setup-python@v5)         │
          │ - Node.js LTS (actions/setup-node@v4)           │
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
          │   * GATE-001: Zero Failure (110+ tests PASS)    │
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

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir y rechazar la configuración:
- Proponer desplegar a producción o staging directamente desde el pipeline de CI (debe postergarse a `10-deployment`).
- Hardcodear secrets, tokens o credenciales en el archivo YAML del workflow.
- Omitir el paso de configuración de Node.js, provocando el fallo del test de carrito en `tests/frontend/test_catalog_frontend.py`.
- Omitir la inicialización de la base de datos de arnés (`init_harness_db()`), causando errores `sqlite3.OperationalError: no such table: graph_nodes`.
- Agregar matrices complejas de sistemas operativos (Windows + macOS + Linux) cuando el objetivo del MVP es validación ligera y rápida en `ubuntu-latest`.
- Añadir etapas de linting que introduzcan dependencias de desarrollo pesadas no declaradas en `requirements.txt`.

---

## 9. Contrato de Salida Formal: `docs/CICD.md` y `.github/workflows/ci.yml`
La skill produce obligatoriamente dos artefactos complementarios:

### A. Documento de Gobernanza: `docs/CICD.md`
El documento debe contener el siguiente frontmatter y 6 secciones estructuradas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "bajo"
pipeline_provider: "github-actions"
quality_gates_count: 3
last_audit: "YYYY-MM-DD"
---

# docs/CICD.md — Especificación de Pipeline CI/CD y Quality Gates

## 1. Identidad del Pipeline y Objetivos de Calidad
Definición de PIPE-001, objetivos de automatización determinista y relación con el nivel de gobernanza bajo.

## 2. Matriz de Quality Gates Contractuales (GATE-xxx)
Tabla detallando:
- GATE-001: Zero Failure (pytest exit_code == 0).
- GATE-002: Acceptance Coverage al 100.0% (AC-001 a AC-006 certificados).
- GATE-003: Scope Policy Enforcement (cero infracciones perimetrales y cero secrets).

## 3. Especificación de Etapas y Triggers
Triggers de ejecución (push y pull_request a main), concurrencia y secuenciamiento de STAGE-001 a STAGE-003.

## 4. Dependencias y Tiempos de Ejecución
Inventario de dependencias requeridas en el runner, caché de pip y tiempo objetivo de ejecución (< 3.0s de pruebas, < 1 min total).

## 5. Política de Seguridad en CI/CD
Controles de menor privilegio (permissions: contents: read), ausencia de secrets en workflows y timeouts.

## 6. Matriz de Linaje con TEST_PLAN.md y PRD.md
Trazabilidad de compuertas con criterios de aceptación y requisitos de calidad.
```

### B. Workflow Ejecutable: `.github/workflows/ci.yml`
El archivo de workflow de GitHub Actions debe incluir:
```yaml
name: CI Quality Gates

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    name: Verify Quality Gates
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Set up Node.js LTS
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Initialize Harness Database
        run: |
          python -c "from src.harness.db import init_harness_db; init_harness_db()"

      - name: Run Test Suite & Quality Gates
        run: |
          pytest tests/harness/ tests/catalog/ tests/frontend/ -v
```

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_cicd_skill.py`:
1. **Verificación Estructural de la Skill:** Frontmatter normativo v2.0, 11 secciones obligatorias y sincronización exacta con `harness/skills/09_ci_cd.md`.
2. **Auditoría de TaskSpec:** `allowed_paths` restringido a `docs/CICD.md` y `.github/workflows/ci.yml`. Rechazo inmediato ante intentos de modificar `src/` o `tests/`.
3. **Auditoría de Anti-Patrones:** Rechazo de menciones a Kubernetes, Docker Swarm, Terraform o herramientas de lenguajes ajenos.
4. **Verificación de Esquema Documental:** `docs/CICD.md` contiene frontmatter válido, 6 secciones requeridas y definición de `GATE-001` a `GATE-003`.
5. **Verificación del Workflow de CI:** `.github/workflows/ci.yml` contiene permisos `contents: read`, triggers `push`/`pull_request`, configuración dual de Python y Node, paso de `init_harness_db` y comando de pruebas `pytest`.

---

## 11. Criterio de Término
La etapa de `cicd-automation` se considera formalmente concluida cuando:
- [ ] La skill `cicd-automation` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/09-cicd/SKILL.md` y `harness/skills/09_ci_cd.md`.
- [ ] La suite determinista `tests/harness/test_cicd_skill.py` está implementada y pasa 100% en verde.
- [ ] El artefacto documental `docs/CICD.md` y el workflow físico `.github/workflows/ci.yml` han sido generados y certificados sin violaciones de linter ni de TaskSpec.
- [ ] La totalidad de la suite de pruebas del arnés y de la aplicación se ejecuta con cero fallos (`exit_code == 0`).
