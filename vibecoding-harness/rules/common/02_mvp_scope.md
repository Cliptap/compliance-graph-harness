---
name: mvp-scope
type: rule
priority: critical
always_on: true
---

# Regla 2: Alcance MVP — Sin Goldplating

## Principio Fundamental

> El MVP (Minimum Viable Product) es el conjunto mínimo de funcionalidades que resuelven
> el problema del usuario. Todo lo demás es desperdicio hasta que el MVP esté validado.

## Reglas de Alcance

1. **Solo implementa lo que está explícitamente definido en el PRD o solicitado por el desarrollador.**
   Si no está escrito, no se hace. Sin excepciones.

2. **No agregues "buenas prácticas" automáticas no solicitadas.**
   - Sin el usuario pedirlo: no agregues CI/CD, Docker, tests, linting, formateo, SEO, analytics, etc.
   - Cada "buena práctica" debe ser una decisión consciente del desarrollador.

3. **No implementes features "por si acaso" o "porque todos los proyectos lo tienen".**
   - "Por si acaso necesitas un panel de admin" → NO
   - "Todos los proyectos tienen dark mode" → NO
   - "Es común tener filtros de búsqueda" → NO (a menos que el PRD lo pida)

4. **Si una feature no está en el PRD y toma más del 5% del esfuerzo total, es goldplating.**
   Antes de implementarla, pregunta obligatoriamente.

5. **Ante la duda entre simple y complejo, elige SIMPLE.**
   El MVP debe ser la versión más simple que resuelva el problema. La complejidad se agrega
   en iteraciones posteriores, cuando haya feedback real de usuarios.

6. **No optimices prematuramente.**
   - No agregues caché si no hay problema de performance
   - No uses colas de mensajes si un llamado directo funciona
   - No implementes microservicios si un monolito resuelve el problema

## Checklist Anti-Goldplating

Antes de implementar cualquier cosa no explicitada en el PRD, pregúntate:

- [ ] ¿Está esto en el PRD o fue solicitado explícitamente?
- [ ] ¿El producto funciona sin esto?
- [ ] ¿El usuario pidió esto o lo estoy asumiendo?
- [ ] ¿Agregar esto retrasa la entrega del MVP?

Si respondiste NO a la primera y SÍ a la segunda, probablemente es goldplating.

## Cómo Proponer (no Imponer) Mejoras

Si identificas algo que genuinamente mejoraría el producto, NO lo implementes.
En su lugar, pregunta:

```
Noté que [observación]. ¿Quieres que [mejora concreta]?

Esto tomaría aproximadamente [X tiempo] y aportaría [beneficio concreto].
Si prefieres mantener el alcance actual, continúo sin agregarlo.

⏳ Esperando tu decisión.
```

## Ejemplos de Goldplating por Tipo de Proyecto

| Tipo de proyecto | Goldplating común a evitar |
|-----------------|---------------------------|
| Web app | Panel admin, dark mode, i18n, SEO, analytics, PWA, notificaciones push |
| API | Rate limiting, versionado, webhooks, SDK, documentación OpenAPI (si no se pidió) |
| Data pipeline | Dashboard en tiempo real, notificaciones de error, data quality framework, lineage |
| CLI tool | Auto-update, analytics, telemetría, plugins, shell completion, man pages |
| Mobile | Offline mode, sincronización, push notifications, biometric auth, app store screenshots |
