# PRD — Iteración 4: Trazabilidad Alta Gobernanza

## 0. Tipo de Proyecto
- **Tipo:** web_app
- **Justificación:** Sistema full-stack existente (Vue 3 + FastAPI + PostgreSQL) que requiere extensión de capacidades de auditoría y trazabilidad sin modificar el stack.

## 1. Propósito
- **Problema:** El sistema actual no registra quién crea, modifica o elimina datos. No hay trazabilidad de operaciones CRUD a nivel de campo, impidiendo auditoría clínica-profesional y cumplimiento normativo.
- **Objetivo MVP:** Implementar trazabilidad granular de todas las operaciones CRUD (actor, acción, timestamp, campo, valor anterior/nuevo) sobre pacientes, médicos y citas, con vista de auditoría accesible solo por admin, construido y medido usando el harness de skills para evidenciar objetivamente su aporte.
- **No incluye:** Facturación, integración MINSAL, telemedicina, recetas electrónicas, historial clínico completo (solo datos administrativos de citas).

## 2. Usuarios
- **Roles:** admin, médico (medico), recepcionista (recepcionista) — se mantienen los 3 existentes.
- **Casos de uso principales:**
  - **Admin:** Ver historial de auditoría completo (todas las entidades), filtrar por entidad/entidad_id/actor/fecha. Borrar logs de auditoría (requiere escribir "delete" como confirmación).
  - **Médico / Recepcionista:** Operar pacientes, médicos y citas sin cambios en su flujo. Toda operación CRUD genera trazabilidad automática.
- **Escala esperada:** ~10 pacientes/día, volumen de auditoría bajo.
- **Autenticación:** Todos los usuarios requieren login. Sin usuarios anónimos.

## 3. Stack Tecnológico
- **Frontend:** Vue 3 + Vite + Tailwind CSS (existente)
- **Backend:** FastAPI + Pydantic 2.x (existente)
- **Base de datos:** PostgreSQL (existente)
- **ORM:** SQLAlchemy 2.0 con event listeners (existente, extender para capturar cambios por campo)
- **Auth:** OAuth2 + JWT + RBAC con `SecurityScopes` (existente)
- **Auditoría:** Tabla única `audit_logs` con columnas: `id, entity_type, entity_id, field_name, old_value, new_value, operation (CREATE/UPDATE/DELETE), changed_by, changed_at`
- **Infraestructura:** Docker + Docker Compose (existente)
- **Testing:** Pytest con TDD estricto (existente)

## 4. Datos
- **Tipo:** Estructurados (SQL relacional)
- **Volumen estimado de auditoría:** ~50-100 filas/día (10 pacientes × ~5 campos modificados × 2 operaciones). PostgreSQL lo maneja sin optimización especial.
- **Requisitos especiales:**
  - Tabla `audit_logs` en misma instancia PostgreSQL que las entidades principales.
  - Logs de auditoría solo pueden ser borrados por admin mediante endpoint que requiere escribir la palabra "delete" en el body como confirmación explícita.
  - Los logs de auditoría son modificables por admin (no inmutables a nivel DB).
  - Sin política de retención automática — el admin decide cuándo borrar.
- **Soft-delete:** Ya implementado mediante `SoftDeleteMixin`. La operación DELETE genera registro de auditoría con `old_value` = datos completos del registro eliminado.

## 5. Infraestructura
- **Entorno:** Docker Compose local (3 servicios: db, api, frontend)
- **Servicios cloud:** Ninguno
- **BD de auditoría:** Misma instancia PostgreSQL. Si escala en el futuro, se considera separación.

## 6. Contexto Normativo
- **Regulación aplicable:** Ninguna formal. Solo buenas prácticas.
- **Nota:** El consultorio opera en Chile y maneja datos administrativos de citas (no diagnósticos ni tratamientos). Ley 20.584 no aplica directamente a datos administrativos, pero se siguen estándares de seguridad como buena práctica.

## 7. Gobernanza
- **Nivel:** Alto
- **Implicaciones:**
  - RBAC con 3 roles (existente, se mantiene)
  - Trazabilidad granular por campo: todo CREATE/UPDATE/DELETE en pacientes, médicos y citas genera registro en `audit_logs`
  - Vista de auditoría exclusiva para admin (frontend + endpoint protegido por `SecurityScopes`)
  - Soft-delete en todas las entidades (existente)
  - Historial de cambios consultable por entidad y entidad_id
  - Borrado de logs con doble confirmación (palabra "delete")

## 8. Restricciones
- **Presupuesto:** $0 (herramientas open source, entorno local)
- **Deadline MVP:** Sábado 13 de junio de 2026
- **Licencias:** Sin restricción específica
- **Otras:**
  - **Evidencia de skills (obligatorio):** Se deben generar durante el desarrollo:
    - **ADRs (Architecture Decision Records):** Un mini-ADR en markdown antes de cada decisión de diseño (nueva entidad, patrón, cambio de estructura DB) conteniendo: problema, decisión tomada, por qué mejora la escalabilidad.
    - **Changelog de Impacto:** Ante cada bug fix o refactor, reportar complejidad anterior vs nueva, líneas de código muerto eliminadas.
    - **Entrevista de Cierre:** Al completar el sprint, el modelo debe generar un resumen de 3 puntos: ventaja de vibecoding vs escritura manual, cuellos de botella evitados, esfuerzo cognitivo ahorrado.
