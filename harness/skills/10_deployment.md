---
name: deployment
version: 2.0.0
depends_on: [prd-generation, architecture-design, backend-implementation]
stage: cross-cutting
project_types: [web_app, api, data_pipeline]
governance: all
description: Configuracion de despliegue. Define Docker, orquestacion, entornos, health checks y estrategia de secrets.
---

# Skill: Despliegue (Deployment)

## Objetivo
Configurar el despliegue del proyecto en el entorno objetivo, con Docker (si aplica),
health checks, variables de entorno y separacion dev/prod.

## Instrucciones
- **NO asumir Docker si el proyecto no lo necesita.**
- Cargar PRD y Arquitectura como contexto.
- Preguntar por seccion.
- Al final, generar archivos de configuracion de despliegue.

---

## Flujo de Interaccion

### 1. Estrategia de Containerizacion

```
? El proyecto necesita Docker?

a) Si — necesito containerizacion para estandarizar el entorno
   [RECOMENDADO si hay backend + base de datos]

b) Si, y necesito orquestacion (Docker Compose para multi-contenedor)

c) Si, usare Docker en produccion con orquestador cloud

d) No — el proyecto no necesita Docker
   (ej: CLI tool, script simple, frontend estatico en Vercel/Netlify)

⏳ Esperando tu respuesta.
```

### 2. Dockerfile (si aplica)

```
? Como debe ser la imagen Docker?

a) Multi-stage build — etapa de build + etapa runtime minimal
   [RECOMENDADO] Imagen final mas pequena y segura

b) Single stage — solo runtime, build fuera del Dockerfile

c) Distroless / Scratch — imagen minima sin shell
   Maxima seguridad, mas dificil de debuggear

? Imagen base?
  Python: python:3.12-slim (recomendado) o python:3.12-alpine
  Node: node:22-alpine (recomendado)
  Go: golang:1.22-alpine (build) + alpine:latest (runtime)

? Usuario non-root en el contenedor?
  [RECOMENDADO] Por seguridad, no ejecutar como root en produccion.
```

### 3. Docker Compose (si aplica)

```
? Que servicios necesitan correr juntos?

a) Solo backend: API + base de datos

b) Full stack: frontend + backend + base de datos

c) Con servicios adicionales:
   Redis (cache, colas), worker (background jobs), nginx (reverse proxy)

? Los volumenes para persistencia?
  - PostgreSQL data: volumen nombrado para que los datos sobrevivan reinicios
  - Archivos subidos: volumen compartido con la API

? Health checks para cada servicio?
  [RECOMENDADO] Para que Docker sepa si un contenedor esta realmente listo.
```

### 4. Separacion de Entornos

```
? Como separas dev y produccion?

a) docker-compose.override.yml para desarrollo
   Valores por defecto + override con puertos expuestos, hot reload, volumes

b) Archivos separados: docker-compose.dev.yml + docker-compose.prod.yml

c) Mismo archivo, variables de entorno diferentes (.env.dev vs .env.prod)

d) Solo necesito un entorno (desarrollo = produccion)

⏳ Esperando tu respuesta.
```

### 5. Variables de Entorno y Secrets

```
? Como manejas las variables de entorno?

a) Archivo .env (NO commitear, agregar .env.example al repo)
   [RECOMENDADO para MVP y desarrollo]

b) Secrets del orquestador (Docker Secrets, Kubernetes Secrets)

c) Servicio de secrets (AWS Secrets Manager, GCP Secret Manager, Vault)

? Que variables son secretas?
  - DATABASE_URL, SECRET_KEY, JWT_SECRET
  - API keys de terceros
  - SMTP password, credenciales cloud

? El .env.example debe estar commiteado con valores de ejemplo (sin secrets reales)
```

### 6. Health Checks

```
? Que endpoints de health necesita el proyecto?

a) Liveness: GET /health — responde 200 si el proceso esta vivo
   [MINIMO RECOMENDADO]

b) Readiness: GET /health/ready — verifica DB, cache, servicios externos
   Mejor para: orquestadores que necesitan saber si el servicio puede recibir trafico

c) Sin health checks — no necesario para MVP

⏳ Esperando tu respuesta.
```

### 7. SSL y Dominio (Produccion)

```
? La app se sirve con SSL en produccion?

a) Si — nginx reverse proxy con Let's Encrypt (certbot)
b) Si — Cloud Load Balancer con certificado gestionado (AWS/GCP)
c) Si — plataforma lo maneja (Vercel, Railway, Fly.io)
d) No — solo HTTP, es un entorno interno/desarrollo

? Tienes un dominio?
  Si: configurar DNS y SSL
  No: usar IP o subdominio de la plataforma
```

---

## Verificacion Post-Generacion

- [ ] Dockerfile usa multi-stage build
- [ ] El contenedor ejecuta como non-root
- [ ] docker-compose.yml define todos los servicios necesarios
- [ ] Health checks configurados para servicios criticos
- [ ] Volumenes para datos persistentes estan definidos
- [ ] .env.example existe con variables documentadas
- [ ] .env esta en .gitignore
- [ ] Puertos expuestos solo los necesarios (no exponer DB al host en prod)

## Condicion de Cierre

```
Voy a generar los archivos de configuracion de despliegue.
¿Confirmas que la estrategia es correcta?

⏳ Esperando tu confirmacion.
```
