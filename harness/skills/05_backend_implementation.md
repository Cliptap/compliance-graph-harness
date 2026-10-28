---
name: backend-implementation
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling, api-design]
stage: 4
project_types: [web_app, api, data_pipeline, mobile]
governance: all
description: Implementacion modular del backend. Define arquitectura por capas (TaskSpec), modelos ORM, servicios, repositorios, routers REST y configuracion paramétrica según el PRD, la Arquitectura y el Modelo de Datos.
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
    * Patrón y estilo macro (`AD-xxx`).
    * Transporte y estilo de comunicación (`AD-xxx`).
    * Frontera cliente-servidor y localización de estado (`AD-xxx`).
    * Organización de código por módulos (`AD-xxx`).
    * Stack tecnológico y motor de persistencia (`AD-xxx`).
    * Estrategia de manejo de errores (`AD-xxx`).
    * Nivel de seguridad y autenticación (`AD-xxx`).
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
> 1. **Anti-Amnesia Estricta:** Queda **ESTRICTAMENTE PROHIBIDO** crear modelos, tablas, routers, middlewares o dependencias de usuarios, login, contraseñas, tokens JWT, roles, pagos o recomendaciones declarados `OUT OF SCOPE`.
> 2. **No-Goldplating y Fidelidad a Contratos:** La API de backend debe implementar estrictamente los métodos y operaciones autorizados en `docs/API_DESIGN.md`. Queda **ESTRICTAMENTE PROHIBIDO** implementar métodos de mutación (`POST`, `PUT`, `PATCH`, `DELETE`) no contemplados en la especificación de API aprobada.
> 3. **Respeto a la Localización de Estado:** Si la arquitectura delegó el almacenamiento de determinado estado o entidad al cliente, queda **ESTRICTAMENTE PROHIBIDO** implementar modelos, tablas relacionales o routers en el servidor para dicho estado.
> 4. **Aislamiento de Pruebas:** Los tests unitarios deben operar sobre SQLite en memoria (`sqlite:///:memory:`) o base de datos descartable aislada para evitar polución del repositorio.
> 5. **Preservación de Manifiestos:** Queda **ESTRICTAMENTE PROHIBIDO** agregar dependencias no autorizadas en `requirements.txt`. El stack se sustenta en las dependencias normadas en la arquitectura.

---

## 7. Workflow de Implementación Interactiva

El agente debe proceder siguiendo la secuencia de construcción modular:

### Paso 1: Configuración de Capa Compartida (`src/shared/`)
- `src/shared/database.py`: Creación del motor SQLAlchemy (`create_engine`) para SQLite, sesión local (`sessionmaker`) y clase base declarativa (`Base`).
- `src/shared/config.py`: Definición de configuración tipada para variables de base de datos y directivas CORS locales.

### Paso 2: Modelo de Persistencia y Datos Semilla (`src/<bounded_context>/`)
- `src/<bounded_context>/models.py`: Declaración del modelo ORM mapeado a la tabla relacional con columnas e índices normados (`ENT-xxx`).
- `src/<bounded_context>/seed.py`: Función de inicialización que precarga de forma idempotente los registros declarativos de datos semilla (`SEED-xxx`).

### Paso 3: Esquemas DTO de Validación Pydantic (`src/<bounded_context>/`)
- `src/<bounded_context>/schemas.py`:
  - Esquema DTO unitario con modo `from_attributes = True`.
  - Envelope estructurado de colección `{ items: list, total: int }`.
  - Esquema estándar de error estructurado (`DTO-ERR-001`).

### Paso 4: Capa de Acceso a Datos y Servicio de Dominio (`src/<bounded_context>/`)
- `src/<bounded_context>/repository.py`: Consultas SQLAlchemy para listar, filtrar y obtener por clave primaria.
- `src/<bounded_context>/service.py`: Lógica de dominio (`COMP-xxx`) encapsulando las operaciones de lectura y formateo de respuestas.

### Paso 5: Router REST y Aplicación Principal
- `src/<bounded_context>/router.py`: Router FastAPI con endpoints de colección y unitarios según contratos `EP-xxx`.
- `src/main.py`: Instancia de FastAPI, configuración de CORS, inclusión del router con prefijo `/api/v1` y hook de inicialización de base de datos/seed.

### Paso 6: Suite de Pruebas Unitarias de Backend (`tests/<bounded_context>/`)
- `tests/<bounded_context>/test_<bounded_context>_backend.py`: Pruebas con `TestClient` sobre base de datos en memoria (`sqlite:///:memory:`):
  - Consulta exitosa de colección.
  - Búsqueda filtrada y casos sin coincidencias.
  - Consulta de registro existente e inexistente por ID con error estructurado.

---

## 8. Señales de Alerta (Red Flags)

Si se detecta cualquiera de las siguientes conductas, la ejecución debe detenerse de inmediato:
- 🚩 **Amnesia de Scope:** Crear módulos de usuarios, autenticación, contraseñas, JWT o pagos.
- 🚩 **Invasión Perimetral:** Modificar archivos en capas o contextos preexistentes protegidos.
- 🚩 **Violación de Estado en Cliente:** Codificar persistencia o endpoints para estados delegados al cliente.
- 🚩 **Goldplating de Mutación:** Implementar métodos `POST`, `PUT`, `PATCH`, `DELETE` sin respaldo en contratos de API.
- 🚩 **Polución de Base de Datos:** Generar archivos binarios de base de datos local al correr pruebas en lugar de usar `sqlite:///:memory:`.
- 🚩 **Dependencias No Autorizadas:** Agregar paquetes nuevos a `requirements.txt`.

---

## 9. Contrato de Salida Formal

La implementación backend DEBE ubicarse estrictamente dentro de los siguientes archivos:

```text
src/
├── <bounded_context>/
│   ├── __init__.py
│   ├── models.py        # Modelos ORM (<EntidadDominio>)
│   ├── schemas.py       # DTOs Pydantic
│   ├── repository.py    # Consultas SQLAlchemy a base de datos
│   ├── service.py       # Lógica de dominio COMP-xxx
│   ├── router.py        # Endpoints EP-xxx
│   └── seed.py          # Precarga SEED-xxx
├── shared/
│   ├── __init__.py
│   ├── database.py      # Engine y SessionLocal SQLite/SQLAlchemy
│   └── config.py        # Typed settings
└── main.py              # Aplicación FastAPI y montaje de router /api/v1
tests/
└── <bounded_context>/
    └── test_<bounded_context>_backend.py # Tests con TestClient y SQLite en memoria
```

---

## 10. Verificación del Artefacto

Antes de considerar concluida la implementación de backend, verificar:
- [ ] Todos los archivos creados están dentro de `allowed_paths` del `TaskSpec`.
- [ ] Cero archivos modificados en rutas de código preexistente protegido (cero regresiones).
- [ ] Fidelidad estricta al contrato de API (métodos y endpoints autorizados).
- [ ] Los modelos ORM reflejan estrictamente las entidades aprobadas en `docs/DATA_MODEL.md`.
- [ ] Cero lógica o persistencia de servidor para estados formalmente delegados al cliente.
- [ ] Los tests unitarios operan sobre `sqlite:///:memory:` y pasan 100% en verde en `pytest`.
- [ ] Cero dependencias añadidas a `requirements.txt`.

---

## 11. Criterio de Término

La etapa de implementación backend concluye cuando:
1. Todos los archivos requeridos existen en disco y compilan limpiamente sin errores sintácticos ni tracebacks.
2. La suite `pytest tests/<bounded_context>/test_<bounded_context>_backend.py` finaliza con código de salida 0 (100% verde).
3. El `ValidationEngine` del arnés emite `PASS` en `ScopePolicy` y `DependencyPolicy`.

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En la implementación de referencia demostrativa (`catalogo-carrito-web`), los principios metodológicos generales de esta skill se instancian en la siguiente arquitectura de backend:

### 1. TaskSpec Concreto de la Demo
```python
TaskSpec(
    task_id="TS-BACKEND-001",
    goal="Implementar el backend de catálogo en FastAPI y SQLite",
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
        "src/cart/**",         # Blindaje AD-003: cero servidor para carrito
        "src/auth/**",         # Blindaje Anti-Amnesia: sin autenticación
        "src/users/**",        # Blindaje Anti-Amnesia: sin usuarios
        "src/payments/**",     # Blindaje Anti-Amnesia: sin pasarelas de pago
        "src/frontend/**",     # Blindaje de separación de capas
    ],
    constraints=[
        "API 100% de solo lectura (únicamente endpoints GET para catálogo)",
        "Respeto a AD-003: Cero tablas o endpoints para carritos en backend (almacenamiento en Web Storage / localStorage del cliente)",
        "Stack: Python 3.12, FastAPI, SQLite con SQLAlchemy (AD-005)",
        "Zero new external dependencies en requirements.txt",
        "Aislamiento de base de datos en tests (sqlite:///:memory:)",
    ],
    acceptance_criteria=[
        "GET /api/v1/products retorna 200 con lista de productos y total (AC-001, REQ-001)",
        "GET /api/v1/products?q=... filtra insensible a mayúsculas o retorna [] (AC-002, AC-003, REQ-002)",
        "GET /api/v1/products/{id} retorna 200 o 404 estructurado (DTO-ERR-001)",
    ],
    test_targets=["tests/catalog/test_catalog_backend.py"]
)
```

### 2. Topología de Archivos de la Demo
- `src/catalog/models.py`: Declaración del modelo ORM `Product` mapeado a la tabla `products` con columnas `id`, `name`, `description`, `price` e índice `IDX-001` sobre `name` (`ENT-001`).
- `src/catalog/schemas.py`: DTOs Pydantic `ProductResponse` (`DTO-PROD-RES-001`), `ProductListResponse` (`DTO-PROD-LIST-001`) y `ErrorResponse` (`DTO-ERR-001`).
- `src/catalog/repository.py`: Consultas SQLAlchemy a SQLite con filtrado insensible a mayúsculas sobre `Product.name`.
- `src/catalog/service.py`: Lógica de dominio `COMP-001` encapsulando operaciones de lectura.
- `src/catalog/router.py`: Endpoints REST `EP-001` y `EP-002`.
- `src/catalog/seed.py`: Función `seed_initial_catalog` que precarga los 5 productos demostrativos de `SEED-001`.
- `src/shared/database.py`: Engine y SessionLocal para SQLite (`sqlite:///./catalog.db`).
- `src/shared/config.py`: Configuración tipada de base de datos y CORS.
- `src/main.py`: Aplicación FastAPI y montaje del router en `/api/v1`.
- `tests/catalog/test_catalog_backend.py`: Suite de pruebas unitarias sobre `sqlite:///:memory:`.
