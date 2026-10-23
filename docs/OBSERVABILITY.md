---
status: "APPROVED"
version: 1
governance_level: "bajo"
logging_format: "json"
log_sink: "stdout"
request_id_header: "X-Request-ID"
healthcheck_endpoint: "/health"
last_audit: "2026-10-22"
---

# docs/OBSERVABILITY.md — Especificación de Observabilidad y Captura de Evidencia

## 1. Identidad de Observabilidad y Principios de Evidencia
El sistema **Catálogo Comercial y Carrito de Compras Desacoplado** (`catalogo-carrito-web`) formaliza su arquitectura de observabilidad bajo la directiva **`OBS-003` (Logging Estructurado en Salida Estándar para Entornos Contenerizados)**.

En estricta concordancia con la **Sección 18 de `plan.md`**, el propósito fundamental de la observabilidad en este sistema no es acumular registros indiscriminados ni introducir sobrecarga operacional, sino capturar evidencia verificable del comportamiento del runtime que responda de forma taxativa a la tríada de reproducibilidad:

1. **¿Qué ocurrió?**
   Cada transacción HTTP, operación del catálogo y cambio de estado se registra mediante un evento estructurado en formato JSON emitido a la salida estándar (`sys.stdout`) bajo el esquema canónico **`LOG-001`**. Este evento captura la marca de tiempo precisa en formato ISO 8601, el nivel de severidad (`INFO`, `WARNING`, `ERROR`), el método HTTP, la ruta solicitada, el código de estado retornado y la duración total del procesamiento.

2. **¿Qué cambio o causa lo provocó?**
   Ante cualquier condición de error o rechazo (códigos HTTP 4xx o 5xx), el sistema intercepta la excepción mediante la estrategia Fail-Fast (**`AD-006`**) y registra de forma contextual el código de negocio machine-readable (**`ERR-001`**, **`ERR-002`**, **`ERR-500`**) y el detalle de la causa de falla encapsulados en el envelope unificado **`DTO-ERR-001`**, permitiendo diagnosticar inmediatamente el parámetro infractor o la condición anómala.

3. **¿Cómo puedo reproducirlo?**
   Cada interacción se vincula biunívocamente a un identificador determinista de trazabilidad mediante la directiva **`OBS-001` (Trazabilidad y Correlación por Request-ID)**. Este identificador se propaga en el encabezado HTTP estándar `X-Request-ID` tanto en la solicitud como en la respuesta, permitiendo a los operadores correlacionar cualquier anomalía observada en la bitácora y reproducir exactamente la misma petición con comandos de terminal reproducibles (`curl`).

### Principio de Proporcionalidad y No-Goldplating
De acuerdo con el nivel de gobernanza asignado (**`governance_level: "bajo"`**), el sistema adopta una postura de mínima superficie de fallo y sobriedad técnica (**KISS / YAGNI**):
- **Cero dependencias externas:** No se instalan recolectores pesados de telemetría, servidores de métricas ni agentes de tracing distribuido.
- **Doce Factores (Twelve-Factor App):** Los eventos se canalizan directamente hacia `sys.stdout` como un flujo continuo, delegando la captura, retención y rotación al motor de contenedores Docker (**`DEP-001`**).

---

## 2. Arquitectura de Logging Estructurado JSON
La emisión de registros en el sistema se rige formalmente por la especificación **`LOG-001` (Esquema Canónico de Registro de Evento HTTP en JSON unilínea)**.

### 2.1 Esquema Canónico de Eventos (`LOG-001`)
Cada línea emitida hacia `sys.stdout` es un objeto JSON autónomo y sintácticamente válido con los siguientes atributos:

| Campo | Tipo | Obligatorio | Descripción y Formato | Ejemplo |
| :--- | :---: | :---: | :--- | :--- |
| `timestamp` | String | Sí | Marca temporal en estándar ISO 8601 en zona horaria UTC (`YYYY-MM-DDTHH:MM:SS.mmmZ`). | `"2026-10-22T14:15:30.125Z"` |
| `level` | String | Sí | Nivel de severidad del evento: `INFO`, `WARNING` o `ERROR`. | `"INFO"` |
| `request_id` | String | Sí | Identificador UUIDv4 unívoco de la petición para correlación (`OBS-001`). | `"3fa85f64-5717-4562-b3fc-2c963f66afa6"` |
| `method` | String | Sí | Método HTTP de la solicitud (`GET`, `OPTIONS`). | `"GET"` |
| `path` | String | Sí | Ruta canónica del endpoint solicitado (`/api/v1/products`, `/health`). | `"/api/v1/products"` |
| `status_code` | Integer | Sí | Código de estado HTTP de la respuesta entregada. | `200` |
| `duration_ms` | Float | Sí | Tiempo total de cómputo en milisegundos (`MET-001`). | `14.28` |
| `message` | String | Sí | Descripción legible del resultado de la operación. | `"Consulta exitosa del catálogo comercial"` |
| `error_code` | String | No | Código formal de negocio extraído de `DTO-ERR-001` (`ERR-001`, `ERR-002`, `ERR-500`). | `"ERR-001"` |
| `detail` | String | No | Detalle complementario o parámetro causante de la falla (sanitizado). | `"No existe un producto con el identificador 99"` |

### 2.2 Política de Severidad
- **`INFO`:** Solicitudes procesadas exitosamente con códigos HTTP 2xx o redirecciones 3xx (ej. `200 OK` en consulta de catálogo o `/health`).
- **`WARNING`:** Peticiones rechazadas por validación de entrada o recursos no localizados con códigos HTTP 4xx (ej. `400 Bad Request` por parámetro excedido o `404 Not Found`).
- **`ERROR`:** Fallas no controladas del servidor, excepciones internas o fallos de conexión relacional con códigos HTTP 5xx (ej. `500 Internal Server Error`).

### 2.3 Ejemplos Estructurados de Emisión

**Ejemplo 1: Petición Exitosa de Consulta de Catálogo (HTTP 200)**
```json
{"timestamp":"2026-10-22T14:15:30.125Z","level":"INFO","request_id":"3fa85f64-5717-4562-b3fc-2c963f66afa6","method":"GET","path":"/api/v1/products","status_code":200,"duration_ms":12.45,"message":"Consulta exitosa del catálogo comercial"}
```

**Ejemplo 2: Petición Rechazada por Validación de Entrada (HTTP 400)**
```json
{"timestamp":"2026-10-22T14:16:02.841Z","level":"WARNING","request_id":"8c7e1b42-12f4-419b-a320-f4b6d059012a","method":"GET","path":"/api/v1/products?q=termino_muy_largo...","status_code":400,"duration_ms":3.12,"message":"Parámetro inválido","error_code":"ERR-002","detail":"El parámetro de búsqueda 'q' no puede exceder 100 caracteres"}
```

---

## 3. Trazabilidad y Correlación de Peticiones por Request-ID
El mecanismo **`OBS-001` (Trazabilidad y Correlación de Peticiones con Request-ID)** garantiza la auditabilidad extremo a extremo de cada ciclo HTTP.

### 3.1 Ciclo de Propagación del Identificador
1. **Inspección de Encabezados:** Al ingresar una solicitud HTTP, el middleware perimetral examina la presencia del encabezado `X-Request-ID`.
2. **Preservación o Generación:**
   - Si el cliente proporciona un valor válido en `X-Request-ID`, dicho identificador se preserva para garantizar la correlación con sistemas aguas arriba o pruebas de integración.
   - Si el encabezado está ausente o vacío, el servidor genera de forma autónoma un identificador único en formato **UUIDv4**.
3. **Inyección en Contexto de Registro:** El `request_id` se asocia al contexto de ejecución de la petición y se incorpora obligatoriamente en el payload JSON emitido (`LOG-001`).
4. **Respuesta al Cliente:** El servidor inyecta invariablemente el encabezado `X-Request-ID` en la respuesta HTTP entregada al cliente.

### 3.2 Procedimiento Operativo de Reproducción
Cuando un fallo operacional es reportado o identificado en la bitácora del contenedor, el operador puede reproducir deterministamente la llamada:

```powershell
# 1. Localización del evento anómalo en la bitácora Docker mediante su request_id
docker logs catalogo-app | grep "8c7e1b42-12f4-419b-a320-f4b6d059012a"

# 2. Reproducción idéntica de la solicitud inyectando el mismo Request-ID para verificación
curl -v -H "X-Request-ID: 8c7e1b42-12f4-419b-a320-f4b6d059012a" http://localhost:8000/api/v1/products/99
```

---

## 4. Auditoría de Seguridad y Cero Fuga de Datos Sensibles (CWE-532)
En estricto cumplimiento del control de seguridad **`SEC-CTRL-004`** establecido en [`docs/SECURITY.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md), el sistema implementa la directiva **`OBS-002` (Política de Cero Fuga de Datos Sensibles en Bitácoras)** para prevenir de forma determinista vulnerabilidades clasificadas como **CWE-532 (Insertion of Sensitive Information into Log File)**.

### 4.1 Reglas Deterministas de Prevención
1. **Prohibición de Emisión de Identificadores y Credenciales:**
   - Queda estrictamente prohibido registrar números de identificación personal (RUT, RUN, DNI, cédulas), claves de acceso, contraseñas, secretos, tokens de autenticación o diagnósticos de salud en sumideros de depuración (`print`, `logger.*`, `console.*`, `sys.stdout`).
2. **Evaluación de Conformidad con `SensitiveLoggingPolicy`:**
   - Todo módulo o middleware de observabilidad debe ser validado por el evaluador determinista [`SensitiveLoggingPolicy`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/harness/policy_engine.py#L107-L199) del arnés, garantizando cero hallazgos de severidad crítica (`policy_id: privacy.cwe_532`).
3. **Política de Enmascaramiento Dinámico:**
   - En caso fortuito de requerir la captura de cargas que contengan identificadores de depuración, se aplicará una política de sustitución explícita (`[redacted]`) previo a la serialización JSON.
4. **Sanitización de Parámetros de Consulta:**
   - La cota máxima de 100 caracteres en el parámetro `q` (`AD-006`) protege a la bitácora de desbordamientos de memoria o inyecciones deliberadas de texto no estructurado en los registros de auditoría.
5. **Supresión de Stack Traces Desnudas:**
   - Los fallos no controlados (`ERR-500`) emiten un mensaje genérico al cliente y encapsulan la descripción del incidente en el campo `detail` del log JSON, prohibiendo el volcado de rutas físicas del servidor hacia la consola sin estructuración.

---

## 5. Métricas Operacionales Mínimas y Health Checks
En concordancia con el principio de proporcionalidad del MVP, el monitoreo del sistema se realiza en memoria y por ciclo de transacción, evitando la sobrecarga de agentes de métricas o infraestructuras externas.

### 5.1 Latencia de Peticiones en Milisegundos (`MET-001`)
- **Definición:** Medición precisa del tiempo transcurrido desde la recepción del paquete HTTP hasta la entrega completa de la respuesta (`duration_ms`).
- **Mecanismo:** Captura mediante cronómetro de alta resolución (`time.perf_counter()`) en el middleware perimetral.
- **Utilidad:** Permite identificar degradación de rendimiento en consultas relacionales o abusos de cómputo en filtros de texto.

### 5.2 Distribución de Códigos de Estado y Errores (`MET-002`)
- **Definición:** Seguimiento de la frecuencia y distribución de respuestas HTTP y códigos de negocio (`ERR-xxx`).
- **Categorías Clave:**
  - Tasa de éxito: Porcentaje de respuestas `200 OK` sobre `EP-001` y `EP-002`.
  - Errores de cliente (`ERR-001` y `ERR-002`): Frecuencia de parámetros inválidos o productos no encontrados.
  - Tasa de error del servidor (`ERR-500`): Frecuencia de excepciones internas no recuperables (umbral operacional esperado: 0.0%).

### 5.3 Sondeo de Salud Operativa (`HC-001`)
- **Definición:** Endpoint nativo de verificación de liveness expuesto en `GET /health` ([`src/main.py`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/main.py#L57-L61)).
- **Respuesta Estándar:** `{"status": "healthy", "database": "connected"}` con código HTTP 200 (o `503 Service Unavailable` con `{"status": "unhealthy", "database": "disconnected"}` si SQLite falla).
- **Integración con Despliegue:** Consumido por la directiva `HEALTHCHECK` del contenedor Docker formalizada en [`docs/DEPLOYMENT.md`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md#L68-L72):
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
  ```

---

## 6. Matriz de Linaje con PRD, Arquitectura, Seguridad, API y Despliegue

La siguiente matriz documenta la trazabilidad biunívoca entre las directivas de observabilidad formalizadas y los contratos precedentes aprobados:

| Identificador Formal | Concepto de Observabilidad | Directiva Upstream | Documento Fuente | Justificación y Cumplimiento Técnico |
| :--- | :--- | :--- | :--- | :--- |
| **`OBS-001`** | Correlación por Request-ID | `AD-002`, `AD-006` | [docs/ARCHITECTURE.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md) | Propaga `X-Request-ID` para asociar deterministamente peticiones, logs y respuestas. |
| **`OBS-002`** | Prevención de Fugas CWE-532 | `SEC-CTRL-004`, `CONST-003` | [docs/SECURITY.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md) | Garantiza cero PII y cero credenciales en logs; auditado por `SensitiveLoggingPolicy`. |
| **`OBS-003`** | Logging JSON a stdout | `DEP-001`, Doce Factores | [docs/DEPLOYMENT.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md) | Flujo unilínea hacia `sys.stdout` consumible de forma transparente por `docker logs`. |
| **`LOG-001`** | Esquema Canónico de Log | `DTO-ERR-001`, `EP-001`, `EP-002` | [docs/API_DESIGN.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/API_DESIGN.md) | Estructura homogénea que captura `timestamp`, `level`, `duration_ms` y `error_code`. |
| **`MET-001`** | Latencia de Endpoints (`duration_ms`) | `AD-006` (Fail-Fast) | [docs/ARCHITECTURE.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md) | Métricas en memoria calculadas por petición sin intermediarios ni agentes pesados. |
| **`MET-002`** | Conteo de Estados y Errores | `ERR-001`, `ERR-002`, `ERR-500` | [docs/API_DESIGN.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/API_DESIGN.md) | Supervisa la distribución de respuestas para detectar anomalías operacionales. |
| **`HC-001`** | Sondeo de Liveness `/health` | `DEP-001`, `HEALTHCHECK` | [docs/DEPLOYMENT.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md) | Endpoint de disponibilidad utilizado por Docker para certificar el estado saludable del servicio. |
