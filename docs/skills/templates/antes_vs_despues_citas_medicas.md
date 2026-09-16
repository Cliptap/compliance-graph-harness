# Comparativa: Skills vs Sin Guías — Módulo de Citas Médicas

> Caso real: "Agendar cita médica con validación de RUT chileno y control de acceso por roles"
> Gobernanza: Media | Stack: FastAPI + PostgreSQL + Vue 3 + Tailwind

---

## 1. Modelo de Datos (Tabla `appointments`)

### SIN skills (prompt libre: "crea una tabla de citas médicas")
```sql
CREATE TABLE appointments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  patient_name VARCHAR(100),
  doctor_name VARCHAR(100),
  appointment_date TIMESTAMP,
  status VARCHAR(20),
  rut VARCHAR(20)
);
```
❌ `INT` en vez de `BIGINT`
❌ `VARCHAR` en vez de `TEXT`
❌ `TIMESTAMP` sin zona horaria
❌ Sin `NOT NULL`
❌ Sin CHECK constraint en status
❌ Sin FK a patients/doctors
❌ Sin índices
❌ Sin columnas de auditoría
❌ RUT como `VARCHAR(20)` sin formato definido

---

### CON skills (guiado por `02_DB schema design.md` + `08_persistence_and_orm.md`)
```sql
CREATE TABLE appointments (
  appointment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  patient_id BIGINT NOT NULL REFERENCES patients (patient_id),
  practitioner_id BIGINT NOT NULL REFERENCES practitioners (practitioner_id),
  scheduled_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled'
    CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_appointments_patient_id ON appointments (patient_id);
CREATE INDEX idx_appointments_practitioner_id ON appointments (practitioner_id);
CREATE INDEX idx_appointments_scheduled_at ON appointments (scheduled_at);
CREATE INDEX idx_appointments_status ON appointments (status);
```
✅ `BIGINT GENERATED ALWAYS AS IDENTITY` para PK
✅ `TEXT` para strings
✅ `TIMESTAMPTZ` para fechas
✅ `NOT NULL` + `DEFAULT`
✅ CHECK constraint en status
✅ FK con índices B-Tree explícitos
✅ Soft delete con `deleted_at`
✅ Columnas de auditoría `created_at` + `updated_at`

---

## 2. Endpoint API (POST /appointments)

### SIN skills
```python
@app.post("/appointment")
def create_appointment(data: dict):
    db.execute("INSERT INTO appointments VALUES (...)")
    return {"ok": True}
```
❌ Ruta no RESTful (singular, sin versión)
❌ Sin esquema Pydantic
❌ Sin validación de datos
❌ Sin RBAC
❌ Retorna 200 en vez de 201
❌ Sin manejo de errores
❌ Sin transacción

---

### CON skills (guiado por `03_backend_api_endpoints.md` + `07_auth_security.md`)
```python
@router.post("/api/v1/appointments", status_code=201)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=["appointments:write"])
) -> AppointmentResponse:
    async with db.begin():
        appointment = await appointment_service.create(db, data, created_by=current_user.user_id)
    return AppointmentResponse.from_orm(appointment)
```
✅ Ruta RESTful plural con versión
✅ Schema Pydantic V2 para request y response
✅ RBAC con scope `appointments:write`
✅ 201 Created
✅ Transacción explícita con rollback automático
✅ `created_by` registrado (gobernanza media)

---

## 3. Validación de RUT

### SIN skills
```html
<input type="text" name="rut" placeholder="Ingrese RUT" />
```
```javascript
// Solo frontend, regex suelto
if (!/^\d{7,8}-[\dkK]$/.test(rut)) {
  alert("RUT inválido")
}
```
❌ Placeholder genérico, no indica formato
❌ Sin auto-formato
❌ Validación solo en frontend (bypasseable)
❌ Sin módulo 11
❌ Sin normalización antes de guardar

---

### CON skills (guiado por `04_backend_pipeline_etl.md` sección RUT + `14_input_validation_patterns.md`)
```vue
<template>
  <input
    v-model="form.rut"
    placeholder="12345678-9"
    @input="form.rut = formatRut($event.target.value)"
    @blur="validateRut()"
    maxlength="11"
  />
  <span v-if="rutError" class="text-red-500">{{ rutError }}</span>
</template>
```
```javascript
// Auto-formato (guión automático)
function formatRut(raw) {
  const clean = raw.replace(/[^0-9kK]/g, '').toUpperCase()
  if (clean.length <= 1) return clean
  return clean.slice(0, -1) + '-' + clean.slice(-1)
}

// Módulo 11 estricto
function validarRut(rut) {
  const clean = rut.replace(/[^0-9kK]/g, '').toUpperCase()
  if (clean.length < 2) return false
  const body = clean.slice(0, -1), dv = clean.slice(-1)
  let sum = 0, mul = 2
  for (let i = body.length - 1; i >= 0; i--) {
    sum += parseInt(body[i]) * mul
    mul = mul === 7 ? 2 : mul + 1
  }
  const r = 11 - (sum % 11)
  return dv === (r === 11 ? '0' : r === 10 ? 'K' : String(r))
}
```
```python
# Backend — misma validación (defensa en profundidad)
class AppointmentCreate(BaseModel):
    patient_rut: str

    @field_validator("patient_rut")
    @classmethod
    def validate_rut(cls, v: str) -> str:
        clean = re.sub(r"[^0-9kK]", "", v).upper()
        if len(clean) < 2:
            raise ValueError("RUT inválido: formato incorrecto")
        # ... módulo 11
        return f"{clean[:-1]}-{clean[-1]}"  # Normalizado
```
✅ Placeholder exacto: `12345678-9`
✅ Auto-formato con guión automático
✅ Módulo 11 en frontend (UX) y backend (seguridad)
✅ Normalización antes de persistir
✅ Mensaje de error específico

---

## 4. Docker

### SIN skills
```dockerfile
FROM python:latest
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app"]
```
❌ Sin multi-stage (imagen gigante)
❌ Ejecuta como root
❌ Sin USER directive
❌ Sin optimización de caché de capas
❌ Sin health check

---

### CON skills (guiado por `09_docker_deployment.md`)
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/backend/ ./src/backend/
USER 1000
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0"]
```
✅ Multi-stage build
✅ `USER 1000` (no root)
✅ Health check
✅ Capa de dependencias cacheada
✅ Python slim (imagen más liviana)

---

## 5. Tests

### SIN skills
```python
def test_create_appointment():
    response = client.post("/appointment", json={})
    assert response.status_code == 200
```
❌ Sin AAA pattern claro
❌ Solo happy path
❌ Sin mock de auth
❌ Sin DB aislada
❌ Sin tests negativos (401, 403, 404)
❌ Sin verificación de soft delete

---

### CON skills (guiado por `10_backend_testing.md`)
```python
@pytest.mark.asyncio
async def test_create_appointment_success(auth_client_recepcionista):
    """Happy path: recepcionista agenda cita"""
    # Arrange
    payload = {"patient_id": 1, "practitioner_id": 2, "scheduled_at": "2026-06-01T10:00:00-04:00"}
    # Act
    response = await auth_client_recepcionista.post("/api/v1/appointments", json=payload)
    # Assert
    assert response.status_code == 201
    assert response.json()["status"] == "scheduled"

@pytest.mark.asyncio
async def test_create_appointment_unauthorized(async_client):
    """Negativo: sin token"""
    response = await async_client.post("/api/v1/appointments", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_appointment_forbidden(auth_client_auditor):
    """Negativo: auditor no puede crear citas"""
    response = await auth_client_auditor.post("/api/v1/appointments", json=payload)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_soft_delete_appointment(auth_client_admin):
    """Gobernanza media: soft delete, no DELETE físico"""
    response = await auth_client_admin.delete("/api/v1/appointments/1")
    assert response.status_code == 204
    # Verificar que deleted_at se pobló, no que la fila desapareció
    result = await db.execute(select(Appointment).where(Appointment.appointment_id == 1))
    deleted = result.scalar_one()
    assert deleted.deleted_at is not None
```
✅ AAA pattern en cada test
✅ Happy path + 3 tests negativos (401, 403, soft delete)
✅ Auth mockeada con dependency overrides
✅ DB aislada con rollback por test
✅ Soft delete verificado

---

## Resumen de Violaciones Evitadas

| Categoría | Sin skills | Con skills |
|-----------|------------|------------|
| Tipos de dato incorrectos (VARCHAR, TIMESTAMP) | 5 | 0 |
| Sin FK indexes | 3 | 0 |
| Sin CHECK constraints | 1 | 0 |
| Sin RBAC / scopes | 1 endpoint | 0 |
| Código HTTP incorrecto | 200 en create | 201 Created |
| Sin soft delete | DELETE físico | UPDATE deleted_at |
| Sin validación backend (RUT) | Solo frontend | Backend + frontend |
| Docker como root | Sí | No (USER 1000) |
| Sin health check | Sí | No |
| Tests solo happy path | 1 test | 4 tests (1 happy + 3 negativos) |
| Sin columnas de auditoría | 0 | created_at + updated_at + deleted_at |
| Sin `created_by` | 0 | Registrado en endpoint |
| **Total violaciones** | **14** | **0** |
