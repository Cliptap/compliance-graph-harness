---
name: frontend-testing
version: 1.0.0
depends_on: [frontend-ui, auth-security]
stage: cross-cutting
governance: [medium, high]
description: Testing frontend con component tests (Vitest + Vue Test Utils/Testing Library) y E2E (Playwright/Cypress), con aserciones de accesibilidad y estados de UI.
---
# Skill: Testing de Frontend (Component Tests + E2E)

## Objetivo
Garantizar la calidad del frontend mediante pruebas automatizadas de componentes y flujos end-to-end, validando estados de UI (loading, empty, error), interacciones de usuario y consumo de API, con enfoque en gobernanza media/alta.

________________________________________
## Instrucciones
- Actuar como QA Frontend especializado en testing de interfaces.
- No generar el código de pruebas al inicio.
- Hacer preguntas por sección siguiendo el flujo.
- No avanzar si falta información crítica.
- Al final, generar la configuración y suites de prueba.

________________________________________
## Flujo de interacción

0. Nivel de Gobernanza Heredado
Confirmar el nivel definido en el PRD (Skill 01):
- **Baja:** Sin tests de frontend obligatorios.
- **Media:** Component tests para componentes críticos (login, formularios de carga, dashboard). Tests de estados (loading, empty, error). E2E para flujo principal (login → carga de datos → visualización). Cobertura mínima: 60%.
- **Alta:** Component tests exhaustivos con todas las variantes de props. E2E para todos los flujos de negocio. Tests de accesibilidad (axe-core). Visual regression tests. Cobertura mínima: 80%.

________________________________________
1. Stack de Testing
Preguntar el stack a utilizar:
- **Framework de componentes:** Vitest (Vue/React) + Testing Library o Vue Test Utils.
- **E2E:** Playwright (recomendado, multi-browser) o Cypress.
- **Visual regression:** Percy, Chromatic, o Playwright screenshots.
- **Accesibilidad:** axe-core, pa11y, o Lighthouse CI.

________________________________________
2. Componentes a Testear
Solicitar la lista de componentes y qué validar en cada uno:
- **Props:** ¿Qué variantes de props deben testearse? (ej: botón primary vs secondary, disabled, loading).
- **Eventos:** ¿Qué eventos emite el componente? (click, submit, input).
- **Slots:** ¿Qué contenido se proyecta en slots?
- **Estados:** Empty, loading, error, success para cada componente de datos.

________________________________________
3. Flujos E2E Prioritarios
Solicitar los flujos de negocio que deben cubrirse:
- Flujo feliz principal (happy path): ¿Cuál es el recorrido completo del usuario?
- Flujos alternativos: ¿Qué pasa si el usuario cancela a mitad del flujo?
- Flujos de error: ¿Qué pasa si la API devuelve 401, 403, 500?
- Si gobernanza media/alta: verificar que los indicadores de auditoría son visibles.

________________________________________
4. Mocking de API
Preguntar cómo se simulará el backend:
- **Mock Service Worker (MSW):** recomendado para component tests y E2E (intercepta a nivel de red).
- **JSON fixtures locales:** para datos estáticos de prueba.
- **Backend real con datos de prueba:** para E2E en staging.

________________________________________
## Reglas OBLIGATORIAS

- **Arrange-Act-Assert en todo test:** Preparar estado → Ejecutar acción → Verificar resultado.
- **Independencia de tests:** Ningún test E2E debe depender del estado dejado por otro test.
- **Estados de UI obligatorios:** Todo componente que muestra datos debe tener tests para estados loading, empty y error (no solo el happy path).
- **Accesibilidad mínima:** Todo formulario debe testearse con `axe-core` para detectar violaciones WCAG A/AA.
- **Selectores resilientes:** Usar `data-testid` o roles ARIA (`getByRole`), nunca selectores CSS frágiles (`.btn-primary`).
- **CI-ready:** Los tests deben poder ejecutarse en CI sin interfaz gráfica (`--headless`).

________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el código de testing generado:
- [ ] Component tests para componentes críticos con variantes de props
- [ ] Tests de estados: loading (spinner/skeleton visible), empty (mensaje sin datos), error (toast/mensaje rojo)
- [ ] E2E cubre el flujo principal de negocio
- [ ] E2E incluye flujos de error: 401, 403, 500 con aserciones de UI
- [ ] MSW o fixtures configurados para simular API
- [ ] Selectores usan `data-testid` o roles ARIA (no clases CSS)
- [ ] Si gobernanza alta: tests de accesibilidad con axe-core incluidos
- [ ] Comando `npm run test` y `npm run test:e2e` funcionando

________________________________________
## Condición de cierre
Antes de generar el código:
"Voy a generar la configuración de testing frontend con [Stack elegido]. Component tests para [Componentes] y E2E para [Flujos]. ¿Confirmas?"

________________________________________
## Formato de salida

1. Configuración de testing
- `vitest.config.ts` o `jest.config.ts` con setup de ambiente (jsdom/happy-dom).
- `playwright.config.ts` con browsers y baseURL.
- Setup de MSW con handlers para endpoints mockeados.

2. Component Tests
- Archivos `*.spec.ts` o `*.test.ts` para cada componente.
- Tests de renderizado, props, eventos, slots, y estados (loading/empty/error).

3. E2E Tests
- Archivos `*.e2e.ts` para cada flujo de negocio.
- Tests con assertions de navegación, llenado de formularios, y respuestas del backend.

________________________________________
## Modo Caveman (atajo para usuarios avanzados)

Si el usuario solicita "Caveman Mode" o "solo código":
- Omite el flujo de preguntas y genera directamente configuración + tests.
- Incluye bloque `## Decisiones Asumidas` listando stack de testing, componentes testeados y flujos E2E cubiertos.
- **ADVERTENCIA:** La selección de flujos E2E y componentes críticos puede no reflejar el alcance real del proyecto.
