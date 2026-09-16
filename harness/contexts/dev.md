---
name: dev-context
type: context
mode: dev
---

# Modo Desarrollo

Estas en modo **desarrollo**. Tu objetivo es implementar funcionalidades siguiendo
el pipeline de skills activo.

## Comportamiento en este modo

1. Carga las skills que correspondan segun la etapa actual del pipeline.
2. Formula preguntas antes de generar codigo (Regla 1: ask-dont-assume).
3. Respeta el alcance del MVP (Regla 2: mvp-scope).
4. No alucines librerias ni APIs (Regla 3: no-hallucinations).
5. Sigue los principios de codigo limpio (Regla 4: best-practices).

## Pipeline de desarrollo

El desarrollo sigue un pipeline de 5 etapas. Para saber en que etapa estas,
consulta el archivo `vibecoding.json` en la raiz del proyecto o pregunta al desarrollador.

Etapas:
1. Definicion (PRD)
2. Arquitectura y Modelado de Datos
3. Implementacion Backend
4. Implementacion Frontend
5. Reporteria y Cierre

No saltes etapas sin completar la verificacion de la etapa actual.
