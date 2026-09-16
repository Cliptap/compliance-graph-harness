# Tarea 02 — Endpoint GET /appointments con filtros

## Contexto del proyecto

API FastAPI con SQLAlchemy async, JWT auth, RBAC. La tabla `appointments` ya existe (modelo ORM en `src/database/models.py`). Necesitamos exponer un endpoint de listado con filtros.

## Requisito funcional

Agregar en `src/backend/api/appointments.py` (o crear el archivo si no existe) un endpoint:

```
GET /appointments
```

### Query params (todos opcionales)

| Param | Tipo | Descripción |
|---|---|---|
| `patient_id` | int (UUID/ID interno) | Filtra por paciente |
| `practitioner_id` | int | Filtra por médico |
| `date_from` | ISO date | Citas desde esta fecha (inclusive) |
| `date_to` | ISO date | Citas hasta esta fecha (inclusive) |
| `status` | str enum: `pending`,`confirmed`,`cancelled`,`completed` | Filtra por estado |
| `limit` | int (default 50, max 200) | Tamaño de página |
| `offset` | int (default 0) | Offset de paginación |

### Comportamiento

- Solo devuelve citas **no eliminadas** (soft delete: `deleted_at IS NULL`).
- **No** devuelve citas de pacientes también soft-deleted.
- Ordena por `scheduled_at` ascendente.
- Requiere JWT válido (usar dependency `get_current_user` que ya existe en `src/backend/security/`).
- Si el usuario tiene rol `receptionist`, solo ve citas de su `practitioner_id` (forzar el filtro aunque no lo pida).
- Si el usuario tiene rol `medico`, solo ve citas donde él es el practitioner.
- Si el usuario tiene rol `admin`, ve todo.
- **No** incluir datos sensibles del paciente (RUT, email) en la respuesta para roles no-admin.

## Formato de respuesta

```json
{
  "items": [
    {
      "id": 1,
      "patient_id": 42,
      "practitioner_id": 7,
      "scheduled_at": "2026-07-15T09:00:00",
      "status": "confirmed",
      "duration_minutes": 30
    }
  ],
  "total": 123,
  "limit": 50,
  "offset": 0
}
```

## Criterios de aceptación

- El endpoint existe en `/docs` (OpenAPI).
- Pasar `limit=999` → devuelve error 422 (no 200 silencioso).
- Pasar `status=invalid` → 422.
- Sin token → 401.
- Con token de `receptionist` pidiendo citas de otro médico → 403 o lista vacía (decisión tuya, pero documentala en un comment).
- Test unitario: filtrar por `date_from` y `date_to` excluye correctamente las citas fuera de rango.

## Restricciones explícitas

- **NO** crear un módulo de "filtros reutilizables" ni clases de query builder.
- **NO** agregar cache (Redis, etc.).
- **NO** agregar paginación con cursor / links HATEOAS. Offset/limit alcanza.
- **NO** agregar endpoints extra (`POST`, `DELETE`, etc.). Solo `GET`.
- **NO** incluir el response model con campos que no se devuelven realmente.
- **SÍ** type hints en todo.
- **SÍ** reusar las dependencias de auth/RBAC que ya existen en el proyecto.
