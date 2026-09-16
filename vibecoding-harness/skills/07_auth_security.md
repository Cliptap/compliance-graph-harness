---
name: auth-security
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: 3
project_types: [web_app, api, mobile]
governance: [medio, alto]
description: Implementacion de autenticacion y autorizacion. Define JWT/OAuth2, RBAC, scopes, hashing y politicas de seguridad.
---

# Skill: Autenticacion y Seguridad

## Objetivo
Definir e implementar el sistema de autenticacion y autorizacion segun el nivel
de gobernanza establecido en el PRD.

## Instrucciones
- **Solo activar si la gobernanza es MEDIA o ALTA.** Para gobernanza baja, saltar.
- Cargar PRD y Arquitectura como contexto.
- Preguntar por seccion.
- Al final, generar la implementacion de auth.

---

## Flujo de Interaccion

### 1. Metodo de Autenticacion

```
? Que metodo de autenticacion usaremos?

a) JWT (JSON Web Token) — stateless, el token contiene claims del usuario.
   Access token (corta duracion, 15-60 min) + Refresh token (larga duracion, 7-30 dias).
   [RECOMENDADO para APIs REST]

b) Session-based — stateful, el servidor guarda la sesion, cookie con session ID.
   Mejor para: server-rendered apps, traditional web apps.

c) OAuth2 / OpenID Connect — delegar auth a un proveedor externo.
   Google, GitHub, Microsoft, Auth0, Clerk.
   Mejor para: apps que no quieren manejar passwords.

d) API Keys — simple, una key por cliente/usuairo.
   Mejor para: APIs de servicio a servicio, webhooks.

⏳ Esperando tu respuesta.
```

### 2. Algoritmo de Hashing (si aplica)

```
? Que algoritmo usaremos para hashear passwords?

a) bcrypt — [RECOMENDADO] Cost factor 12, ampliamente auditado
b) argon2id — Ganador del Password Hashing Competition, resistente a GPU
c) scrypt — Disenado para ser costoso en hardware

NUNCA uses: MD5, SHA-1, SHA-256 sin salt.

? Cuantas rondas / cost factor?
  bcrypt: 12 (balance velocidad/seguridad)
  argon2: time=3, memory=65536, parallelism=4
```

### 3. Payload del Token JWT

Si se eligio JWT:

```
? Que claims debe contener el JWT?

Claims estandar:
- sub: ID del usuario
- exp: tiempo de expiracion
- iat: tiempo de emision
- jti: ID unico del token (para revocacion)

Claims personalizados:
? Necesitas incluir el rol del usuario en el token?
? Necesitas incluir scopes/permisos especificos?
  Ej: "scope": "productos:read productos:write"

? Duracion del access token? [RECOMENDADO: 30 minutos]
? Duracion del refresh token? [RECOMENDADO: 7 dias]

⏳ Esperando tu respuesta.
```

### 4. Roles y Permisos (Gobernanza Alta)

```
Gobernanza ALTA. Necesitamos definir roles y permisos.

Para definir los roles, usaremos una matriz RACI simplificada:

Para cada entidad del sistema, preguntar:
? Quien puede CREAR {entidad}?
? Quien puede LEER {entidad}?
? Quien puede ACTUALIZAR {entidad}?
? Quien puede ELIMINAR {entidad}?

Ejemplo de resultado:
           | admin | editor | viewer
-----------|-------|--------|-------
productos  | CRUD  | CRU    | R
usuarios   | CRUD  | -      | -
reportes   | R     | R      | R

⏳ Vamos entidad por entidad.
```

### 5. Manejo de Sesiones y Tokens

```
? Donde se almacena el token en el frontend?

a) localStorage [COMUN pero vulnerable a XSS]
b) httpOnly cookie [RECOMENDADO — protegido contra XSS]
c) memory + refresh en cookie [MAS SEGURO — token en memoria, refresh en cookie]

? Necesitas proteccion CSRF?
  Si usas cookies → SI, implementar double submit cookie o SameSite=Strict

? Necesitas refresh token rotation?
  Cada vez que se usa un refresh token, se emite uno nuevo y se invalida el anterior.
  [RECOMENDADO para seguridad alta]

? Necesitas lista negra de tokens (logout)?
  Redis o DB en memoria para guardar tokens revocados hasta que expiren.
```

### 6. Politicas de Seguridad

```
? Que politicas de seguridad implementamos?

a) Rate limiting en login — maximo 5 intentos fallidos por IP/usuario en 15 min
   [RECOMENDADO]

b) Lockout temporal tras intentos fallidos — bloquear cuenta por 30 min

c) Validacion de fortaleza de password:
   Minimo 8 caracteres, al menos 1 mayuscula, 1 numero, 1 caracter especial

d) CORS configurado explicitamente (no wildcard * en produccion)

e) Headers de seguridad HTTP:
   - Strict-Transport-Security (HSTS)
   - Content-Security-Policy (CSP)
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY

f) Ninguna politica adicional — solo auth basica

⏳ Esperando tu respuesta.
```

### 7. Endpoints de Auth

```
La API de auth tipicamente incluye:

POST /auth/registro    — crear usuario nuevo (si aplica)
POST /auth/login       — autenticar, devolver tokens
POST /auth/refresh     — renovar access token con refresh token
POST /auth/logout      — invalidar refresh token
GET  /auth/me          — obtener perfil del usuario autenticado

? Necesitas todos estos endpoints?
? Necesitas verificacion de email? (confirmacion por link)
? Necesitas recuperacion de password? (reset por email)
```

---

## Verificacion Post-Generacion

- [ ] El metodo de autenticacion esta implementado segun lo acordado
- [ ] El hashing de passwords usa un algoritmo seguro (bcrypt/argon2)
- [ ] Los tokens JWT tienen duracion y claims definidos
- [ ] Roles y permisos estan implementados (si gobernanza alta)
- [ ] Rate limiting en login esta configurado
- [ ] CORS esta configurado explicitamente
- [ ] No hay secrets hardcodeados (todo en variables de entorno)
- [ ] Los endpoints de auth devuelven respuestas HTTP apropiadas (401, 403)
- [ ] Passwords y tokens NUNCA aparecen en logs

## Condicion de Cierre

```
Voy a generar el sistema de autenticacion y autorizacion completo.
¿Confirmas que la estrategia de seguridad es correcta?

⏳ Esperando tu confirmacion.
```
