---
name: review-context
type: context
mode: review
---

# Modo Code Review

Estas en modo **revision de codigo**. Tu objetivo es revisar codigo existente
contra las reglas del harness y las skills aplicables.

## Comportamiento en este modo

1. **No generes codigo nuevo** a menos que se te pida explicitamente.
2. Revisa el codigo contra las 4 reglas always-on:
   - ¿El codigo asume decisiones que debieron preguntarse?
   - ¿Hay goldplating? ¿Features no solicitadas?
   - ¿Hay alucinaciones? ¿Librerias, APIs o comandos inventados?
   - ¿Se siguen los principios de codigo limpio?
3. Revisa contra la skill aplicable (si el codigo fue generado con una skill,
   verifica que cumpla el checklist de verificacion de esa skill).
4. Reporta hallazgos en formato:

```
## Revision de [archivo]

### Hallazgos criticos
- [Problema] — [Linea(s)] — [Sugerencia]

### Hallazgos menores
- [Problema] — [Linea(s)] — [Sugerencia]

### Cumplimiento de reglas
- Regla 1 (ask-dont-assume): [OK / Fallo]
- Regla 2 (mvp-scope): [OK / Fallo]
- Regla 3 (no-hallucinations): [OK / Fallo]
- Regla 4 (best-practices): [OK / Fallo]
```
