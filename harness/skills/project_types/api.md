---
name: project-type-api
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: cross-cutting
project_types: [api]
governance: all
description: Especificaciones adicionales para APIs puras (sin frontend). Cubre rate limiting, versionamiento, webhooks, SDK generation y monitoreo de API.
---

# Skill: API Pura (Backend sin Frontend)

## Objetivo
Refinar la arquitectura y el desarrollo para proyectos que son exclusivamente
un backend/API, sin interfaz grafica.

## Instrucciones
- Esta skill **complementa** las skills base, no las reemplaza.
- Activar solo si el tipo de proyecto es `api`.
- Hacer preguntas adicionales especificas de APIs.

---

## Flujo de Interaccion

### 1. Consumidores de la API

```
? Quienes van a consumir esta API?

a) Frontend propio (web o mobile) desarrollado por el mismo equipo

b) Desarrolladores externos / terceros (API publica)
   Implica: documentacion excelente, versionamiento, rate limiting, SLAs

c) Servicios internos (microservicios, backend-to-backend)
   Implica: latencia baja, alta disponibilidad, posiblemente gRPC

d) Mixto — frontend propio + posibles terceros en el futuro

⏳ Esperando tu respuesta.
```

### 2. Rate Limiting

```
? Necesitas rate limiting?

a) Si — para todos los endpoints
   Estrategia: X requests por ventana de tiempo por IP/usuario/API key

b) Si — solo en endpoints sensibles (login, registro, password reset)

c) No — no necesario para MVP o API interna

? Que limites?
  - Global: 100 requests/minuto por IP
  - Endpoints sensibles: 5 requests/minuto (login, password reset)
  - Endpoints costosos: 10 requests/minuto (reportes, exports)

? Como se informa al cliente?
  Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
  Retry-After cuando se excede el limite
```

### 3. Versionamiento de API

```
? Como versionas la API?

a) URL prefix: /api/v1/..., /api/v2/...
   [RECOMENDADO — mas simple, visible]

b) Header: Accept: application/vnd.api+json; version=1

c) Query param: /api/usuarios?version=1 (menos comun)

d) Sin versionamiento — MVP o API interna

? Cuantas versiones mantienes simultaneamente?
  [RECOMENDADO: solo la ultima + 1 version anterior por 6 meses]
```

### 4. Webhooks (Opcional)

```
? La API necesita enviar webhooks a sistemas externos?

a) Si — notificar eventos a URLs registradas por el cliente
   Ej: "orden.creada", "pago.completado", "usuario.eliminado"

b) No — solo request-response tradicional

Si si:
? Que eventos disparan webhooks?
? Los webhooks necesitan firma HMAC para que el receptor verifique autenticidad?
  [RECOMENDADO] — evita que cualquiera envie payloads falsos
? Estrategia de reintentos? (exponential backoff, max 5 intentos)
```

### 5. API Keys y Autenticacion de Servicios

```
? Como se autentican los consumidores de la API?

a) JWT (usuarios finales) — mismo sistema que auth normal

b) API Keys — keys estaticas para servicios/terceros
   Header: X-API-Key: abc123
   Mejor para: integraciones server-to-server

c) OAuth2 Client Credentials — client_id + client_secret → access token
   Mejor para: APIs publicas con registro de aplicaciones

d) Sin autenticacion — API abierta/privada

⏳ Esperando tu respuesta.
```

### 6. SDK y Client Libraries (Opcional)

```
? Necesitas generar SDKs o client libraries para tu API?

a) Si — OpenAPI Generator genera clients automaticamente
   Lenguajes: TypeScript, Python, Go, Java, etc.
   [RECOMENDADO si tienes consumidores externos]

b) Si, manual — escribir un client ligero en 1-2 lenguajes

c) No — los consumidores usaran HTTP directo
```

### 7. API Gateway / Reverse Proxy

```
? Necesitas un API Gateway?

a) No — la API recibe requests directamente

b) Si — nginx / Traefik como reverse proxy
   Funciones: SSL termination, CORS, compression, rate limiting basico

c) Si — API Gateway cloud (AWS API Gateway, GCP API Gateway, Kong)
   Funciones: rate limiting, authentication, request transformation, analytics

⏳ Esperando tu respuesta.
```

---

## Verificacion Post-Generacion

- [ ] Rate limiting configurado (si se solicito)
- [ ] Versionamiento documentado (si se solicito)
- [ ] Webhooks con firma HMAC (si se solicitaron)
- [ ] API Keys o Client Credentials (si se solicito)
- [ ] OpenAPI spec completa y validada
- [ ] SDK generado (si se solicito)
- [ ] Headers de seguridad HTTP configurados

## Condicion de Cierre

```
Voy a generar la configuracion adicional para API.
¿Confirmas que estas features son necesarias?

⏳ Esperando tu confirmacion.
```
