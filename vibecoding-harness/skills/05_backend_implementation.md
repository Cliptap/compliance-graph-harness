---
name: backend-implementation
version: 2.0.0
depends_on: [prd-generation, architecture-design, data-modeling, api-design]
stage: 3
project_types: [web_app, api, data_pipeline, mobile]
governance: all
description: Implementacion del backend. Define estructura del proyecto, ORM, servicios, validaciones y configuracion.
---

# Skill: Implementacion Backend

## Objetivo
Implementar el backend del proyecto siguiendo la arquitectura, modelo de datos
y API definidos en las etapas anteriores.

## Instrucciones
- Cargar PRD, Arquitectura, Modelo de Datos y API Design como contexto.
- **NO escribir codigo sin haber definido la estructura y convenciones.**
- Preguntar por seccion.
- Al final, generar el codigo del backend completo.

---

## Flujo de Interaccion

### 1. Lenguaje y Framework

Si no se definio en Arquitectura:

```
? Que lenguaje y framework usaremos para el backend?

Python:
a) FastAPI — [RECOMENDADO] Async, validacion automatica con Pydantic, OpenAPI
b) Django + DRF — Baterias incluidas, admin automatico, ORM potente
c) Flask — Minimalista, flexible

TypeScript/JavaScript:
d) Express — El mas usado, ecosistema enorme
e) Fastify — Mas rapido que Express, schema-first
f) NestJS — Opinionado, decorators, inspirado en Angular

Go:
g) Chi — Ligero, idiomatico, compatible con net/http
h) Gin — Rapido, popular, buena documentacion

i) Otro (especificar)

⏳ Esperando tu respuesta.
```

### 2. ORM / Capa de Datos

```
? Como manejaremos la persistencia?

a) ORM completo — modelos como clases, migraciones automaticas.
   Python: SQLAlchemy 2.0, Django ORM
   TypeScript: Prisma, TypeORM, Drizzle
   Go: GORM, Ent
   [RECOMENDADO para proyectos con relaciones complejas]

b) Query Builder — queries tipadas sin abstraccion completa.
   Python: SQLAlchemy Core
   TypeScript: Knex, Drizzle
   Go: sqlc

c) SQL raw — queries escritas a mano.
   Mejor para: queries muy especificas, maximo control.

d) Sin BD — el proyecto no persiste datos.

⏳ Esperando tu respuesta.
```

### 3. Estructura del Proyecto

```
? Como organizamos el codigo del backend?

a) Por feature:
   src/
     users/
       router.py / controller.ts
       service.py / service.ts
       repository.py / repository.ts
       model.py / model.ts
       schemas.py / dto.ts
       tests/
     products/
       ...
   [RECOMENDADO — escala bien, facil de navegar]

b) Por capa tecnica:
   src/
     routes/
     services/
     repositories/
     models/
     schemas/
   Mejor para: proyectos pequenos (menos de 5 features)

c) Clean Architecture:
   src/
     domain/       (entidades, interfaces)
     application/  (casos de uso, servicios)
     infrastructure/ (ORM, APIs externas)
     presentation/ (routers, controllers)

⏳ Esperando tu respuesta.
```

### 4. Manejo de Configuracion

```
? Como manejaremos la configuracion?

a) Variables de entorno + archivo .env [RECOMENDADO]
   Python: pydantic-settings, python-dotenv
   TypeScript: dotenv + zod
   Go: viper, envconfig

b) Archivo de configuracion YAML/JSON
   Mejor para: configuraciones complejas con estructuras anidadas

c) Variables de entorno directamente (os.getenv / process.env)
   Mejor para: proyectos muy simples

? Que variables de configuracion necesitamos?
  - DATABASE_URL
  - SECRET_KEY / JWT_SECRET
  - API_PORT
  - LOG_LEVEL
  - Otras especificas del proyecto?

? Necesitamos diferentes configuraciones por entorno?
  (desarrollo, testing, produccion)
```

### 5. Validaciones

Basado en el nivel de gobernanza:

```
Gobernanza {nivel}. Estrategia de validacion:

Bajo: Validaciones basicas de tipo (string, int, email).
Medio: Validaciones de formato, longitud, rangos, unicidad.
Alto: Validaciones completas + sanitizacion + reglas de negocio complejas.

? Que campos necesitan validaciones especiales?
  Ej: RUT, telefono, moneda, fechas con formato regional.

? Las validaciones se ejecutan en el frontend, backend o ambos?
  [RECOMENDADO: Ambos — frontend para UX, backend para seguridad]
```

### 6. Logging y Observabilidad

```
? Que nivel de logging necesitas?

a) Minimo — print / console.log. Solo para desarrollo.

b) Estructurado — JSON logs con niveles (DEBUG, INFO, WARNING, ERROR).
   Python: structlog, logging + python-json-logger
   TypeScript: pino, winston
   Go: slog, zerolog
   [RECOMENDADO para produccion]

c) Avanzado — logs + metricas (Prometheus) + tracing distribuido.
   OpenTelemetry para tracing entre servicios.

? Que informacion NO debe aparecer en logs?
  (passwords, tokens, datos personales — nunca loguear esto)
```

### 7. Dependencias y Paquetes

```
? Como gestionamos las dependencias?

Python: requirements.txt + pip, pyproject.toml + poetry
TypeScript: package.json + npm/yarn/pnpm
Go: go.mod + go.sum

? Necesitas un gestor de entornos virtuales?
  Python: venv, poetry, conda
  TypeScript: nvm, fnm para Node.js
```

---

## Verificacion Post-Generacion

- [ ] El framework backend esta correctamente configurado
- [ ] La estructura de directorios coincide con lo acordado
- [ ] Los modelos reflejan el esquema de datos definido
- [ ] Cada endpoint de la API esta implementado
- [ ] Las validaciones corresponden al nivel de gobernanza
- [ ] La configuracion usa variables de entorno (nada hardcodeado)
- [ ] El logging esta configurado segun lo acordado
- [ ] El manejo de errores sigue el formato definido en API Design

## Condicion de Cierre

```
Voy a generar el codigo del backend completo.
¿Confirmas que la estructura y convenciones son correctas?

⏳ Esperando tu confirmacion.
```
