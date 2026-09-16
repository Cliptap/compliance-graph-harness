# Clinical Governance System

Sistema de gestión de datos clínicos con gobernanza media, construido con FastAPI, PostgreSQL, Vue 3 y Docker. Cumple con Ley 20.584 (Chile) para manejo de fichas clínicas, con RBAC, soft deletes y trazabilidad completa.

---

## Requisitos

- Docker 24+ y Docker Compose v2
- Python 3.12+ (solo para desarrollo local)
- Node 20+ (solo para desarrollo local del frontend)

---

## Inicio Rápido (Docker Compose)

```powershell
git clone <repo-url>
cd vibecoding
docker compose up --build
```

Esto levanta 3 servicios:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| PostgreSQL 15 | `5432` | Base de datos relacional |
| FastAPI Backend | `8000` | API REST con JWT + RBAC |
| Vue 3 Frontend (Nginx) | `8080` | Interfaz de usuario |

El backend espera a que PostgreSQL esté healthy antes de arrancar y crea las tablas automáticamente al iniciar.

### Accesos

| Recurso | URL |
|---------|-----|
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Frontend | http://localhost:8080 |

### Credenciales por defecto

| Campo | Valor |
|-------|-------|
| Email | `admin@clinic.com` |
| Password | `admin123` |

---

## Desarrollo Local

### Backend

```powershell
# Solo la base de datos en Docker
docker compose up -d db

# Entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# Dependencias
pip install -r requirements.txt

# Servidor en modo recarga automática
uvicorn src.backend.main:app --reload --port 8000
```

### Frontend

```powershell
cd src\frontend
npm install
npm run dev
```

El frontend corre en http://localhost:5173 y hace proxy a la API en `:8000`.

### Tests

```powershell
# Con la DB corriendo (docker compose up -d db)
pytest tests\unit\ -v

# Test manual de la API
python test_api.py
```

---

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:super_password@localhost:5432/vibedb` | Conexión a PostgreSQL |
| `SECRET_KEY` | `super_secret_hipaa_key` | Clave de firma JWT |

En Docker Compose se inyectan automáticamente. Para desarrollo local los defaults inline funcionan contra el PostgreSQL de Docker.

---

## Estructura del Proyecto

```
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── src/
│   ├── backend/
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── schemas.py           # Pydantic DTOs
│   │   ├── api/                 # Routers (patients, appointments, auth, etc.)
│   │   ├── security/            # JWT + bcrypt + RBAC dependencies
│   │   └── services/            # Business logic
│   ├── database/
│   │   ├── database.py          # SQLAlchemy async engine + session
│   │   ├── models.py            # ORM models
│   │   ├── repository.py        # Generic CRUD repository
│   │   └── events.py            # Soft-delete event listener
│   └── frontend/
│       ├── Dockerfile           # Vue build + Nginx
│       ├── package.json
│       └── src/
│           ├── main.js          # Vue 3 entry
│           ├── App.vue          # Root component
│           └── style.css        # Tailwind v4
├── tests/
│   └── unit/                    # Pytest tests (AAA, DB aislada, auth mocks)
└── docs/
    ├── CONTEXT.md               # Pipeline de desarrollo y conceptos
    ├── contexto/                # Artefactos del proyecto (product, tech-stack, workflow)
    └── skills/                  # Biblioteca de skills para vibecoding guiado
```

---

## Gobernanza

Este proyecto usa **gobernanza media**, lo que implica:

- Validaciones en frontend y backend para todo campo regulado
- RBAC con 3 roles: admin, médico, recepcionista
- Soft deletes en todas las entidades (`deleted_at`)
- Columnas de auditoría: `created_at`, `updated_at`
- Trazabilidad de quién crea y modifica cada registro
- Logs estructurados de ejecución
