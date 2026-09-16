---
name: persistence-orm
version: 1.0.0
depends_on: [db-schema-design]
stage: 3
governance: all
description: Capa de acceso a datos ORM-agnóstica con migraciones, transacciones explícitas, soft deletes y patrón repositorio.
---
# Skill: Capa de Persistencia y ORM (Agnóstico)

## Objetivo
Diseñar y construir los repositorios de acceso a datos utilizando patrones declarativos y migraciones seguras para la evolución persistente del esquema, garantizando la integridad transaccional y manejando estados complejos (como soft-deletes) sin importar el lenguaje de programación subyacente.
________________________________________
Instrucciones
• Asumir el rol de Arquitecto de Base de Datos enfocado en escalabilidad y transaccionalidad.
• Analizar el stack tecnológico actual del repositorio (`/src/`) e inferir el ORM más moderno y seguro aplicable (ej. SQLAlchemy 2.0 para Python, Prisma/TypeORM para Node/TS, Entity Framework para .NET).
• No devolver el código final de los repositorios sin antes evaluar los requerimientos estructurales.
• Navegar por las etapas de diseño haciendo consultas dirigidas.
• Referenciar obligatoriamente el contexto de la aplicación, identificando si existen normativas en juego (ej: nunca borrar datos físicos en entornos médicos).
________________________________________
Flujo de interacción

0. Nivel de Gobernanza Heredado
Confirmar el nivel definido en el PRD (Skill 01) antes de diseñar la capa de persistencia:
- **Baja:** Sin soft deletes. Sin columnas de auditoría. Transacciones opcionales.
- **Media:** Soft deletes en todas las entidades principales (`deleted_at`). Columnas de auditoría (`created_at`, `updated_at`). Transacciones explícitas con rollback.
- **Alta:** Soft deletes + columnas `created_by`, `updated_by`, `deleted_by`. Triggers de auditoría o temporal tables para historial completo de cambios. Row-Level Security (RLS) en PostgreSQL.

Preguntar: "¿El PRD definió gobernanza media o alta? Esto determina si se requieren soft deletes, columnas de auditoría y RLS."

________________________________________
1. Herramientas y Stack
Preguntar o confirmar cuál es el motor RDBMS principal y el framework de la aplicación. Confirmar el ORM a utilizar según las mejores prácticas del ecosistema detectado.

2. Motores y Tipos de Datos
Indagar sobre la necesidad de usar características especializadas (UUIDs nativos, JSONB, arreglos) soportadas por la base de datos y cómo mapearlas en el ORM elegido.

3. Transacciones y Concurrencia
Preguntar cómo deben manejarse las carreras críticas. ¿Se requieren bloqueos (locks) a nivel de fila o columnas de control de concurrencia optimista (versiones)?
________________________________________
Reglas y Patrones OBLIGATORIOS (Agnósticos)

• Transaccionalidad: Todo cambio múltiple debe ocurrir dentro de una transacción explícita que permita hacer `rollback` en caso de fallo parcial.
• Evolución de Esquemas: Prohibido sincronizar modelos directamente a la base de datos (ej. `sync_db()`, `db.create_all()` en producción). Siempre se debe inicializar y usar una herramienta de migración de esquemas (Alembic, Prisma Migrate, etc.).
• Gobernanza de Borrado (Soft Deletes): Salvo instrucción explícita contraria, todas las entidades principales deben implementar Soft Deletes (borrado lógico con columna `deleted_at` o `is_deleted`) en lugar de usar comandos `DELETE` directos.
• Patrón Repositorio: Aislar la lógica de consultas complejas en repositorios o Data Access Objects (DAOs). Los controladores/rutas no deben contener código SQL ni consultas ORM puras.
________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el código ORM generado:
- [ ] Transacciones explícitas con `rollback` en caso de fallo parcial
- [ ] Herramienta de migración configurada (Alembic/Prisma Migrate) — nunca `sync_db()` o `create_all()` en producción
- [ ] Soft deletes implementados en todas las entidades principales (`deleted_at` o `is_deleted`)
- [ ] Patrón repositorio: controladores no contienen SQL ni queries ORM directas
- [ ] Tipos especializados mapeados correctamente (UUID nativo, JSONB, arrays)
- [ ] Si gobernanza media/alta: columnas de auditoría `created_at`, `updated_at`, `created_by`, `updated_by`
- [ ] Estrategia de concurrencia definida: locks optimistas (version column) o pesimistas (SELECT FOR UPDATE)

________________________________________
Condición de cierre
Antes de emitir los archivos ORM y las configuraciones de migraciones, pide confirmación del diseño.
“Generaré el patrón de acceso a datos usando [ORM Seleccionado] incluyendo el sistema de migraciones. ¿Comenzamos con la configuración base?”
________________________________________
Formato de salida

1. Archivos de Modelos/Esquemas usando la sintaxis del ORM acordado.
2. Clases de Repositorio o Servicios para el acceso encapsulado a la base de datos.
3. Comandos o scripts iniciales para arrancar el sistema de migraciones asociado al framework elegido.
