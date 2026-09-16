---
name: architecture-design
version: 2.0.0
depends_on: [prd-generation]
stage: 2
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Diseno de arquitectura del sistema. Define patron, estructura de componentes, comunicacion y decisiones tecnicas estructurales.
---

# Skill: Diseno de Arquitectura

## Objetivo
Definir la arquitectura del sistema a partir del PRD, tomando decisiones estructurales
que condicionaran todo el desarrollo posterior.

## Instrucciones
- **NO empezar a disenar sin tener el PRD completo.**
- Cargar el PRD generado en la etapa anterior como contexto.
- Hacer preguntas por seccion.
- No avanzar sin respuesta.
- Al final, generar el Documento de Arquitectura y pedir confirmacion.

---

## Flujo de Interaccion

### 1. Patron Arquitectonico Principal

```
Segun el PRD (tipo: {tipo_proyecto}, escala: {escala}), recomiendo:

? Que patron arquitectonico prefieres?

a) Monolito — toda la logica en un solo deployable.
   Mejor para: MVPs, equipos pequenos, proyectos con baja complejidad.
   [RECOMENDADO para MVP]

b) Monolito modular — un deployable con modulos bien separados.
   Mejor para: proyectos que creceran, pero sin complejidad de microservicios.

c) Microservicios — servicios independientes comunicandose por API/eventos.
   Mejor para: equipos grandes, alta escala, despliegues independientes.

d) Serverless — funciones cloud sin gestion de servidores.
   Mejor para: cargas variables, bajo trafico inicial, eventos.

e) No estoy seguro — ayudame a decidir.

⏳ Esperando tu respuesta.
```

### 2. Estructura de Componentes

Solicitar o recomendar la division en capas/modulos:

```
Para un proyecto tipo {tipo}, una estructura tipica es:

- Capa de presentacion (frontend / CLI / API surface)
- Capa de aplicacion (logica de negocio, servicios, casos de uso)
- Capa de dominio (entidades, reglas de negocio puras)
- Capa de infraestructura (base de datos, APIs externas, filesystem)

? Esta estructura de capas te parece adecuada?
? Necesitas modulos adicionales? (ej: modulo de notificaciones, modulo de reportes)
? Hay integraciones con sistemas externos? (APIs de terceros, servicios cloud)

⏳ Esperando tu respuesta.
```

### 3. Comunicacion Entre Componentes

```
? Como se comunicaran los componentes?

Para frontend ↔ backend:
a) REST API — endpoints HTTP tradicionales
b) GraphQL — queries flexibles desde el cliente
c) gRPC — alta performance, tipado estricto
d) WebSockets — comunicacion bidireccional en tiempo real

Para backend ↔ backend (si aplica):
a) HTTP/REST directo
b) Cola de mensajes (RabbitMQ, SQS, Kafka)
c) Eventos (EventBridge, Pub/Sub)
d) No aplica — es un monolito

⏳ Esperando tu respuesta.
```

### 4. Estructura de Directorios

Preguntar y recomendar la organizacion de archivos:

```
? Como prefieres organizar el codigo?

a) Por feature/caso de uso:
   src/users/    (modelo + servicio + rutas + tests)
   src/orders/   (modelo + servicio + rutas + tests)
   [RECOMENDADO para la mayoria de proyectos]

b) Por tipo tecnico:
   src/models/
   src/services/
   src/routes/
   src/tests/
   Mejor para: proyectos muy pequenos (menos de 5 entidades)

c) Clean Architecture / Hexagonal:
   src/domain/
   src/application/
   src/infrastructure/
   src/presentation/
   Mejor para: proyectos que requieren alta testeabilidad y desacoplamiento

⏳ Esperando tu respuesta.
```

### 5. Decisiones de Stack Especifico

Si el PRD no definio stack concreto, preguntar ahora:

```
Necesito definir el stack concreto. Segun el tipo de proyecto ({tipo}):

Backend:
? Que lenguaje?
  a) Python (FastAPI / Django / Flask) — [RECOMENDADO para datos/API]
  b) TypeScript (Express / Fastify / NestJS)
  c) Go (Chi / Gin / Echo)
  d) Otro (especificar)

Base de datos:
? SQL o NoSQL?
  a) PostgreSQL — [RECOMENDADO para la mayoria de casos]
  b) MySQL / MariaDB
  c) SQLite — solo para desarrollo local o apps de escritorio
  d) MongoDB — documentos, esquema flexible
  e) Otra (especificar)

⏳ Esperando tu respuesta.
```

### 6. Estrategia de Manejo de Errores

```
? Como debe comportarse el sistema ante errores?

a) Fail Fast — fallar inmediatamente con mensaje claro.
   Mejor para: APIs, CLIs, sistemas donde el error debe ser visible.

b) Graceful Degradation — continuar con funcionalidad reducida.
   Mejor para: sistemas criticos que no pueden caer completamente.

c) Retry con backoff — reintentar operaciones fallidas automaticamente.
   Mejor para: llamadas a servicios externos, operaciones de red.

¿Necesitas alguna combinacion de estas estrategias?
```

### 7. Seguridad (Nivel Segun Gobernanza)

Basado en el nivel de gobernanza del PRD:

```
Gobernanza {nivel}. Eso implica:

Bajo: Sin autenticacion. Validacion basica de inputs.
Medio: Autenticacion basica (JWT/sesiones). Logs de actividad.
Alto: RBAC, auditoria completa, cifrado, secrets management.

? Confirmas este nivel de seguridad?
? Necesitas algo adicional no cubierto por la gobernanza?
```

---

## Verificacion Post-Generacion

- [ ] El patron arquitectonico esta justificado segun tipo y escala
- [ ] Los componentes estan claramente definidos con sus responsabilidades
- [ ] La comunicacion entre componentes esta especificada
- [ ] La estructura de directorios esta definida
- [ ] El stack tecnologico concreto esta decidido (lenguajes, frameworks, DB)
- [ ] La estrategia de errores esta definida
- [ ] El nivel de seguridad coincide con la gobernanza del PRD
- [ ] No se asumio nada que el PRD no contemple

## Condicion de Cierre

```
Voy a generar el Documento de Arquitectura.
¿Confirmas que la informacion es correcta?

⏳ Esperando tu confirmacion.
```
