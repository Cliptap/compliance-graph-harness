---
name: documentation
version: 2.0.0
depends_on: [prd-generation, backend-implementation, frontend-implementation]
stage: cross-cutting
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Generacion de documentacion del proyecto. Define README, API docs, ADRs, diagramas y guia de contribucion.
---

# Skill: Documentacion

## Objetivo
Generar la documentacion del proyecto: README, documentacion de API, guia de
desarrollo local, ADRs y cualquier otra documentacion necesaria.

## Instrucciones
- **NO generar documentacion sin preguntar que necesita el proyecto.**
- No todos los proyectos necesitan toda la documentacion posible.
- Preguntar por seccion.
- Al final, generar los archivos de documentacion.

---

## Flujo de Interaccion

### 1. README (OBLIGATORIO)

Todo proyecto necesita un README. Preguntar que secciones incluir:

```
El README es obligatorio. ?Que secciones necesita?

Secciones minimas recomendadas:
- [x] Titulo y descripcion (una frase)
- [x] Requisitos previos (lenguaje, herramientas)
- [x] Instalacion y configuracion local
- [x] Como ejecutar en desarrollo
- [x] Como ejecutar tests
- [x] Estructura del proyecto (arbol de directorios simplificado)

Secciones opcionales:
- [ ] Demo / screenshots
- [ ] Deploy a produccion
- [ ] Contribucion (CONTRIBUTING.md separado)
- [ ] Licencia
- [ ] Arquitectura (diagrama simplificado)
- [ ] Decisiones tecnicas (link a ADRs)
- [ ] API Reference (link a docs de API)

? Cuales secciones opcionales necesitas?
```

### 2. Documentacion de API

```
? Como documentamos la API?

a) OpenAPI / Swagger — generado automaticamente por el framework
   FastAPI: automatico en /docs
   Express: swagger-jsdoc + swagger-ui-express
   [RECOMENDADO]

b) Archivo API.md con endpoints documentados manualmente
   Mejor para: pocos endpoints, documentacion simple

c) Postman Collection exportada al repo (/docs/postman_collection.json)

d) Sin documentacion de API — MVP o API interna

⏳ Esperando tu respuesta.
```

### 3. Guia de Desarrollo Local

```
? Necesitas una guia de desarrollo local? (recomendado si hay +1 desarrollador)

La guia tipicamente incluye:
- Requisitos de software (versiones especificas)
- Clonar el repo
- Instalar dependencias
- Configurar variables de entorno (.env)
- Levantar servicios (DB, cache, etc.)
- Ejecutar migraciones
- Ejecutar seed data
- Correr la app en dev mode
- Correr tests

? Cuanta informacion quieres incluir?
```

### 4. Diagramas

```
? Necesitas diagramas en la documentacion?

a) Diagrama de arquitectura — componentes, servicios, comunicacion
   Herramientas: Mermaid (texto en markdown), draw.io (imagen)

b) Diagrama de base de datos — entidades y relaciones (ERD)
   Herramientas: dbdocs, SchemaSpy, Mermaid erDiagram

c) Diagrama de flujo — proceso de negocio, secuencia
   Herramientas: Mermaid sequenceDiagram

d) Sin diagramas — no necesario para MVP

? Los diagramas como texto (Mermaid) o como imagenes?
  [RECOMENDADO: Mermaid — se versiona en git, facil de editar]
```

### 5. Architecture Decision Records (ADRs)

```
? Necesitas ADRs para documentar decisiones arquitectonicas?

a) Si — para decisiones importantes (ej: por que PostgreSQL y no MongoDB)
   Formato: titulo, contexto, decision, consecuencias
   [RECOMENDADO para gobernanza alta o equipos de 3+]

b) No — el proyecto es pequeno o las decisiones estan en el README

Si si, ?que decisiones deberian documentarse?
  - Eleccion de base de datos
  - Eleccion de framework backend
  - Eleccion de framework frontend
  - Patron arquitectonico
  - Estrategia de autenticacion
```

### 6. Guia de Contribucion (Opcional)

```
? El proyecto es open source o tiene multiples contribuidores?

Si si, crear CONTRIBUTING.md con:
- Como reportar bugs
- Como proponer features
- Flujo de trabajo (fork, branch, PR)
- Estandares de codigo
- Como ejecutar tests antes de commit
- Convencion de commits (conventional commits)

? Necesitas esto ahora?
```

---

## Verificacion Post-Generacion

- [ ] README.md existe con las secciones minimas
- [ ] Las instrucciones de instalacion son correctas y reproducibles
- [ ] La documentacion de API es accesible (Swagger UI o archivo)
- [ ] Los diagramas son correctos y reflejan la arquitectura real
- [ ] Los ADRs siguen el formato estandar (si aplica)
- [ ] No hay informacion sensible en la documentacion (passwords, keys)
- [ ] Los comandos documentados funcionan (probados)

## Condicion de Cierre

```
Voy a generar la documentacion del proyecto.
¿Confirmas que las secciones y contenido son correctos?

⏳ Esperando tu confirmacion.
```
