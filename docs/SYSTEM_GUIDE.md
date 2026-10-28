---
status: "APPROVED"
version: 1
governance_level: "bajo"
project_id: "catalogo-carrito-web"
total_stages: 12
last_audit: "2026-10-22"
---

# docs/SYSTEM_GUIDE.md — Guía Integral del Sistema y Gobernanza de Arquitectura

## 1. Propósito y Alcance Consolidado del Sistema (PRD)
El sistema **Catálogo Comercial y Carrito de Compras Desacoplado** (`catalogo-carrito-web`) formaliza su manual integral de gobernanza técnica como resultado de la consolidación de las 12 etapas normativas del arnés.

### 1.1 Objetivos y Requisitos del Producto
De conformidad con [`docs/PRD.md`](docs/PRD.md):
- **REQ-001 (Visualización de Catálogo):** Consulta pública y paginada de productos comerciales disponibles, exponiendo denominación, descripción y precio unitario en moneda base.
- **REQ-002 (Búsqueda Textual):** Filtrado insensible a mayúsculas sobre el nombre de producto mediante parámetro de consulta (`q`), con cota máxima de 100 caracteres.
- **REQ-003 (Gestión de Carrito en Cliente):** Incorporación reactiva de ítems desde el catálogo hacia el carrito de compras con cantidad inicial.
- **REQ-004 (Modificación Interactiva de Carrito):** Modificación dinámica de cantidades (incrementar, reducir y remover ítems), recalculando subtotales y total general en tiempo real.

### 1.2 Límites de Alcance Inmutables (`OUT OF SCOPE`)
Por decisión contractual y mandato Anti-Amnesia, se excluyen de forma permanente del sistema:
- Pasarelas, intermediarios y procesamiento de pagos (tarjetas, billeteras virtuales o transferencias). Prohibida su reintroducción sin Change Request formal.
- Autenticación, registro de usuarios, sesiones con tokens o perfiles de clientes.
- Persistencia de carritos o transacciones en base de datos de servidor.

---

## 2. Topología Arquitectónica y Componentes (Monolito Liviano)
En total coherencia con el nivel de gobernanza asignado (**`governance_level: "bajo"`**), la arquitectura del sistema implementa un **Monolito Modular Desacoplado (`AD-001`)** estructurado en dos subsistemas principales:

```text
    ┌─────────────────────────────────────────────────────────────┐
    │ CLIENTE WEB (Navegador - Vanilla HTML5/CSS/JS)               │
    │                                                             │
    │  ┌───────────────────────┐       ┌───────────────────────┐  │
    │  │ COMP-002: UI Catálogo │       │ COMP-002: Carrito     │  │
    │  │ (Render reactivo DOM) │       │ (Web Storage / Local) │  │
    │  └───────────┬───────────┘       └───────────────────────┘  │
    │              │                                              │
    │              ▼                                              │
    │  ┌───────────────────────────────────────────────────────┐  │
    │  │ Cliente de API (api.js - Fetch asíncrono GET)          │  │
    │  └───────────────────────────┬───────────────────────────┘  │
    └──────────────────────────────┼──────────────────────────────┘
                                   │ HTTP REST /api/v1 (AD-002)
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ SERVIDOR BACKEND (Python 3.12 / FastAPI - Monolito DEP-001) │
    │                                                             │
    │  ┌───────────────────────────────────────────────────────┐  │
    │  │ Middleware: Request-ID (OBS-001) + Latencia (MET-001) │  │
    │  └───────────────────────────┬───────────────────────────┘  │
    │                              │                              │
    │  ┌───────────────────────────▼───────────────────────────┐  │
    │  │ COMP-001: Router de Catálogo (/api/v1/products)       │  │
    │  │ Manejo Fail-Fast de errores (DTO-ERR-001)             │  │
    │  └───────────────────────────┬───────────────────────────┘  │
    │                              │ SQLAlchemy ORM               │
    │  ┌───────────────────────────▼───────────────────────────┐  │
    │  │ Base de Datos Relacional Embebida: SQLite (AD-005)    │  │
    │  │ Precarga declarativa de 5 productos semilla (SEED-001)│  │
    │  └───────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
```

### 2.1 Decisiones Arquitectónicas Vinculantes (`AD-xxx`)
- **`AD-001`:** Patrón monolítico modular desacoplado en una sola unidad ejecutable.
- **`AD-002`:** Transporte HTTP REST síncrono bajo el prefijo canónico `/api/v1`.
- **`AD-003`:** Retención de estado del carrito en Web Storage del cliente (`localStorage`), validando precios contra el catálogo.
- **`AD-005`:** Stack tecnológico oficial basado en Python 3.12, FastAPI, SQLite con SQLAlchemy y Vanilla HTML5/CSS/JS.
- **`AD-006`:** Estrategia Fail-Fast con respuestas de error estructuradas (`DTO-ERR-001`).
- **`AD-007`:** Modo visitante anónimo sin esquemas de credenciales ni secretos obligatorios.

---

## 3. Modelo de Dominio y Persistencia (SQLite + Web Storage)
El sistema formaliza un esquema de datos híbrido desacoplado entre servidor y cliente:

### 3.1 Modelo de Datos del Servidor (`ENT-001`: Product)
Persistido de forma local en SQLite mediante SQLAlchemy:
- `id` (Integer, Primary Key, autoincremental).
- `name` (String(100), Not Null, indexado en `IDX-001`).
- `description` (Text, Nullable).
- `price` (Float / Numeric(10, 2), Not Null, cota `price >= 0.0`).

### 3.2 Invariantes de Dominio (`INV-xxx`)
- **`INV-001`:** El precio unitario de cualquier producto debe ser mayor o igual a cero (`price >= 0.0`).
- **`INV-002`:** La cantidad de un ítem en el carrito debe ser un entero positivo ($cantidad \ge 1$).
- **`INV-003`:** La denominación comercial del producto no puede estar vacía (`LENGTH(TRIM(name)) > 0`).
- **`INV-004`:** El subtotal de un ítem corresponde a $precio \times cantidad$ y el total del carrito a la sumatoria exacta de sus subtotales.

### 3.3 Datos Semilla Declarativos (`SEED-001`)
El evento `lifespan` de FastAPI inicializa automáticamente cinco productos de librería técnica:
1. Cuaderno Universitario (Precio: $2.500)
2. Bolígrafo Tinta Negra (Precio: $800)
3. Set de Marcadores Fluorescentes (Precio: $4.200)
4. Archivador Palanca Carta (Precio: $3.900)
5. Libreta de Notas de Bolsillo (Precio: $1.800)

---

## 4. Contrato de Integración REST y Manejo de Errores

### 4.1 Endpoints de la API
- **`GET /health` (`HC-001`):** Sondeo de salud operativa del servicio (`{"status": "healthy"}`).
- **`GET /api/v1/products` (`EP-001`):** Retorna la colección completa o filtrada por el parámetro `q` en el sobre `DTO-PROD-LIST-001`.
- **`GET /api/v1/products/{id}` (`EP-002`):** Retorna el detalle comercial unitario en `DTO-PROD-RES-001`.

### 4.2 Esquema Unificado de Error (`DTO-ERR-001`)
Toda respuesta de error HTTP 4xx o 5xx utiliza la estructura homogénea Fail-Fast:
```json
{
  "error_code": "ERR-002",
  "message": "Parámetro inválido",
  "detail": "El parámetro de búsqueda 'q' no puede exceder 100 caracteres"
}
```
- **`ERR-001` (404 Not Found):** Producto no localizado en el catálogo.
- **`ERR-002` (400 Bad Request):** Parámetro inválido (`q > 100` o `id < 1`).
- **`ERR-500` (500 Internal Server Error):** Fallo no previsto del servidor.

---

## 5. Postura de Seguridad Defensiva y Privacidad (CWE-532)
De conformidad con [`docs/SECURITY.md`](docs/SECURITY.md):
- **Defensa en Profundidad (`SEC-CTRL-001`):** El contenedor Docker de producción se ejecuta bajo el usuario sin privilegios `appuser` (`uid: 1000`).
- **Cero Secrets Hardcodeados (`SEC-CTRL-003`, `SEC-DEC-001`):** El arranque del sistema no requiere claves privadas ni contraseñas.
- **Prevención de Fugas de Información en Bitácoras (`SEC-CTRL-004`, `OBS-002`):** Prohibición estricta de emitir RUT, contraseñas, secretos o datos de salud en bitácoras o consolas (**CWE-532**), certificado de forma continua por `SensitiveLoggingPolicy`.
- **Sanitización de Transporte (`SEC-CTRL-005`):** Cotas numéricas y restricciones de longitud estrictas para mitigar abusos de memoria.

---

## 6. Matriz Consolidada de Trazabilidad End-to-End (Etapas 01 a 12)

La siguiente matriz certifica la integridad y linaje ininterrumpido a lo largo de las 12 etapas del arnés:

| Etapa | Nombre Canónico de la Skill | Insumos Upstream Consumidos | Contrato / Directiva Formal | Artefacto de Salida Emitido | Cobertura y Verificación |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **01** | `01-prd` | Requerimiento de negocio | `REQ-001` a `REQ-004`, `AC-001` a `AC-006` | [`docs/PRD.md`](docs/PRD.md) | Alcance MVP, 0 pagos, 0 cuentas, baja gobernanza. |
| **02** | `02-architecture` | `docs/PRD.md` | `AD-001` a `AD-007`, `COMP-001`, `COMP-002` | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Monolito desacoplado, SQLite embebido, carrito en cliente. |
| **03** | `03-data-modeling` | `PRD`, `ARCHITECTURE` | `ENT-001`, `INV-001` a `INV-004`, `SEED-001` | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Esquema relacional de catálogo y DTO de carrito. |
| **04** | `04-api-design` | `PRD`, `ARCHITECTURE`, `DATA_MODEL` | `EP-001`, `EP-002`, `DTO-ERR-001`, `ERR-xxx` | [`docs/API_DESIGN.md`](docs/API_DESIGN.md) | API REST `/api/v1` de solo lectura y Fail-Fast. |
| **05** | `05-backend` | `ARCHITECTURE`, `DATA_MODEL`, `API` | `src/catalog/`, `src/shared/`, `src/main.py` | [`src/main.py`](src/main.py) | FastAPI + SQLite con datos semilla e invariantes. |
| **06** | `06-frontend` | `PRD`, `ARCHITECTURE`, `API` | `src/frontend/` (HTML/CSS/JS Vanilla) | [`src/frontend/index.html`](src/frontend/index.html) | UI reactiva en cliente sin dependencias pesadas. |
| **07** | `07-auth` | `PRD`, `ARCHITECTURE`, `SECURITY` | `SEC-CTRL-001` a `005`, `SEC-DEC-001` | [`docs/SECURITY.md`](docs/SECURITY.md) | Modo visitante anónimo y cero fugas CWE-532. |
| **08** | `08-testing` | `PRD`, `ARCHITECTURE`, `TEST_PLAN` | Matriz AC -> Test, Acceptance Coverage | [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) | 100.0% cobertura de requisitos sin tests huérfanos (150 tests deterministas). |
| **09** | `09-cicd` | `TEST_PLAN`, `ARCHITECTURE` | `PIPE-001`, `GATE-001`, `002`, `003` | [`docs/CICD.md`](docs/CICD.md), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Pipeline continuo reproducible en GitHub Actions. |
| **10** | `10-deployment` | `ARCHITECTURE`, `CICD`, `SECURITY` | `DEP-001`, `HC-001`, Non-Root User | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`Dockerfile`](Dockerfile) | Contenedor multi-stage Python 3.12 y sondeo `/health`. |
| **11** | `11-observability`| `PRD`, `ARCHITECTURE`, `DEPLOYMENT` | `LOG-001`, `OBS-001`, `002`, `MET-001` | [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) | Logging JSON a stdout y correlación por `X-Request-ID`. |
| **12** | `12-documentation`| Las 11 etapas precedentes | Regla de Oro (Zero Drift), Guía E2E | [`README.md`](README.md), [`docs/SYSTEM_GUIDE.md`](docs/SYSTEM_GUIDE.md) | Síntesis canónica y manual integral del sistema. |
