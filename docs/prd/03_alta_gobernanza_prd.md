# PRD Técnico: Iteración 3 - Alta Gobernanza (Cumplimiento HIPAA)

## 1. Contexto y Objetivo
Migración del MVP a un sistema de salud de misión crítica. Implementación de Alta Gobernanza asegurando confidencialidad (HIPAA), trazabilidad e interoperabilidad.

## 2. Pila Tecnológica
* **Backend:** FastAPI (tipado estricto).
* **DB:** PostgreSQL.
* **ORM:** SQLAlchemy 2.0 (v1.x estrictamente prohibido).
* **Despliegue:** Docker, Docker Compose (Healthchecks y `depends_on: condition: service_healthy` orquestados secuencialmente).

## 3. Estándares de Datos Clínicos (HL7 FHIR)
Modelado de recursos estrictamente alineado a especificaciones HL7 FHIR:
* `Patient` (Ficha clínica del paciente).
* `Practitioner` (Profesional de salud/médico).
* `Appointment` (Cita clínica transaccional).
* Prohibición absoluta de modelos ad-hoc arbitrarios.

## 4. Seguridad de Ecosistema (Accesos)
* **Estándar:** OAuth2 combinado con JWT.
* **Autorización:** Control de Acceso Basado en Roles/Atributos (RBAC) vía `SecurityScopes` en FastAPI.
* **Permisos:** Definición granular (ej. `appointments:write`, `patients:read`).
* **Bloqueos:** Retorno determinista de HTTP 401/403 ante carencia de privilegios.

## 5. Auditoría y Trazabilidad Continua
* **Transaccionalidad:** Reemplazo de DELETE físico por Eliminación Lógica (Soft Delete) a través de Mixins.
* **Captura de Deltas:** Eventos nativos núcleo SQLAlchemy 2.0 (`do_orm_execute`).
* **Metadatos de Auditoría Inmutables:** Identificador del actor (NHI o UUID), Timestamp (UTC exacto), Operación (CRUD), Payload afectado.

## 6. Metodología de Integración Continuada
* **TDD Estricto (Test-Driven Development):** Rojo-Verde-Refactor mediante Pytest.
* **Secuencia de Desarrollo:** Generación de aserciones de validación esquemática y seguridad *previo* a la escritura del código funcional. Implementación mínima para asegurar pases verdes.