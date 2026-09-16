---
name: data-modeling
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: 2
project_types: [web_app, api, data_pipeline]
governance: all
description: Diseno del modelo de datos. Define entidades, relaciones, tipos, indices y estrategia de persistencia.
---

# Skill: Modelado de Datos

## Objetivo
Definir el esquema de datos del proyecto: entidades, atributos, relaciones,
tipos de datos, indices y estrategia de persistencia.

## Instrucciones
- Cargar PRD y Documento de Arquitectura como contexto.
- **NO generar SQL ni modelos sin tener todas las respuestas.**
- Preguntar por seccion.
- Al final, generar el esquema y el DDL.

---

## Flujo de Interaccion

### 1. Entidades Principales

```
Segun el PRD, los casos de uso principales involucran:

[Listar entidades candidatas inferidas de los casos de uso]

? Cuales son las entidades principales del sistema?
? Que atributos tiene cada una? (nombre, tipo, si es obligatorio)
? Hay entidades que se relacionan entre si? ?Como?

Ejemplo de respuesta esperada:
- Usuario: id, nombre, email (unico), password_hash, rol, fecha_creacion
- Producto: id, nombre, descripcion, precio, stock, categoria_id
- Categoria: id, nombre, descripcion

⏳ Describi las entidades y sus atributos.
```

### 2. Relaciones

```
Para cada par de entidades relacionadas, necesito saber:

? Que tipo de relacion es?

a) Uno a Uno (1:1)
   Ej: Usuario → Perfil (cada usuario tiene exactamente un perfil)

b) Uno a Muchos (1:N)
   Ej: Categoria → Productos (una categoria tiene muchos productos)

c) Muchos a Muchos (N:M)
   Ej: Estudiante ↔ Cursos (un estudiante toma muchos cursos y viceversa)

? La relacion es obligatoria en algun lado?
  Ej: Un producto SIEMPRE debe tener una categoria (NOT NULL),
  o un producto PUEDE no tener categoria (NULL permitido)

⏳ Esperando tu respuesta.
```

### 3. Motor de Base de Datos

Si no se definio en Arquitectura:

```
? Que motor de base de datos prefieres?

SQL (relacional):
a) PostgreSQL — [RECOMENDADO] Robusto, open source, mejor soporte para features avanzadas
b) MySQL / MariaDB — Ampliamente usado, buen ecosistema
c) SQLite — Sin servidor, ideal para desarrollo local, apps de escritorio

NoSQL:
d) MongoDB — Documentos JSON flexibles, sin esquema fijo
e) DynamoDB — Serverless en AWS, escalado automatico

⏳ Esperando tu respuesta.
```

### 4. Caracteristicas de los Datos

```
Necesito entender como se usaran los datos:

? Cual es el ratio estimado de lecturas vs escrituras?
  a) Mayormente lecturas (+80% reads) — tipico de catalogos, blogs, dashboards
  b) Balanceado (50/50) — tipico de CRUDs estandar
  c) Mayormente escrituras (+60% writes) — tipico de logging, eventos, IoT

? Hay picos de carga predecibles?
  Ej: fin de mes, horario laboral, eventos especiales

? Que consultas seran las mas frecuentes?
  Ej: "buscar por email", "listar productos por categoria", "filtrar por fecha"

⏳ Esta informacion determina que indices crear y como optimizar.
```

### 5. Estrategia de IDs y Llaves

```
? Como quieres identificar los registros?

IDs:
a) UUID v4 — aleatorio, no secuencial, seguro en APIs publicas [RECOMENDADO]
b) UUID v7 — ordenable por tiempo, compatible con indices B-tree
c) Auto-incremental (SERIAL / AUTO_INCREMENT) — simple, secuencial
d) Nanoid / ULID — alternativas modernas
e) ID de negocio — ej: SKU, RUN, codigo de cliente

Llaves foraneas:
a) Con integridad referencial (FOREIGN KEY con ON DELETE RESTRICT/CASCADE)
b) Sin integridad referencial (solo columnas con IDs, sin constraint)
   [No recomendado para gobernanza media/alta]

⏳ Esperando tu respuesta.
```

### 6. Indices y Performance

```
Segun el ratio de lectura/escritura y las consultas frecuentes:

? Que campos necesitan indices?

Sugerencia basada en lo que definiste:
- Indices para busquedas frecuentes: [lista inferida]
- Indices para claves foraneas: [lista inferida]
- Indices compuestos: [si hay queries con multiples filtros]

? Necesitas indices de texto completo? (para busquedas tipo Google)
? Necesitas indices geoespaciales? (para busquedas por ubicacion)

⏳ Esperando tu respuesta.
```

### 7. Auditoria y Trazabilidad (Segun Gobernanza)

Basado en el nivel de gobernanza del PRD:

```
Gobernanza {nivel}. Campos de auditoria requeridos:

Bajo: Sin campos de auditoria.
Medio: created_at, updated_at
Alto:  created_at, created_by, updated_at, updated_by, deleted_at (soft delete)

? Confirmas estos campos de auditoria?
? Para gobernanza alta: necesitas tabla de auditoria separada (event sourcing)
  o campos en cada tabla?
```

### 8. Estrategia de Migraciones

```
? Como manejaremos los cambios de esquema?

a) Migraciones versionadas (Alembic para Python, Knex/Prisma para TypeScript, golang-migrate)
b) Schema-first (definir esquema en SQL y generar codigo desde ahi)
c) Code-first (definir modelos en codigo y generar migraciones desde ahi)

? Necesitas datos semilla (seed data)? ?Que datos iniciales deberia tener la BD?
```

---

## Verificacion Post-Generacion

- [ ] Todas las entidades del PRD estan modeladas
- [ ] Atributos con tipo de dato definido para cada entidad
- [ ] Relaciones con cardinalidad y obligatoriedad especificadas
- [ ] Motor de BD elegido con justificacion
- [ ] PKs definidas (tipo y estrategia)
- [ ] FKs definidas con comportamiento ON DELETE
- [ ] Indices justificados por consultas frecuentes
- [ ] Campos de auditoria segun nivel de gobernanza
- [ ] Estrategia de migraciones definida

## Condicion de Cierre

```
Voy a generar el esquema de datos (DDL o definicion de modelos).
¿Confirmas que las entidades y relaciones son correctas?

⏳ Esperando tu confirmacion.
```
