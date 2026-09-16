# Modelo de Datos — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Arquitectura:** `docs/arquitectura/04_trazabilidad_alta_gobernanza.md`
> **Fecha:** 2026-06-11
> **Gobernanza:** Alta

## 1. Entidades Existentes (Sin Cambios)

### Patient
| Columna | Tipo | Restricciones |
|---------|------|---------------|
| id | UUID | PK, default gen_random_uuid() |
| rut | VARCHAR(20) | NOT NULL, UNIQUE |
| nombre_completo | VARCHAR(200) | NOT NULL |
| email | VARCHAR(200) | |
| prevision | VARCHAR(50) | |
| activo | BOOLEAN | NOT NULL, default TRUE |
| created_at | TIMESTAMPTZ | NOT NULL, default NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL, default NOW() |
| deleted_at | TIMESTAMPTZ | (soft delete) |

### Practitioner
| Columna | Tipo | Restricciones |
|---------|------|---------------|
| id | UUID | PK |
| rut | VARCHAR(20) | NOT NULL, UNIQUE |
| nombre_completo | VARCHAR(200) | NOT NULL |
| especialidad | VARCHAR(100) | |
| email | VARCHAR(200) | |
| telefono | VARCHAR(20) | |
| activo | BOOLEAN | NOT NULL, default TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | (soft delete) |

### Appointment
| Columna | Tipo | Restricciones |
|---------|------|---------------|
| id | UUID | PK |
| paciente_id | UUID | FK → patients.id, NOT NULL |
| medico_id | UUID | FK → practitioners.id, NOT NULL |
| fecha_hora | TIMESTAMPTZ | NOT NULL |
| duracion_minutos | INTEGER | NOT NULL, default 30 |
| estado | VARCHAR(20) | NOT NULL (Programada/Confirmada/Completada/Cancelada) |
| motivo_consulta | TEXT | |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | (soft delete) |

## 2. Nueva Entidad: AuditLog

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | UUID | PK, default gen_random_uuid() | Identificador único del registro de auditoría |
| entity_type | VARCHAR(50) | NOT NULL | Tipo de entidad: 'patient', 'practitioner', 'appointment' |
| entity_id | UUID | NOT NULL | ID del registro modificado |
| field_name | VARCHAR(100) | NOT NULL | Nombre del campo modificado |
| old_value | TEXT | NULL | Valor anterior (NULL en CREATE) |
| new_value | TEXT | NULL | Valor nuevo (NULL en DELETE) |
| operation | VARCHAR(10) | NOT NULL, CHECK IN ('CREATE','UPDATE','DELETE') | Tipo de operación |
| changed_by | VARCHAR(100) | NOT NULL | Username del actor (sin FK — sobrevive a borrado de usuario) |
| changed_at | TIMESTAMPTZ | NOT NULL, default NOW() | Timestamp UTC de la operación |

## 3. Relaciones

**AuditLog** — Sin FK hacia entidades ni usuarios:
- `entity_type` + `entity_id` identifican lógicamente el registro afectado
- `changed_by` almacena el username como texto (no FK)
- Justificación: los logs deben persistir aunque la entidad o el usuario se eliminen

**Entidades existentes** — Sin cambios:
- `Appointment.paciente_id` → FK `patients.id`
- `Appointment.medico_id` → FK `practitioners.id`

## 4. Motor de Base de Datos

**PostgreSQL** (existente). Justificación: ACID, integridad referencial, soporte nativo de UUID, TIMESTAMPTZ, y JSONB. Misma instancia que las entidades principales.

## 5. Características de los Datos

| Propiedad | Valor |
|-----------|-------|
| Ratio lecturas/escrituras | +90% escrituras (cada CRUD → N inserts en audit_logs) |
| Volumen estimado | ~50-100 filas/día (~10 pacientes × 5 campos × 2 ops) |
| Consultas más frecuentes | `WHERE entity_type = ? AND entity_id = ? ORDER BY changed_at DESC` |
| Picos | Sin picos predecibles (acoplados al uso normal del consultorio) |

## 6. Estrategia de IDs

**UUID v4** en todas las entidades (existente + nueva). Justificación: no secuencial, seguro en APIs, compatible con generación distribuida.

## 7. Índices

```sql
-- Consulta principal: historial de una entidad
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);

-- Búsqueda por actor
CREATE INDEX idx_audit_changed_by ON audit_logs(changed_by);

-- Orden cronológico (las queries siempre ordenan por fecha)
CREATE INDEX idx_audit_changed_at ON audit_logs(changed_at DESC);
```

## 8. Campos de Auditoría — Gobernanza Alta

| Entidad | Campos de auditoría |
|---------|-------------------|
| Patient | `created_at`, `updated_at`, `deleted_at` (SoftDeleteMixin) |
| Practitioner | `created_at`, `updated_at`, `deleted_at` (SoftDeleteMixin) |
| Appointment | `created_at`, `updated_at`, `deleted_at` (SoftDeleteMixin) |
| AuditLog | `changed_at` — registro inmutable de cuándo ocurrió cada cambio |

**Trazabilidad granular:** `AuditLog` captura cambios a nivel de campo (no solo de registro). Un UPDATE de 3 campos genera 3 filas en `audit_logs`.

## 9. Estrategia de Migraciones

**Alembic** (existente). Nueva migración:

```
alembic revision -m "add_audit_logs_table"
```

Contenido de la migración:
- `CREATE TABLE audit_logs` con todas las columnas
- `CREATE INDEX` para los 3 índices
- Sin seed data (los logs se generan automáticamente con el uso)

## 10. DDL Completo

```sql
-- Nueva tabla: audit_logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE')),
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indices
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_changed_by ON audit_logs(changed_by);
CREATE INDEX idx_audit_changed_at ON audit_logs(changed_at DESC);
```

## 11. Ejemplo de Datos de Auditoría

**CREATE paciente:**
| entity_type | entity_id | field_name | old_value | new_value | operation | changed_by |
|-------------|-----------|------------|-----------|-----------|-----------|------------|
| patient | abc-123 | — | NULL | (todos los campos) | CREATE | recepcionista1 |

**UPDATE paciente (cambia email y prevision):**
| entity_type | entity_id | field_name | old_value | new_value | operation | changed_by |
|-------------|-----------|------------|-----------|-----------|-----------|------------|
| patient | abc-123 | email | viejo@mail.com | nuevo@mail.com | UPDATE | recepcionista1 |
| patient | abc-123 | prevision | Fonasa | Isapre | UPDATE | recepcionista1 |

**DELETE cita (soft-delete):**
| entity_type | entity_id | field_name | old_value | new_value | operation | changed_by |
|-------------|-----------|------------|-----------|-----------|-----------|------------|
| appointment | xyz-456 | — | (snapshot completo) | NULL | DELETE | admin |
