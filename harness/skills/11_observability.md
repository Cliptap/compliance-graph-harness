---
name: observability-setup
version: 2.0.0
stage: 10
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance, testing-strategy, cicd-automation, deployment-automation]
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
produces_artifact: [docs/OBSERVABILITY.md]
description: Implementación y gobernanza de observabilidad proporcional. Define logging estructurado en JSON hacia stdout, correlación de cada unidad de trabajo mediante un identificador de petición (X-Request-ID), auditoría de cero fuga de datos sensibles CWE-532, métricas de latencia y de códigos de resultado, y sondeo de salud sin goldplating de herramientas externas.
---

# Skill: Implementación y Gobernanza de Observabilidad (observability-setup)

## 1. Overview
Esta skill define, estandariza y gobierna la estrategia de observabilidad y captura de evidencia del sistema en tiempo de ejecución.
En cumplimiento directo de la **Sección 18 de `plan.md`**, la finalidad de la observabilidad dentro de este arnés no es acumular bitácoras sin criterio, sino capturar evidencia útil, estructurada y reproducible que responda taxativamente a la tríada fundamental:
> **¿Qué ocurrió, qué cambio o causa lo provocó y cómo puedo reproducirlo?**

Bajo el nivel de gobernanza sellado en `docs/PRD.md` (`governance_level`) y los principios universales de sobriedad arquitectónica (**KISS / YAGNI**):
- Implementa una arquitectura de **Logging Estructurado en JSON unilínea (`LOG-001`)** emitido exclusivamente a la salida estándar (`stdout`), adhiriéndose a las directivas de *Twelve-Factor App* para el entorno de ejecución sellado en `docs/DEPLOYMENT.md` (`DEP-xxx`).
- Garantiza la **Trazabilidad y Correlación Determinista (`OBS-001`)** mediante un identificador de correlación por unidad de trabajo: en servicios HTTP, el encabezado estándar `X-Request-ID`; en pipelines de datos o herramientas CLI, un identificador de ejecución (`run_id`/`job_id`) equivalente. Cada unidad de trabajo queda vinculada con su log operativo para permitir su reproducción inmediata (por ejemplo con `curl` o re-ejecutando el comando).
- Aplica la política de **Cero Fuga de Datos Personales o Sensibles (`OBS-002`)** en estricto cumplimiento del control `SEC-CTRL-004`, previniendo vulnerabilidades clasificadas como **CWE-532** y certificando total compatibilidad con el evaluador determinista `SensitiveLoggingPolicy`.
- Captura métricas operacionales mínimas calculadas en memoria por unidad de trabajo: latencia en milisegundos (`MET-001`, `duration_ms`), distribución de códigos de estado o de resultado y códigos de negocio (`MET-002`, `ERR-xxx`).
- Integra el sondeo de liveness del servicio sobre el endpoint o mecanismo de salud sellado en `docs/DEPLOYMENT.md` (`HC-xxx`).
- Prohíbe de forma tajante el goldplating de plataformas externas (Prometheus, Grafana, OpenTelemetry, Jaeger, Datadog o canales de alerta) que no estén respaldadas por una decisión arquitectónica sellada.
- Emite como artefacto canónico de gobernanza la especificación formal `docs/OBSERVABILITY.md`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 10** del pipeline de desarrollo, inmediatamente después de que el sistema ha formalizado su empaquetado y estrategia de despliegue en `10-deployment` (`docs/DEPLOYMENT.md` y sus artefactos de empaquetado).
- Se utiliza para establecer el estándar de instrumentación y emisión de evidencia reproducible del sistema antes de pasar a la consolidación documental final en `12-documentation`.
- Aplica a la verificación de las unidades de trabajo del sistema (peticiones REST, ejecuciones de jobs o comandos), al monitoreo de liveness en el entorno de ejecución y a la auditoría de seguridad en bitácoras.

---

## 3. Precondiciones
1. **Artefactos Previos Formalmente Aprobados:**
   - `docs/PRD.md` en estado `APPROVED`, declarando `governance_level`, el alcance `IN SCOPE` / `OUT OF SCOPE` y las restricciones sobre datos personales.
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, con las decisiones vinculantes (`AD-xxx`) que afectan a la observabilidad: topología (monolito o distribuida), transporte y prefijo de rutas, motor de persistencia, estrategia de manejo de errores, modelo de identidad/autenticación y localización del estado.
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con las entidades (`ENT-xxx`) e invariantes (`INV-xxx`) del dominio.
   - `docs/API_DESIGN.md` en estado `APPROVED` (cuando el proyecto expone una API), con los contratos de endpoints (`EP-xxx`), el esquema de error estructurado (`DTO-ERR-xxx`) y el catálogo de códigos de negocio (`ERR-xxx`).
   - `docs/SECURITY.md` en estado `APPROVED`, especificando el control de prevención de fugas CWE-532 (`SEC-CTRL-004`) y la política de secrets (`SEC-CTRL-xxx`, `SEC-DEC-xxx`).
   - `docs/DEPLOYMENT.md` en estado `APPROVED`, formalizando la directiva de despliegue (`DEP-xxx`) y el sondeo de salud (`HC-xxx`).
2. **Políticas Deterministas del Arnés Habilitadas:**
   - Evaluador `SensitiveLoggingPolicy` (en `src/harness/policy_engine.py`) operativo en el motor de políticas del arnés.
3. **Código Base Operativo y Estable:**
   - Suite de tests deterministas del proyecto ejecutándose 100% en verde.
   - Punto de entrada de la aplicación (por ejemplo `src/main.py`) operativo, con el sondeo de salud `HC-xxx` y los componentes de cada `<bounded_context>` montados.

---

## 4. Entradas
La skill consume estrictamente los siguientes contratos upstream:
- **Desde `docs/PRD.md`:**
  - `governance_level` sellado.
  - Alcance `OUT OF SCOPE`: conceptos excluidos que la observabilidad no debe instrumentar ni registrar (por ejemplo, categorías de datos personales que el sistema no debe capturar).
- **Desde `docs/ARCHITECTURE.md`:**
  - `AD-xxx` de topología: un sistema monolítico autónomo elimina la necesidad de tracing distribuido; solo una topología distribuida sellada lo justifica.
  - `AD-xxx` de transporte: protocolo y prefijo de rutas sobre los que se intercepta cada unidad de trabajo.
  - `AD-xxx` de manejo de errores: estrategia de respuestas estructuradas (por ejemplo Fail-Fast).
  - `AD-xxx` de identidad: modelo de autenticación/usuarios, que determina qué identificadores de actor pueden (o no) aparecer en logs.
- **Desde `docs/SECURITY.md`:**
  - `SEC-CTRL-004`: Prevención obligatoria de inserción de información sensible en bitácoras (CWE-532).
  - `SEC-DEC-xxx` / `SEC-CTRL-xxx`: Política de secrets y tokens de acceso.
- **Desde `docs/API_DESIGN.md`:**
  - Cada `EP-xxx` declarado (método, ruta y parámetros), que define las unidades de trabajo a instrumentar.
  - `DTO-ERR-xxx`: Estructura unificada de error (por ejemplo `error_code`, `message`, `detail`).
  - Mapeo de errores `ERR-xxx` a códigos de estado.
- **Desde `docs/DEPLOYMENT.md`:**
  - `DEP-xxx`: Plataforma y empaquetado de ejecución.
  - `HC-xxx`: Endpoint o mecanismo de liveness.
  - Destino de consumo de logs emitidos hacia `stdout` (por ejemplo el colector del runtime de contenedores).

---

## 5. Taxonomía Formal
Toda directiva, formato de evento, métrica o sondeo de salud definido por esta skill debe utilizar identificadores unívocos y trazables:
- **`OBS-xxx` (Observability Directive):** Directivas y políticas normativas de observabilidad:
  * `OBS-001`: "Trazabilidad y Correlación de Peticiones con Request-ID (propagación en header `X-Request-ID` o identificador de ejecución equivalente, y en el log)".
  * `OBS-002`: "Política de Cero Fuga de Datos Sensibles en Bitácoras (CWE-532 / SensitiveLoggingPolicy)".
  * `OBS-003`: "Arquitectura de Logging Estructurado JSON en Salida Estándar (Twelve-Factor App)".
- **`LOG-xxx` (Log Event Schema):** Especificación formal de esquema de eventos de bitácora:
  * `LOG-001`: "Esquema Canónico de Registro de Evento en JSON unilínea hacia `stdout`".
- **`MET-xxx` (Operational Metric):** Métricas de rendimiento y salud en memoria:
  * `MET-001`: "Latencia de Unidades de Trabajo en Milisegundos (`duration_ms`)".
  * `MET-002`: "Distribución y Conteo de Códigos de Estado o Resultado y Códigos de Error (`ERR-xxx`)".
- **`HC-xxx` (Health Check):** Directivas de sondeo de salud operativa:
  * `HC-001`: "Sondeo de Liveness sobre el endpoint o mecanismo de salud sellado en `docs/DEPLOYMENT.md`".

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición Estricta de Herramientas y Servicios Externos Pesados:**
   - Salvo que una decisión `AD-xxx` sellada en `docs/ARCHITECTURE.md` lo exija expresamente, el agente **TIENE ESTRICTAMENTE PROHIBIDO** proponer, configurar o incorporar:
     * Servidores o clientes de métricas: Prometheus (`prometheus_client`, `prom-client`), Pushgateway, StatsD.
     * Plataformas de visualización o dashboards: Grafana, Kibana, Chronograf.
     * Tracing distribuido: OpenTelemetry (`opentelemetry-api`, `opentelemetry-sdk`, `otel`), Jaeger, Zipkin, AWS X-Ray.
     * APMs o plataformas SaaS: Datadog, New Relic, Dynatrace, Sentry, Splunk, Elastic APM.
     * Canales externos de notificación o alertas: Webhooks de Slack, Discord, PagerDuty, OpsGenie o correo SMTP.
2. **Prohibición de Amnesia Contractual:**
   - Prohibido re-preguntar por decisiones ya selladas aguas arriba. La skill las lee del artefacto correspondiente y las aplica:
     * Motor de persistencia, topología, transporte y modelo de identidad: resueltos en los `AD-xxx` de `docs/ARCHITECTURE.md`.
     * Contratos de endpoints, esquema de error y códigos de negocio: resueltos en los `EP-xxx`, `DTO-ERR-xxx` y `ERR-xxx` de `docs/API_DESIGN.md`.
     * Endpoint o mecanismo de salud: resuelto en el `HC-xxx` de `docs/DEPLOYMENT.md`.
     * Nivel de gobernanza: resuelto en el `governance_level` de `docs/PRD.md`.
     * Secrets, autenticación y llaves criptográficas: resueltos en los `SEC-DEC-xxx` de `docs/SECURITY.md`.
     * Tracing distribuido: resuelto por el `AD-xxx` de topología; si el sistema es un monolito autónomo sin dependencias de red distribuidas, no procede.
   - Si una decisión requerida no está sellada aguas arriba, se registra como brecha y se devuelve a la etapa propietaria; no se resuelve dentro de esta skill.
3. **Cumplimiento Estricto de Privacidad y CWE-532:**
   - Ningún log puede contener tokens sensibles sin enmascarar (`rut`, `password`, `secret`, `token`, etc.). Toda emisión debe superar sin excepciones la evaluación determinista de `SensitiveLoggingPolicy`.
4. **Delimitación de Perímetro (TaskSpec):**
   El `TaskSpec` de la etapa autoriza únicamente el artefacto de observabilidad, el punto de entrada donde se monta la intercepción y las pruebas del contexto acotado instrumentado; prohíbe el código preexistente protegido, las capas propiedad de otras etapas, la CI y el empaquetado de despliegue:
   ```yaml
   task_spec:
     allowed_paths:
       - "docs/OBSERVABILITY.md"
       - "src/main.py"                    # Punto de entrada sellado de la aplicación
       - "tests/<bounded_context>/**"
     forbidden_paths:
       - "src/<preexisting_protected>/**" # Código preexistente protegido declarado en docs/ARCHITECTURE.md
       - "src/<other_layer>/**"           # Capas propiedad de otras etapas (por ejemplo frontend)
       - ".github/**"                     # Propiedad de 09-cicd
       - "Dockerfile"                     # Propiedad de 10-deployment
   ```

---

## 7. Workflow de Implementación (Flujo Reproducible)

El ciclo de observabilidad intercepta cada unidad de trabajo (petición HTTP, ejecución de job o comando) y emite evidencia determinista respondiendo a la Sección 18 de `plan.md`:

```text
    [ Unidad de Trabajo Entrante (HTTP Client / curl / Job / CLI) ]
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 1: Intercepción y Correlación (OBS-001)                │
   │ - Extraer encabezado 'X-Request-ID' (o id de ejecución).    │
   │ - Si no está presente, generar un UUIDv4 canónico.          │
   │ - Iniciar cronómetro de alta resolución (start_time).       │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 2: Ejecución de la Operación de Negocio                │
   │ - Enrutar hacia el EP-xxx declarado en docs/API_DESIGN.md   │
   │   (o hacia el paso del job/comando correspondiente).        │
   │ - Si ocurre error de validación o recurso no encontrado:    │
   │   Capturar DTO-ERR-xxx ('error_code', 'message', 'detail'). │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 3: Cómputo de Evidencia y Métricas (MET-001, MET-002)  │
   │ - Calcular duration_ms = (end_time - start_time) * 1000.    │
   │ - Determinar código de estado/resultado (2xx, 4xx, 5xx).    │
   │ - Determinar severidad de log:                              │
   │   * 2xx/3xx -> INFO                                         │
   │   * 4xx     -> WARNING                                      │
   │   * 5xx     -> ERROR                                        │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 4: Auditoría de Privacidad y Emisión JSON (LOG-001)    │
   │ - Sanitizar payload (garantía CWE-532 / OBS-002).           │
   │ - Construir payload JSON unilínea estandarizado.            │
   │ - Emitir a stdout (consumible por el runtime de DEP-xxx).   │
   │ - Adjuntar 'X-Request-ID' a la respuesta (o al resultado).  │
   └─────────────────────────────────────────────────────────────┘
```

Para proyectos sin transporte HTTP (pipelines de datos, herramientas CLI), los códigos de estado se sustituyen por los códigos de resultado o de salida declarados aguas arriba, manteniendo la misma correspondencia de severidad.

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir y bloquear la acción:
- Proponer instalar librerías externas de telemetría (`prometheus_client`, `opentelemetry`, `jaeger-client`, `datadog`).
- Loguear stack traces desnudas con rutas del sistema operativo o excepciones internas no sanitizadas sin estructuración JSON.
- Emitir variables o parámetros que contengan tokens sensibles (`rut`, `password`, `secret`, `token`) en texto plano hacia la consola (violación de `SensitiveLoggingPolicy` / CWE-532).
- Proponer configurar dashboards de Grafana o receptores de alertas en Slack/PagerDuty sin una decisión `AD-xxx` sellada que lo exija, especialmente en sistemas de bajo gobierno.
- Re-preguntar decisiones ya selladas aguas arriba (`AD-xxx`, `EP-xxx`, `HC-xxx`, `SEC-DEC-xxx`, `governance_level`).
- Extender `allowed_paths` en TaskSpec para mutar código en `src/`, `tests/` o `.github/` fuera del perímetro autorizado durante la emisión de la especificación de observabilidad.

---

## 9. Contrato de Salida Formal: `docs/OBSERVABILITY.md`

El documento emitido por esta skill debe respetar estrictamente el siguiente frontmatter YAML y las 6 secciones canónicas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "<governance_level sellado en docs/PRD.md>"
logging_format: "json"
log_sink: "stdout"
request_id_header: "X-Request-ID"
healthcheck_endpoint: "<endpoint de salud sellado en HC-xxx de docs/DEPLOYMENT.md>"
last_audit: "YYYY-MM-DD"
---

# docs/OBSERVABILITY.md — Especificación de Observabilidad y Captura de Evidencia

## 1. Identidad de Observabilidad y Principios de Evidencia
Definición de la arquitectura de evidencia conforme a la Sección 18 de plan.md. Respuesta explícita a la tríada "¿Qué ocurrió, qué cambio lo provocó y cómo puedo reproducirlo?" bajo OBS-003.

## 2. Arquitectura de Logging Estructurado JSON
Especificación formal de LOG-001 (esquema canónico de log en JSON unilínea hacia stdout). Definición de niveles de severidad (INFO, WARNING, ERROR) y atributos obligatorios (timestamp ISO 8601, level, request_id, method, path, status_code, duration_ms, message).

## 3. Trazabilidad y Correlación de Peticiones por Request-ID
Mecanismo OBS-001: generación y propagación determinista del identificador de correlación mediante el encabezado X-Request-ID (o identificador de ejecución equivalente) en solicitudes y respuestas. Procedimiento reproducible (por ejemplo con curl).

## 4. Auditoría de Seguridad y Cero Fuga de Datos Sensibles (CWE-532)
Directiva OBS-002: alineación obligatoria con SEC-CTRL-004 y SensitiveLoggingPolicy. Reglas de enmascaramiento ([redacted]) y prohibición absoluta de emisión de PII, credenciales o tokens en logs.

## 5. Métricas Operacionales Mínimas y Health Checks
Especificación de métricas en memoria: latencia de unidades de trabajo (MET-001, duration_ms), conteo de códigos de respuesta y errores de negocio (MET-002, ERR-xxx), y sondeo de liveness sobre el endpoint de salud sellado (HC-001).

## 6. Matriz de Linaje con PRD, Arquitectura, Seguridad, API y Despliegue
Mapeo de trazabilidad de directivas de observabilidad con PRD.md, ARCHITECTURE.md, SECURITY.md, API_DESIGN.md y DEPLOYMENT.md.
```

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_observability_skill.py`:
1. **Sincronización y Simetría:** Paridad idéntica byte a byte entre `.agents/skills/11-observability/SKILL.md` y `harness/skills/11_observability.md`.
2. **Esquema de Frontmatter:** Validación de `version: 2.0.0`, `stage: 10`, `governance: all`, dependencias upstream y artefacto producido `docs/OBSERVABILITY.md`.
3. **Estructura Canónica:** Presencia obligatoria de las 11 secciones normativas v2.0 en la skill.
4. **Reglas Anti-Amnesia:** Verificación de prohibición explícita de re-preguntar decisiones selladas aguas arriba (`AD-xxx`, `EP-xxx`, `HC-xxx`, `SEC-DEC-xxx`, `governance_level`).
5. **Auditoría Anti-Goldplating:** Detección y bloqueo de Prometheus, Grafana, Jaeger, Zipkin, OpenTelemetry, Datadog o webhooks de alerta.
6. **Delimitación de TaskSpec:** Validación perimetral estricta (`docs/OBSERVABILITY.md`, el punto de entrada y `tests/<bounded_context>/**` autorizados; código preexistente protegido, otras capas, `.github/**` y `Dockerfile` prohibidos).
7. **Auditoría de Privacidad CWE-532:** Evaluación de `SensitiveLoggingPolicy` sobre las especificaciones para garantizar cero tolerancia a fugas de PII o credenciales.
8. **Linter Determinista:** Ejecución del analizador sintáctico `lint_observability_contract` sobre `docs/OBSERVABILITY.md` (con comprobación condicional/skip si el archivo aún no ha sido generado en disco).

---

## 11. Criterio de Término
La etapa de `observability-setup` se considera formalmente concluida cuando:
- [ ] La skill `observability-setup` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/11-observability/SKILL.md` y `harness/skills/11_observability.md`.
- [ ] La suite determinista `tests/harness/test_observability_skill.py` está implementada y pasa 100% en verde.
- [ ] El artefacto canónico `docs/OBSERVABILITY.md` ha sido generado y certificado con cero violaciones de linter ni de TaskSpec.
- [ ] La totalidad de la suite de pruebas del arnés y de la aplicación se ejecuta con cero fallos (`exit_code == 0`).

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian de la siguiente forma:

### 1. Decisiones Upstream Selladas en la Demo
- **`docs/PRD.md`:** `governance_level: "bajo"`, modo visitante anónimo. `OUT OF SCOPE`: cero pasarelas de pago, cero cuentas de usuario, cero captura de PII.
- **`docs/ARCHITECTURE.md`:** Monolito modular (`AD-001`, elimina la necesidad de tracing distribuido entre microservicios), transporte HTTP REST en `/api/v1` (`AD-002`), almacenamiento del carrito en el cliente (`AD-003`), base relacional SQLite embebida (`AD-005`), manejo estructurado de errores Fail-Fast (`AD-006`) y modo visitante anónimo (`AD-007`).
- **`docs/DATA_MODEL.md`:** invariantes de catálogo `INV-001` a `INV-004`.
- **`docs/API_DESIGN.md`:**
  - `EP-001`: `GET /api/v1/products` (soporta parámetro de filtrado `q`).
  - `EP-002`: `GET /api/v1/products/{id}` (identificador numérico `id >= 1`).
  - `DTO-ERR-001`: Estructura unificada de error con `error_code`, `message`, `detail`.
  - Mapeo de errores: `ERR-001` (404 Not Found), `ERR-002` (400 Bad Request), `ERR-500` (500 Internal Error).
- **`docs/SECURITY.md`:** `SEC-CTRL-004` (CWE-532), cero secrets hardcodeados (`SEC-CTRL-003`) y cero secrets o tokens de acceso requeridos (`SEC-DEC-001`).
- **`docs/DEPLOYMENT.md`:** `DEP-001` contenedor Docker liviano (`Dockerfile`), `HC-001` liveness en `/health`, logs hacia `stdout` consumidos con `docker logs`.

### 2. Código Base de la Demo al Iniciar la Etapa
- Suite de 126 tests deterministas ejecutándose 100% en verde.
- Servidor FastAPI en `src/main.py` con endpoint `/health` y routers de catálogo montados.
- Evaluador `SensitiveLoggingPolicy` en `src/harness/policy_engine.py`.

### 3. Anti-Amnesia Instanciada en la Demo
- Prohibido re-preguntar por el motor de base de datos (resuelto: SQLite embebido `AD-005`).
- Prohibido re-preguntar por el endpoint de salud (resuelto: `/health` `HC-001`).
- Prohibido re-preguntar por el nivel de gobernanza (resuelto: `governance_level: "bajo"`).
- Prohibido re-preguntar por autenticación, usuarios o llaves criptográficas (resuelto: visitante anónimo `AD-007`, `SEC-DEC-001`).
- Prohibido re-preguntar por tracing distribuido (resuelto: el sistema es un monolito autónomo sin dependencias de red distribuidas `AD-001`).
- Prohibido re-preguntar por los endpoints de catálogo (`EP-001`, `EP-002`).
- Prohibido proponer dashboards de Grafana o alertas en Slack/PagerDuty para este MVP de bajo gobierno.

### 4. TaskSpec Concreto de la Demo
```yaml
task_spec:
  allowed_paths:
    - "docs/OBSERVABILITY.md"
    - "src/main.py"
    - "tests/catalog/**"
  forbidden_paths:
    - "src/backend/**"      # Preserva código clínico preexistente
    - "src/database/**"     # Preserva esquemas clínicos preexistentes
    - "src/frontend/**"     # Blindaje de separación de capas
    - ".github/**"
    - "Dockerfile"
```

### 5. Workflow Instanciado en la Demo
- FASE 2 enruta hacia los endpoints de catálogo (`/api/v1/products`, `EP-001` y `EP-002`); los errores de validación o no encontrado se capturan como `DTO-ERR-001`.
- FASE 3 determina el código HTTP entre 200, 400, 404 y 500.
- FASE 4 emite a `sys.stdout`, consumible por `docker logs`.

### 6. Frontmatter Esperado de `docs/OBSERVABILITY.md` en la Demo
```yaml
governance_level: "bajo"
logging_format: "json"
log_sink: "stdout"
request_id_header: "X-Request-ID"
healthcheck_endpoint: "/health"
```
