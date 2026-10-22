---
status: "APPROVED"
version: 1
governance_level: "bajo"
deployment_target: "docker"
container_engine: "docker"
exposed_port: 8000
healthcheck_endpoint: "/health"
last_audit: "2026-10-22"
---

# docs/DEPLOYMENT.md — Especificación de Despliegue y Empaquetado

## 1. Identidad de Despliegue y Arquitectura de la Unidad Desplegable
El sistema **Catálogo Comercial y Carrito de Compras Desacoplado** (`catalogo-carrito-web`) formaliza su empaquetado de producción bajo la directiva **`DEP-001` (Unidad Desplegable Monolítica Contenerizada)**.

En total coherencia con el nivel `governance_level: "bajo"` y la decisión arquitectónica `AD-001`, el sistema se empaqueta como un monolito desacoplado y autónomo. Esta unidad contiene la totalidad de los componentes operativos del sistema:
- El servidor web y API REST FastAPI ([`src/main.py`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/main.py)).
- El motor de catálogo y datos relacionales embebidos en SQLite ([`src/catalog/`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/catalog/)).
- La interfaz gráfica estática en HTML5, CSS y JavaScript Vanilla ([`src/frontend/`](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/src/frontend/)).

Esta aproximación elimina por completo la necesidad de orquestadores distribuidos, servidores proxy auxiliares o componentes intermedios de red, garantizando un despliegue inmediato con un solo comando.

---

## 2. Estrategia de Empaquetado en Contenedor

La construcción de la imagen de producción se realiza mediante una estrategia **Multi-Stage Build** estandarizada sobre la imagen base oficial `python:3.12-slim`:

1. **Etapa de Construcción (`builder`):**
   - Inicializa un entorno virtual aislado en `/opt/venv`.
   - Instala exclusivamente las dependencias declaradas en `requirements.txt` sin almacenar cachés transitorias de paquetes.
2. **Etapa de Ejecución (`runtime`):**
   - Se basa en una imagen limpia de `python:3.12-slim`.
   - Copia únicamente el entorno virtual `/opt/venv` desde la etapa `builder`, manteniendo la superficie de ataque al mínimo estricto.
   - Copia el código fuente del sistema ubicado en `src/`.
   - **Seguridad Defensiva y Usuario sin Privilegios:** Se crea el usuario de sistema `appuser` (`uid: 1000`) y se transfiere la propiedad del directorio `/app`. El contenedor se ejecuta bajo la directiva `USER appuser`, prohibiendo la ejecución como superusuario (`root`).
   - Expone formalmente el puerto TCP 8000 (`EXPOSE 8000`).
   - Define el comando de entrada canónico de la aplicación: `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`.

---

## 3. Gestión de Persistencia y Datos Semilla

De conformidad con `AD-005`, la persistencia relacional del catálogo comercial se gestiona de manera local mediante SQLite con SQLAlchemy:
- **Base de Datos Embebida:** No se requieren servicios de persistencia externos en red. La base de datos reside en el archivo relacional local gestionado por SQLAlchemy.
- **Ciclo de Vida y Precarga de Datos Semilla (`SEED-001`):** Durante el evento de arranque (`lifespan`) de FastAPI en `src/main.py`, la aplicación crea automáticamente las tablas requeridas e inicializa el catálogo con los cinco productos semilla declarativos (`SEED-001`) si no existen previamente.
- **Persistencia Opcional de Catálogo:** Para entornos donde se requiera preservar alteraciones locales entre reinicios de contenedor, basta con montar un volumen local sobre el archivo de base de datos o directorio de trabajo de la aplicación.

---

## 4. Variables de Entorno y Política de Secrets

En cumplimiento estricto de las directivas `AD-007` y `SEC-DEC-001` (Modo visitante anónimo):
- **Cero Secrets Obligatorios:** El contenedor no exige claves privadas, tokens JWT, contraseñas de bases de datos ni llaves de cifrado para arrancar y prestar servicio de catálogo. Todo acceso es público de solo lectura.
- **Variables Operacionales Opcionales:**
  - `PORT`: Puerto de escucha del servidor (por defecto: `8000`).
  - `HOST`: Interfaz de red de enlace (por defecto: `0.0.0.0`).
  - `DATABASE_URL`: Cadena de conexión relacional (por defecto: base de datos SQLite embebida).
- **Prohibición de Secrets en Imágenes:** Ningún archivo de configuración, token o credencial se copia a la imagen Docker (`SEC-CTRL-003`).

---

## 5. Health Checks y Procedimiento Operativo de Verificación

### 5.1 Directiva de Salud del Sistema (`HC-001`)
El sistema dispone del endpoint nativo de comprobación de salud en `/health` que responde `{"status": "healthy"}` con código HTTP 200.
El `Dockerfile` incorpora la directiva nativa:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

### 5.2 Procedimiento de Ejecución Local Reproducible
Para construir y ejecutar la unidad desplegable en cualquier entorno local:

```powershell
# 1. Construcción de la imagen inmutable de contenedor
docker build -t catalogo-carrito:1.0.0 .

# 2. Arranque del contenedor en segundo plano exponiendo el puerto 8000
docker run -d --name catalogo-app -p 8000:8000 catalogo-carrito:1.0.0

# 3. Verificación de liveness y estado de salud
curl -f http://localhost:8000/health

# 4. Verificación de consumo de API de catálogo (EP-001)
curl -f http://localhost:8000/api/v1/products
```

---

## 6. Matriz de Linaje con ARCHITECTURE.md, SECURITY.md y CICD.md

| Directiva de Despliegue | Requisito / Decisión Upstream | Documento Fuente | Propósito y Cumplimiento Técnico |
| :--- | :--- | :--- | :--- |
| **`DEP-001`** | `AD-001` (Monolito modular liviano) | [docs/ARCHITECTURE.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md) | Empaqueta frontend, backend y datos en una única unidad sin sobrecarga de microservicios. |
| **`DEP-001`** | `AD-005` (Stack tecnológico) | [docs/ARCHITECTURE.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/ARCHITECTURE.md) | Utiliza Python 3.12, FastAPI, SQLite y Vanilla JS en imagen ligera `python:3.12-slim`. |
| **Non-Root User** | `SEC-CTRL-001`, Defensa en Profundidad | [docs/SECURITY.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md) | Mitiga riesgos de elevación de privilegios ejecutando como `appuser` (UID 1000). |
| **Zero Secrets** | `AD-007`, `SEC-DEC-001` | [docs/SECURITY.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/SECURITY.md) | Modo visitante anónimo sin credenciales ni dependencias de bóvedas externas. |
| **`HC-001`** | `TP-001`, `GATE-001` | [docs/CICD.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/CICD.md), [docs/TEST_PLAN.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/TEST_PLAN.md) | Sondeo de salud en `/health` verificable por el arnés y por motores de contenedores. |
| **Multi-Stage Build** | `PIPE-001` | [docs/CICD.md](file:///c:/Users/oyana/OneDrive/Documentos/GitHub/compliance-graph-harness/docs/CICD.md) | Aislamiento de compilación vs runtime para imágenes finales pequeñas (< 200 MB). |
