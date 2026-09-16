---
name: best-practices
type: rule
priority: high
always_on: true
---

# Regla 4: Principios Universales de Desarrollo

## Principios Fundamentales

Estos principios aplican a todo código generado, independientemente del stack o dominio.
No requieren configuración — son universales.

## KISS (Keep It Simple, Stupid)

- La solución más simple que funcione **es** la mejor solución.
- Si necesitas explicar tu código con un párrafo, es demasiado complejo.
- Prefiere funciones pequeñas con una sola responsabilidad.
- Un archivo de más de 300 líneas probablemente debería dividirse.

## YAGNI (You Ain't Gonna Need It)

- No implementes abstracciones "por si acaso".
- No crees interfaces genéricas si solo tienes una implementación.
- No reserves espacio para features futuras.
- El código que no existe no tiene bugs.

## SOLID (aplica según escala del proyecto)

- **S**ingle Responsibility: Una clase/función = una razón para cambiar.
- **O**pen/Closed: Abierto a extensión, cerrado a modificación (solo si el proyecto lo justifica).
- **L**iskov Substitution: Las subclases deben ser sustituibles por sus clases base.
- **I**nterface Segregation: Interfaces pequeñas y específicas, no monolíticas.
- **D**ependency Inversion: Depende de abstracciones, no de implementaciones concretas.

> Solo aplica SOLID completo si el proyecto tiene +3 entidades o +10 endpoints.
> Para MVPs pequeños, KISS + YAGNI es suficiente.

## DRY (Don't Repeat Yourself) — Con Cuidado

- No dupliques lógica de negocio.
- **Pero** no sobre-abstraigas prematuramente. Dos bloques similares no siempre justifican
  una abstracción. La regla de tres: si se repite 3 veces, abstrae.
- Duplicar es mejor que la abstracción incorrecta.

## Principios de Código Limpio

1. **Nombres descriptivos**: `calculate_total_price()` no `calc()`. `user_repository` no `ur`.
2. **Funciones cortas**: Idealmente menos de 20 líneas. Máximo 50.
3. **Menos de 4 parámetros**: Si una función necesita más de 3-4 parámetros, usa un objeto/dict.
4. **Early returns**: Evita anidamiento profundo de if-else. Retorna temprano.
5. **Sin números mágicos**: `MAX_RETRY_ATTEMPTS = 3` no `if attempts > 3`.
6. **Sin efectos secundarios ocultos**: Una función debe hacer lo que su nombre indica, nada más.

## Principios de Estructura de Proyecto

1. **Separa configuración de código**: Usa variables de entorno, no hardcodees.
2. **Separa lógica de negocio de infraestructura**: Servicios no deben conocer HTTP/DB directamente.
3. **Agrupa por feature, no por tipo**: `src/users/` mejor que `src/models/` + `src/routes/` + `src/services/`.
4. **Un solo entry point claro**: `main.py`, `index.ts`, `main.go` — fácil de encontrar.

## Manejo de Errores

1. **Nunca uses excepciones para flujo de control**.
2. **Nunca captures excepciones sin hacer nada con ellas** (sin `except: pass`).
3. **Siempre provee mensajes de error descriptivos** que ayuden a debuggear.
4. **Valida inputs temprano**: Falla rápido, en la capa más externa posible.

## Seguridad (Mínimo Universal)

1. **Nunca hardcodees secrets, tokens, keys o passwords**.
2. **Usa variables de entorno** para configuración sensible.
3. **No loguees información sensible** (passwords, tokens, datos personales).
4. **Usa HTTPS en producción** — asume que el entorno lo configura.
5. **Sanitiza inputs de usuario** — nunca confíes en datos externos.

## Testing (Solo Si Se Solicitó)

No escribas tests a menos que el PRD o el desarrollador lo pidan explícitamente.
Cuando se pidan tests:
- Sigue el patrón AAA: Arrange, Act, Assert
- Un test = un comportamiento verificable
- Nombra los tests describiendo el escenario: `test_login_fails_with_wrong_password`
