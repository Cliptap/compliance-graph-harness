---
name: stack-go
type: rule
priority: medium
always_on: true
---

# Reglas Especificas para Go

## Estilo de Codigo

1. **Seguir `go fmt` y `go vet`** — formato oficial, no discutible.
2. **Nombres en camelCase** — exportados con mayuscula inicial.
3. **Errores como valores** — retornar `(T, error)`, nunca usar panic para flujo.
4. **Manejar errores inmediatamente** — no ignorar `_`.
5. **Interfaces pequenas** — 1-3 metodos, definir donde se consumen.

## Estructura

```
project/
  cmd/          # entry points (main packages)
  internal/     # codigo privado del modulo
  pkg/          # codigo publico reutilizable
  go.mod
  go.sum
```

## Buenas Practicas

- Usar `context.Context` como primer parametro en funciones que hacen I/O.
- Usar `defer` para cleanup.
- No usar `init()` a menos que sea estrictamente necesario.
- Tests en `*_test.go` en el mismo paquete (white box) o `_test` (black box).
- Usar table-driven tests.

## Anti-Patrones a Evitar

- Ignorar errores con `_`.
- Usar `panic` para errores recuperables.
- Mutex copiados por valor.
- Goroutines sin mecanismo de cancelacion.
- Cerrar canales desde el receptor.
