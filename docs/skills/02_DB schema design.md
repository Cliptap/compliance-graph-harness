---
name: db-schema-design
version: 1.0.0
depends_on: [prd-generation]
stage: 2
governance: all
description: Diseño de esquema PostgreSQL con tipos de datos estrictos, índices explícitos, restricciones CHECK y nomenclatura snake_case.
---
# Skill: Diseño de Esquema de Base de Datos en PostgreSQL

## Objetivo
Construir un esquema de base de datos relacional optimizado para PostgreSQL, aplicando las mejores prácticas de arquitectura, tipos de datos, restricciones e indexación.

________________________________________
Instrucciones
• No generar el código SQL al inicio.
• Hacer preguntas por sección siguiendo el flujo.
• Evaluar cada requerimiento aplicando las reglas de PostgreSQL (ver sección "Reglas y Mejores Prácticas de Postgres").
• No avanzar si falta información crítica.
• Al final, generar el esquema en código SQL limpio.
________________________________________
Flujo de interacción

1. Entidades y Propósito
Solicitar cuáles son las entidades principales del sistema (ej: Usuarios, Pedidos, Productos) y cuál es el propósito general del modelo.

2. Relaciones y Gobernanza de Datos
Solicitar cómo se relacionan las entidades (1:1, 1:N, N:M) y si existen reglas de negocio estrictas (ej: borrado en cascada, auditoría de cambios, RLS - Row Level Security).

3. Atributos y Naturaleza de los Datos
Para cada entidad, preguntar por los atributos clave. Evaluar si hay datos semi-estructurados que requieran JSONB, listas, rangos de fechas, o datos espaciales.

4. Patrones de Acceso y Volumen
Solicitar:
• ¿Cuál es el ratio esperado de lecturas vs escrituras? (ej: 80% lecturas, 20% escrituras). Esto determina la agresividad de los índices.
• ¿Hay picos de carga predecibles? (ej: lunes 8am después del fin de semana). Esto define estrategia de VACUUM y particionamiento.
• ¿Cómo se van a consultar más estos datos? (Filtros comunes, búsquedas de texto).
• Volumen estimado de registros por tabla a 1 año (para decidir si requiere particionamiento).
________________________________________
Reglas y Mejores Prácticas de Postgres (OBLIGATORIAS)

Aplicar estrictamente estas reglas al diseñar el modelo final:
• Llaves Primarias (PK): Usar `BIGINT GENERATED ALWAYS AS IDENTITY`. Usar `UUID` (gen_random_uuid) solo si se necesita opacidad o sistemas distribuidos.
• Tipos de Datos: 
  - Usar `TEXT` (nunca CHAR o VARCHAR). 
  - Usar `TIMESTAMPTZ` para fechas/horas (nunca TIMESTAMP sin zona horaria).
  - Usar `NUMERIC` para dinero o cálculos exactos (nunca FLOAT o MONEY).
  - Usar `BOOLEAN` (siempre con NOT NULL a menos que requiera 3 estados).
• Llaves Foráneas (FK): Siempre agregar índices B-Tree explícitos a las columnas que son FK, Postgres no lo hace automáticamente.
• JSONB: Usar `JSONB` (nunca JSON) para datos opcionales/variables y agregar índice `GIN`.
• Restricciones: Abusar de `NOT NULL`, constraints `CHECK` explícitos y `DEFAULT`.
• Nomenclatura: Todo en `snake_case` y en minúsculas (sin comillas dobles).

________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el esquema SQL generado:
- [ ] Todas las PK usan `BIGINT GENERATED ALWAYS AS IDENTITY` (o UUID justificado)
- [ ] Todos los textos usan `TEXT` (nunca VARCHAR/CHAR)
- [ ] Todas las fechas/horas usan `TIMESTAMPTZ`
- [ ] Dinero/cálculos exactos usan `NUMERIC` (nunca FLOAT/MONEY)
- [ ] Toda FK tiene índice B-Tree explícito
- [ ] JSONB con índice GIN (nunca JSON plano)
- [ ] CHECK constraints y NOT NULL donde corresponde
- [ ] Nomenclatura 100% snake_case en minúsculas
- [ ] Si gobernanza media/alta: columnas `created_at`, `updated_at`, `deleted_at` presentes

________________________________________
Condición de cierre
Antes de escribir el SQL, presentar un breve resumen de las tablas y relaciones y decir:
“Voy a generar el script SQL para PostgreSQL. ¿Confirmas o quieres ajustar algo?”

________________________________________
Formato de salida

1. Resumen de Arquitectura
• Tablas principales y sus relaciones funcionales.
• Decisiones clave de rendimiento (índices elegidos, uso de JSONB, particiones si aplica).

2. Script SQL Completo
```sql
-- Ejemplo de formato esperado:
CREATE TABLE users (
  user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices explícitos
CREATE UNIQUE INDEX users_lower_email_idx ON users (LOWER(email));
```
