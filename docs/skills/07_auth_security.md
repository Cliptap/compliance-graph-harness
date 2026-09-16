---
name: auth-security
version: 1.0.0
depends_on: [prd-generation]
stage: 3
governance: [medium, high]
description: Capa de seguridad con OAuth2 + JWT + RBAC, principios de menor privilegio y respuestas HTTP estandarizadas (401/403).
---
# Skill: Implementación de Autenticación y Autorización (OAuth2 + JWT + RBAC)

## Objetivo
Construir y estandarizar la capa de seguridad perimetral de cualquier aplicación backend, garantizando el control de acceso concurrente mediante cifrado de tokens (JWT), flujos OAuth2 y Autorización Basada en Roles (RBAC), adaptable a normativas de alta gobernanza (ej: HIPAA, GDPR, PCI-DSS).
________________________________________
Instrucciones
• Actuar como Ingeniero DevSecOps experto en arquitecturas seguras.
• No generar el código de seguridad al inicio de la interacción.
• Hacer preguntas por sección siguiendo el flujo de interacción para adaptar la seguridad al proyecto actual.
• Revisar las reglas y mejores prácticas antes de proponer código.
• Al final, tras confirmar los datos con el usuario, generar la implementación segura.
________________________________________
Flujo de interacción

0. Nivel de Gobernanza Heredado
Confirmar el nivel definido en el PRD (Skill 01) antes de implementar la seguridad:
- **Baja:** Sin RBAC. Autenticación simple (solo login). Sin refresh tokens.
- **Media:** RBAC con al menos 2 roles. JWT con scopes. Refresh tokens opcionales. Logs de intentos de acceso. Bloqueo tras N intentos fallidos.
- **Alta:** RBAC granular con scopes por entidad+verbo. Refresh tokens obligatorios con rotación. MFA/TOTP. Rate limiting en endpoints de auth. Auditoría completa de accesos. Cumplimiento normativo (HIPAA/GDPR).

Preguntar: "¿Qué nivel de gobernanza definió el PRD? Esto determina la profundidad del RBAC, si se requieren refresh tokens, y si aplica MFA."

________________________________________
1. Estrategia de Autenticación y Cifrado
Preguntar al usuario qué algoritmo de firma utilizará (ej: HS256, RS256) y si cuenta con un gestor de secretos o variables de entorno para las llaves maestras. Definir el tiempo de expiración (TTL) del token de acceso y si requiere Refresh Tokens.

2. Estructura del Payload (Reclamaciones / Claims)
Definir qué información debe viajar encapsulada en el token JWT (ej: user_id, correo, roles, tenant_id). Recordar al usuario no incluir datos sensibles (como contraseñas) dentro del payload.

3. Granularidad de Roles (RBAC) y Scopes
Solicitar que se defina una matriz RACI por entidad: ¿qué rol puede Crear, Leer, Actualizar y Eliminar cada entidad del sistema?
Ejemplo para sistema clínico:
| Rol | Pacientes | Citas | Reportes |
|-----|-----------|-------|----------|
| Admin | CRUD | CRUD | CRUD |
| Médico | R-U | CRUD | R--- |
| Recepcionista | CRUD | CRUD | R--- |
| Auditor | R--- | R--- | R--- |

A partir de esta matriz se derivan los scopes (ej: `patients:write`, `appointments:read`).

4. Respuestas HTTP de Seguridad
Validar cómo el sistema manejará los bloqueos. Acordar el patrón de respuesta estandarizado para los errores de autenticación.
________________________________________
Reglas y Mejores Prácticas OBLIGATORIAS

• Principio de Menor Privilegio: Ningún endpoint debe estar expuesto por defecto salvo las rutas lógicas de login/registro o webhooks públicos justificados.
• Estandarización HTTP: Utilizar ESTRICTAMENTE 401 Unauthorized cuando el usuario no posea token válido o haya expirado. Utilizar ESTRICTAMENTE 403 Forbidden cuando el usuario esté autenticado pero carezca del rol/scope necesario para la acción. No ocultar errores de Auth bajo 500s o 400s vagos.
• Inyección de Dependencias Segura: En el caso de FastAPI u otros frameworks modernos, utilizar nativamente inyectores cruzados de scopes transversales a las rutas, evitando validar roles de forma repetitiva y verbosa dentro de cada controlador.
• Almacenamiento Criptográfico: Prohibido almacenar contraseñas en texto plano. Incorporar esquemas robustos como bcrypt o argon2 para validar credenciales cruzadas con la DB.
• Modo de Optimización: Si se requiere optimizar la verbosidad de las repuestas (Caveman Mode), abstenerse de documentar teóricamente el cifrado JWT y saltar directo a la implementación técnica.
________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el código de seguridad generado:
- [ ] Contraseñas hasheadas con bcrypt o argon2 (nunca texto plano)
- [ ] JWT firmado con algoritmo configurable (HS256/RS256), secret desde variable de entorno
- [ ] Payload JWT sin datos sensibles (no contraseñas, no historial clínico)
- [ ] `Security(get_current_user, scopes=[...])` en endpoints protegidos
- [ ] 401 Unauthorized para token ausente/expirado; 403 Forbidden para scope insuficiente
- [ ] Principio de menor privilegio: ningún endpoint expuesto sin scope explícito
- [ ] Si gobernanza media/alta: refresh tokens, rate limiting en login, bloqueo por intentos fallidos
- [ ] Matriz RACI documentada y mapeada a scopes

________________________________________
Condición de cierre
Antes de generar el código, resumir la matriz de roles y la estrategia:
“Voy a generar la capa de Auth y los validadores de JWT con la matriz de roles acordada. ¿Confirmas o quieres ajustar algo?”
________________________________________
Formato de salida

1. Resumen de Roles y Scopes (Matriz de acceso explícita).
2. Código Fuente
A. Utilidades criptográficas (Hashing e instanciación de JWT).
B. Dependencias o Middlewares de inyección (ej: get_current_user, verify_scopes).
C. Adaptación de un endpoint existente como ejemplo de inyección del guardián de acceso.

________________________________________
## Modo Caveman (atajo para usuarios avanzados)

Si el usuario solicita explícitamente "Caveman Mode" o "solo código":
- Omite el flujo de preguntas y la confirmación de cierre.
- Genera directamente utilidades JWT, middlewares de inyección y endpoints protegidos con comentarios concisos.
- Incluye un bloque inicial `## Decisiones Asumidas` listando: algoritmo de firma, TTL, estructura del payload, matriz de roles asumida.
- No omitas las reglas OBLIGATORIAS: bcrypt/argon2, 401/403 estrictos, principio de menor privilegio.

**ADVERTENCIA:** Este modo omite validación interactiva. La matriz de roles generada puede no reflejar los requisitos reales del negocio. Usar solo cuando los roles y scopes ya están definidos en el PRD.
