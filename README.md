# Sistema Web Básico de Catálogo Comercial y Carrito de Compras (`catalogo-carrito-web`)

Sistema web monolítico ligero de catálogo de productos y carrito de compras desacoplado, desarrollado bajo el arnés de gobernanza y trazabilidad estricta **VibeCoding Harness** con nivel de gobernanza bajo (**`governance_level: "bajo"`**).

---

## 1. Identidad del Sistema y Arquitectura Monolítica Liviana
El proyecto implementa un **Monolito Modular Desacoplado (`AD-001`)** autónomo y de alta cohesión:
- **API REST de Solo Lectura (`AD-002`, `EP-001`, `EP-002`):** Desarrollada en FastAPI bajo el prefijo canónico `/api/v1`, proveyendo consulta y búsqueda textual de productos sin mutaciones de estado en el servidor.
- **Carrito en Almacenamiento Cliente (`AD-003`, `DTO-CART-001`):** El estado del carrito reside íntegramente en Web Storage (`localStorage`) gestionado por el frontend, verificando precios e integridad contra el catálogo del servidor sin requerir endpoints transaccionales ni tablas de carritos en backend.
- **Persistencia Relacional Embebida (`AD-005`):** Base de datos relacional SQLite gestionada mediante SQLAlchemy, precargada automáticamente con el catálogo inicial de cinco productos semilla (`SEED-001`).
- **Manejo de Errores Fail-Fast (`AD-006`, `DTO-ERR-001`):** Respuestas de error estructuradas con validación perimetral estricta de parámetros (ej. límite de 100 caracteres en búsqueda) y códigos machine-readable (`ERR-001`, `ERR-002`, `ERR-500`).
- **Seguridad Baseline y Modo Visitante Anónimo (`AD-007`, `SEC-DEC-001`):** Acceso público sin esquemas de autenticación, sesiones, contraseñas ni secrets obligatorios.

---

## 2. Stack Tecnológico Oficial
El stack tecnológico del sistema se define de forma estricta y sin librerías superfluas (**KISS / YAGNI**):
- **Runtime Backend:** Python 3.12 con FastAPI y servidor ASGI Uvicorn.
- **ORM y Persistencia:** SQLAlchemy sobre SQLite embebido.
- **Frontend:** Vanilla HTML5 semántico, CSS3 moderno con variables de diseño y JavaScript ES6+ desacoplado en módulos nativos.
- **Empaquetado y Contenedores:** Docker Multi-Stage Build sobre imagen base `python:3.12-slim` con usuario no-root (`appuser:1000`).
- **Aseguramiento de Calidad:** Pytest, AnyIO y suite determinista del arnés de cumplimiento.
- **Integración Continua:** GitHub Actions con ejecución reproducible y permisos mínimos de lectura (`contents: read`).

---

## 3. Requisitos de Entorno y Prerrequisitos
Para ejecutar o desarrollar sobre este repositorio se requiere:
- **Python:** Versión 3.12 o superior.
- **Node.js:** Versión 20 LTS o superior (utilizado en el setup dual de CI para linters y validación de activos estáticos).
- **Docker:** Docker Engine 24+ o Docker Desktop (opcional para ejecución contenerizada).
- **PowerShell / Bash:** Intérprete de comandos estándar.

---

## 4. Guía Rápida de Despliegue con Contenedor Docker
De conformidad con la directiva **`DEP-001` (Unidad Desplegable Monolítica Contenerizada)**:

```powershell
# 1. Construir la imagen de producción multi-stage (python:3.12-slim)
docker build -t catalogo-carrito:1.0.0 .

# 2. Arrancar el contenedor en segundo plano exponiendo el puerto 8000
docker run -d --name catalogo-app -p 8000:8000 catalogo-carrito:1.0.0

# 3. Verificar el estado de salud operativa del servicio (HC-001)
curl -f http://localhost:8000/health

# 4. Probar la consulta del catálogo de productos (EP-001)
curl -f http://localhost:8000/api/v1/products
```

El contenedor cuenta con directiva nativa de `HEALTHCHECK` sondeando `http://localhost:8000/health` cada 30 segundos y se ejecuta bajo el usuario sin privilegios `appuser` (`SEC-CTRL-001`).

---

## 5. Guía de Desarrollo y Ejecución Local Reproducible

### 5.1 Configuración del Entorno Virtual
```powershell
# 1. Clonar el repositorio y posicionarse en la raíz
cd compliance-graph-harness

# 2. Crear y activar el entorno virtual de Python
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Instalar dependencias exactas
pip install -r requirements.txt
```

### 5.2 Inicialización de la Base de Datos
```powershell
# Inicializa la base de datos relacional y precarga los 5 productos semilla (SEED-001)
python -c "from src.harness.db import init_harness_db; init_harness_db()"
```

### 5.3 Arranque del Servidor Backend
```powershell
# Iniciar Uvicorn con recarga automática en el puerto 8000
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

La aplicación estará disponible inmediatamente en:
- **API REST Base:** `http://localhost:8000/api/v1/products`
- **Health Check:** `http://localhost:8000/health`
- **Documentación Interactiva Swagger:** `http://localhost:8000/docs`
- **Interfaz Gráfica Frontend:** Abrir directamente [`src/frontend/index.html`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/frontend/index.html) en cualquier navegador web moderno.

---

## 6. Ejecución de la Suite Completa de Pruebas
El sistema garantiza calidad determinista con compuertas de bloqueo automatizadas en CI (**`GATE-001`**, **`GATE-002`**, **`GATE-003`**):

```powershell
# Ejecución de la suite completa de pruebas deterministas
pytest tests/harness/ tests/catalog/ tests/frontend/ -v
```

La suite valida:
- **`tests/harness/`:** Contratos y linters de las 12 skills normativas, políticas de gobernanza (`ScopePolicy`, `SensitiveLoggingPolicy`), persistencia del arnés y grafo de compliance.
- **`tests/catalog/`:** Invariantes de catálogo de solo lectura, validación Fail-Fast y datos semilla.
- **`tests/frontend/`:** Pruebas DOM con JSDOM para accesibilidad ARIA, diseño responsivo, API client y estado del carrito en `localStorage`.

---

## 7. Referencia de Endpoints de Servidor
La API es estrictamente de solo lectura (**`AD-002`**):

| Identificador | Método | Ruta Canónica | Descripción | Respuesta Exitosa | Códigos de Error |
| :---: | :---: | :--- | :--- | :---: | :---: |
| **`HC-001`** | `GET` | `/health` | Sondeo de salud operativa del servicio. | `200 OK`: `{"status":"healthy"}` | — |
| **`EP-001`** | `GET` | `/api/v1/products` | Lista productos con soporte de búsqueda textual insensible a mayúsculas mediante query param `q`. | `200 OK`: `DTO-PROD-LIST-001` | `400`: `ERR-002` (si `q > 100`) |
| **`EP-002`** | `GET` | `/api/v1/products/{id}` | Obtiene el detalle unitario de un producto por identificador numérico ($id \ge 1$). | `200 OK`: `DTO-PROD-RES-001` | `400`: `ERR-002` (`id < 1`), `404`: `ERR-001` |

*Nota Arquitectónica:* Conforme a **`AD-003`**, el sistema no expone endpoints para carritos (`/carts` o similares).

---

## 8. Observabilidad, Logging JSON y Trazabilidad por Request-ID
El sistema implementa observabilidad proporcional conforme a la Sección 18 de `plan.md`:
- **Logging Estructurado en JSON (`LOG-001`, `OBS-003`):** Todos los eventos se emiten a `sys.stdout` como objetos JSON unilínea con `timestamp` ISO 8601, `level`, `request_id`, `method`, `path`, `status_code`, `duration_ms` y `message`.
- **Trazabilidad por Request-ID (`OBS-001`):** Inyección y propagación determinista del encabezado `X-Request-ID` para correlación de solicitudes.
- **Prevención de Fugas de Datos Sensibles (`OBS-002`, `SEC-CTRL-004`):** Cero emisión de PII, credenciales o tokens en bitácoras, auditado deterministamente contra **CWE-532** por `SensitiveLoggingPolicy`.
- **Métricas Operacionales Mínimas:** Medición en memoria de latencia por endpoint (`MET-001`, `duration_ms`) y distribución de códigos de estado (`MET-002`).

Para consultar las bitácoras en Docker:
```powershell
docker logs catalogo-app
```

---

## 9. Índice y Navegación hacia las Especificaciones Formales en `docs/`
El sistema cuenta con 10 especificaciones formales aprobadas y sincronizadas:

1. **[docs/PRD.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/PRD.md):** Documento de Requisitos de Producto y alcance funcional.
2. **[docs/ARCHITECTURE.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md):** Decisiones arquitectónicas estructurales y diseño modular.
3. **[docs/DATA_MODEL.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DATA_MODEL.md):** Modelo relacional, invariantes y datos semilla.
4. **[docs/API_DESIGN.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/API_DESIGN.md):** Contrato REST, esquemas DTO y catálogo de errores.
5. **[docs/SECURITY.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md):** Postura de seguridad baseline, modo visitante y prevención CWE-532.
6. **[docs/TEST_PLAN.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/TEST_PLAN.md):** Plan de pruebas, Quality Gates y matriz de cobertura AC -> Test.
7. **[docs/CICD.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/CICD.md):** Automatización de pipeline y compuertas deterministas.
8. **[docs/DEPLOYMENT.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/DEPLOYMENT.md):** Empaquetado en contenedor Docker multi-stage y directiva de salud.
9. **[docs/OBSERVABILITY.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/OBSERVABILITY.md):** Arquitectura de logging estructurado JSON y trazabilidad.
10. **[docs/SYSTEM_GUIDE.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SYSTEM_GUIDE.md):** Guía integral consolidada y Matriz de Trazabilidad End-to-End.
