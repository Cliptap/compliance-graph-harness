# Auth & Seguridad — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Arquitectura:** `docs/arquitectura/04_trazabilidad_alta_gobernanza.md`
> **Fecha:** 2026-06-11

## 1. Sistema Existente (Sin Cambios)

- OAuth2 + JWT con `python-jose`
- bcrypt para hashing de passwords
- RBAC con `SecurityScopes` de FastAPI
- 3 roles: admin, medico, recepcionista

## 2. Scopes Nuevos

Se agregan 2 scopes al sistema de RBAC existente:

| Scope | Rol | Endpoint |
|-------|-----|----------|
| `audit:read` | admin | GET /api/v1/audit |
| `audit:delete` | admin | DELETE /api/v1/audit |

## 3. Matriz RACI Actualizada

| Entidad | admin | medico | recepcionista |
|---------|-------|--------|---------------|
| patients | CRUD | R | CRUD |
| practitioners | CRUD | R | CRUD |
| appointments | CRUD | CRU | CRUD |
| **audit:read** | **R** | — | — |
| **audit:delete** | **D** | — | — |

## 4. Payload JWT

El JWT actual ya incluye `sub` y `scopes`. Se extienden los scopes:

```json
{
  "sub": "admin",
  "scopes": ["patients:read", "patients:write", "audit:read", "audit:delete"],
  "exp": 1718000000
}
```

## 5. Endpoints de Auth

Sin cambios. Los existentes (`POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`) siguen igual.

## 6. Políticas de Seguridad

Se mantienen las existentes:
- Rate limiting en login (5 intentos/15 min)
- CORS configurado explícitamente
- Headers de seguridad HTTP (HSTS, CSP)
- Secrets en `.env`

Se agrega:
- Validación `"confirm": "delete"` en DELETE /audit (previene borrados accidentales)
- Campos sensibles redactados como `[REDACTED]` en `audit_logs`

## 7. Propagación de Usuario a Event Listeners

Mecanismo: `ContextVar` de Python (thread-safe, compatible con async).

```python
# src/backend/security/context.py
from contextvars import ContextVar
current_user: ContextVar[str] = ContextVar("current_user", default="system")

# src/backend/security/dependencies.py
async def get_current_user(...):
    user = verify_token(...)
    current_user.set(user.username)  # ← propagar al listener
    return user

# src/database/events.py
from src.backend.security.context import current_user

def _get_current_user() -> str:
    try:
        return current_user.get()
    except LookupError:
        return "system"
```
