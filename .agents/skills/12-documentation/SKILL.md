---
name: documentation-generation
version: 2.0.0
stage: 11
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance, testing-strategy, cicd-automation, deployment-automation, observability-setup]
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
produces_artifact: [README.md, docs/SYSTEM_GUIDE.md]
description: Generación y consolidación de documentación técnica y operativa del sistema. Emite el README.md canónico y la Guía Integral del Sistema con la Matriz de Trazabilidad E2E a partir de los 9 contratos formalmente aprobados sin inventar requisitos ni alterar código fuente.
---

# Skill: Generación y Consolidación de Documentación Técnica (documentation-generation)

## 1. Overview
Esta skill diseña, consolida y emite la documentación técnica, arquitectónica y operativa definitiva del sistema.
En cumplimiento directo de la **Sección 19 de `plan.md`**, esta etapa se ubica en el cierre absoluto del workflow de desarrollo gobernado porque cuenta con acceso privilegiado a la totalidad de la información y decisiones consolidadas en las etapas precedentes.

Su directriz fundamental es la **Regla de Oro de la Fidelidad Documental (Zero Drift / Cero Alucinación)**:
> **La documentación debe reflejar con total exactitud los artefactos formalmente aprobados y el código validado en el repositorio, absteniéndose taxativamente de inventar requisitos, endpoints, dependencias o configuraciones ausentes en las etapas previas, y evitando convertirse en una fuente alternativa de verdad.**

Bajo esta premisa y respetando el nivel de gobernanza (**`governance_level: "bajo"`**):
- Sustituye la documentación legacy desalineada por el **`README.md` canónico** en la raíz del repositorio, proporcionando una guía operativa clara, reproducible y libre de dependencias fantasma.
- Emite como manual técnico de gobernanza **`docs/SYSTEM_GUIDE.md`**, consolidando la **Matriz de Trazabilidad End-to-End (E2E)** que une la cadena de custodia completa desde los requisitos del PRD hasta la observabilidad y el despliegue.
- Garantiza que cada comando documentado (instalación, arranque con Uvicorn, ejecución de pruebas con Pytest y despliegue en contenedor Docker) sea **100% reproducible y ejecutable**.
- Opera bajo una estricta delimitación de **TaskSpec**, restringiéndose exclusivamente a la emisión de archivos de documentación y prohibiendo la mutación de código en `src/`, pruebas en `tests/`, pipelines en `.github/` o manifiestos en `Dockerfile`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 11** del pipeline de desarrollo, inmediatamente después de haber validado y aprobado la estrategia de observabilidad y captura de evidencia en `11-observability` ([`docs/OBSERVABILITY.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/OBSERVABILITY.md)).
- Se utiliza para consolidar el conocimiento técnico acumulado y entregar las guías definitivas de operación y mantenimiento del sistema antes de certificar la finalización completa del ciclo de desarrollo.

---

## 3. Precondiciones
Para que esta skill pueda activarse, el repositorio debe contar con la totalidad de los 9 artefactos contractuales previos en estado formalmente aprobado (**`status: "APPROVED"`**):
1. [`docs/PRD.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md): Requisitos funcionales (`REQ-001` a `REQ-003`), criterios de aceptación (`AC-001` a `AC-006`) y alcance `OUT OF SCOPE`.
2. [`docs/ARCHITECTURE.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md): Decisiones estructurales (`AD-001` a `AD-007`) y topología monolítica modular.
3. [`docs/DATA_MODEL.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DATA_MODEL.md): Entidad `Product` (`ENT-001`), invariantes (`INV-001` a `INV-004`) y datos semilla (`SEED-001`).
4. [`docs/API_DESIGN.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/API_DESIGN.md): Endpoints `EP-001` y `EP-002`, esquema `DTO-ERR-001` y catálogo `ERR-001`, `ERR-002`, `ERR-500`.
5. [`docs/SECURITY.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md): Controles mínimos (`SEC-CTRL-001` a `SEC-CTRL-005`), prevención CWE-532 y modo anónimo (`SEC-DEC-001`).
6. [`docs/TEST_PLAN.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/TEST_PLAN.md): Estrategia de pruebas transversal, matriz bidireccional AC -> Test y cobertura al 100.0%.
7. [`docs/CICD.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/CICD.md): Flujo continuo GitHub Actions (`PIPE-001`) y compuertas de bloqueo `GATE-001` a `GATE-003`.
8. [`docs/DEPLOYMENT.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md): Unidad monolítica en Docker (`DEP-001`), usuario no-root `appuser` y sondeo `/health` (`HC-001`).
9. [`docs/OBSERVABILITY.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/OBSERVABILITY.md): Logging JSON a stdout (`LOG-001`), correlación `X-Request-ID` (`OBS-001`), cero PII (`OBS-002`) y métricas (`MET-001`, `MET-002`).
10. **Suite de Pruebas 100% en Verde:** Ejecución certificada de 135 tests deterministas en memoria.

---

## 4. Entradas
La skill consume de forma estricta y exhaustiva la síntesis de los contratos previos y el código físico:
- **Desde la Especificación de Producto y Negocio:**
  - `docs/PRD.md`: Requisitos del catálogo y carrito en cliente, cláusula de exclusión explícita (cero pasarelas de pago, cero registro de usuarios).
- **Desde la Arquitectura y Modelo de Datos:**
  - `docs/ARCHITECTURE.md` y `docs/DATA_MODEL.md`: Monolito modular desacoplado en Python 3.12 y SQLite embebido; retención del carrito en Web Storage del navegador (`localStorage`).
- **Desde la Capa de API y Seguridad:**
  - `docs/API_DESIGN.md` y `docs/SECURITY.md`: Endpoints REST bajo `/api/v1`, respuestas Fail-Fast con `DTO-ERR-001`, postura de seguridad anónima sin tokens ni contraseñas, y prevención de fugas CWE-532.
- **Desde la Estrategia de Pruebas y CI/CD:**
  - `docs/TEST_PLAN.md` y `docs/CICD.md`: Quality Gates deterministas y pipeline de integración continua.
- **Desde el Empaquetado y la Observabilidad:**
  - `docs/DEPLOYMENT.md` y `docs/OBSERVABILITY.md`: Manifiesto `Dockerfile` multi-stage, sondeo `GET /health` (`HC-001`) y formato JSON de eventos con trazabilidad mediante `X-Request-ID`.
- **Desde el Código Fuente en Repositorio:**
  - Rutas reales de archivos (`src/main.py`, `src/catalog/`, `src/frontend/`, `src/shared/`, `tests/`).

---

## 5. Taxonomía Formal
Toda referencia documental generada debe preservar y utilizar consistentemente la taxonomía canónica establecida en las etapas 01 a 11:
- **`REQ-xxx`**: Requisitos funcionales de producto (`REQ-001` Catálogo, `REQ-002` Búsqueda, `REQ-003` Carrito).
- **`AC-xxx`**: Criterios de aceptación verificables (`AC-001` a `AC-006`).
- **`AD-xxx`**: Decisiones arquitectónicas estructurales (`AD-001` Monolito, `AD-002` REST, `AD-003` Carrito en cliente, `AD-005` SQLite, `AD-006` Fail-Fast, `AD-007` Modo anónimo).
- **`ENT-xxx`**: Entidades del modelo de datos (`ENT-001` Product).
- **`INV-xxx`**: Invariantes de datos (`INV-001` a `INV-004`).
- **`EP-xxx`**: Endpoints de servidor (`EP-001` list_products, `EP-002` get_product_by_id).
- **`DTO-xxx`**: Esquemas de transferencia de datos (`DTO-PROD-RES-001`, `DTO-PROD-LIST-001`, `DTO-ERR-001`, `DTO-CART-001`).
- **`ERR-xxx`**: Códigos de error de negocio (`ERR-001`, `ERR-002`, `ERR-500`).
- **`SEC-xxx`**: Controles y decisiones de seguridad (`SEC-CTRL-001` a `005`, `SEC-DEC-001`).
- **`GATE-xxx`**: Compuertas de calidad de CI/CD (`GATE-001`, `GATE-002`, `GATE-003`).
- **`DEP-xxx`**: Directivas de despliegue (`DEP-001`).
- **`OBS-xxx` / `LOG-xxx` / `MET-xxx` / `HC-xxx`**: Directivas de observabilidad y telemetría (`OBS-001` a `003`, `LOG-001`, `MET-001`, `MET-002`, `HC-001`).

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición de Inventar o Revivir Tecnologías Descartadas:**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** documentar tecnologías ajenas al sistema aprobado, incluyendo:
     * Bases de datos externas en red: PostgreSQL, MySQL, MongoDB, Redis, DynamoDB.
     * Frameworks frontend ajenos: Vue.js, React, Angular, Svelte (el sistema es Vanilla HTML/CSS/JS).
     * Esquemas de autenticación ausentes: JWT, OAuth2, sesiones de usuario, contraseñas de admin (`admin@clinic.com`), tablas de usuarios o roles RBAC.
     * Pasarelas financieras: Stripe, PayPal, Webpay, procesamiento de pagos.
     * Endpoints de servidor inventados: `/carts`, `/checkout`, `/orders` o endpoints de escritura en catálogo (`POST`, `PUT`, `DELETE`).
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
   │ - Purgar la deuda técnica del "Clinical Governance System". │
   │ - Redactar el README.md canónico de 'catalogo-carrito-web'. │
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
   │ - Ejecutar suite de pruebas (135 tests en verde).           │
   └─────────────────────────────────────────────────────────────┘
```

---

## 8. Señales de Alerta
Si el agente exhibe alguna de las siguientes conductas, el arnés debe intervenir y detener la acción:
- Mantener o citar datos del README legacy (PostgreSQL, Vue, admin123, tokens JWT, fichas clínicas).
- Proponer instalar generadores de sitios estáticos (Docusaurus, MkDocs) para publicar la documentación.
- Documentar endpoints ficticios que no existan en `src/catalog/router.py` o en `docs/API_DESIGN.md`.
- Describir procesos manuales de despliegue que contradigan el `Dockerfile` oficial de producción (`DEP-001`).
- Modificar archivos fuera de `allowed_paths` (ej. tocar `src/main.py`, `tests/` o `.github/ci.yml`).

---

## 9. Contrato de Salida Formal: `README.md` y `docs/SYSTEM_GUIDE.md`

### A. Documento Principal de Entrada: `README.md` (Raíz del Repositorio)
Debe estructurarse obligatoriamente bajo las siguientes 9 secciones canónicas:
1. **Identidad del Sistema y Arquitectura Monolítica Liviana:** Título oficial, propósito del sistema y resumen del patrón modular desacoplado.
2. **Stack Tecnológico Oficial:** Detalle explícito de Python 3.12, FastAPI, SQLite con SQLAlchemy, Vanilla HTML5/CSS/JS y Docker.
3. **Requisitos de Entorno y Prerrequisitos:** Versiones requeridas de Python, Node.js y Docker.
4. **Guía Rápida de Despliegue con Contenedor Docker:** Comandos reproducibles `docker build`, `docker run` y verificación de `HC-001` sobre `/health`.
5. **Guía de Desarrollo y Ejecución Local Reproducible:** Setup de virtualenv, instalación de dependencias, inicialización de BD y comando `uvicorn src.main:app`.
6. **Ejecución de la Suite Completa de Pruebas:** Comandos para reproducir los 135 tests deterministas en verde.
7. **Referencia de Endpoints de Servidor:** Documentación de `EP-001`, `EP-002` y `HC-001` con sus esquemas y códigos de retorno.
8. **Observabilidad, Logging JSON y Trazabilidad por Request-ID:** Explicación del formato `LOG-001`, uso de `X-Request-ID` y consulta de logs en Docker.
9. **Índice y Navegación hacia las Especificaciones Formales en `docs/`:** Enlaces directos a los 9 documentos contractuales del proyecto.

### B. Manual Técnico Consolidado: `docs/SYSTEM_GUIDE.md`
Debe estructurarse obligatoriamente con el siguiente frontmatter YAML y 6 secciones canónicas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "bajo"
project_id: "catalogo-carrito-web"
total_stages: 12
last_audit: "YYYY-MM-DD"
---

# docs/SYSTEM_GUIDE.md — Guía Integral del Sistema y Gobernanza de Arquitectura

## 1. Propósito y Alcance Consolidado del Sistema (PRD)
Síntesis de identidad, objetivos comerciales, requisitos funcionales (REQ-001 a REQ-003) y límites inmutables de alcance.

## 2. Topología Arquitectónica y Componentes (Monolito Liviano)
Diagrama y descripción de componentes (COMP-001, COMP-002), decisiones estructurales (AD-001 a AD-007) y topología de red.

## 3. Modelo de Dominio y Persistencia (SQLite + Web Storage)
Detalle de la entidad Product (ENT-001), invariantes (INV-001 a INV-004), datos semilla (SEED-001) y retención del carrito en cliente.

## 4. Contrato de Integración REST y Manejo de Errores
Especificación de endpoints (EP-001, EP-002), envelopes DTO y taxonomía de errores Fail-Fast (ERR-001, ERR-002, ERR-500).

## 5. Postura de Seguridad Defensiva y Privacidad (CWE-532)
Auditoría de controles mínimos (SEC-CTRL-001 a 005), prevención estricta de fugas de datos en logs (CWE-532) y modo visitante anónimo.

## 6. Matriz Consolidada de Trazabilidad End-to-End (Etapas 01 a 12)
Tabla exhaustiva que traza biunívocamente cada requisito desde PRD hasta Documentation uniendo las 12 etapas gobernadas.
```

---

## 10. Verificación del Artefacto
El arnés valida el cumplimiento mediante pruebas deterministas en `tests/harness/test_documentation_skill.py`:
1. **Sincronización y Simetría:** Paridad idéntica entre `.agents/skills/12-documentation/SKILL.md` y `harness/skills/12_documentation.md`.
2. **Esquema de Frontmatter:** Validación de `version: 2.0.0`, `stage: 11`, `governance: all`, dependencias upstream completas y artefactos producidos.
3. **Estructura Canónica:** Presencia de las 11 secciones normativas en la skill.
4. **Reglas Anti-Amnesia:** Detección y bloqueo de tecnologías descartadas (PostgreSQL, Vue, JWT, RBAC, etc.).
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
