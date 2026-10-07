# SKILLS_WORKFLOW_AUDIT.md — Auditoría Crítica y Normalización del Workflow de Skills

> **Fecha:** 30 de septiembre de 2026  
> **Proyecto:** Arnés de Gobernanza para Desarrollo de Software Asistido por Agentes de IA  
> **Objetivo del Documento:** Auditar exhaustivamente las 12 skills existentes en `.agents/skills/`, analizar su coherencia como workflow de ingeniería para un coding agent, evaluar su potencial de control de alcance desde el PRD y proponer la arquitectura canónica de contratos antes de cualquier implementación.

---

## 1. Propósito General del Pipeline de 12 Skills

El catálogo de 12 skills fue concebido como la formalización procedimental del ciclo de vida del software (SDLC) para ser ejecutado por un modelo generativo bajo supervisión humana:

```text
01-prd ──► 02-architecture ──► 03-data-modeling ──► 04-api-design ──► 05-backend ──► 06-frontend
                                                                          │
  ┌───────────────────────────────────────────────────────────────────────┴───────────────────────┐
  ▼                                                                                               ▼
07-auth ────────────────► 08-testing ─────────────► 09-cicd ──► 10-deployment ──► 11-observability ──► 12-documentation
```

### Diagnóstico Sistémico: ¿Workflow o Colección de Prompts Aislados?
La auditoría revela que actualmente las 12 skills **operan como cuestionarios conversacionales aislados y no como un sistema de control de ingeniería integrado**:
1. **Pérdida de Contratos:** Cada skill asume que el contexto previo reside de forma difusa en la ventana de chat del modelo, sin verificar la presencia de artefactos físicos estructurados en disco.
2. **Re-interrogación Cíclica:** Skills posteriores vuelven a preguntar por decisiones que debieron quedar selladas en fases previas (por ejemplo, el stack tecnológico se interroga en `01-prd`, se re-evalúa en `02-architecture`, se vuelve a cuestionar en `03-data-modeling` y se pide definir nuevamente en `05-backend`).
3. **Ausencia de Fronteras Negativas:** Ninguna skill actual delimita de forma ejecutable qué está **fuera de alcance** (*Out-of-Scope*), permitiendo que el agente introduzca librerías, capas intermedias o abstracciones no autorizadas.
4. **Desconexión con la Validación:** Los criterios de aceptación definidos en `01-prd` no son consumidos programáticamente por `08-testing` ni por el `ValidationEngine`.

---

## 2. Auditoría Individual de las 12 Skills

A continuación se audita cada una de las 12 skills bajo las 8 dimensiones operativas requeridas:

---

### Skill 01: `prd-generation` (`.agents/skills/01-prd/SKILL.md`)
* **A. Propósito:** Delimitar el problema, objetivos, usuarios, casos de uso, restricciones técnicas y nivel de gobernanza de una nueva iniciativa o feature.
* **B. Inputs Requeridos:** Descripción en lenguaje natural del problema o necesidad del usuario/desarrollador.
* **C. Outputs Obligatorios:** `PRD.md` estructurado que incluya obligatoriamente una sección de frontera de alcance (`IN SCOPE` vs. `OUT OF SCOPE`) y criterios de aceptación verificables.
* **D. Preconditions:** Solicitud inicial de proyecto o requerimiento de cambio mayor. No debe haber un PRD contradictorio vigente.
* **E. Postconditions:** `PRD.md` generado, confirmado por el usuario y persistido en el repositorio como línea base inmutable para el ciclo actual.
* **F. Scope y Límites:**
  * *Puede decidir:* Estructura de requerimientos, clasificación de usuarios, priorización de casos de uso del MVP y nivel de gobernanza.
  * *NO puede decidir por sí sola:* Detalles de implementación de bajo nivel, ORMs específicos, patrones de base de datos ni sintaxis de endpoints.
* **G. Criterios de Verificación:**
  * *Deterministas:* El archivo `PRD.md` existe; contiene secciones obligatorias (`Problema`, `Casos de Uso`, `IN SCOPE`, `OUT OF SCOPE`, `Criterios de Aceptación`).
  * *De Juicio:* Claridad y relevancia de los requerimientos para resolver el problema expuesto.
* **H. Dependencias:**
  * *Precedentes:* Ninguna (punto de origen del workflow).
  * *Subsiguientes:* Alimenta a `02-architecture`, `03-data-modeling`, `04-api-design` y `08-testing`.

---

### Skill 02: `architecture-design` (`.agents/skills/02-architecture/SKILL.md`)
* **A. Propósito:** Definir el patrón estructural del sistema (monolito modular, capas), boundaries entre módulos, estilo de comunicación y organización de directorios.
* **B. Inputs Requeridos:** `PRD.md` (tipo de proyecto, escala estimada, restricciones, nivel de gobernanza).
* **C. Outputs Obligatorios:** `ARCHITECTURE.md` y/o registros de decisiones arquitectónicas (`docs/adr/001-patron-arquitectonico.md`).
* **D. Preconditions:** `PRD.md` formalmente aprobado y persistido.
* **E. Postconditions:** Capas lógicas, contratos de aislamiento entre componentes y estructura de directorios claramente normados.
* **F. Scope y Límites:**
  * *Puede decidir:* Patrón estructural (KISS/YAGNI), división de directorios y estilo general de interacción interna.
  * *NO puede decidir por sí sola:* Introducir patrones distribuidos complejos (microservicios, event-sourcing, colas) si el PRD estableció un MVP monolítico de baja escala.
* **G. Criterios de Verificación:**
  * *Deterministas:* Existencia de `ARCHITECTURE.md`; declaración unívoca de patrón (monolito, modular) y árbol de directorios permitido.
  * *De Juicio:* Si la arquitectura seleccionada es la más simple que satisface los requerimientos del PRD (adherencia a KISS).
* **H. Dependencias:**
  * *Precedentes:* `01-prd`.
  * *Subsiguientes:* `03-data-modeling`, `04-api-design`, `05-backend`, `10-deployment`.

---

### Skill 03: `data-modeling` (`.agents/skills/03-data-modeling/SKILL.md`)
* **A. Propósito:** Diseñar el modelo de dominio y persistencia: entidades, atributos, tipos de datos, relaciones de cardinalidad, claves foráneas e índices.
* **B. Inputs Requeridos:** `PRD.md` (casos de uso y datos involucrados), `ARCHITECTURE.md` (motor y estrategia de persistencia).
* **C. Outputs Obligatorios:** Esquema relacional o DDL (`schema.sql` o modelos base ORM) y diccionario de datos (`docs/data_model.md`).
* **D. Preconditions:** `PRD.md` y `ARCHITECTURE.md` aprobados.
* **E. Postconditions:** Toda entidad responde a un caso de uso del PRD; no existen tablas huérfanas; relaciones 1:N o N:M están tipadas con restricciones de nulidad e integridad.
* **F. Scope y Límites:**
  * *Puede decidir:* Nombres de campos, normalización (3NF), tipos de datos SQL, índices y claves primarias/foráneas.
  * *NO puede decidir por sí sola:* Inventar entidades de negocio no contempladas en el PRD ni cambiar el motor de persistencia acordado.
* **G. Criterios de Verificación:**
  * *Deterministas:* Archivo de esquema sintácticamente válido (compilable en SQLite/PostgreSQL); coincidencia de entidades con el PRD.
  * *De Juicio:* Eficiencia del modelado y normalización según el ratio de lectura/escritura declarado.
* **H. Dependencias:**
  * *Precedentes:* `01-prd`, `02-architecture`.
  * *Subsiguientes:* `04-api-design`, `05-backend`.

---

### Skill 04: `api-design` (`.agents/skills/04-api-design/SKILL.md`)
* **A. Propósito:** Definir el contrato de interfaz pública del sistema: endpoints, verbos HTTP, schemas DTO de entrada/salida, códigos de estado y manejo de errores.
* **B. Inputs Requeridos:** `PRD.md` (casos de uso y requerimientos de usuario), `ARCHITECTURE.md` (estilo REST/RPC), `docs/data_model.md` (entidades).
* **C. Outputs Obligatorios:** Especificación de API canónica (`docs/api_spec.md` o `openapi.json`/`openapi.yaml`).
* **D. Preconditions:** Modelo de datos validado y arquitectura de comunicación establecida.
* **E. Postconditions:** Cada endpoint documenta su URL, método HTTP, parámetros de ruta/query, payload JSON esperado, response 2xx/4xx/5xx y control de errores normalizado.
* **F. Scope y Límites:**
  * *Puede decidir:* Nomenclatura de endpoints (kebab-case plural), schemas de request/response y códigos HTTP estándar.
  * *NO puede decidir por sí sola:* Exponer datos sensibles en texto plano sin enmascarar (violando Ley 21.719 / CWE-532) ni agregar endpoints para acciones fuera del PRD.
* **G. Criterios de Verificación:**
  * *Deterministas:* Validador OpenAPI en verde (o parsing JSON/YAML válido); correspondencia biunívoca entre operaciones CRUD y entidades del modelo.
  * *De Juicio:* Usabilidad de la API y cumplimiento de principios RESTful.
* **H. Dependencias:**
  * *Precedentes:* `01-prd`, `02-architecture`, `03-data-modeling`.
  * *Subsiguientes:* `05-backend`, `06-frontend`, `08-testing`.

---

### Skill 05: `backend-implementation` (`.agents/skills/05-backend/SKILL.md`)
* **A. Propósito:** Construir el código ejecutable del servidor: routers, servicios de aplicación, repositorios de acceso a datos, validaciones y configuración.
* **B. Inputs Requeridos:** `PRD.md`, `ARCHITECTURE.md`, `data_model` y la especificación formal de `04-api-design`.
* **C. Outputs Obligatorios:** Código fuente backend ejecutable (`src/backend/`), manifiesto de dependencias (`requirements.txt` o `package.json`), configuración de entorno (`.env.example`).
* **D. Preconditions:** Especificación de API y modelo de persistencia aprobados y congelados.
* **E. Postconditions:** La aplicación backend compila e inicializa sin errores; todos los endpoints implementados respetan fielmente el schema de `04-api-design`.
* **F. Scope y Límites:**
  * *Puede decidir:* Lógica algorítmica interna, consultas a base de datos y librerías estándar auxiliares.
  * *NO puede decidir por sí sola:* Alterar las rutas de API acordadas, incorporar dependencias externas no autorizadas (violando `DependencyPolicy`), ni modificar entidades fuera del alcance autorizado por el `TaskSpec`.
* **G. Criterios de Verificación:**
  * *Deterministas:* Servidor inicia sin traceback; pruebas unitarias/integración pasan en `pytest`; el validador del arnés (`ValidationEngine`) emite `PASS` en `ScopePolicy` y `DependencyPolicy`.
  * *De Juicio:* Legibilidad del código, funciones de menos de 50 líneas, bajo acoplamiento (KISS/Clean Code).
* **H. Dependencias:**
  * *Precedentes:* `01` a `04`.
  * *Subsiguientes:* `06-frontend`, `07-auth`, `08-testing`, `10-deployment`.

---

### Skill 06: `frontend-implementation` (`.agents/skills/06-frontend/SKILL.md`)
* **A. Propósito:** Implementar la interfaz gráfica de usuario (SPA o multipágina), componentes visuales, navegación, gestión de estado y consumo de la API.
* **B. Inputs Requeridos:** `PRD.md` (casos de uso de usuario, roles) y `04-api-design` (contrato OpenAPI / endpoints).
* **C. Outputs Obligatorios:** Código fuente del frontend (`src/frontend/`), componentes, assets y configuración de build (`vite.config.ts`, etc.).
* **D. Preconditions:** Especificación de API congelada o endpoints backend disponibles (reales o simulados).
* **E. Postconditions:** El frontend compila/empaqueta sin errores (`build` exitoso); las llamadas HTTP del cliente coinciden exactamente con la especificación de `04-api-design`.
* **F. Scope y Límites:**
  * *Puede decidir:* Disposición visual de componentes, estilos CSS y manejo de estado local en la UI.
  * *NO puede decidir por sí sola:* Inventar endpoints inexistentes en el backend, ni bypasses de lógica de validación de negocio.
* **G. Criterios de Verificación:**
  * *Deterministas:* Proceso de build (`npm run build` o equivalente) finaliza con código 0; linter sin errores; cero llamadas HTTP a URLs no declaradas en la API.
  * *De Juicio:* Fidelidad estética, accesibilidad y experiencia de usuario.
* **H. Dependencias:**
  * *Precedentes:* `01-prd`, `04-api-design`, `05-backend`.
  * *Subsiguientes:* `08-testing`, `10-deployment`.

---

### Skill 07: `auth-security` (`.agents/skills/07-auth/SKILL.md`)
* **A. Propósito:** Implementar mecanismos de autenticación (JWT/sesiones), control de acceso basado en roles (RBAC), hashing robusto de credenciales y protección de endpoints.
* **B. Inputs Requeridos:** `PRD.md` (roles, nivel de gobernanza), `ARCHITECTURE.md` (estrategia de sesión), `04-api-design` (endpoints protegidos).
* **C. Outputs Obligatorios:** Middleware de autenticación/autorización, servicios de hashing (bcrypt/argon2id), decoradores o dependencias de seguridad por ruta.
* **D. Preconditions:** Backend básico y modelo de usuarios implementados. Solo se activa si la gobernanza es MEDIA o ALTA según el PRD.
* **E. Postconditions:** Los endpoints protegidos rechazan peticiones sin credenciales con HTTP 401/403; contraseñas nunca se persisten en texto plano; tokens tienen expiración acotada.
* **F. Scope y Límites:**
  * *Puede decidir:* Algoritmo de hashing específico (dentro de los estándares seguros), estructura de claims del token y validación de expiración.
  * *NO puede decidir por sí sola:* Desactivar la seguridad en endpoints sensibles para "simplificar pruebas" ni utilizar algoritmos inseguros o deprecados (MD5, SHA1).
* **G. Criterios de Verificación:**
  * *Deterministas:* Pruebas automatizadas de seguridad que certifiquen el rechazo de peticiones anónimas o con rol insuficiente; verificación de que no hay secrets hardcodeados.
  * *De Juicio:* Claridad de la jerarquía de roles y política de privilegios mínimos.
* **H. Dependencias:**
  * *Precedentes:* `01-prd`, `02-architecture`, `05-backend`.
  * *Subsiguientes:* `06-frontend`, `08-testing`, `11-observability`.

---

### Skill 08: `testing-strategy` (`.agents/skills/08-testing/SKILL.md`)
* **A. Propósito:** Definir el plan de aseguramiento de calidad e implementar las suites de pruebas automatizadas (unitarias, integración, endpoints) alineadas a los criterios de aceptación.
* **B. Inputs Requeridos:** `PRD.md` (criterios de aceptación funcionales y no funcionales), `04-api-design` (contratos), código en `05-backend` y `06-frontend`.
* **C. Outputs Obligatorios:** Suites de pruebas ejecutables (`tests/demo/`, `tests/harness/`), fixtures, configuración del test runner (`pytest.ini`).
* **D. Preconditions:** Código base implementado sujeto a verificación.
* **E. Postconditions:** Suite de pruebas automatizadas ejecuta al 100% en verde; cada criterio de aceptación del PRD tiene al menos una prueba asociada.
* **F. Scope y Límites:**
  * *Puede decidir:* Organización de fixtures, mocks y estrategias de test aisladas (patrón AAA).
  * *NO puede decidir por sí sola:* Reducir o eliminar aserciones para forzar el paso en verde de un test que falla; ni omitir pruebas críticas de negocio.
* **G. Criterios de Verificación:**
  * *Deterministas:* Ejecución de `pytest` con código de salida 0 (100% verde); reporte de cobertura sin fallos de regresión.
  * *De Juicio:* Significancia de los casos de prueba (evitar pruebas tautológicas que solo testeen mocks).
* **H. Dependencias:**
  * *Precedentes:* `01-prd`, `04-api-design`, `05-backend`, `07-auth`.
  * *Subsiguientes:* `09-cicd`, `ValidationEngine`.

---

### Skill 09: `ci-cd-pipeline` (`.agents/skills/09-cicd/SKILL.md`)
* **A. Propósito:** Automatizar la integración continua mediante pipelines que ejecuten linters, comprobaciones de tipo, suites de pruebas y quality gates ante cada commit o PR.
* **B. Inputs Requeridos:** `PRD.md` (gobernanza, plataforma CI preferida), `08-testing` (comandos exactos de ejecución de tests), `05-backend`/`06-frontend` (manifiestos).
* **C. Outputs Obligatorios:** Archivos de configuración de pipeline versionados (`.github/workflows/ci.yml`, etc.).
* **D. Preconditions:** Suite de pruebas automatizadas localmente verde y scripts de ejecución consolidados.
* **E. Postconditions:** El archivo de pipeline está syntácticamente validado y contiene los pasos de checkout, instalación de dependencias, linting y ejecución de tests.
* **F. Scope y Límites:**
  * *Puede decidir:* Caching de paquetes y división de stages/jobs para optimizar tiempo de ejecución.
  * *NO puede decidir por sí sola:* Desactivar quality gates que fallen ni inyectar secrets o tokens en texto plano dentro del repositorio.
* **G. Criterios de Verificación:**
  * *Deterministas:* Validación sintáctica del YAML (ej. `actionlint`); verificación de que las rutas y comandos invocados existen en el repositorio.
  * *De Juicio:* Eficiencia del pipeline y preservación de aislamiento en los entornos de ejecución efímeros.
* **H. Dependencias:**
  * *Precedentes:* `05-backend`, `08-testing`.
  * *Subsiguientes:* `10-deployment`.

---

### Skill 10: `deployment` (`.agents/skills/10-deployment/SKILL.md`)
* **A. Propósito:** Configurar la contenerización del software, orquestación local, gestión de variables de entorno seguras y health checks de infraestructura.
* **B. Inputs Requeridos:** `PRD.md` (infraestructura objetivo), `ARCHITECTURE.md` (componentes del sistema), código fuente en `05-backend` y `06-frontend`.
* **C. Outputs Obligatorios:** `Dockerfile` (multi-stage optimizado), `docker-compose.yml` (si aplica), `.env.example`, scripts de entrada (`entrypoint.sh`).
* **D. Preconditions:** Backend y frontend ejecutables y testeados.
* **E. Postconditions:** Los contenedores compilan limpiamente sin warnings de seguridad críticos; el servicio expone un endpoint de salud funcional.
* **F. Scope y Límites:**
  * *Puede decidir:* Base image ligera (slim/alpine), orden de capas para caching de build y configuración de puertos de escucha.
  * *NO puede decidir por sí sola:* Incorporar orquestadores pesados (Kubernetes, Swarm) cuando el PRD definió un despliegue simple; ni correr contenedores como `root` sin justificación técnica.
* **G. Criterios de Verificación:**
  * *Deterministas:* `docker build` exitoso con código 0; archivo `.env.example` contiene todas las variables requeridas sin valores secretos reales.
  * *De Juicio:* Tamaño mínimo de la imagen final y ausencia de herramientas de compilación innecesarias en la imagen de producción.
* **H. Dependencias:**
  * *Precedentes:* `02-architecture`, `05-backend`, `09-cicd`.
  * *Subsiguientes:* `11-observability`.

---

### Skill 11: `observability` (`.agents/skills/11-observability/SKILL.md`)
* **A. Propósito:** Instrumentar logging estructurado (JSON), recolección de métricas operativas (latencia, error rate) y salvaguarda contra fugas de información sensible en tiempo de ejecución.
* **B. Inputs Requeridos:** `PRD.md` (nivel de gobernanza y exigencias normativas como Ley 21.719), `05-backend` (código a instrumentar).
* **C. Outputs Obligatorios:** Módulos de logging estructurado, middlewares de inyección de `request_id`, endpoints `/health` y `/metrics`.
* **D. Preconditions:** Backend funcional con rutas y persistencia operativa.
* **E. Postconditions:** Todos los eventos de acceso y auditoría se registran con formato unificado; ninguna emisión en log expone identificadores directos ni datos de salud sin enmascarar (CWE-532).
* **F. Scope y Límites:**
  * *Puede decidir:* Niveles de log (`DEBUG`, `INFO`, `ERROR`) y formato de timestamp/campos de contexto técnico.
  * *NO puede decidir por sí sola:* Desactivar el enmascaramiento de datos personales ni imprimir payloads completos de solicitudes con información sensible.
* **G. Criterios de Verificación:**
  * *Deterministas:* Evaluación de `SensitiveLoggingPolicy` sobre todo el código modificado (cero violaciones CWE-532); endpoint `/health` responde con 200 OK.
  * *De Juicio:* Calidad del diagnóstico y facilidad para trazar una transacción de extremo a extremo sin saturar el almacenamiento de logs.
* **H. Dependencias:**
  * *Precedentes:* `01-prd`, `05-backend`, `07-auth`.
  * *Subsiguientes:* `12-documentation`, `PolicyEngine`.

---

### Skill 12: `documentation` (`.agents/skills/12-documentation/SKILL.md`)
* **A. Propósito:** Consolidar la documentación integral del proyecto: guía de inicio rápido (`README.md`), referencia de arquitectura, manual de desarrollo local y directivas de contribución.
* **B. Inputs Requeridos:** Artefactos generados por todas las etapas previas (`01` a `11`).
* **C. Outputs Obligatorios:** `README.md` estandarizado, `docs/architecture.md`, `docs/api.md`, `CONTRIBUTING.md`.
* **D. Preconditions:** Software implementado, suites de prueba aprobadas y despliegue configurado.
* **E. Postconditions:** El repositorio contiene documentación verídica, ejecutable y alineada exactamente con el código fuente real existente.
* **F. Scope y Límites:**
  * *Puede decidir:* Estructura pedagógica del README, diagramas Mermaid y ejemplos de uso de la API.
  * *NO puede decidir por sí sola:* Documentar endpoints o funcionalidades inexistentes (alucinación de documentación) ni omitir advertencias de seguridad o variables de entorno requeridas.
* **G. Criterios de Verificación:**
  * *Deterministas:* Linter de Markdown en verde; todas las rutas de archivo citadas en el `README.md` existen físicamente en el repositorio; comandos de instalación coinciden con los scripts reales.
  * *De Juicio:* Claridad expositiva y reproducibilidad para un desarrollador que se incorpora por primera vez al proyecto.
* **H. Dependencias:**
  * *Precedentes:* Todas las skills previas (`01` a `11`).
  * *Subsiguientes:* Cierre del ciclo de entrega del producto.

---

## 3. Matriz Input → Output → Dependencias → Verificación

| Skill | Inputs Obligatorios | Outputs Requeridos | Depende de | Alimenta a | Verificación Determinista | Verificación por Juicio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01 PRD** | Problema y visión del usuario | `PRD.md` (con Scope IN/OUT) | — | 02, 03, 04, 08 | Archivo existe + secciones requeridas | Relevancia y factibilidad del MVP |
| **02 Architecture** | `PRD.md` | `ARCHITECTURE.md`, ADRs | 01 | 03, 04, 05, 10 | Estructura de carpetas válida | Cumplimiento estricto de KISS/YAGNI |
| **03 Data Modeling** | `PRD.md`, `ARCHITECTURE.md` | DDL (`schema.sql`), Data Model | 01, 02 | 04, 05 | Sintaxis DDL compilable + claves válidas | Normalización y diseño relacional |
| **04 API Design** | `PRD.md`, `docs/data_model.md` | `openapi.json` o `docs/api_spec.md` | 01, 02, 03 | 05, 06, 08 | Validador OpenAPI 3.0 conforme | Cohesión RESTful y semántica HTTP |
| **05 Backend** | `04-api-design`, `data_model` | `src/backend/`, `requirements.txt` | 01, 02, 03, 04 | 06, 07, 08, 10 | Compilación OK + PolicyEngine PASS | Modularidad y funciones < 50 líneas |
| **06 Frontend** | `PRD.md`, `04-api-design` | `src/frontend/`, componentes UI | 01, 04, 05 | 08, 10 | `npm run build` exitoso (Exit Code 0) | Usabilidad y responsividad |
| **07 Auth** | `PRD.md` (Gobernanza), `04-api` | Middlewares auth, hashing seguro | 01, 02, 05 | 06, 08, 11 | Tests de rutas 401/403 en verde | Idoneidad de expiración de tokens |
| **08 Testing** | `PRD.md` (Criterios), API Spec, Code | `tests/`, `pytest.ini`, Test Plan | 01, 04, 05, 07 | 09, Validador | `pytest` 100% verde (Exit Code 0) | Significancia real de las aserciones |
| **09 CI/CD** | `PRD.md` (Plataforma), Tests | `.github/workflows/ci.yml` | 05, 08 | 10 | Linter de YAML (`actionlint`) en verde | Eficiencia de etapas y caching |
| **10 Deployment** | `ARCHITECTURE.md`, Backend/Front | `Dockerfile`, `docker-compose.yml` | 02, 05, 09 | 11 | `docker build` con éxito (Exit Code 0) | Imagen minimal (multi-stage) y segura |
| **11 Observability**| `PRD.md` (Gobernanza/Privacidad) | Logging JSON, `/health`, `/metrics` | 01, 05, 07 | 12, Validador | `SensitiveLoggingPolicy` (0 CWE-532) | Pertinencia de métricas y granularidad |
| **12 Documentation**| Artefactos de etapas 01 a 11 | `README.md`, `docs/architecture.md` | 01 a 11 | Entrega final | Enlaces y comandos ejecutables válidos | Claridad didáctica y completitud |

---

## 4. Dependencias y Tránsito de Información entre Skills

La orquestación revela tres fases secuenciales y una transversal:

```text
[FASE 1: CONTRATACIÓN Y DISEÑO FORMAL]
  01-prd ──► 02-architecture ──► 03-data-modeling ──► 04-api-design
   (Alcance)      (Patrón)           (Esquema)           (Contrato)
      │
      └────────────────────────────────────────────────────────┐ (Criterios de Aceptación)
                                                               ▼
[FASE 2: CONSTRUCCIÓN NUCLEAR]                        [FASE 3: ASEGURAMIENTO]
  05-backend ────────┬────────► 06-frontend             08-testing
      │              │                                     │
      ▼              ▼                                     ▼
   07-auth      10-deployment                           09-cicd
      │              │                                     │
      ▼              ▼                                     │
  11-observability ──┴─────────────────────────────────────┼──► 12-documentation
```

### Quiebres Críticos Detectados en el Tránsito:
1. **La Brecha PRD ↔ Testing:** Los criterios de aceptación formulados en `01-prd` se redactan en lenguaje natural y nunca se convierten en una lista tipada de casos que `08-testing` deba validar exhaustivamente.
2. **La Brecha API Design ↔ Frontend:** El frontend actualmente asume que "conoce" las rutas porque comparte sesión de chat, en lugar de consultar un archivo de contrato OpenAPI (`openapi.json`).
3. **El Teléfono Descompuesto del Stack:** `05-backend` y `06-frontend` no leen programáticamente el archivo de decisiones de `02-architecture`, permitiendo que el modelo proponga librerías prohibidas o incompatibles.

---

## 5. Problemas de Coherencia Detectados

La auditoría valida empíricamente los 5 problemas de orquestación advertidos:

* **Problema A (Desviación de Alcance en Backend):** En la práctica actual, al invocar `05-backend`, el agente añade servicios no solicitados (como capas intermedias de caché Redis, adaptadores de colas o utilidades accesorias) porque el prompt de la skill carece de una cláusula que restrinja la generación a las entidades listadas en el PRD.
* **Problema B (Contradicción Frontend vs. API):** `06-frontend` inventa rutas ad-hoc (por ejemplo, `POST /api/patients/search`) cuando `04-api-design` había definido estrictamente `GET /api/v1/patients?q=`. Esto ocurre por falta de un archivo de interfaz vinculante.
* **Problema C (Testing Desconectado de Criterios de Negocio):** `08-testing` genera pruebas genéricas sobre funciones triviales (tests tautológicos que prueban mocks de Python), omitiendo probar los casos de fallo o los límites establecidos en los criterios de aceptación del PRD.
* **Problema D (Contradicción de Infraestructura):** `10-deployment` genera un `docker-compose.yml` con servicios de bases de datos pesadas o balanceadores NGINX, contradiciendo la decisión de `01-prd` y `02-architecture` que establecía un MVP simple con persistencia local SQLite.
* **Problema E (Alucinación Documental):** `12-documentation` describe cómo configurar características que fueron explícitamente descartadas durante el diseño, o cita comandos bash que fallan en el sistema operativo del usuario (Windows PowerShell).

---

## 6. Riesgos de Scope Creep y Deriva del Proyecto

El *Scope Creep* (expansión descontrolada de alcance) se produce en los modelos generativos por tres factores estructurales identificados en las skills actuales:
1. **Instrucciones Positivas sin Límites Negativos:** Las skills le dicen al agente qué debe hacer, pero no le prohíben explícitamente lo que no debe hacer en esa etapa específica.
2. **Sesgo hacia la "Completitud Empresarial":** Al solicitar una entidad simple, el modelo asume por entrenamiento que "debe" incluir auditoría avanzada, soft-delete, eventos asíncronos y múltiples capas de indirección, violando el principio MVP y la Regla 2 de `AGENTS.md`.
3. **Falta de Trazabilidad entre Turnos:** Cuando el contexto crece, el modelo olvida la respuesta que el desarrollador dio tres turnos atrás respecto a "no usar dependencias externas", reintroduciendo paquetes en manifiestos.

---

## 7. Papel de `01-prd` como Origen y Frontera del Alcance

Para que el arnés pueda gobernar el desarrollo, la Skill 01 no puede limitarse a generar un texto descriptivo. **Debe actuar como la aduana de alcance del proyecto.**

### Frontera Contractual de Alcance:
La salida de `01-prd` debe obligatoriamente establecer la partición formal:

```markdown
### FRONTERA CONTRACTUAL DE ALCANCE (SCOPE BOUNDARY)

#### EN ALCANCE (IN SCOPE)
- Entidad Paciente: Registro y consulta por ID/RUT.
- Persistencia relacional local (SQLite).
- Endpoints REST: GET /patients/{id}, POST /patients.
- Validación básica de formato RUT (Módulo 11).

#### FUERA DE ALCANCE (OUT OF SCOPE) - PROHIBIDO EN ESTE SPRINT
- Persistencia en servidor externo o Docker.
- Autenticación OAuth / JWT (acordado MVP sin login en Turno 1).
- Notificaciones por correo electrónico o SMS.
- Caché externa (Redis, Memcached).
- Modificación de cualquier archivo en frontend/.
```

### Conexión Conceptual PRD ↔ Gobernanza del Arnés:
1. Los ítems de `IN SCOPE` determinan las rutas autorizadas en `TaskSpec.allowed_paths` y las entidades permitidas en el modelo de datos.
2. Los ítems de `OUT OF SCOPE` se traducen automáticamente en `TaskSpec.forbidden_paths`, `TaskSpec.forbidden_patterns` y restricciones evaluadas por `PolicyEngine`.
3. Si el agente intenta crear `src/backend/services/redis_cache.py`, el `ValidationEngine` detecta la infracción de alcance mediante `ScopePolicy` y rechaza la integración con un `Finding` de severidad `CRITICAL`.

---

## 8. Propuesta de Estructura Canónica para `SKILL.md`

Para transformar las directivas en un workflow uniforme y predecible para los agentes, cada archivo `SKILL.md` debe evolucionar a la siguiente estructura estándar:

```markdown
---
name: [identificador-kebab-case]
version: 2.1.0
stage: [1-spec | 2-design | 3-implementation | 4-assurance]
governance: [all | medium-high]
inputs:
  required_artifacts: [lista de archivos previos requeridos en disco]
outputs:
  produced_artifacts: [lista de archivos que deben ser generados]
---

# Overview
[Propósito técnico conciso y objetivo específico de la etapa]

# Use When (Condiciones de Activación)
[Cuándo se debe invocar esta skill y cuándo debe omitirse o posponerse]

# Preconditions (Estado Previo Requerido)
[Comprobaciones que deben cumplirse antes de permitir la ejecución]

# Inputs & Context (Entradas Formales)
[Artefactos y contratos que el agente debe cargar obligatoriamente como contexto]

# Outputs & Deliverables (Entregables Esperados)
[Archivos físicos concretos que deben quedar escritos y persistidos]

# Workflow (Pasos de Ejecución)
[Pasos secuenciales estrictos de preguntas y toma de decisiones trazables]

# Policies & Constraints (Restricciones Inviolables)
[Reglas duras de gobernanza que aplican específicamente a esta etapa]

# Red Flags (Antipatrones Prohibidos)
[Lista de errores comunes que el agente comete en esta etapa y debe evitar]

# Verification & Exit Criteria (Criterios de Cierre)
[Lista de verificación binaria para determinar objetivamente cuándo concluyó la skill]
```

---

## 9. Delimitación de Responsabilidades: Skill vs. TaskSpec vs. Motores del Arnés

Para evitar la mezcla de conceptos en la arquitectura del arnés, se define la siguiente separación estricta:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARQUITECTURA DE CONCEPTOS                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. SKILL            ► ¿CÓMO TRABAJAR?                                                  │
│                       Metodología de fase, preguntas procedimentales, guías de diseño  │
│                       y buenas prácticas del oficio de ingeniería.                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. TASKSPEC         ► ¿QUÉ TRABAJAR HOY?                                               │
│                       La asignación concreta: rutas autorizadas para esta tarea,       │
│                       archivos prohibidos, criterios de aceptación específicos y tests.│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. CONTEXT ENGINE   ► ¿CON QUÉ INFORMACIÓN?                                            │
│                       Extracción quirúrgica por AST/Grafo (símbolos exactos, DTOs,     │
│                       firmas de funciones) para evitar saturar tokens.                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. POLICY ENGINE    ► ¿QUÉ ESTÁ ESTRICTAMENTE PROHIBIDO?                               │
│                       Reglas deterministas duras: no fugas CWE-532, no goldplating     │
│                       de archivos, no dependencias inventadas, no borrado físico.      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. VALIDATION ENGINE► ¿CÓMO CERTIFICAR EL RESULTADO?                                  │
│                       Compuerta que coordina políticas + pytest, computa el veredicto  │
│                       (PASS/FAIL) y formula el feedback con la directiva correctiva.   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Análisis de Suficiencia del Actual `TaskSpec`

El contrato actual en `src/harness/contracts.py`:

```python
class TaskSpec(BaseModel):
    task_id: str
    goal: str
    category: Literal["bug_fix", "feature", "refactor", "compliance", "adversarial"]
    difficulty: Literal["low", "medium", "high"]
    allowed_paths: list[str]
    forbidden_paths: list[str]
    allowed_symbol_mutations: list[str]
    forbidden_patterns: list[str]
    constraints: list[str]
    acceptance_criteria: list[str]
    test_targets: list[str]
```

### Diagnóstico de Brechas para el Workflow Completo:
El `TaskSpec` actual es **suficiente para evaluar tareas de codificación atómicas**, pero para orquestar la transición entre las 12 skills requerirá (en fases posteriores) tres adiciones conceptuales:
1. `required_artifacts` (list[str]): Archivos previos que deben existir en disco antes de admitir la tarea (ej: `["docs/PRD.md", "docs/api_spec.md"]`).
2. `produced_artifacts` (list[str]): Archivos que la tarea debe haber generado o modificado obligatoriamente como entregable.
3. `skill_id` (str | None): Identificador de la skill metodológica asociada al ciclo actual de la tarea.

*Nota de gobernanza: No implementaremos estos campos de forma inmediata en código; se reservan para cuando el runner experimental lo requiera.*

---

## 11. Criterios de Verificación: Verificación Determinista vs. Juicio

No todo aspecto de la ingeniería de software puede ni debe reducirse a un script automatizado. La validación se divide limpiamente en:

### Verificaciones 100% Deterministas (Automatizables por el Arnés):
- **Existencia de Artefactos:** `PRD.md`, `schema.sql`, `openapi.json` existen en disco.
- **Conformidad Sintáctica:** El schema OpenAPI es válido; el DDL de SQL compila; el YAML de CI es parseable.
- **Perímetro de Archivos:** Cero archivos modificados fuera de `TaskSpec.allowed_paths`.
- **Integridad de Manifiestos:** No se agregaron dependencias en `requirements.txt` sin autorización.
- **Cumplimiento de Políticas de Código:** Cero llamadas a logging de depuración con tokens sensibles sin enmascarar (CWE-532).
- **Preservación Funcional:** `pytest` finaliza con código de salida 0 (100% de tests aprobados).

### Verificaciones por Juicio (Humano o Agente Revisor):
- **Calidad de Requerimientos:** Si el problema descrito en el PRD representa una necesidad genuina del usuario.
- **Elegancia Arquitectónica:** Si la separación de capas es limpia o si existe sobre-abstracción innecesaria.
- **Diseño de Interfaz:** Si la ergonomía de la API y la experiencia de usuario en frontend son intuitivas.
- **Completitud Semántica:** Si los casos de prueba cubren las intenciones sutiles del negocio más allá del código superficial.

---

## 12. Recomendación de Modificaciones Prioritarias en las Skills

Tras la auditoría exhaustiva, las 12 skills no requieren la misma urgencia de intervención. Se clasifican según su impacto en la gobernanza:

### Nivel 1: Reestructuración Urgente (Eje Central de Gobernanza)
1. **`01-prd`:** Debe incorporar de inmediato la sección obligatoria de frontera de alcance (`IN SCOPE` / `OUT OF SCOPE`) y formato canónico de criterios de aceptación.
2. **`04-api-design`:** Debe generar un artefacto de contrato vinculante (`openapi.json` o markdown estructurado) para evitar que frontend y backend diverjan.
3. **`08-testing`:** Debe transformarse de un cuestionario de "qué te gustaría testear" a un workflow riguroso que mapee cada criterio del PRD con un test ejecutable.

### Nivel 2: Normalización Media (Desacoplamiento y Prevención de Redundancia)
4. **`02-architecture`:** Eliminar re-preguntas del stack; emitir ADR formal y matriz de capas permitidas.
5. **`05-backend`:** Condicionar la implementación a leer los artefactos de API y modelo de datos sin formular preguntas de arquitectura ya resueltas.
6. **`03-data-modeling`:** Asegurar que el DDL sea compilable y verificado contra SQLite/PostgreSQL.
7. **`07-auth`:** Conectar directamente con el nivel de gobernanza del PRD para activarse solo cuando corresponde.

### Nivel 3: Ajustes Menores de Formato (Fases Accesorias)
8. **`06-frontend`:** Forzar consumo de la API congelada.
9. **`10-deployment`:** Forzar Docker multi-stage y validación de `.env.example`.
10. **`11-observability`:** Integrar de forma nativa con los detectores de CWE-532 del arnés.
11. **`09-cicd`:** Estandarizar workflows mínimos para pytest.
12. **`12-documentation`:** Checklist de verificación cruzada entre código real y README.

---

## 13. Secuencia Recomendada para la Normalización Gradual

Para avanzar sin generar desorden ni refactorizaciones masivas, la evolución canónica de las skills debe seguir estrictamente este orden:

```text
[FASE 1: CONTRATO DE ALCANCE]
  └── Normalizar 01-prd (Scope Boundary + Acceptance Criteria)

[FASE 2: CONTRATOS DE INTERFAZ Y COMPROBACIÓN]
  ├── Normalizar 04-api-design (Especificación de API vinculante)
  └── Normalizar 08-testing (Trazabilidad Criterios PRD -> Tests)

[FASE 3: IMPLEMENTACIÓN GOBERNADA]
  ├── Normalizar 02-architecture y 03-data-modeling
  └── Normalizar 05-backend (Alineado a TaskSpec y PolicyEngine)

[FASE 4: CAPAS ACCESORIAS Y OPERATIVAS]
  └── Normalizar 06, 07, 09, 10, 11 y 12
```

---
*Documento de auditoría y diagnóstico completado. Listo para revisión antes de iniciar cualquier modificación en el repositorio.*
