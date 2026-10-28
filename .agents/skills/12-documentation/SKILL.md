---
name: documentation-generation
version: 2.0.0
stage: 11
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance, testing-strategy, cicd-automation, deployment-automation, observability-setup]
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
produces_artifact: [README.md, docs/SYSTEM_GUIDE.md]
description: Generación y consolidación de documentación técnica y operativa del sistema. Emite el README.md canónico y la Guía Integral del Sistema con la Matriz de Trazabilidad E2E a partir de los contratos upstream formalmente aprobados y del código validado, sin inventar requisitos ni alterar código fuente.
---

# Skill: Generación y Consolidación de Documentación Técnica (documentation-generation)

## 1. Overview
Esta skill diseña, consolida y emite la documentación técnica, arquitectónica y operativa definitiva del sistema.
En cumplimiento directo de la **Sección 19 de `plan.md`**, esta etapa se ubica en el cierre absoluto del workflow de desarrollo gobernado porque cuenta con acceso privilegiado a la totalidad de la información y decisiones consolidadas en las etapas precedentes.

Su directriz fundamental es la **Regla de Oro de la Fidelidad Documental (Zero Drift / Cero Alucinación)**:
> **La documentación debe reflejar con total exactitud los artefactos formalmente aprobados y el código validado en el repositorio, absteniéndose taxativamente de inventar requisitos, endpoints, dependencias o configuraciones ausentes en las etapas previas, y evitando convertirse en una fuente alternativa de verdad.**

Bajo esta premisa y respetando el nivel de gobernanza heredado de `docs/PRD.md` (**`governance_level`**):
- Sustituye la documentación legacy desalineada por el **`README.md` canónico** en la raíz del repositorio, proporcionando una guía operativa clara, reproducible y libre de dependencias fantasma.
- Emite como manual técnico de gobernanza **`docs/SYSTEM_GUIDE.md`**, consolidando la **Matriz de Trazabilidad End-to-End (E2E)** que une la cadena de custodia completa desde los requisitos del PRD hasta la observabilidad y el despliegue.
- Garantiza que cada comando documentado (instalación, arranque local, ejecución de pruebas y despliegue) sea **100% reproducible y ejecutable**, y que coincida exactamente con los comandos validados en el repositorio y en los contratos aprobados.
- Opera bajo una estricta delimitación de **TaskSpec**, restringiéndose exclusivamente a la emisión de archivos de documentación y prohibiendo la mutación de código en `src/`, pruebas en `tests/`, pipelines en `.github/` o manifiestos en `Dockerfile`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 11** del pipeline de desarrollo, inmediatamente después de haber validado y aprobado la estrategia de observabilidad y captura de evidencia en `11-observability` ([`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md)).
- Se utiliza para consolidar el conocimiento técnico acumulado y entregar las guías definitivas de operación y mantenimiento del sistema antes de certificar la finalización completa del ciclo de desarrollo.

---

## 3. Precondiciones
Para que esta skill pueda activarse, el repositorio debe contar con la totalidad de los 9 artefactos contractuales previos en estado formalmente aprobado (**`status: "APPROVED"`**):
1. [`docs/PRD.md`](docs/PRD.md): Requisitos funcionales (`REQ-xxx`), criterios de aceptación (`AC-xxx`), `project_id`, `governance_level` y alcance `OUT OF SCOPE`.
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Decisiones estructurales (`AD-xxx`), componentes (`COMP-xxx`), stack aprobado, alternativas descartadas y topología del sistema.
3. [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md): Entidades (`ENT-xxx`), invariantes (`INV-xxx`), datos semilla (`SEED-xxx`, si aplica) y localización del estado (servidor o cliente).
4. [`docs/API_DESIGN.md`](docs/API_DESIGN.md): Endpoints o interfaces aprobados (`EP-xxx`), esquemas `DTO-xxx` (incluido el esquema de error) y códigos de error de negocio (`ERR-xxx`).
5. [`docs/SECURITY.md`](docs/SECURITY.md): Controles (`SEC-CTRL-xxx`), decisiones de seguridad (`SEC-DEC-xxx`), modelo de acceso aprobado y prevención de fugas de datos sensibles en logs (CWE-532).
6. [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md): Estrategia de pruebas transversal, matriz bidireccional AC -> Test y umbral de cobertura aprobado.
7. [`docs/CICD.md`](docs/CICD.md): Pipeline de integración continua (`PIPE-xxx`) y compuertas de bloqueo (`GATE-xxx`).
8. [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Unidad de despliegue (`DEP-xxx`), postura de ejecución del contenedor y sondeo de salud (`HC-xxx`).
9. [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md): Formato de logging (`LOG-xxx`), directivas de correlación y privacidad (`OBS-xxx`) y métricas (`MET-xxx`).
10. **Suite de Pruebas 100% en Verde:** Ejecución certificada de la suite determinista completa definida en `docs/TEST_PLAN.md`, sin fallos.

Si alguna etapa no aplica al `project_type` del proyecto, el artefacto aprobado correspondiente debe declararlo explícitamente; la documentación lo refleja como "No aplica" con su justificación, nunca lo omite ni lo rellena con contenido inventado.

---

## 4. Entradas
La skill consume de forma estricta y exhaustiva la síntesis de los contratos previos y el código físico:
- **Desde la Especificación de Requisitos y Negocio:**
  - `docs/PRD.md`: Requisitos funcionales aprobados, criterios de aceptación y cláusula de exclusión explícita (`OUT OF SCOPE`), que delimita todo lo que la documentación no puede describir como capacidad del sistema.
- **Desde la Arquitectura y Modelo de Datos:**
  - `docs/ARCHITECTURE.md` y `docs/DATA_MODEL.md`: Topología aprobada, stack tecnológico oficial, motor de persistencia y localización sellada del estado (servidor o cliente).
- **Desde la Capa de API y Seguridad:**
  - `docs/API_DESIGN.md` y `docs/SECURITY.md`: Endpoints o interfaces aprobados con su prefijo de versión, esquema de error, postura de autenticación y autorización aprobada, y prevención de fugas CWE-532.
- **Desde la Estrategia de Pruebas y CI/CD:**
  - `docs/TEST_PLAN.md` y `docs/CICD.md`: Quality Gates deterministas, comandos de prueba y pipeline de integración continua.
- **Desde el Empaquetado y la Observabilidad:**
  - `docs/DEPLOYMENT.md` y `docs/OBSERVABILITY.md`: Manifiesto de despliegue aprobado, sondeo de salud (`HC-xxx`) y formato de eventos con su mecanismo de correlación.
- **Desde el Código Fuente en Repositorio:**
  - Rutas reales de archivos (`src/main.py`, `src/<bounded_context>/`, `src/shared/`, `tests/`), verificadas en disco antes de ser citadas.

---

## 5. Taxonomía Formal
Toda referencia documental generada debe preservar y utilizar consistentemente la taxonomía canónica establecida en las etapas 01 a 11. Los identificadores se citan exactamente como fueron definidos en el artefacto aprobado que los origina; la documentación nunca crea, renumera ni redefine IDs:
- **`REQ-xxx`**: Requisitos funcionales definidos en `docs/PRD.md`.
- **`AC-xxx`**: Criterios de aceptación verificables definidos en `docs/PRD.md`.
- **`AD-xxx`**: Decisiones arquitectónicas estructurales definidas en `docs/ARCHITECTURE.md`.
- **`ENT-xxx`**: Entidades del modelo de datos definidas en `docs/DATA_MODEL.md`.
- **`INV-xxx`**: Invariantes de datos definidas en `docs/DATA_MODEL.md`.
- **`EP-xxx`**: Endpoints o interfaces de servidor definidos en `docs/API_DESIGN.md`.
- **`DTO-xxx`**: Esquemas de transferencia de datos definidos en `docs/API_DESIGN.md`, incluido el esquema de error.
- **`ERR-xxx`**: Códigos de error de negocio definidos en `docs/API_DESIGN.md`.
- **`SEC-xxx`**: Controles (`SEC-CTRL-xxx`) y decisiones (`SEC-DEC-xxx`) de seguridad definidos en `docs/SECURITY.md`.
- **`GATE-xxx`**: Compuertas de calidad de CI/CD definidas en `docs/CICD.md`.
- **`DEP-xxx`**: Directivas de despliegue definidas en `docs/DEPLOYMENT.md`.
- **`OBS-xxx` / `LOG-xxx` / `MET-xxx` / `HC-xxx`**: Directivas de observabilidad y telemetría definidas en `docs/OBSERVABILITY.md` y `docs/DEPLOYMENT.md`.

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición de Inventar o Revivir Tecnologías Descartadas:**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** documentar tecnologías, capacidades o componentes ausentes en los artefactos `APPROVED` o en el código validado, incluyendo:
     * Motores de persistencia, frameworks o librerías que no figuren en el stack aprobado de `docs/ARCHITECTURE.md`, o que figuren como alternativas descartadas.
     * Esquemas de autenticación, autorización, usuarios o roles que no estén aprobados en `docs/SECURITY.md`.
     * Capacidades declaradas en `OUT OF SCOPE` en `docs/PRD.md`; solo pueden mencionarse dentro de una cláusula explícita de exclusión.
     * Endpoints, entidades u operaciones que no existan en `docs/API_DESIGN.md`, `docs/DATA_MODEL.md` o en el código (incluidas operaciones de escritura cuando el contrato aprobado es de solo lectura).
     * Credenciales, secretos o datos heredados de documentación legacy.
2. **Prohibición de Generadores de Sitios y Herramientas Pesadas (No-Goldplating):**
   - Prohibido configurar o exigir herramientas pesadas de documentación como Docusaurus, MkDocs, GitBook, Sphinx, Confluence o portales SaaS externos.
   - Toda la documentación debe residir en archivos Markdown estándar de GitHub (`README.md` y `docs/*.md`).
3. **Fidelidad y Cero Divergencia:**
   - La documentación no puede contradecir ninguna directiva de los documentos aprobados en `docs/`.
4. **Delimitación de Perímetro (TaskSpec):**
   ```yaml
   task_spec:
     allowed_paths:
       - "README.md"
       - "docs/SYSTEM_GUIDE.md"
     forbidden_paths:
       - "src/**"
       - "tests/**"
       - ".github/**"
       - "Dockerfile"
       - ".dockerignore"
   ```

---

## 7. Workflow de Implementación (Flujo Reproducible)

La consolidación documental sintetiza los 9 contratos previos en una guía integral coherente:

```text
    [ 9 Contratos Aprobados en docs/ + Código Fuente Validado ]
                               │
                               ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 1: Extracción de Evidencia y Linaje Contractual        │
   │ - Recopilar requisitos, decisiones, endpoints y directivas. │
   │ - Extraer comandos físicos validados de instalación y test. │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 2: Sustitución del README.md en la Raíz                │
   │ - Purgar contenido legacy desalineado con los contratos.    │
   │ - Redactar el README.md canónico de '<project_id>'.         │
   │ - Documentar guía rápida, Docker, local, tests y endpoints. │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 3: Emisión de docs/SYSTEM_GUIDE.md                     │
   │ - Redactar el manual técnico integral del sistema.          │
   │ - Construir la Matriz Consolidada de Trazabilidad E2E       │
   │   (mapeo exhaustivo de las etapas 01 a 12).                 │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 4: Verificación Determinista y Certificación Final     │
   │ - Ejecutar linter lint_documentation_contract.              │
   │ - Ejecutar la suite completa de pruebas (100% en verde).    │
   └─────────────────────────────────────────────────────────────┘
```

---

## 8. Señales de Alerta
Si el agente exhibe alguna de las siguientes conductas, el arnés debe intervenir y detener la acción:
- Mantener o citar datos del README legacy (tecnologías descartadas, credenciales, dominios ajenos al sistema aprobado).
- Proponer instalar generadores de sitios estáticos (Docusaurus, MkDocs) para publicar la documentación.
- Documentar endpoints ficticios que no existan en el router del contexto acotado (`src/<bounded_context>/router.py`) o en `docs/API_DESIGN.md`.
- Describir procesos manuales de despliegue que contradigan el `Dockerfile` oficial de producción (`DEP-xxx`).
- Citar comandos, rutas o conteos de pruebas que no se hayan verificado contra el repositorio.
- Modificar archivos fuera de `allowed_paths` (ej. tocar `src/main.py`, `tests/` o `.github/workflows/`).

---

## 9. Contrato de Salida Formal: `README.md` y `docs/SYSTEM_GUIDE.md`

### A. Documento Principal de Entrada: `README.md` (Raíz del Repositorio)
Debe estructurarse obligatoriamente bajo las siguientes 9 secciones canónicas:
1. **Identidad del Sistema y Arquitectura:** Título oficial, propósito del sistema y resumen del patrón arquitectónico aprobado en `docs/ARCHITECTURE.md`.
2. **Stack Tecnológico Oficial:** Detalle explícito del stack aprobado (lenguaje, framework, persistencia, interfaz y empaquetado), sin agregar tecnologías ausentes en los contratos.
3. **Requisitos de Entorno y Prerrequisitos:** Versiones requeridas de los runtimes y herramientas del stack aprobado.
4. **Guía Rápida de Despliegue con Contenedor Docker:** Comandos reproducibles `docker build`, `docker run` y verificación del sondeo de salud (`HC-xxx`) definidos en `docs/DEPLOYMENT.md`.
5. **Guía de Desarrollo y Ejecución Local Reproducible:** Preparación del entorno, instalación de dependencias, inicialización de la persistencia y comando exacto de arranque validado en el repositorio.
6. **Ejecución de la Suite Completa de Pruebas:** Comandos exactos para reproducir la suite determinista en verde definida en `docs/TEST_PLAN.md`.
7. **Referencia de Endpoints de Servidor:** Documentación de los `EP-xxx` aprobados y del sondeo `HC-xxx`, con sus esquemas y códigos de retorno.
8. **Observabilidad, Logging JSON y Trazabilidad por Request-ID:** Explicación del formato `LOG-xxx`, del mecanismo de correlación por request y de la consulta de logs en el entorno de ejecución.
9. **Índice y Navegación hacia las Especificaciones Formales en `docs/`:** Enlaces directos a los 9 documentos contractuales del proyecto.

### B. Manual Técnico Consolidado: `docs/SYSTEM_GUIDE.md`
Debe estructurarse obligatoriamente con el siguiente frontmatter YAML y 6 secciones canónicas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "<bajo | medio | alto>"  # heredado de docs/PRD.md
project_id: "<project_id>"                 # heredado de docs/PRD.md
total_stages: 12
last_audit: "YYYY-MM-DD"
---

# docs/SYSTEM_GUIDE.md — Guía Integral del Sistema y Gobernanza de Arquitectura

## 1. Propósito y Alcance Consolidado del Sistema (PRD)
Síntesis de identidad, objetivos de negocio, requisitos funcionales (REQ-xxx) y límites inmutables de alcance (OUT OF SCOPE).

## 2. Topología Arquitectónica y Componentes
Diagrama y descripción de componentes (COMP-xxx), decisiones estructurales (AD-xxx) y topología de red.

## 3. Modelo de Dominio y Persistencia
Detalle de las entidades (ENT-xxx), invariantes (INV-xxx), datos semilla (SEED-xxx, si aplica) y localización del estado (servidor o cliente).

## 4. Contrato de Integración REST y Manejo de Errores
Especificación de endpoints (EP-xxx), envelopes DTO-xxx y taxonomía de errores de negocio (ERR-xxx).

## 5. Postura de Seguridad Defensiva y Privacidad (CWE-532)
Auditoría de controles (SEC-CTRL-xxx), prevención estricta de fugas de datos en logs (CWE-532) y modelo de acceso aprobado.

## 6. Matriz Consolidada de Trazabilidad End-to-End (Etapas 01 a 12)
Tabla exhaustiva que traza biunívocamente cada requisito desde PRD hasta Documentation uniendo las 12 etapas gobernadas.
```

---

## 10. Verificación del Artefacto
El arnés valida el cumplimiento mediante pruebas deterministas en `tests/harness/test_documentation_skill.py`:
1. **Sincronización y Simetría:** Paridad idéntica entre `.agents/skills/12-documentation/SKILL.md` y `harness/skills/12_documentation.md`.
2. **Esquema de Frontmatter:** Validación de `version: 2.0.0`, `stage: 11`, `governance: all`, dependencias upstream completas y artefactos producidos.
3. **Estructura Canónica:** Presencia de las 11 secciones normativas en la skill.
4. **Reglas Anti-Amnesia:** Detección y bloqueo de tecnologías descartadas o ausentes en los contratos aprobados.
5. **Auditoría Anti-Goldplating:** Bloqueo de generadores pesados externos (Docusaurus, MkDocs, GitBook).
6. **Delimitación de TaskSpec:** Validación de límites perimetrales estrictos (`README.md` y `docs/SYSTEM_GUIDE.md` permitidos; `src/**`, `tests/**`, `.github/**`, `Dockerfile` prohibidos).
7. **Matriz de Trazabilidad E2E:** Verificación de que la especificación prescribe y valida la cobertura de las 12 etapas en la matriz.
8. **Linter Determinista:** Ejecución de `lint_documentation_contract` sobre los artefactos generados.

---

## 11. Criterio de Término
La etapa de `documentation-generation` y el ciclo completo de normalización de las 12 skills se consideran concluidos cuando:
- [ ] La skill `documentation-generation` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/12-documentation/SKILL.md` y `harness/skills/12_documentation.md`.
- [ ] La suite determinista `tests/harness/test_documentation_skill.py` está implementada y pasa 100% en verde.
- [ ] El archivo `README.md` en la raíz del repositorio ha sido renovado fielmente reflejando el sistema real sin rastros legacy.
- [ ] El artefacto canónico `docs/SYSTEM_GUIDE.md` ha sido generado con su frontmatter y Matriz de Trazabilidad E2E completa.
- [ ] La totalidad de la suite de pruebas del arnés y de la aplicación se ejecuta con cero fallos (`exit_code == 0`).

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`, sistema web básico de catálogo comercial y carrito de compras), los principios metodológicos generales de esta skill se instancian de la siguiente forma:

### 1. Identidad y Gobernanza de la Demo
- `project_id: "catalogo-carrito-web"` y `governance_level: "bajo"`.
- Topología: monolito modular liviano desacoplado.
- Stack aprobado: Python 3.12, FastAPI, SQLite con SQLAlchemy (`AD-005`), Vanilla HTML5/CSS/JS y Docker; prerrequisitos de entorno: Python 3.12, Node.js LTS y Docker.
- Arranque local: `uvicorn src.main:app --port 8000`; pruebas con Pytest (`pytest tests/harness/ tests/catalog/ tests/frontend/ -v`); despliegue en contenedor Docker.
- Suite certificada: 135 tests deterministas en memoria, cobertura al 100.0%.
- Rutas reales de código citadas: `src/main.py`, `src/catalog/` (router en `src/catalog/router.py`), `src/frontend/`, `src/shared/`, `tests/`.

### 2. Artefactos Upstream Aprobados de la Demo
1. `docs/PRD.md`: Requisitos `REQ-001` a `REQ-003`, criterios `AC-001` a `AC-006`; requisitos del catálogo y carrito en cliente; exclusión explícita de pasarelas de pago y de registro de usuarios.
2. `docs/ARCHITECTURE.md`: Decisiones `AD-001` a `AD-007`, componentes `COMP-001` y `COMP-002`, topología monolítica modular.
3. `docs/DATA_MODEL.md`: Entidad `Product` (`ENT-001`), invariantes `INV-001` a `INV-004`, datos semilla `SEED-001`; SQLite embebido y retención del carrito en Web Storage del navegador (`localStorage`).
4. `docs/API_DESIGN.md`: Endpoints REST bajo `/api/v1` (`EP-001` list_products y `EP-002` get_product_by_id), esquema `DTO-ERR-001`, catálogo de errores `ERR-001`, `ERR-002`, `ERR-500`, respuestas Fail-Fast.
5. `docs/SECURITY.md`: Controles `SEC-CTRL-001` a `SEC-CTRL-005`, prevención CWE-532 y modo visitante anónimo (`SEC-DEC-001`), sin tokens ni contraseñas.
6. `docs/TEST_PLAN.md`: Matriz bidireccional AC -> Test y cobertura al 100.0%.
7. `docs/CICD.md`: Flujo GitHub Actions (`PIPE-001`) y compuertas `GATE-001` a `GATE-003`.
8. `docs/DEPLOYMENT.md`: Unidad monolítica en Docker (`DEP-001`), usuario no-root `appuser` y sondeo `GET /health` (`HC-001`) con `Dockerfile` multi-stage.
9. `docs/OBSERVABILITY.md`: Logging JSON a stdout (`LOG-001`), correlación `X-Request-ID` (`OBS-001`), cero PII (`OBS-002`), `OBS-003` y métricas `MET-001`, `MET-002`.

### 3. Glosario de IDs Instanciado en la Demo
- `REQ-001` Catálogo, `REQ-002` Búsqueda, `REQ-003` Carrito.
- `AD-001` Monolito, `AD-002` REST, `AD-003` Carrito en cliente, `AD-005` SQLite, `AD-006` Fail-Fast, `AD-007` Modo anónimo.
- `ENT-001` Product; `INV-001` a `INV-004`.
- `EP-001` list_products, `EP-002` get_product_by_id.
- `DTO-PROD-RES-001`, `DTO-PROD-LIST-001`, `DTO-ERR-001`, `DTO-CART-001`.
- `ERR-001`, `ERR-002`, `ERR-500`; `SEC-CTRL-001` a `005`, `SEC-DEC-001`; `GATE-001` a `GATE-003`; `DEP-001`; `OBS-001` a `003`, `LOG-001`, `MET-001`, `MET-002`, `HC-001`.

### 4. Anti-Amnesia Instanciada en la Demo
En la demo, el agente tiene prohibido documentar:
- Bases de datos externas en red: PostgreSQL, MySQL, MongoDB, Redis, DynamoDB (contradicen SQLite embebido `AD-005`).
- Frameworks frontend ajenos: Vue.js, React, Angular, Svelte (el sistema es Vanilla HTML/CSS/JS).
- Esquemas de autenticación ausentes: JWT, OAuth2, sesiones de usuario, contraseñas de admin (`admin@clinic.com`), tablas de usuarios o roles RBAC (contradicen el modo anónimo `AD-007`).
- Pasarelas financieras: Stripe, PayPal, Webpay, procesamiento de pagos (solo admitidas dentro de cláusulas `OUT OF SCOPE` / Exclusiones / Alternativas Descartadas).
- Endpoints de servidor inventados: `/carts`, `/checkout`, `/orders` o endpoints de escritura en catálogo (`POST`, `PUT`, `DELETE`); la API es 100% de solo lectura.
- Deuda del README legacy: "Clinical Governance System" con PostgreSQL, Vue, `admin123`, tokens JWT y fichas clínicas, que debe purgarse en la Fase 2.

### 5. Contrato de Salida Instanciado en la Demo
- `README.md`: Secciones con los tokens que el linter de la demo exige literalmente: `EP-001`, `EP-002`, `HC-001`, `DEP-001` y `uvicorn src.main:app`.
- `docs/SYSTEM_GUIDE.md`, frontmatter y encabezados usados en la demo:

```markdown
---
status: "APPROVED"
version: 1
governance_level: "bajo"
project_id: "catalogo-carrito-web"
total_stages: 12
last_audit: "YYYY-MM-DD"
---

## 1. Propósito y Alcance Consolidado del Sistema (PRD)
Síntesis de REQ-001 a REQ-003 y límites inmutables de alcance.

## 2. Topología Arquitectónica y Componentes (Monolito Liviano)
Componentes COMP-001, COMP-002 y decisiones AD-001 a AD-007.

## 3. Modelo de Dominio y Persistencia (SQLite + Web Storage)
Entidad Product (ENT-001), invariantes INV-001 a INV-004, datos semilla SEED-001 y retención del carrito en cliente.

## 4. Contrato de Integración REST y Manejo de Errores
EP-001, EP-002, DTO-ERR-001 y errores Fail-Fast ERR-001, ERR-002, ERR-500.

## 5. Postura de Seguridad Defensiva y Privacidad (CWE-532)
SEC-CTRL-001 a SEC-CTRL-005, prevención CWE-532 y modo visitante anónimo.

## 6. Matriz Consolidada de Trazabilidad End-to-End (Etapas 01 a 12)
```
