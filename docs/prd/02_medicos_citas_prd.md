# PRD Técnico: Iteración 2 - Médicos y Citas

## 1. Contexto y Objetivo
Tras completar el MVP de gestión de pacientes (Iteración 1), el sistema requiere evolucionar para soportar el "core" de un consultorio: el agendamiento clínico. 

**Objetivo:** Extender el sistema actual para gestionar el personal médico y coordinar las atenciones mediante citas, elevando la arquitectura a un nivel de **Gobernanza Media** que asegure la integridad transaccional y evite colisiones operativas.

## 2. Definición de Entidades y Cruce de Datos

Se incorporan dos nuevas entidades que se relacionarán con la tabla existente de `Pacientes`:

### Entidad: Médico (`doctors`)
* **Propósito:** Almacenar a los profesionales que atienden en el consultorio.
* **Atributos Principales:** 
  * `id` (PK, UUID)
  * `rut` (Único)
  * `nombre_completo`
  * `especialidad` (Ej: Medicina General, Pediatría)
  * `email` y `telefono`
  * `activo` (Booleano para soft-delete)

### Entidad Transaccional: Cita (`appointments`)
* **Propósito:** Registrar el encuentro programado entre un paciente y un médico.
* **Atributos Principales:**
  * `id` (PK, UUID)
  * `paciente_id` (FK -> `patients.id`)
  * `medico_id` (FK -> `doctors.id`)
  * `fecha_hora` (Timestamp)
  * `duracion_minutos` (Por defecto 30 min)
  * `estado` (Enum: Programada, Confirmada, Completada, Cancelada)
  * `motivo_consulta`

**Cruce de Datos (Relacionamiento):**
* **1:N (Médico a Citas):** Un médico tiene múltiples citas, pero solo puede tener una a la vez.
* **1:N (Paciente a Citas):** Un paciente tiene múltiples citas a lo largo de su historia clínica.

## 3. Lógica de Agendamiento y Reglas de Negocio (Gobernanza Media)

Para subir el nivel de gobernanza, el sistema de agendamiento debe aplicar reglas estrictas de validación de datos (cruce) *antes* de confirmar una inserción:

1. **Prevención de Colisiones (Double-Booking):** El sistema debe impedir transaccionalmente que un `medico_id` tenga dos citas con estado "Programada" o "Confirmada" cuyos bloques de tiempo (`fecha_hora` hasta `fecha_hora + duracion_minutos`) se superpongan.
2. **Restricción Temporal:** No se pueden agendar citas con `fecha_hora` en el pasado.
3. **Integridad Referencial Estricta:** No se puede crear una cita para un `paciente_id` o `medico_id` inexistente o inactivo.

## 4. Requisitos Técnico-Arquitectónicos

**Backend (API & DB):**
* **Endpoints Médicos:** CRUD estándar (`/doctors`).
* **Endpoints Citas:** Creación, lectura (filtrada por paciente o por médico), cancelación y actualización de estado (`/appointments`).
* **Base de datos (o Memoria temporal):** Definir constrains/validaciones que simulen y preparen el camino para índices únicos condicionales en PostgreSQL (Ej. `EXCLUDE` constraints temporalmente manejados por lógica de negocio en Pydantic/Service).

**Frontend:**
* Vista simple para ingresar médicos.
* Modal o formulario de "Nueva Cita" que permita seleccionar un paciente y un médico, mostrando un error amigable si el horario cruza con otro agendamiento.

## 5. Auditoría Básica
Para cumplir la gobernanza media, tanto `Médicos` como `Citas` deben incluir:
* `created_at` (Timestamp de creación).
* `updated_at` (Timestamp de última modificación).