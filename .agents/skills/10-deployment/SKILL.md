---
name: deployment-automation
version: 2.0.0
stage: 9
depends_on: [prd-generation, architecture-design, data-modeling, api-design, backend-implementation, frontend-implementation, auth-governance, testing-strategy, cicd-automation]
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
produces_artifact: [docs/DEPLOYMENT.md, Dockerfile, .dockerignore]
description: Automatización y empaquetado de despliegue reproducible. Define la unidad desplegable monolítica liviana en Docker multi-stage con usuario non-root, SQLite embebido, sondeo de salud y cero goldplating.
---

# Skill: Automatización de Despliegue y Empaquetado (deployment-automation)

## 1. Overview
Esta skill define, estandariza y automatiza el empaquetado y la estrategia de despliegue del sistema en una unidad autocontenida, inmutable y reproducible.
A diferencia de enfoques tradicionales que improvisan plataformas DevOps masivas, clústeres complejos o infraestructuras multi-nube prematuras, esta skill implementa el principio de **Unidad Desplegable Canónica y Proporcional (KISS / YAGNI)**:
- Empaqueta el sistema como un **Monolito Modular Ligero** (`AD-001`, `AD-005`), consolidando la API REST FastAPI (`src/main.py`), la base de datos relacional SQLite embebida y los activos estáticos del frontend Vanilla (`src/frontend/`) en una única imagen de contenedor Docker.
- Implementa una construcción segura y liviana mediante **Docker Multi-Stage Build** sobre `python:3.12-slim`, separando tajantemente las dependencias de compilación del entorno de ejecución.
- Aplica directivas de seguridad defensiva en contenedor: ejecución bajo un **usuario sin privilegios** (`appuser:appuser`, non-root) y sondeo periódico de salud operativa (`HEALTHCHECK` sobre `/health`).
- Respeta estrictamente el modelo de acceso público anónimo sin requerir variables secretas obligatorias para arrancar el sistema (`AD-007`, `SEC-DEC-001`).
- Emite tres artefactos canónicos: la especificación de gobernanza `docs/DEPLOYMENT.md`, el `Dockerfile` de producción y `.dockerignore`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 9** del pipeline de desarrollo, inmediatamente después de que el código fuente ha superado satisfactoriamente los Quality Gates de Integración Continua en `09-cicd` (`docs/CICD.md` y `.github/workflows/ci.yml`).
- Se utiliza para transformar el software validado en una unidad ejecutable lista para producción, asegurando que el despliegue no introduzca mutaciones inesperadas sobre la aplicación.
- Precede a la etapa de observabilidad y telemetría (`11-observability`).

---

## 3. Precondiciones
1. **Pipeline de Calidad Superado:**
   - Quality Gates `GATE-001` (Zero Failure), `GATE-002` (Acceptance Coverage 100%) y `GATE-003` (ScopePolicy) certificados en verde por la suite de pruebas del arnés y CI/CD.
2. **Artefactos Previos Sellados:**
   - `docs/PRD.md` en estado `APPROVED`, clasificando el sistema con `governance_level: "bajo"`.
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, con las decisiones estructurales vinculantes: Monolito modular (`AD-001`), almacenamiento del carrito en cliente (`AD-003`), runtime Python 3.12 + FastAPI + SQLite embebido (`AD-005`) y seguridad baseline sin tokens de sesión (`AD-007`).
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con invariantes de datos (`INV-001` a `INV-004`) y datos semilla declarativos (`SEED-001`).
   - `docs/SECURITY.md` en estado `APPROVED`, formalizando la exclusión de autenticación (`SEC-DEC-001`) y cero secrets hardcodeados (`SEC-CTRL-003`).
   - `docs/TEST_PLAN.md` y `docs/CICD.md` en estado `APPROVED`.
3. **Código Base Funcional y Verificado:**
   - Módulo principal [`src/main.py`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/main.py) con endpoint `/health` y montaje de catálogo en `/api/v1`.
   - Manifiesto `requirements.txt` sincronizado.

---

## 4. Entradas
La skill consume de manera estricta y exclusiva:
- **Desde `docs/ARCHITECTURE.md`:**
  - `AD-001`: Patrón monolítico desacoplado en una sola unidad de ejecución.
  - `AD-003`: El carrito reside en Web Storage, eliminando la necesidad de persistencia transaccional multi-dispositivo en backend.
  - `AD-005`: Stack tecnológico oficial (Python 3.12, FastAPI, SQLite con SQLAlchemy, Vanilla HTML5/CSS/JS).
  - `AD-007`: Modo visitante anónimo sin credenciales ni secrets obligatorios.
- **Desde `docs/PRD.md`:**
  - Alcance MVP y cláusula `OUT OF SCOPE`: Prohíbe arquitecturas de microservicios, bases de datos cloud distribuidas o integración con CDNs de pago.
- **Desde `docs/SECURITY.md`:**
  - `SEC-DEC-001`: Omisión total de autenticación/sesiones de usuario.
  - `SEC-CTRL-003`: Cero secrets o claves privadas hardcodeadas en manifiestos de despliegue.
- **Desde `docs/CICD.md`:**
  - Validación previa superada por el flujo `PIPE-001` y compuertas `GATE-001` a `GATE-003`.
- **Desde el Código Fuente Físico:**
  - Entrypoint canónico: `src/main.py` (`app = FastAPI(...)`).
  - Interfaz de usuario: `src/frontend/` (`index.html`, `styles.css`, `app.js`, `cart.js`, `api.js`).
  - Endpoint de liveness: `GET /health` respondiendo `{"status": "healthy"}`.

---

## 5. Taxonomía Formal
Toda directiva, variable de entorno o comprobación de salud definida por esta skill debe utilizar identificadores estables y trazables:
- **`DEP-xxx` (Deployment Strategy):** Identificador de la estrategia y directivas de despliegue (ej. `DEP-001`: "Unidad Desplegable Monolítica Contenerizada en Docker Multi-Stage").
- **`ENV-xxx` (Environment Variable):** Variables de configuración operacional no confidenciales (ej. `ENV-PORT`: puerto TCP de escucha del servidor, `ENV-HOST`: interfaz de red).
- **`HC-xxx` (Health Check):** Directiva de comprobación de salud y disponibilidad operativa (ej. `HC-001`: "Sondeo de Liveness HTTP sobre `/health`").

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición de Infraestructura Pesada y Orquestadores Complejos:**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** introducir:
     * Orquestadores de clústeres: Kubernetes (K8s), Helm, Docker Swarm, Nomad o Apache Mesos.
     * Infraestructura como Código (IaC): Terraform, Pulumi, CloudFormation, Ansible.
     * Servidores proxy inversos redundantes en contenedores separados (Nginx, Traefik, HAProxy) para este MVP monolítico.
     * Motores de bases de datos externas en red (PostgreSQL, MySQL, Redis, DynamoDB) que violen la directiva de SQLite embebido (`AD-005`).
2. **Prohibición de Mutación de Código de Producción:**
   - La skill de despliegue tiene prohibido modificar archivos dentro de `src/**` o agregar dependencias a la aplicación. Su rol es **empaquetar el código validado existente, no reescribirlo**.
3. **Contenedor Seguro sin Privilegios (Non-Root User):**
   - El contenedor final de producción debe crear y ejecutar bajo un usuario de sistema dedicado sin privilegios de superusuario (`appuser:appuser`, `uid: 1000`), mitigando riesgos de escape de contenedor.
4. **Respeto al Modo Anónimo sin Secrets Obligatorios (`AD-007`):**
   - Prohibido configurar variables obligatorias tipo `JWT_SECRET`, `SECRET_KEY` o `DATABASE_PASSWORD` que impidan el arranque directo de la aplicación en modo visitante anónimo.
5. **Delimitación de Perímetro (TaskSpec):**
   ```yaml
   task_spec:
     allowed_paths:
       - "docs/DEPLOYMENT.md"
       - "Dockerfile"
       - ".dockerignore"
     forbidden_paths:
       - "src/**"
       - "tests/**"
       - ".github/**"
   ```

---

## 7. Workflow de Implementación (Flujo Reproducible)

El flujo de empaquetado y despliegue debe ser 100% determinista, reproducible localmente y en cualquier motor compatible con OCI/Docker:

```text
       [ Código Validado por CI/CD (Quality Gates PASS) ]
                               │
                               ▼
     ┌───────────────────────────────────────────────────┐
     │ FASE 1: Docker Multi-Stage Build (Dockerfile)     │
     │ 1. Etapa Builder (python:3.12-slim):              │
     │    - Creación de virtualenv aislado (/opt/venv)   │
     │    - pip install -r requirements.txt              │
     │ 2. Etapa Runtime (python:3.12-slim):              │
     │    - Copia exclusiva del virtualenv (/opt/venv)   │
     │    - Copia del árbol de aplicación (src/)         │
     │    - Creación de usuario non-root (appuser:1000)  │
     │    - Exposición de puerto 8000                    │
     │    - HEALTHCHECK CMD curl /health                 │
     │    - CMD: uvicorn src.main:app --host 0.0.0.0     │
     │                   --port 8000                     │
     └─────────────────────────┬─────────────────────────┘
                               │
                               ▼
     ┌───────────────────────────────────────────────────┐
     │ FASE 2: Filtrado de Artefactos (.dockerignore)    │
     │ - Excluir .git, tests/, .venv, .pytest_cache      │
     │ - Mantener imagen final ligera (< 250 MB)         │
     └─────────────────────────┬─────────────────────────┘
                               │
                               ▼
     ┌───────────────────────────────────────────────────┐
     │ FASE 3: Verificación Operativa Local              │
     │ - docker build -t catalogo-carrito:latest .       │
     │ - docker run -d -p 8000:8000 catalogo-carrito     │
     │ - curl -f http://localhost:8000/health (STATUS 200)│
     └───────────────────────────────────────────────────┘
```

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir y detener la acción:
- Configurar servicios de base de datos separados (PostgreSQL, MySQL) en lugar de utilizar la persistencia SQLite embebida de `AD-005`.
- Ejecutar el contenedor como usuario `root` en la etapa final de runtime.
- Hardcodear rutas erróneas en el `CMD` de Uvicorn (ej. `src.backend.main:app` en vez de `src.main:app`).
- Incorporar herramientas pesadas de orquestación en la nube (Kubernetes, Terraform, AWS ECS) no requeridas en el MVP.
- Omitir el `.dockerignore`, provocando la inclusión de cachés de pruebas, base de datos local de desarrollo o historiales Git dentro de la imagen de producción.
- Introducir secrets obligatorios o credenciales en el `Dockerfile` o variables de entorno mínimas.

---

## 9. Contrato de Salida Formal: `docs/DEPLOYMENT.md`, `Dockerfile` y `.dockerignore`

### A. Documento de Gobernanza: `docs/DEPLOYMENT.md`
El documento debe contener el siguiente frontmatter y 6 secciones canónicas estructuradas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "bajo"
deployment_target: "docker"
container_engine: "docker"
exposed_port: 8000
healthcheck_endpoint: "/health"
last_audit: "YYYY-MM-DD"
---

# docs/DEPLOYMENT.md — Especificación de Despliegue y Empaquetado

## 1. Identidad de Despliegue y Arquitectura de la Unidad Desplegable (DEP-001)
Definición de la unidad desplegable como monolito liviano desacoplado en contenedor Docker.

## 2. Estrategia de Empaquetado en Contenedor
Diseño multi-stage build, imagen base python:3.12-slim, usuario no-root (appuser) y optimización de tamaño.

## 3. Gestión de Persistencia y Datos Semilla
Estrategia de base de datos SQLite embebida, directorio de datos local (/app/data o SQLite in-memory) y precarga automática de SEED-001 en el lifespan de FastAPI.

## 4. Variables de Entorno y Política de Secrets
Modo visitante anónimo sin secrets requeridos (AD-007, SEC-DEC-001). Variables de configuración operacionales no sensibles (PORT, HOST).

## 5. Health Checks y Procedimiento Operativo de Verificación
Sondeo de salud mediante HC-001 (/health), comando HEALTHCHECK y procedimiento reproducible con docker build y docker run.

## 6. Matriz de Linaje con ARCHITECTURE.md, SECURITY.md y CICD.md
Trazabilidad de directivas de despliegue con decisiones arquitectónicas y controles de seguridad.
```

### B. Manifiesto de Contenedor: `Dockerfile`
Estructura canónica requerida:
```dockerfile
# Stage 1: Build de dependencias
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime de producción
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY src/ ./src/

# Usuario sin privilegios por seguridad defensiva
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### C. Manifiesto de Exclusión: `.dockerignore`
Debe excluir: `.git`, `tests/`, `.pytest_cache`, `.venv`, `.harness`, `*.pyc`, `__pycache__`, `docs/`, `demo_apps/`.

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_deployment_skill.py`:
1. **Verificación Estructural de la Skill:** Frontmatter normativo v2.0, dependencias aguas arriba (etapas 01 a 09) y paridad idéntica entre `.agents/skills/10-deployment/SKILL.md` y `harness/skills/10_deployment.md`.
2. **Auditoría de TaskSpec:** `allowed_paths` delimitado a `docs/DEPLOYMENT.md`, `Dockerfile` y `.dockerignore`. Rechazo de modificaciones a `src/` o `tests/`.
3. **Auditoría de Anti-Patrones:** Detección y rechazo de Kubernetes, Helm, Swarm, Terraform o bases de datos externas cloud.
4. **Verificación de Coherencia Arquitectónica:** Empaquetado monolítico en Python 3.12, entrypoint canónico `src.main:app`, usuario non-root y endpoint `/health`.
5. **Verificación de Esquema Documental:** Comprobación de frontmatter y 6 secciones canónicas en `docs/DEPLOYMENT.md`.

---

## 11. Criterio de Término
La etapa de `deployment-automation` se considera formalmente concluida cuando:
- [ ] La skill `deployment-automation` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/10-deployment/SKILL.md` y `harness/skills/10_deployment.md`.
- [ ] La suite determinista `tests/harness/test_deployment_skill.py` está implementada y pasa 100% en verde.
- [ ] Los artefactos `docs/DEPLOYMENT.md`, `Dockerfile` y `.dockerignore` han sido generados y certificados sin violaciones de linter ni de TaskSpec.
- [ ] La totalidad de la suite de pruebas del arnés y de la aplicación se ejecuta con cero fallos (`exit_code == 0`).
