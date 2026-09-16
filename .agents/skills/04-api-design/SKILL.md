---
name: api-design
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: 3
project_types: [web_app, api, mobile]
governance: all
description: Diseno de API. Define endpoints, metodos HTTP, DTOs, manejo de errores, autenticacion y documentacion.
---

# Skill: Diseno de API

## Objetivo
Definir la interfaz de API del sistema: endpoints, schemas de request/response,
codigos de estado, manejo de errores y documentacion.

## Instrucciones
- Cargar PRD, Arquitectura y Modelo de Datos como contexto.
- **NO generar codigo de endpoints sin tener el diseno completo.**
- Preguntar por seccion.
- Al final, generar la especificacion de API (OpenAPI o similar).

---

## Flujo de Interaccion

### 1. Estilo de API

```
? Que estilo de API prefieres?

a) REST — endpoints por recurso, HTTP methods, status codes.
   [RECOMENDADO para la mayoria de APIs]

b) GraphQL — queries flexibles, el cliente pide exactamente lo que necesita.
   Mejor para: frontends complejos, datos muy relacionados, equipos separados.

c) gRPC — alta performance, tipado estricto, streaming.
   Mejor para: microservicios internos, alta carga, comunicacion server-to-server.

d) RPC-style — endpoints por accion en vez de recurso.
   Mejor para: operaciones complejas que no mapean bien a CRUD.

⏳ Esperando tu respuesta.
```

### 2. Convenciones de Nombrado

```
? Que convenciones prefieres para los endpoints REST?

a) Plural + kebab-case:
   GET    /api/v1/productos
   POST   /api/v1/productos
   GET    /api/v1/productos/{id}
   PATCH  /api/v1/productos/{id}
   DELETE /api/v1/productos/{id}
   [RECOMENDADO]

b) Singular + camelCase (menos comun):
   GET    /api/v1/producto/{id}

c) Accion + recurso (RPC-style):
   POST   /api/v1/productos/buscar
   POST   /api/v1/productos/{id}/activar

⏳ Esperando tu respuesta.
```

### 3. Versionamiento

```
? Necesitas versionar la API desde el inicio?

a) Si, con prefijo en URL: /api/v1/..., /api/v2/...
   Mejor para: APIs publicas o que evolucionaran.

b) Si, con header: Accept: application/vnd.api+v1+json
   Mejor para: APIs que no quieren exponer version en URL.

c) No, por ahora no necesito versionamiento.
   Mejor para: MVP, APIs internas, prototipos.

⏳ Esperando tu respuesta.
```

### 4. Endpoints por Entidad

Para cada entidad del modelo de datos, preguntar:

```
Para la entidad {Entidad}:

? Que operaciones CRUD necesita?

a) GET /{entidades}        — listar (con paginacion? filtros? orden?)
b) GET /{entidades}/{id}   — obtener uno
c) POST /{entidades}       — crear
d) PATCH /{entidades}/{id} — actualizar parcial
e) PUT /{entidades}/{id}   — actualizar completo
f) DELETE /{entidades}/{id} — eliminar (soft o hard delete?)

? Necesita endpoints adicionales no CRUD?
  Ej: POST /productos/{id}/activar, GET /usuarios/{id}/reportes

⏳ Vamos entidad por entidad. Empecemos por {primera entidad}.
```

### 5. Paginacion, Filtros y Ordenamiento

```
Para los endpoints que devuelven listas:

? Que tipo de paginacion prefieres?

a) Offset-based: ?page=1&limit=20
   Simple, familiar. Problema: inconsistencia si se insertan/borran registros.

b) Cursor-based: ?cursor=abc123&limit=20
   Consistente. Mejor para datos que cambian frecuentemente.
   [RECOMENDADO para datos en tiempo real o feeds]

c) Sin paginacion — devolver todo (solo si el volumen es muy bajo)

? Que campos se podran filtrar?
  Ej: ?estado=activo&categoria=electronica&precio_min=1000

? Que campos se podran ordenar?
  Ej: ?order_by=nombre&order_dir=asc

⏳ Esperando tu respuesta.
```

### 6. Formato de Request/Response

```
? Como deben verse las respuestas?

a) Data plana:
   { "id": 1, "nombre": "Producto X", "precio": 100 }

b) Envelope estandar:
   {
     "data": { "id": 1, "nombre": "Producto X" },
     "meta": { "request_id": "abc" }
   }
   [RECOMENDADO para APIs que necesitan metadata]

c) Listas con envelope:
   {
     "data": [...],
     "meta": { "page": 1, "limit": 20, "total": 150 }
   }

? Incluimos campos de auditoria en la respuesta?
  (created_at, updated_at — segun gobernanza)

? Las fechas en que formato? ISO 8601? Timestamp Unix?

⏳ Esperando tu respuesta.
```

### 7. Manejo de Errores

```
? Como deben reportarse los errores?

a) RFC 7807 (Problem Details):
   {
     "type": "https://api.ejemplo.com/errores/validacion",
     "title": "Error de validacion",
     "status": 422,
     "detail": "El campo 'email' no es valido",
     "instance": "/api/v1/usuarios",
     "errors": [
       { "field": "email", "message": "Formato de email invalido" }
     ]
   }
   [RECOMENDADO para APIs publicas o de terceros]

b) Formato simple:
   { "error": "El campo 'email' no es valido" }
   Mejor para: APIs internas, MVPs.

? Que codigos HTTP usaremos consistentemente?
  - 200 OK, 201 Created
  - 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found
  - 409 Conflict, 422 Unprocessable Entity
  - 500 Internal Server Error

⏳ Esperando tu respuesta.
```

### 8. Autenticacion en Endpoints

Basado en el nivel de gobernanza:

```
Gobernanza {nivel}. Estrategia de auth:

Bajo: Sin autenticacion en endpoints.
Medio: JWT en header Authorization: Bearer {token} para endpoints protegidos.
       Endpoints publicos: login, registro (si aplica).
Alto: JWT + RBAC. Cada endpoint declara que roles pueden acceder.

? Que endpoints son publicos y cuales requieren autenticacion?
? Que endpoints requieren roles especificos?
```

### 9. Documentacion

```
? Como documentaremos la API?

a) OpenAPI (Swagger) — especificacion YAML/JSON, UI interactiva con Swagger UI
   [RECOMENDADO]

b) Postman Collection — exportable como JSON

c) Markdown manual — archivo API.md con endpoints documentados

d) Sin documentacion por ahora — MVP

⏳ Esperando tu respuesta.
```

---

## Verificacion Post-Generacion

- [ ] Todos los endpoints mapean a entidades del modelo de datos
- [ ] Cada endpoint tiene metodo HTTP, path, request/response schema
- [ ] Estrategia de paginacion, filtros y orden definida
- [ ] Formato de respuesta (envelope o plano) definido
- [ ] Manejo de errores definido (RFC 7807 o simple)
- [ ] Endpoints publicos vs protegidos claramente marcados
- [ ] Roles requeridos documentados (si gobernanza media/alta)
- [ ] Estrategia de documentacion definida

## Condicion de Cierre

```
Voy a generar la especificacion de API con todos los endpoints.
¿Confirmas que el diseno es correcto?

⏳ Esperando tu confirmacion.
```
