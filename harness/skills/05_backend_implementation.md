---
name: backend-implementation
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling, api-design]
stage: 4
project_types: [web_app, api, data_pipeline, mobile]
governance: all
description: Implementacion del backend. Define estructura modular del proyecto (TaskSpec), modelos ORM, servicios, routers REST de solo lectura y configuracion en Python con SQLite y SQLAlchemy respetando el PRD, la Arquitectura, el Modelo de Datos y el Diseno de API.
---

# Skill 05: Implementación de Backend (Backend Implementation)

## 1. Overview y Propósito

Esta skill gobierna la **transición crítica desde la especificación documental hacia la construcción física de código ejecutable** en `src/`. Traduce los requerimientos de `docs/PRD.md`, las directivas arquitectónicas de `docs/ARCHITECTURE.md`, el esquema relacional de `docs/DATA_MODEL.md` y los contratos de transporte de `docs/API_DESIGN.md` en código fuente modular, tipado y testeable.

Su propósito fundamental es responder con rigor de ingeniería:
> **¿Cómo implementar los componentes de backend del sistema de forma limpia, modular y desacoplada, garantizando que cada archivo y línea de código tenga linaje causal estricto, sin introducir dependencias no autorizadas ni realizar cambios fuera de alcance?**

La skill opera bajo cuatro principios fundamentales de gobernanza:
1. **Linaje Contractual Causal y Cero Cambios Huérfanos (*No Orphan Changes*):** Todo archivo, modelo, router o función en `src/` debe responder directamente a un componente arquitectónico (`COMP-xxx`), una entidad de datos (`ENT-xxx`) o un contrato de endpoint (`EP-xxx`). El arnés rechaza terminantemente cualquier archivo accesorio no justificado (`orphan changes`).
2. **Delimitación Perimetral Estricta mediante `TaskSpec`:** La codificación nunca se realiza de forma libre sobre todo el repositorio. Requiere la definición formal de `allowed_paths` y `forbidden_paths` para aislar el trabajo en el contexto acotado (bounded context) aprobado y prevenir la modificación de código ajeno o preexistente.
3. **Regla de Oro Anti-Amnesia:** Queda estrictamente prohibido implementar modelos, tablas, routers o dependencias para conceptos sentenciados en `OUT OF SCOPE`.
4. **No-Goldplating y Fidelidad a Contratos:** El backend solo codifica las operaciones y métodos respaldados por los requerimientos del PRD y los contratos de API aprobados. Si el contrato de API sellado es de solo lectura, queda prohibido codificar repositorios, servicios o endpoints de mutación.
5. **Respeto a Fronteras Arquitectónicas:** Respetar la localización de estado (cliente vs servidor) sellada en la arquitectura.

---

## 2. Cuándo Usar (Use When)

- Inmediatamente después de que `docs/API_DESIGN.md` haya alcanzado el estado `status: APPROVED`.
- Cuando se requiere codificar los modelos ORM de persistencia, servicios de dominio, routers HTTP y configuraciones del backend.
- Previo al desarrollo de la interfaz de usuario en `06-frontend` y a la consolidación de las pruebas de integración en `08-testing`.

---

## 3. Precondiciones

1. **Aprobación Formal de la Cadena Upstream:**
   - `docs/PRD.md` DEBE existir con `status: APPROVED`.
   - `docs/ARCHITECTURE.md` DEBE existir con `status: APPROVED`.
   - `docs/DATA_MODEL.md` DEBE existir con `status: APPROVED`.
   - `docs/API_DESIGN.md` DEBE existir con `status: APPROVED`.
   - Queda prohibido escribir código en `src/` si cualquiera de los artefactos previos se encuentra en `DRAFT` o ausente.
2. **Definición de `TaskSpec` Perimetral:**
   - Debe establecerse el `TaskSpec` de la tarea delimitando `allowed_paths` antes de iniciar la creación o edición de archivos.
3. **Aislamiento de Pruebas:**
   - Las pruebas unitarias de backend deben ejecutarse sobre una base de datos SQLite en memoria (`sqlite:///:memory:`) o archivo temporal descartable para evitar polución del repositorio.

---

## 4. Entradas (Inputs) desde Upstream

La skill extrae deterministamente:
- **Desde `docs/PRD.md`:**
  - `project_id`, `governance_level`.
  - `REQ-xxx` e `IN SCOPE`: Requerimientos funcionales asignados al contexto acotado (bounded context).
  - `AC-xxx`: Criterios de aceptación observables del contexto acotado.
  - `OUT OF SCOPE`: Conceptos expresamente excluidos que no deben codificarse.
- **Desde `docs/ARCHITECTURE.md`:**
  - `COMP-xxx`: Componentes asignados a la capa de backend.
  - `AD-xxx`: Decisiones arquitectónicas vinculantes:
    * Patrón y estilo macro (`AD-001`).
    * Transporte y estilo de comunicación (`AD-002`).
    * Frontera cliente-servidor y localización de estado (`AD-003`).
    * Organización de código por módulos (`AD-004`).
    * Stack tecnológico y motor de persistencia (`AD-005`).
    * Estrategia de manejo de errores (`AD-006`).
    * Nivel de seguridad y autenticación (`AD-007`).
- **Desde `docs/DATA_MODEL.md`:**
  - `ENT-xxx`: Entidades relacionales o de persistencia asignadas al componente.
  - `IDX-xxx`: Índices para optimización de consultas.
  - `INV-xxx`: Invariantes y reglas de validación en modelos y servicios.
  - `SEED-xxx`: Registros semilla declarativos de inicialización.
- **Desde `docs/API_DESIGN.md`:**
  - `EP-xxx`: Endpoints con métodos, rutas y parámetros query/path.
  - `DTO-xxx`: Esquemas de datos para request y response (Envelope estructurado).
  - `ERR-xxx`: Códigos de error y excepciones estructuradas (`DTO-ERR-001`).

---

## 5. Taxonomía Formal y Mecanismo `TaskSpec`

Toda tarea de implementación física en backend debe estar formalmente delimitada bajo el contrato `TaskSpec` del arnés según el contexto acotado (bounded context) aprobado:

```python
TaskSpec(
    task_id="TS-BACKEND-xxx",
    goal="Implementar los componentes de backend del contexto acotado (bounded context) aprobado",
    category="feature",
    allowed_paths=[
        "src/<bounded_context>/**",
        "src/shared/**",
        "src/main.py",
        "tests/<bounded_context>/**",
    ],
    forbidden_paths=[
        "src/<other_context>/**",  # Preserva contextos acotados ajenos o preexistentes
        "src/frontend/**",         # Aislamiento estricto de frontend
        # Rutas de conceptos excluidos en OUT OF SCOPE o fronteras arquitectónicas
    ],
    constraints=[
        "Fidelidad estricta a los contratos de API aprobados en docs/API_DESIGN.md",
        "Persistencia y ORM conformes a las decisiones estructurales de docs/ARCHITECTURE.md",
        "Zero new external dependencies no autorizadas",
        "Aislamiento de base de datos en pruebas (ej. SQLite en memoria)",
    ],
    acceptance_criteria=[
        "Trazabilidad 100% de los criterios de aceptación del contexto acotado",
    ],
    test_targets=["tests/<bounded_context>/..."]
)
```

Cualquier archivo fuera de `allowed_paths` o no justificable en la cadena de linaje será clasificado como **`orphan_change`** y rechazado por el `ValidationEngine`.

---

## 6. Regla de Oro Anti-Amnesia y No-Goldplating

> 🛑 **REGLAS CONTRACTUALES DE IMPLEMENTACIÓN:**
> 1. **Anti-Amnesia Estricta:** Queda **ESTRICTAMENTE PROHIBIDO** crear modelos, tablas, routers, middlewares o dependencias de usuarios, login, contraseñas, tokens JWT, roles, pagos o recomendaciones.
> 2. **No-Goldplating (API de Solo Lectura):** La API de backend para este MVP es **100% de solo lectura**. Queda **ESTRICTAMENTE PROHIBIDO** implementar métodos `POST`, `PUT`, `PATCH`, `DELETE` en routers o repositorios de productos (`create_product`, `update_product`, `delete_product`).
> 3. **Respeto a AD-003 (Carrito en Cliente):** El carrito reside en `localStorage`. Queda **ESTRICTAMENTE PROHIBIDO** implementar modelos, tablas relacionales o routers para carritos en el servidor.
> 4. **Aislamiento de Pruebas:** Los tests unitarios en `test_catalog_backend.py` deben operar sobre SQLite en memoria (`sqlite:///:memory:`) para evitar la creación de archivos binarios `.db` en el repositorio.
> 5. **Preservación de Manifiestos:** Queda **ESTRICTAMENTE PROHIBIDO** agregar dependencias no autorizadas en `requirements.txt`. El stack se sustenta en `fastapi`, `sqlalchemy`, `pydantic` y `uvicorn`.

---

## 7. Workflow de Implementación Interactiva

El agente debe proceder siguiendo la secuencia de construcción modular:

### Paso 1: Configuración de Capa Compartida (`src/shared/`)
- `src/shared/database.py`: Creación del motor SQLAlchemy (`create_engine`) para SQLite, sesión local (`sessionmaker`) y clase base declarativa (`Base`).
- `src/shared/config.py`: Definición de configuración tipada para `DATABASE_URL` (`sqlite:///./catalog.db`) y directivas CORS locales.

### Paso 2: Modelo de Persistencia y Datos Semilla (`src/catalog/`)
- `src/catalog/models.py`: Declaración del modelo ORM `Product` mapeado a la tabla `products` con columnas `id`, `name`, `description`, `price` e índice `IDX-001` sobre `name` (`ENT-001`).
- `src/catalog/seed.py`: Función de inicialización `seed_initial_catalog(db)` que precarga de forma idempotente los 5 registros declarativos de `SEED-001`.

### Paso 3: Esquemas DTO de Validación Pydantic (`src/catalog/`)
- `src/catalog/schemas.py`:
  - `ProductResponse` (`DTO-PROD-RES-001`): `{ id: int, name: str, description: str | null, price: float }` con modo `from_attributes = True`.
  - `ProductListResponse` (`DTO-PROD-LIST-001`): Envelope estructurado `{ items: list[ProductResponse], total: int }`.
  - `ErrorResponse` (`DTO-ERR-001`): `{ error_code: str, message: str, detail: str | null }`.

### Paso 4: Capa de Acceso a Datos y Servicio de Dominio (`src/catalog/`)
- `src/catalog/repository.py`: Consultas SQLAlchemy para listar productos, filtrar por coincidencia insensible a mayúsculas (`func.lower(Product.name).contains(q.lower())`) y obtener por clave primaria.
- `src/catalog/service.py`: Lógica de dominio (`COMP-001`) encapsulando las operaciones de lectura y formateo de respuestas.

### Paso 5: Router REST y Aplicación Principal
- `src/catalog/router.py`: Router FastAPI con prefijo `/products`:
  - `EP-001`: `GET /` con parámetro query `q: str | None = None`. Retorna `ProductListResponse`.
  - `EP-002`: `GET /{id}` con parámetro de ruta `id: int`. Retorna `ProductResponse` o lanza excepción HTTP 404 estructurada.
- `src/main.py`: Instancia de FastAPI, configuración de CORS, inclusión del router con prefijo `/api/v1` y hook de inicialización de base de datos/seed.

### Paso 6: Suite de Pruebas Unitarias de Backend (`tests/catalog/`)
- `tests/catalog/test_catalog_backend.py`: Pruebas con `TestClient` sobre base de datos en memoria (`sqlite:///:memory:`):
  - Consulta exitosa de catálogo completo (`EP-001` -> 200 OK, 5 ítems).
  - Búsqueda filtrada insensible a mayúsculas (`EP-001?q=cuaderno` -> 200 OK, 1 ítem).
  - Búsqueda sin coincidencias (`EP-001?q=inexistente` -> 200 OK, 0 ítems).
  - Consulta de producto existente por ID (`EP-002` -> 200 OK).
  - Consulta de producto inexistente por ID (`EP-002` -> 404 estructurado con `ERR-001`).

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse de inmediato:
- 🚩 **Amnesia de Scope:** Crear módulos de usuarios, autenticación, contraseñas, JWT o pagos.
- 🚩 **Invasión Perimetral:** Modificar archivos en `src/backend/` o `src/database/` del sistema clínico preexistente.
- 🚩 **Violación de Carrito en Cliente:** Codificar persistencia o endpoints para carritos en servidor (`AD-003`).
- 🚩 **Goldplating de Mutación:** Implementar métodos `POST`, `PUT`, `PATCH`, `DELETE` en el router de productos.
- 🚩 **Polución de Base de Datos:** Generar archivos binarios `.db` al correr pruebas en lugar de usar `sqlite:///:memory:`.
- 🚩 **Dependencias No Autorizadas:** Agregar paquetes nuevos a `requirements.txt`.

---

## 9. Contrato de Salida Formal

La implementación backend DEBE ubicarse estrictamente dentro de los siguientes archivos:

```text
src/
├── catalog/
│   ├── __init__.py
│   ├── models.py        # ENT-001 [Product]
│   ├── schemas.py       # DTO-PROD-RES-001, DTO-PROD-LIST-001, DTO-ERR-001
│   ├── repository.py    # Consultas SQLAlchemy a SQLite
│   ├── service.py       # Lógica de dominio COMP-001
│   ├── router.py        # Endpoints EP-001 y EP-002
│   └── seed.py          # Precarga SEED-001
├── shared/
│   ├── __init__.py
│   ├── database.py      # Engine y SessionLocal SQLite/SQLAlchemy
│   └── config.py        # Typed settings
└── main.py              # Aplicación FastAPI y montaje de router /api/v1
tests/
└── catalog/
    └── test_catalog_backend.py # Tests con TestClient y SQLite en memoria
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la implementación de backend, verificar:
- [ ] Todos los archivos creados están dentro de `allowed_paths` del `TaskSpec`.
- [ ] Cero archivos modificados en `src/backend/` o `src/database/` (cero regresiones clínicas).
- [ ] La API es 100% de solo lectura (`GET` únicamente). Cero métodos de mutación.
- [ ] Los modelos ORM reflejan estrictamente la entidad `ENT-001` podada en `docs/DATA_MODEL.md`.
- [ ] Cero lógica o persistencia de carrito en servidor (`AD-003`).
- [ ] Los tests unitarios operan sobre `sqlite:///:memory:` y pasan 100% en verde en `pytest`.
- [ ] Cero dependencias añadidas a `requirements.txt`.

---

## 11. Criterio de Término

La etapa de implementación backend concluye cuando:
1. Todos los archivos requeridos existen en disco y compilan limpiamente sin errores sintácticos ni tracebacks.
2. La suite `pytest tests/catalog/test_catalog_backend.py` finaliza con código de salida 0 (100% verde).
3. El `ValidationEngine` del arnés emite `PASS` en `ScopePolicy` y `DependencyPolicy`.

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian en la siguiente arquitectura de backend:
- **TaskSpec de la Demo:**
```python
TaskSpec(
    task_id="TS-BACKEND-001",
    goal="Implementar el backend ligero de catálogo de productos y búsqueda en SQLite/FastAPI",
    category="feature",
    allowed_paths=[
        "src/catalog/**",
        "src/shared/**",
        "src/main.py",
        "tests/catalog/**",
    ],
    forbidden_paths=[
        "src/backend/**",      # Preserva código clínico preexistente
        "src/database/**",     # Preserva esquemas clínicos preexistentes
        "src/frontend/**",     # Aislamiento estricto de frontend
        "src/cart/**",         # Blindaje AD-003: el carrito no reside en backend
        "src/auth/**",         # Blindaje OUT OF SCOPE: sin autenticación
        "src/users/**",        # Blindaje OUT OF SCOPE: sin usuarios
        "src/payments/**",     # Blindaje OUT OF SCOPE: sin pagos
    ],
    constraints=[
        "Read-Only API: Únicamente métodos GET autorizados en routers",
        "SQLite con SQLAlchemy como motor ORM exclusivo (AD-005)",
        "Zero new external dependencies en requirements.txt",
        "Sin credenciales, contraseñas ni tokens de sesión (AD-007)",
        "Base de datos en pruebas desacoplada usando SQLite en memoria (sqlite:///:memory:)",
    ],
    acceptance_criteria=[
        "GET /api/v1/products retorna Envelope { items, total } con SEED-001",
        "GET /api/v1/products?q= filtra insensible a mayúsculas sobre name",
        "GET /api/v1/products/{id} retorna producto o 404 estructurado",
    ],
    test_targets=["tests/catalog/test_catalog_backend.py"]
)
```
- **Contexto Acotado y Topología Física:**
  - `src/catalog/models.py`: Modelo SQLAlchemy `Product` para `ENT-001` con tabla `products`.
  - `src/catalog/schemas.py`: Esquemas Pydantic `ProductResponse` y `ProductListResponse` para `DTO-PROD-RES-001` y `DTO-PROD-LIST-001`.
  - `src/catalog/repository.py`: Consultas de lectura a SQLite con filtrado insensible a mayúsculas sobre `name` (`IDX-001`).
  - `src/catalog/service.py`: Lógica de dominio de catálogo.
  - `src/catalog/router.py`: Endpoints REST `GET /api/v1/products` (`EP-001`) y `GET /api/v1/products/{id}` (`EP-002`) con manejo Fail-Fast (`DTO-ERR-001`, `ERR-001`, `ERR-002`, `ERR-500`).
  - `src/catalog/seed.py`: Inicialización de 5 productos semilla de papelería (`SEED-001`).
  - `src/shared/database.py` y `src/shared/config.py`: Conexión SQLAlchemy y configuración general.
  - `src/main.py`: Entrypoint FastAPI montando `/health` (`HC-001`) y `/api/v1/products`.
- **Aislamiento de Pruebas:** Pruebas unitarias en `tests/catalog/test_catalog_backend.py` ejecutadas contra `sqlite:///:memory:`.
- **Invariante de Solo Lectura y AD-003:** Backend 100% de solo lectura (cero mutaciones POST/PUT/DELETE) y cero persistencia de carrito en servidor (reside en Web Storage del cliente).
