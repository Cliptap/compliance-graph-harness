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
Esta skill define, estandariza y automatiza el empaquetado y la estrategia de despliegue del sistema en una unidad autocontenida, inmutable y reproducible, alineada con las decisiones arquitectónicas aprobadas en `docs/ARCHITECTURE.md`.
A diferencia de enfoques que improvisan plataformas DevOps sobrediseñadas, clústeres complejos o infraestructuras multi-nube prematuras, esta skill implementa el principio de **Unidad Desplegable Canónica y Proporcional (KISS / YAGNI)**:
- Empaqueta el sistema conforme a la arquitectura aprobada, consolidando los módulos y servicios validados en una unidad de despliegue reproducible (ej. contenedor OCI/Docker).
- Implementa una construcción limpia y segura mediante **Multi-Stage Build**, separando taxativamente las dependencias y herramientas de compilación/construcción del entorno liviano de ejecución.
- Aplica directivas de seguridad defensiva en la unidad de ejecución: ejecución bajo un **usuario sin privilegios** (non-root) y sondeo periódico de disponibilidad y salud operativa (`HEALTHCHECK`).
- Respeta estrictamente el modelo de seguridad y autenticación aprobado, evitando requerir credenciales o secrets ficticios en tiempo de arranque.
- Emite tres artefactos canónicos: la especificación de gobernanza `docs/DEPLOYMENT.md`, el `Dockerfile` de producción y `.dockerignore`.

---

## 2. Cuándo Usar
- Se activa en la **Etapa 9** del pipeline de desarrollo, inmediatamente después de que el código fuente ha superado satisfactoriamente los Quality Gates de Integración Continua en `09-cicd` (`docs/CICD.md` y flujos automatizados).
- Se utiliza para transformar el software validado en una unidad ejecutable lista para producción, asegurando que el despliegue no introduzca mutaciones inesperadas sobre la aplicación.
- Precede a la etapa de observabilidad y telemetría (`11-observability`).

---

## 3. Precondiciones
1. **Pipeline de Calidad Superado:**
   - Quality Gates deterministas certificados en verde por la suite de pruebas del arnés y CI/CD.
2. **Artefactos Previos Sellados:**
   - `docs/PRD.md` en estado `APPROVED`, clasificando el sistema y su nivel de gobernanza.
   - `docs/ARCHITECTURE.md` en estado `APPROVED`, con las decisiones estructurales vinculantes sobre el patrón arquitectónico, runtime de ejecución y persistencia.
   - `docs/DATA_MODEL.md` en estado `APPROVED`, con invariantes de datos y esquemas de persistencia.
   - `docs/SECURITY.md` en estado `APPROVED`, formalizando controles de seguridad y política de secretos.
   - `docs/TEST_PLAN.md` y `docs/CICD.md` en estado `APPROVED`.
3. **Código Base Funcional y Verificado:**
   - Módulos de aplicación y punto de entrada (entrypoint) verificados con endpoint de comprobación de salud operativa.
   - Manifiesto de dependencias sincronizado y testeado.

---

## 4. Entradas
La skill consume de manera estricta y exclusiva:
- **Desde `docs/ARCHITECTURE.md`:**
  - Patrón arquitectónico de la unidad desplegable (`AD-xxx`).
  - Runtime, stack tecnológico oficial y dependencias base.
  - Modelo de persistencia y almacenamiento aprobado.
  - Políticas de seguridad, sesiones y acceso.
- **Desde `docs/PRD.md`:**
  - Alcance MVP y cláusula `OUT OF SCOPE`: Prohíbe arquitecturas distribuidas pesadas o infraestructuras en nube no solicitadas.
- **Desde `docs/SECURITY.md`:**
  - Decisiones de autenticación y controles de seguridad para la gestión de credenciales y secrets.
- **Desde `docs/CICD.md`:**
  - Flujo de verificación continua previo y compuertas de calidad superadas.
- **Desde el Código Fuente Físico:**
  - Entrypoint canónico de la aplicación.
  - Interfaz o activos estáticos requeridos por el servicio.
  - Endpoint de comprobación de salud operativa (liveness/readiness).

---

## 5. Taxonomía Formal
Toda directiva, variable de entorno o comprobación de salud definida por esta skill debe utilizar identificadores estables y trazables:
- **`DEP-xxx` (Deployment Strategy):** Identificador formal de la estrategia y directivas de despliegue.
- **`ENV-xxx` (Environment Variable):** Variables de configuración operacional no confidenciales (ej. puerto TCP de escucha, host de interfaz de red).
- **`HC-xxx` (Health Check):** Directiva formal de comprobación de salud y disponibilidad operativa.

---

## 6. Regla de Oro Anti-Amnesia y Prohibición de Goldplating
1. **Prohibición de Infraestructura Pesada y Orquestadores Complejos:**
   - El agente **TIENE ESTRICTAMENTE PROHIBIDO** introducir:
     * Orquestadores de clústeres: Kubernetes (K8s), Helm, Docker Swarm, Nomad o Apache Mesos si no están en el PRD.
     * Infraestructura como Código (IaC): Terraform, Pulumi, CloudFormation, Ansible no solicitados.
     * Servidores proxy redundantes o servicios desacoplados en contenedores ajenos no contemplados en la arquitectura.
     * Bases de datos en red o externas que contradigan las decisiones de persistencia aprobadas en la arquitectura.
2. **Prohibición de Mutación de Código de Producción:**
   - La skill de despliegue tiene prohibido modificar archivos dentro de `src/**` o agregar dependencias a la aplicación. Su rol es **empaquetar el código validado existente, no reescribirlo**.
3. **Contenedor Seguro sin Privilegios (Non-Root User):**
   - El contenedor final de producción debe configurar y ejecutar bajo un usuario de sistema dedicado sin privilegios de superusuario (`non-root`), mitigando riesgos de escape de contenedor.
4. **Respeto a la Política de Secrets:**
   - Prohibido hardcodear secrets, contraseñas o exigir variables confidenciales ficticias que impidan el arranque del sistema.
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

El flujo de empaquetado y despliegue debe ser 100% determinista y reproducible localmente:

### Paso 1: Estrategia de Empaquetado en Contenedor (Multi-Stage Build)
- Etapa Builder: Aislamiento del entorno de dependencias y preparación del artefacto ejecutable.
- Etapa Runtime: Copia exclusiva de los artefactos necesarios, configuración de usuario non-root, exposición de puertos y sondeo de salud operativa.

### Paso 2: Filtrado de Artefactos (.dockerignore)
- Excluir archivos de control de versiones, suites de pruebas, cachés y artefactos locales de desarrollo para mantener la imagen ligera e inmutable.

### Paso 3: Especificación de Gobernanza (docs/DEPLOYMENT.md)
- Formalizar las 6 secciones canónicas documentando la estrategia de despliegue, persistencia, variables operacionales, health checks y matriz de linaje upstream.

### Paso 4: Verificación Operativa Local
- Ejecutar construcción local de la imagen y validación del health check en ejecución.

---

## 8. Señales de Alerta
Si el agente o desarrollador exhibe alguna de las siguientes señales, el arnés debe intervenir y detener la acción:
- Configurar servicios de base de datos o componentes externos incompatibles con la arquitectura aprobada.
- Ejecutar el contenedor como usuario `root` en la etapa final de runtime.
- Modificar el código fuente de la aplicación dentro de tareas de despliegue.
- Incorporar herramientas pesadas de orquestación en la nube (Kubernetes, Terraform) no requeridas en el MVP.
- Omitir el `.dockerignore`, provocando la inclusión de cachés de pruebas o historiales de control de versiones.
- Introducir secrets obligatorios o credenciales en el `Dockerfile` o variables de entorno mínimas.

---

## 9. Contrato de Salida Formal: `docs/DEPLOYMENT.md`, `Dockerfile` y `.dockerignore`

### A. Documento de Gobernanza: `docs/DEPLOYMENT.md`
El documento debe contener el siguiente frontmatter y 6 secciones canónicas estructuradas:

```markdown
---
status: "APPROVED" | "DRAFT"
version: 1
governance_level: "bajo" | "medio" | "alto"
deployment_target: "docker"
container_engine: "docker"
exposed_port: 8000
healthcheck_endpoint: "/health"
last_audit: "YYYY-MM-DD"
---

# docs/DEPLOYMENT.md — Especificación de Despliegue y Empaquetado

## 1. Identidad de Despliegue y Arquitectura de la Unidad Desplegable
Definición de la unidad desplegable y su correspondencia con el patrón arquitectónico aprobado.

## 2. Estrategia de Empaquetado en Contenedor
Diseño multi-stage build, imagen base oficial, configuración de usuario no-root y optimización de capas.

## 3. Gestión de Persistencia y Datos Semilla
Estrategia de persistencia, volúmenes de datos y precarga de semillas requeridas.

## 4. Variables de Entorno y Política de Secrets
Variables de configuración operacionales no sensibles y política de gestión de secrets.

## 5. Health Checks y Procedimiento Operativo de Verificación
Sondeo de salud mediante endpoint de comprobación operativa y comandos de verificación reproducible.

## 6. Matriz de Linaje con ARCHITECTURE.md, SECURITY.md y CICD.md
Trazabilidad de directivas de despliegue con decisiones arquitectónicas y controles de seguridad.
```

### B. Manifiesto de Contenedor: `Dockerfile`
Estructura canónica multi-stage build con usuario non-root y sondeo de salud operativa.

### C. Manifiesto de Exclusión: `.dockerignore`
Exclusión de artefactos temporales, cachés, directorios de pruebas y archivos de control de versiones.

---

## 10. Verificación del Artefacto
El arnés verifica el cumplimiento del contrato mediante pruebas deterministas en `tests/harness/test_deployment_skill.py`:
1. **Verificación Estructural de la Skill:** Frontmatter normativo v2.0, dependencias aguas arriba (etapas 01 a 09) y paridad idéntica entre `.agents/skills/10-deployment/SKILL.md` y `harness/skills/10_deployment.md`.
2. **Auditoría de TaskSpec:** `allowed_paths` delimitado a `docs/DEPLOYMENT.md`, `Dockerfile` y `.dockerignore`. Rechazo de modificaciones a `src/`, `tests/` o `.github/`.
3. **Auditoría de Anti-Patrones:** Detección y rechazo de Kubernetes, Helm, Swarm, Terraform o bases de datos externas no autorizadas.
4. **Verificación de Coherencia Arquitectónica:** Conformidad con la arquitectura y modelo de ejecución aprobados.
5. **Verificación de Esquema Documental:** Comprobación de frontmatter y 6 secciones canónicas en `docs/DEPLOYMENT.md`.

---

## 11. Criterio de Término
La etapa de `deployment-automation` se considera formalmente concluida cuando:
- [ ] La skill `deployment-automation` está normalizada con las 11 secciones canónicas y sincronizada en `.agents/skills/10-deployment/SKILL.md` y `harness/skills/10_deployment.md`.
- [ ] La suite determinista `tests/harness/test_deployment_skill.py` está implementada y pasa 100% en verde.
- [ ] Los artefactos `docs/DEPLOYMENT.md`, `Dockerfile` y `.dockerignore` han sido generados y certificados sin violaciones de linter ni de TaskSpec.
- [ ] La totalidad de la suite de pruebas del arnés y de la aplicación se ejecuta con cero fallos (`exit_code == 0`).

---

## Reference Context: Demo Implementation (catalogo-carrito-web)

En el proyecto de referencia comercial `catalogo-carrito-web`, los principios metodológicos generales de esta skill se instancian de la siguiente manera:

### 1. Entradas Específicas del Proyecto
- **Desde `docs/ARCHITECTURE.md`:**
  - `AD-001`: Patrón monolítico desacoplado en una sola unidad de ejecución.
  - `AD-003`: El carrito reside en Web Storage del cliente, eliminando persistencia transaccional multi-dispositivo en backend.
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

### 2. Taxonomía de Despliegue de la Demo
- `DEP-001`: "Unidad Desplegable Monolítica Contenerizada en Docker Multi-Stage".
- `HC-001`: "Sondeo de Liveness HTTP sobre `/health`".
- `SEED-001`: Datos semilla de catálogo precargados en SQLite embebido durante el startup.

### 3. Manifiesto Dockerfile de la Demo
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

### 4. Manifiesto .dockerignore de la Demo
Excluye: `.git`, `tests/`, `.pytest_cache`, `.venv`, `.harness`, `*.pyc`, `__pycache__`, `docs/`, `demo_apps/`.
