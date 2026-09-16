# Deployment — Iteración 4: Trazabilidad Alta Gobernanza

> **Fecha:** 2026-06-11

## Decisión

**Docker Compose local** (existente). Sin cambios. 3 servicios: db (PostgreSQL), api (FastAPI), frontend (Vue + Nginx).

La nueva tabla `audit_logs` se crea vía migración Alembic al levantar los contenedores.

Health checks existentes se mantienen: `GET /health` en api.
