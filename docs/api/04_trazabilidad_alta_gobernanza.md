# Diseño de API — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Arquitectura:** `docs/arquitectura/04_trazabilidad_alta_gobernanza.md`
> **Modelo de Datos:** `docs/modelo_datos/04_trazabilidad_alta_gobernanza.md`
> **Fecha:** 2026-06-11

## 1. Estilo y Convenciones

- **Estilo:** REST (existente, sin cambios)
- **Convención URL:** Plural + kebab-case: `/api/v1/patients`, `/api/v1/audit`
- **Versionamiento:** Prefijo `/api/v1/` (existente)

## 2. Endpoint Nuevo: Auditoría

### GET /api/v1/audit
- **Descripción:** Listar registros de auditoría con filtros
- **Auth:** JWT + scope `audit:read` (solo admin)
- **Parámetros de query:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `entity_type` | string | — | Filtrar por entidad: `patient`, `practitioner`, `appointment` |
| `entity_id` | UUID | — | Filtrar por ID de entidad |
| `changed_by` | string | — | Filtrar por actor |
| `operation` | string | — | Filtrar por tipo: `CREATE`, `UPDATE`, `DELETE` |
| `date_from` | ISO 8601 | — | Desde fecha |
| `date_to` | ISO 8601 | — | Hasta fecha |
| `page` | int | 1 | Página (offset-based) |
| `limit` | int | 50 | Registros por página (max 100) |
| `order_by` | string | `changed_at` | Campo de orden |
| `order_dir` | string | `desc` | Dirección: `asc` o `desc` |

- **Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "entity_type": "patient",
      "entity_id": "uuid",
      "field_name": "email",
      "old_value": "viejo@mail.com",
      "new_value": "nuevo@mail.com",
      "operation": "UPDATE",
      "changed_by": "recepcionista1",
      "changed_at": "2026-06-11T14:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 230,
    "pages": 5
  }
}
```

- **Response 401:** Token inválido o expirado
- **Response 403:** Usuario sin scope `audit:read`

### DELETE /api/v1/audit
- **Descripción:** Borrar registros de auditoría (requiere confirmación)
- **Auth:** JWT + scope `audit:delete` (solo admin)
- **Body:**
```json
{
  "confirm": "delete"
}
```
- **Response 200:**
```json
{
  "message": "Logs eliminados correctamente",
  "deleted_count": 150
}
```
- **Response 400:** Body no contiene `"confirm": "delete"`
- **Response 401:** Token inválido
- **Response 403:** Usuario sin scope `audit:delete`

## 3. Endpoints Existentes (Sin Cambios)

Patients, Practitioners, Appointments mantienen sus endpoints actuales. Lo único nuevo es que cada operación CRUD ahora dispara el registro automático en `audit_logs` vía SQLAlchemy listeners.

## 4. Paginación, Filtros y Orden

- **Paginación:** Offset-based (`page`, `limit`). Suficiente para el volumen actual (~50-100 logs/día).
- **Filtros:** Todos los campos de `audit_logs` son filtrables por query param.
- **Orden:** Default `changed_at DESC` (los más recientes primero).

## 5. Formato de Respuesta

- **Listas:** Envelope con `data` + `meta` (page, limit, total, pages)
- **Ítem único:** Estructura plana con los campos del modelo
- **Fechas:** ISO 8601 con UTC (`2026-06-11T14:30:00Z`)

## 6. Manejo de Errores

FastAPI ya genera RFC 7807 automáticamente. Se mantiene el formato existente:

```json
{
  "detail": "No tiene permisos para acceder a este recurso"
}
```

Códigos HTTP usados:
- `200 OK`, `201 Created`
- `400 Bad Request` (confirmación inválida en DELETE audit)
- `401 Unauthorized`
- `403 Forbidden` (sin scope requerido)
- `404 Not Found`
- `422 Unprocessable Entity` (validación Pydantic)
- `500 Internal Server Error`

## 7. Autenticación y Roles

| Endpoint | Roles |
|----------|-------|
| `GET /api/v1/audit` | Solo admin (scope `audit:read`) |
| `DELETE /api/v1/audit` | Solo admin (scope `audit:delete`) |
| Endpoints pacientes | admin, medico, recepcionista (según scope existente) |
| Endpoints médicos | admin, recepcionista |
| Endpoints citas | admin, medico, recepcionista |
| `POST /auth/login` | Público |
| `POST /auth/refresh` | Autenticado |
| `GET /auth/me` | Autenticado |

## 8. Documentación

OpenAPI/Swagger — FastAPI lo genera automáticamente en `/docs` y `/redoc`. Sin configuración adicional.

## 9. Diagrama de Secuencia — Registro de Auditoría

```
Cliente (Vue)         FastAPI Router        Service          SQLAlchemy         PostgreSQL
     │                      │                   │                  │                  │
     │ PATCH /patients/{id} │                   │                  │                  │
     │─────────────────────►│                   │                  │                  │
     │                      │ verify JWT+scope  │                  │                  │
     │                      │──────────────────►│                  │                  │
     │                      │                   │ update patient   │                  │
     │                      │                   │─────────────────►│                  │
     │                      │                   │                  │ UPDATE patients  │
     │                      │                   │                  │─────────────────►│
     │                      │                   │                  │◄─────────────────│
     │                      │                   │                  │ after_update     │
     │                      │                   │                  │ (event listener) │
     │                      │                   │                  │ INSERT audit_logs│
     │                      │                   │                  │─────────────────►│
     │                      │                   │                  │◄─────────────────│
     │                      │                   │                  │ COMMIT           │
     │                      │                   │                  │─────────────────►│
     │                      │                   │◄─────────────────│                  │
     │                      │◄──────────────────│                  │                  │
     │◄─────────────────────│                   │                  │                  │
     │ 200 OK               │                   │                  │                  │
```
