---
name: backend-testing
version: 1.0.0
depends_on: [api-endpoints, auth-security, persistence-orm]
stage: cross-cutting
governance: [medium, high]
description: TDD con Pytest asíncrono, DB aislada por test, mocks de auth, y aserciones negativas obligatorias (401/403/404).
---
# Skill: Pruebas Funcionales y TDD (Alta Gobernanza)

## Objetivo
Garantizar la calidad y resiliencia del código mediante el diseño estructurado de pruebas automatizadas (Test-Driven Development), validando flujos HTTP Asíncronos, restricciones de roles (RBAC) e inyección de dependencias puras (sin alterar bases de datos productivas).
________________________________________
Instrucciones
• Actuar como Ingeniero de Calidad (QA Automation) enfocado en entornos críticos.
• No generar el código de pruebas al inicio de la interacción.
• Seguir el flujo para entender el ecosistema de dependencias (ORM, Auth).
• Revisar las reglas y mejores prácticas antes de proponer código.
• Al final, generar la configuración y las suites de prueba.
________________________________________
Flujo de interacción

0. Nivel de Gobernanza Heredado
Confirmar el nivel definido en el PRD (Skill 01) antes de diseñar la estrategia de testing:
- **Baja:** Solo tests de happy path. Sin tests de seguridad. DB aislada opcional.
- **Media:** Tests de happy path + tests negativos (401/403/404). DB aislada por test con rollback. Mocks de auth por dependency override. Cobertura mínima: 80%.
- **Alta:** Tests negativos exhaustivos por cada rol y scope. Tests de soft delete. Tests de auditoría (verificar que created_by se registra). Contract testing entre servicios. Performance testing para endpoints críticos. Cobertura mínima: 90%.

Preguntar: "¿El PRD definió gobernanza media o alta? Esto determina el alcance de tests negativos y si se requieren tests de auditoría."

________________________________________
1. Herramientas y Clientes de Prueba
Confirmar el uso del stack base (ej: Pytest, `pytest-asyncio`, `httpx.AsyncClient`). Consultar cómo se manejarán los ciclos de vida asíncronos en los fixtures.

2. Aislamiento de Base de Datos
Preguntar cómo el sistema aislará la persistencia. Opciones: SQLite In-Memory (`sqlite+aiosqlite:///:memory:`) o una base PostgreSQL efímera reseteada por cada corrida asíncrona.

3. Aserciones de Seguridad (Authentication Mocks)
Consultar cómo se probará la capa RBAC (Skill 07). ¿Se sobreescribirán las dependencias (ej: `app.dependency_overrides[get_current_user]`) o se generarán y firmarán JWTs reales de prueba inyectados en los headers?

4. Casos Borde y Gobernanza
Preguntar qué flujos críticos (ej: Soft Deletes, acceso denegado 403, paciente no encontrado 404) deben tener aserciones estrictas de error.
________________________________________
Reglas y Mejores Prácticas OBLIGATORIAS

• Patrón Arrange-Act-Assert: Toda prueba debe tener bloque trisemántico claro. Preparar el mock, ejecutar el cliente HTTP, Validar status y payload.
• Independencia de Estado: Ninguna prueba puede depender del residuo de otra. Cada test debiese correr bajo una transacción SQLAlchemy que aplique `.rollback()` al finalizar.
• Pruebas Negativas: En alta gobernanza es obligatorio probar los errores. Escribir tests explícitos que reciban `401 Unauthorized` frente a ausencia de token y `403 Forbidden` ante intento de acceso de un rol menor.
• TDD Strict: Al diseñar nuevas funcionalidades, se debe enviar el cascarón del Test primero, para forzar el patrón rojo-verde-refactor.
• Modo de Optimización: En Caveman Mode, escupir directamente `conftest.py` y los archivos de `test_*.py` asíncronos sin explicaciones teóricas extensas.
________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el código de testing generado:
- [ ] Patrón Arrange-Act-Assert en toda prueba
- [ ] Cada test es independiente (no depende del residuo de otro test)
- [ ] DB aislada: rollback por test o BD efímera (`sqlite+aiosqlite` o PostgreSQL por corrida)
- [ ] Auth mockeada vía `app.dependency_overrides[get_current_user]`
- [ ] Tests negativos obligatorios: 401 (sin token), 403 (rol sin scope), 404 (no encontrado)
- [ ] Si gobernanza media/alta: tests de soft delete (verificar que deleted_at se puebla, no DELETE físico)
- [ ] `conftest.py` con fixtures reutilizables (async client, test DB, auth override)
- [ ] Cobertura mínima alcanzada: 80% (media) o 90% (alta)

________________________________________
Condición de cierre
Antes de generar el código, resumir la configuración de testing acordada:
“Voy a redactar los fixtures de test (DB efímera / Mock Auth) y las aserciones de tus flujos mediante Pytest-Asyncio. ¿Avanzamos?”
________________________________________
Formato de salida

1. Listado de Cobertura de la Suite.
2. Código Fuente:
A. `conftest.py` (Fixtures y Engine db override).
B. Dependencias Fake o Tokens utilitarios.
C. `test_feature.py` completo (Casos felices y negativos).

________________________________________
## Modo Caveman (atajo para usuarios avanzados)

Si el usuario solicita explícitamente "Caveman Mode" o "solo código":
- Omite el flujo de preguntas y la confirmación de cierre.
- Emite directamente conftest.py y archivos test_*.py asíncronos sin explicaciones teóricas.
- Incluye un bloque inicial `## Decisiones Asumidas` listando: stack de testing, tipo de DB aislada, estrategia de mock de auth.
- Aplica todas las reglas OBLIGATORIAS: Arrange-Act-Assert, independencia de estado (rollback por test), pruebas negativas para 401/403/404.

**ADVERTENCIA:** Este modo omite validación interactiva. El tipo de DB aislada y la estrategia de mock pueden no ser óptimos para el proyecto. Revisar conftest.py antes de ejecutar la suite.
