---
name: stack-typescript
type: rule
priority: medium
always_on: true
---

# Reglas Especificas para TypeScript

## Estilo de Codigo

1. **Usar TypeScript estrictamente** — `strict: true` en tsconfig.json.
2. **Preferir `interface` sobre `type`** para objetos publicos.
3. **Usar `const` por defecto**, `let` solo si es necesario, NUNCA `var`.
4. **Evitar `any`** — usar `unknown` y narrowing.
5. **Usar template literals** en vez de concatenacion de strings.

## Estructura

- `package.json` con `type: "module"` o configuracion de modulos clara.
- `tsconfig.json` en la raiz.
- Codigo fuente en `src/`.
- Tests en `src/__tests__/` o `tests/`.

## Buenas Practicas

- Usar optional chaining: `obj?.prop?.nested`.
- Usar nullish coalescing: `value ?? defaultValue`.
- Usar `Promise.all` para operaciones paralelas.
- Preferir `Array.map/filter/reduce` sobre bucles imperativos.
- Usar `export default` solo para componentes principales.

## Anti-Patrones a Evitar

- `==` en vez de `===`.
- Callbacks anidados — usar async/await.
- `forEach` con `async` — usar `for...of` o `Promise.all`.
- `enum` de TypeScript (preferir union types o `as const`).
