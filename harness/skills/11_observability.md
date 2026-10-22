---
name: observability-setup
version: 2.0.0
stage: 10
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance, testing-strategy, cicd-automation, deployment-automation]
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
produces_artifact: [docs/OBSERVABILITY.md]
description: Implementación y gobernanza de observabilidad proporcional. Define logging estructurado en JSON hacia stdout, correlación de peticiones por X-Request-ID, auditoría de cero fuga de datos sensibles CWE-532, métricas de latencia de endpoints y sondeo de salud sin goldplating de herramientas externas.
---

# Skill: Implementación y Gobernanza de Observabilidad (observability-setup)

## 1. Overview
Esta skill define, estandariza y gobierna la estrategia de observabilidad y captura de evidencia del sistema en tiempo de ejecución.
En cumplimiento directo de la **Sección 18 de `plan.md`**, la finalidad de la observabilidad dentro de este arnés no es acumular bitácoras sin criterio, sino capturar evidencia útil, estructurada y reproducible que responda taxativamente a la tríada fundamental:
> **¿Qué ocurrió, qué cambio o causa lo provocó y cómo puedo reproducirlo?**

Bajo el nivel de gobernanza asignado (`governance_level: "bajo"`) y los principios universales de sobriedad arquitectónica (**KISS / YAGNI**):
- Implementa una arquitectura de **Logging Estructurado en JSON unilínea (`LOG-001`)** emitido exclusivamente a la salida estándar (`sys.stdout`), adhiriéndose a las directivas de *Twelve-Factor App* para entornos contenerizados en Docker (`DEP-001`).
- Garantiza la **Trazabilidad y Correlación Determinista (`OBS-001`)** mediante el encabezado HTTP estándar `X-Request-ID`, vinculando cada petición entrante con su log operativo correspondiente para permitir la reproducción inmediata con herramientas de línea de comando (`curl`).
- Aplica la política de **Cero Fuga de Datos Personales o Sensibles (`OBS-002`)** en estricto cumplimiento del control `SEC-CTRL-004`, previniendo vulnerabilidades clasificadas como **CWE-532** y certificando total compatibilidad con el evaluador determinista `SensitiveLoggingPolicy`.
- Captura métricas operacionales mínimas calculadas en memoria por petición: latencia de endpoints en milisegundos (`MET-001`, `duration_ms`), distribución de códigos de estado HTTP y códigos de negocio (`MET-002`, `ERR-xxx`).
- Integra el sondeo de liveness del servicio mediante el endpoint nativo `/health` (`HC-001`).
- Prohíbe de forma tajante el goldplating de plataformas externas (Prometheus, Grafana, OpenTelemetry, Jaeger, Datadog o canales de alerta).
- Emite como artefacto canónico de gobernanza la especificación formal [`docs/OBSERVABILITY.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/OBSERVABILITY.md).

---

## 2. Cuándo Usar
- Se activa en la **Etapa 10** del pipeline de desarrollo, inmediatamente después de que el sistema ha formalizado su empaquetado y estrategia de despliegue en `10-deployment` ([`docs/DEPLOYMENT.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md) y [`Dockerfile`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/Dockerfile)).
- Se utiliza para establecer el estándar de instrumentación y emisión de evidencia reproducible del sistema antes de pasar a la consolidación documental final en `12-documentation`.
- Aplica a la verificación de peticiones REST, monitoreo de liveness en contenedores y auditoría de seguridad en bitácoras.

---

## 3. Precondiciones
1. **Artefactos Previos Formalmente Aprobados:**
   - [`docs/PRD.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md) en estado `APPROVED`, clasificando el proyecto con `governance_level: "bajo"` y modo visitante anónimo.
   - [`docs/ARCHITECTURE.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md) en estado `APPROVED`, con las decisiones vinculantes: Monolito modular (`AD-001`), transporte HTTP REST en `/api/v1` (`AD-002`), almacenamiento cliente (`AD-003`), base relacional SQLite embebida (`AD-005`), Fail-Fast (`AD-006`) y modo anónimo (`AD-007`).
   - [`docs/DATA_MODEL.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DATA_MODEL.md) en estado `APPROVED`, con invariantes de catálogo (`INV-001` a `INV-004`).
   - [`docs/API_DESIGN.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/API_DESIGN.md) en estado `APPROVED`, con contratos de endpoints (`EP-001`, `EP-002`), esquema de error estructurado (`DTO-ERR-001`) y catálogo de códigos de negocio (`ERR-001`, `ERR-002`, `ERR-500`).
   - [`docs/SECURITY.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md) en estado `APPROVED`, especificando el control de prevención de fugas CWE-532 (`SEC-CTRL-004`) y cero secrets hardcodeados (`SEC-CTRL-003`, `SEC-DEC-001`).
   - [`docs/DEPLOYMENT.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md) en estado `APPROVED`, formalizando la directiva `DEP-001` y el sondeo de liveness `HC-001` en `/health`.
2. **Políticas Deterministas del Arnés Habilitadas:**
   - Evaluador [`SensitiveLoggingPolicy`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/harness/policy_engine.py#L107-L199) operativo en el motor de políticas del arnés.
3. **Código Base Operativo y Estable:**
   - Suite de 126 tests deterministas ejecutándose 100% en verde.
   - Servidor FastAPI en [`src/main.py`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/main.py) con endpoint `/health` y routers de catálogo montados.

---

## 4. Entradas
La skill consume estrictamente los siguientes contratos upstream:
- **Desde `docs/PRD.md`:**
  - Nivel de gobernanza: `bajo`.
  - Alcance `OUT OF SCOPE`: Cero pasarelas de pago, cero cuentas de usuario, cero captura de PII.
- **Desde `docs/ARCHITECTURE.md`:**
  - `AD-001`: Monolito modular (elimina la necesidad de tracing distribuido entre microservicios).
  - `AD-002`: Transporte REST bajo `/api/v1`.
  - `AD-006`: Manejo estructurado de errores con respuestas Fail-Fast.
  - `AD-007`: Modo visitante anónimo.
- **Desde `docs/SECURITY.md`:**
  - `SEC-CTRL-004`: Prevención obligatoria de inserción de información sensible en bitácoras (CWE-532).
  - `SEC-DEC-001`: Cero secrets o tokens de acceso requeridos.
- **Desde `docs/API_DESIGN.md`:**
  - `EP-001`: `GET /api/v1/products` (soporta parámetro de filtrado `q`).
  - `EP-002`: `GET /api/v1/products/{id}` (identificador numérico `id >= 1`).
  - `DTO-ERR-001`: Estructura unificada de error con `error_code`, `message`, `detail`.
  - Mapeo de errores: `ERR-001` (404 Not Found), `ERR-002` (400 Bad Request), `ERR-500` (500 Internal Error).
- **Desde `docs/DEPLOYMENT.md`:**
  - `DEP-001`: Contenedor Docker liviano.
  - `HC-001`: Endpoint de liveness `/health`.
  - Emisión de logs hacia `stdout` para consumo directo por `docker logs`.

---

## 5. Taxonomía Formal
Toda directiva, formato de evento, métrica o sondeo de salud definido por esta skill debe utilizar identificadores unívocos y trazables:
- **`OBS-xxx` (Observability Directive):** Directivas y políticas normativas de observabilidad:
  * `OBS-001`: "Trazabilidad y Correlación de Peticiones con Request-ID (propagación en header `X-Request-ID` y log)".
  * `OBS-002`: "Política de Cero Fuga de Datos Sensibles en Bitácoras (CWE-532 / SensitiveLoggingPolicy)".
  * `OBS-003`: "Arquitectura de Logging Estructurado JSON en Salida Estándar (Twelve-Factor App)".
- **`LOG-xxx` (Log Event Schema):** Especificación formal de esquema de eventos de bitácora:
  * `LOG-001`: "Esquema Canónico de Registro de Evento HTTP en JSON unilínea hacia `stdout`".
- **`MET-xxx` (Operational Metric):** Métricas de rendimiento y salud en memoria:
  * `MET-001`: "Latencia de Peticiones HTTP en Milisegundos (`duration_ms`)".
  * `MET-002`: "Distribución y Conteo de Códigos de Estado HTTP y Códigos de Error (`ERR-xxx`)".
- **`HC-xxx` (Health Check):** Directivas de sondeo de salud operativa:
  * `HC-001`: "Sondeo de Liveness HTTP sobre `/health`".

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición Estricta de Herramientas y Servicios Externos Pesados:**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** proponer, configurar o incorporar:
     * Servidores o clientes de métricas: Prometheus (`prometheus_client`, `prom-client`), Pushgateway, StatsD.
     * Plataformas de visualización o dashboards: Grafana, Kibana, Chronograf.
     * Tracing distribuido: OpenTelemetry (`opentelemetry-api`, `opentelemetry-sdk`, `otel`), Jaeger, Zipkin, AWS X-Ray.
     * APMs o plataformas SaaS: Datadog, New Relic, Dynatrace, Sentry, Splunk, Elastic APM.
     * Canales externos de notificación o alertas: Webhooks de Slack, Discord, PagerDuty, OpsGenie o correo SMTP.
2. **Prohibición de Amnesia Contractual:**
   - Prohibido re-preguntar por el motor de base de datos (resuelto: SQLite embebido `AD-005`).
   - Prohibido re-preguntar por el endpoint de salud (resuelto: `/health` `HC-001`).
   - Prohibido re-preguntar por el nivel de gobernanza (resuelto: `governance_level: "bajo"`).
   - Prohibido re-preguntar por autenticación, usuarios o llaves criptográficas (resuelto: visitante anónimo `AD-007`, `SEC-DEC-001`).
   - Prohibido re-preguntar por tracing distribuido (resuelto: el sistema es un monolito autónomo sin dependencias de red distribuidas `AD-001`).
3. **Cumplimiento Estricto de Privacidad y CWE-532:**
   - Ningún log puede contener tokens sensibles sin enmascarar (`rut`, `password`, `secret`, `token`, etc.). Toda emisión debe superar sin excepciones la evaluación determinista de `SensitiveLoggingPolicy`.
4. **Delimitación de Perímetro (TaskSpec):**
   ```yaml
   task_spec:
     allowed_paths:
       - "docs/OBSERVABILITY.md"
     forbidden_paths:
       - "src/**"
       - "tests/**"
       - ".github/**"
       - "Dockerfile"
   ```

---

## 7. Workflow de Implementación (Flujo Reproducible)

El ciclo de observabilidad intercepta cada ciclo de solicitud HTTP y emite evidencia determinista respondiendo a la Sección 18 de `plan.md`:

```text
    [ Petición Entrante (HTTP Client / curl / Navegador) ]
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 1: Intercepción y Correlación (OBS-001)                │
   │ - Extraer encabezado 'X-Request-ID' de la petición.        │
   │ - Si no está presente, generar un UUIDv4 canónico.          │
   │ - Iniciar cronómetro de alta resolución (start_time).       │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 2: Ejecución de la Operación de Negocio                │
   │ - Enrutar hacia endpoint de catálogo (/api/v1/products).    │
   │ - Si ocurre error de validación o no encontrado:            │
   │   Capturar DTO-ERR-001 ('error_code', 'message', 'detail'). │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ FASE 3: Cómputo de Evidencia y Métricas (MET-001, MET-002)   │
   │ - Calcular duration_ms = (end_time - start_time) * 1000.    │
   │ - Determinar código HTTP (200, 400, 404, 500).             │
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
   │ - Emitir a sys.stdout (consumible por Docker logs).         │
   │ - Adjuntar header 'X-Request-ID' a la respuesta HTTP.       │
   └─────────────────────────────────────────────────────────────┘
```

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir y bloquear la acción:
- Proponer instalar librerías externas de telemetría (`prometheus_client`, `opentelemetry`, `jaeger-client`, `datadog`).
- Loguear stack traces desnudas con rutas del sistema operativo o excepciones internas no sanitizadas sin estructuración JSON.
- Emitir variables o parámetros que contengan tokens sensibles (`rut`, `password`, `secret`, `token`) en texto plano hacia la consola (violación de `SensitiveLoggingPolicy` / CWE-532).
- Proponer configurar dashboards de Grafana o receptores de alertas en Slack/PagerDuty para un sistema MVP de bajo gobierno.
- Extender `allowed_paths` en TaskSpec para mutar código en `src/`, `tests/` o `.github/` durante la emisión de la especificación de observabilidad.

---

## 9. Contrato de Salida Formal: `docs/OBSERVABILITY.md`

El documento emitido por esta skill debe respetar estrictamente el siguiente frontmatter YAML y las 6 secciones canónicas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "bajo"
logging_format: "json"
log_sink: "stdout"
request_id_header: "X-Request-ID"
healthcheck_endpoint: "/health"
last_audit: "YYYY-MM-DD"
---

# docs/OBSERVABILITY.md — Especificación de Observabilidad y Captura de Evidencia

## 1. Identidad de Observabilidad y Principios de Evidencia
Definición de la arquitectura de evidencia conforme a la Sección 18 de plan.md. Respuesta explícita a la tríada "¿Qué ocurrió, qué cambio lo provocó y cómo puedo reproducirlo?" bajo OBS-003.

## 2. Arquitectura de Logging Estructurado JSON
Especificación formal de LOG-001 (esquema canónico de log en JSON unilínea hacia stdout). Definición de niveles de severidad (INFO, WARNING, ERROR) y atributos obligatorios (timestamp ISO 8601, level, request_id, method, path, status_code, duration_ms, message).

## 3. Trazabilidad y Correlación de Peticiones por Request-ID
Mecanismo OBS-001: generación y propagación determinista del identificador de correlación mediante el encabezado X-Request-ID en solicitudes y respuestas HTTP. Procedimiento reproducible con curl.

## 4. Auditoría de Seguridad y Cero Fuga de Datos Sensibles (CWE-532)
Directiva OBS-002: alineación obligatoria con SEC-CTRL-004 y SensitiveLoggingPolicy. Reglas de enmascaramiento ([redacted]) y prohibición absoluta de emisión de PII, credenciales o tokens en logs.

## 5. Métricas Operacionales Mínimas y Health Checks
Especificación de métricas en memoria: latencia de endpoints (MET-001, duration_ms), conteo de códigos de respuesta y errores de negocio (MET-002, ERR-xxx), y sondeo de liveness sobre /health (HC-001).

## 6. Matriz de Linaje con PRD, Arquitectura, Seguridad, API y Despliegue
Mapeo de trazabilidad de directivas de observabilidad con PRD.md, ARCHITECTURE.md, SECURITY.md, API_DESIGN.md y DEPLOYMENT.md.
```

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_observability_skill.py`:
1. **Sincronización y Simetría:** Paridad idéntica byte a byte entre `.agents/skills/11-observability/SKILL.md` y `harness/skills/11_observability.md`.
2. **Esquema de Frontmatter:** Validación de `version: 2.0.0`, `stage: 10`, `governance: all`, dependencias upstream y artefacto producido `docs/OBSERVABILITY.md`.
3. **Estructura Canónica:** Presencia obligatoria de las 11 secciones normativas v2.0 en la skill.
4. **Reglas Anti-Amnesia:** Verificación de prohibición explícita de re-preguntar por SQLite (`AD-005`), `/health` (`HC-001`), modo anónimo (`AD-007`) o endpoints de catálogo (`EP-001`, `EP-002`).
5. **Auditoría Anti-Goldplating:** Detección y bloqueo de Prometheus, Grafana, Jaeger, Zipkin, OpenTelemetry, Datadog o webhooks de alerta.
6. **Delimitación de TaskSpec:** Validación perimetral estricta (`docs/OBSERVABILITY.md` autorizado; `src/**`, `tests/**`, `.github/**`, `Dockerfile` prohibidos).
7. **Auditoría de Privacidad CWE-532:** Evaluación de `SensitiveLoggingPolicy` sobre las especificaciones para garantizar cero tolerancia a fugas de PII o credenciales.
8. **Linter Determinista:** Ejecución del analizador sintáctico `lint_observability_contract` sobre `docs/OBSERVABILITY.md` (con comprobación condicional/skip si el archivo aún no ha sido generado en disco).

---

## 11. Criterio de Término
La etapa de `observability-setup` se considera formalmente concluida cuando:
- [ ] La skill `observability-setup` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/11-observability/SKILL.md` y `harness/skills/11_observability.md`.
- [ ] La suite determinista `tests/harness/test_observability_skill.py` está implementada y pasa 100% en verde.
- [ ] El artefacto canónico `docs/OBSERVABILITY.md` ha sido generado y certificado con cero violaciones de linter ni de TaskSpec.
- [ ] La totalidad de la suite de pruebas del arnés y de la aplicación se ejecuta con cero fallos (`exit_code == 0`).
