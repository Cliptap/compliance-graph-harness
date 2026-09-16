---
name: testing-strategy
version: 2.0.0
depends_on: [prd-generation, backend-implementation]
stage: cross-cutting
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Define la estrategia de testing: tipos de tests, herramientas, coverage, datos de prueba y CI integration.
---

# Skill: Estrategia de Testing

## Objetivo
Definir que, como y cuanto testear en el proyecto, alineado con el nivel de
gobernanza y las necesidades del MVP.

## Instrucciones
- **NO escribir tests sin tener la estrategia definida.**
- **Solo implementar el nivel de testing solicitado.** No agregar tipos de tests no pedidos.
- Preguntar por seccion.
- Al final, configurar el entorno de testing y generar tests base.

---

## Flujo de Interaccion

### 1. Nivel de Testing

```
? Que tipos de tests necesitas?

a) Unit tests — testear funciones/clases aisladas con mocks.
   Framework: pytest (Python), vitest/jest (TypeScript), testing (Go stdlib)
   Tiempo estimado: ~30% del tiempo de desarrollo
   [RECOMENDADO para todo proyecto]

b) Integration tests — testear integracion entre modulos (DB real o de prueba).
   Tiempo estimado: ~20% adicional

c) API tests — testear endpoints HTTP con cliente de prueba.
   Python: httpx + pytest, TypeScript: supertest

d) E2E tests — testear flujos completos desde el navegador.
   Herramientas: Playwright [RECOMENDADO], Cypress, Selenium
   Tiempo estimado: ~15% adicional

e) Sin tests — el MVP no incluye testing automatizado.
   (Solo recomendado para prototipos desechables)

⏳ Esperando tu respuesta.
```

### 2. Framework y Herramientas

```
Segun el stack definido en Arquitectura, recomiendo:

{recomendacion basada en el lenguaje elegido}

? Que framework de testing prefieres?

Python:
a) pytest — [RECOMENDADO] El standard, fixtures, parametrizacion, plugins

TypeScript:
a) vitest — [RECOMENDADO] Rapido, compatible con Vite, API tipo Jest
b) jest — Mas establecido, mas lento que vitest

Go:
a) testing (stdlib) — [RECOMENDADO] Sin dependencias externas
b) testify — Asserts y mocks mas expresivos

? Necesitas herramientas adicionales?
  - Faker para datos de prueba (Python: factory_boy, TS: @faker-js/faker)
  - Coverage (pytest-cov, vitest coverage, go test -cover)
  - Mocking (unittest.mock, vitest mocks, testify/mock)

⏳ Esperando tu respuesta.
```

### 3. Cobertura Objetivo

```
? Que porcentaje de cobertura necesitas?

a) Sin objetivo de cobertura — testear lo critico, sin numeros

b) 60% — cobertura basica, funciones principales testeadas

c) 80% — [RECOMENDADO para produccion] Buena cobertura sin obsesion

d) 90%+ — alta cobertura, incluye edge cases

? Que archivos/carpetas excluimos de cobertura?
  - Configuracion
  - Migraciones
  - Archivos generados
  - Types/interfaces (si no tienen logica)
```

### 4. Base de Datos para Tests

```
? Como manejamos la base de datos en tests?

a) SQLite en memoria — rapido, sin instalacion, ideal para unit/integration
   [RECOMENDADO para MVPs]

b) PostgreSQL de prueba en Docker — identico a produccion
   docker-compose con servicio db_test
   Mejor para: proyectos que usaran PostgreSQL en prod

c) Testcontainers — levanta DB real en contenedor programaticamente

d) Mock de repositorio — no usar BD real en tests
   Solo para unit tests puros

? Cada test usa una BD limpia? (crear/esquema/sembrar/destruir por test)
? O los tests comparten BD con datos sembrados una vez? (mas rapido, mas fragil)
```

### 5. Datos de Prueba (Fixtures)

```
? Como generamos datos de prueba?

a) Fixtures predefinidos — datos fijos en archivos JSON/YAML o diccionarios
   Mejor para: tests deterministicos, faciles de debuggear

b) Factories — generar datos aleatorios con valores por defecto
   Python: factory_boy, TypeScript: @faker-js/faker
   Mejor para: muchos tests, evitar acoplamiento a datos fijos

c) Mixto — fixtures para datos base, factories para variaciones

? Necesitas datos de prueba para autenticacion?
  - Usuario admin (token JWT)
  - Usuario regular
  - Usuario sin permisos
```

### 6. Ejecucion de Tests

```
? Como se ejecutaran los tests?

a) Manual: pytest / vitest / npm test / go test

b) Pre-commit hook: tests unitarios antes de cada commit
   Herramienta: pre-commit (Python), husky (TypeScript)

c) CI/CD: tests automaticos en cada push/PR
   GitHub Actions, GitLab CI
   [RECOMENDADO si el proyecto tiene CI/CD]

? Los tests deben pasar para hacer deploy? (quality gate)

⏳ Esperando tu respuesta.
```

### 7. Que Testear Primero (Priorizacion)

```
Para MVP, recomiendo testear en este orden de prioridad:

1. Logica de negocio critica (servicios, casos de uso)
2. Validaciones de datos (inputs, schemas)
3. Autenticacion y autorizacion (si aplica)
4. Endpoints de API (casos felices + errores comunes)
5. Edge cases y casos de error

? Estas de acuerdo con esta priorizacion?
? Hay algo especifico que consideres critico testear primero?
```

---

## Verificacion Post-Generacion

- [ ] El framework de testing esta instalado y configurado
- [ ] Hay al menos un test de ejemplo funcionando
- [ ] La configuracion de coverage esta definida
- [ ] Las fixtures/factories para datos de prueba estan creadas
- [ ] La BD de prueba esta configurada (si aplica)
- [ ] Los tests de auth mockean correctamente los tokens (si aplica)
- [ ] No se testearon librerias externas o codigo generado
- [ ] Los tests siguen el patron AAA (Arrange, Act, Assert)

## Condicion de Cierre

```
Voy a generar la configuracion de testing y los tests base.
¿Confirmas que la estrategia de testing es correcta?

⏳ Esperando tu confirmacion.
```
