---
name: api-endpoints
version: 1.0.0
depends_on: [db-schema-design, auth-security, persistence-orm]
stage: 3
governance: [medium, high]
description: Construcción de API REST con FastAPI, Pydantic V2 estricto, inyección de dependencias y RBAC obligatorio.
---
# Skill: Generación de Endpoints y API REST

## Objetivo
Construir una API REST estructurada, segura y eficiente utilizando FastAPI, que garantice la integración limpia con bases de datos asíncronas, esquemas de validación estrictos y control de acceso basado en roles (RBAC) para el cumplimiento normativo.
________________________________________
Instrucciones
• Actuar como Arquitecto Backend experto en FastAPI y dependencias asíncronas.
• No generar el código de la API al inicio.
• Hacer preguntas por sección siguiendo el flujo de interacción.
• Revisar las reglas y mejores prácticas antes de proponer código.
• Al final, generar el código base del servicio.
________________________________________
Flujo de interacción

0. Nivel de Gobernanza Heredado
Antes de diseñar la API, confirmar el nivel definido en el PRD (Skill 01):
- **Baja:** Sin RBAC obligatorio. Endpoints sin scopes. Respuestas HTTP básicas.
- **Media:** RBAC con al menos 2 roles. Logs de acceso. 401/403 estandarizados. Schemas Pydantic con campos de auditoría expuestos donde corresponda.
- **Alta:** RBAC granular con scopes por entidad y verbo. Auditoría completa de accesos. FHIR compliance si es contexto clínico. Rate limiting.

Si la skill 01 (PRD) no se ha ejecutado, preguntar: "¿Qué nivel de gobernanza definió el PRD? Si no existe PRD, ¿qué nivel necesitas?"

________________________________________
1. Configuración de Ciclo de Vida (Lifespan)
Preguntar cómo se manejarán los eventos de inicio y apagado de la aplicación (ej: inicialización de Base de Datos asíncrona, cierre de pools de conexiones) utilizando el decorador @asynccontextmanager.

2. Entidades y Esquemas DTO (Pydantic V2)
Validar cuáles son las entidades expuestas. En contextos clínicos, confirmar restricciones de tipado (ej: Modelos FHIR) y prevenir fugas de datos usando configuraciones de Pydantic como model_config = ConfigDict(from_attributes=True).

3. Inyección de Repositorios y Seguridad
Acordar cómo se inyectarán las dependencias en las rutas. Específicamente, cómo el get_db interactúa con los repositorios y cómo se interceptará a los usuarios mediante SecurityScopes.

4. Manejo Estructurado de Excepciones
Preguntar si el sistema usará Exception Handlers globales para capturar errores del ORM o si se delegará a HTTPException en los controladores.
Además, preguntar: ¿La API es consumida solo por un frontend propio (errores HTTP estándar con mensaje simple) o también por terceros/integraciones (necesitan Problem Details RFC 7807 con type, title, status, detail, instance)?
________________________________________
Reglas y Mejores Prácticas OBLIGATORIAS

• Arquitectura por Capas: Desacoplar Controladores de Lógica. Las rutas de FastAPI (@router.get(...)) deben limitarse a orquestar las Inyecciones de Dependencia (Depends) y delegar la resolución a los Repositorios/Servicios.
• Pydantic Estricto: Separar claramente Schemas de Entrada (Create/Update) de Salida (Response). Nunca devolver el modelo del ORM directamente sin pasarlo por una validación Pydantic que oculte datos sensibles.
• RBAC Obligatorio: En un contexto de Alta Gobernanza, todo endpoint de negocio debe tener el interceptor de seguridad indicando explícitamente los scopes requeridos (ej. Security(get_current_user, scopes=["read:patients"])).
• Convenciones RESTful: Usar rutas plurales (/api/v1/patients) y responder con códigos HTTP correctos (201 CREATED para POST, 204 NO CONTENT para DELETE).
• Modo de Optimización: En Caveman Mode, saltar las explicaciones teóricas y devolver el código fuente del FastAPI Lifespan, los Routers y los Schemas con comentarios concisos.
________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el código API generado:
- [ ] Lifespan con `@asynccontextmanager` para init/shutdown de DB
- [ ] Schemas Pydantic V2 separados: Create/Update vs Response (nunca expone modelo ORM directo)
- [ ] `model_config = ConfigDict(from_attributes=True)` en schemas de respuesta
- [ ] Todos los endpoints de negocio tienen `Security(get_current_user, scopes=[...])`
- [ ] Rutas RESTful plurales (`/api/v1/patients`)
- [ ] Códigos HTTP correctos: 201 para POST, 204 para DELETE, 200 para GET/PUT
- [ ] Exception handlers globales o RFC 7807 si es API para terceros
- [ ] Controladores delegando lógica a servicios/repositorios (no SQL en rutas)

________________________________________
Condición de cierre
Antes de generar el código:
“Voy a generar el esquema de la API con Inyección de Repositorios, manejo Lifespan para DB y validación de scopes obligatoria. ¿Confirmas para emitir el código?”
________________________________________
Formato de salida

1. Listado de Controladores (Routers) propuestos.
2. Código Fuente:
A. main.py (App con Lifespan y montaje de Routers).
B. schemas.py (Pydantic DTOs limpios).
C. Ejemplo de un router.py aplicando la inyección completa.

________________________________________
## Modo Caveman (atajo para usuarios avanzados)

Si el usuario solicita explícitamente "Caveman Mode" o "solo código":
- Omite el flujo de preguntas y la confirmación de cierre.
- Genera directamente main.py, schemas.py y routers con comentarios concisos.
- Incluye un bloque inicial `## Decisiones Asumidas` listando lo que se dio por sentado (stack, RBAC, nivel de gobernanza).
- No omitas las reglas OBLIGATORIAS: el código debe cumplirlas aunque no se discutan.

**ADVERTENCIA:** Este modo omite validación interactiva. Usar solo para prototipado rápido o cuando el contexto del proyecto ya está completamente definido. No usar en entornos con requisitos normativos no resueltos.