# Caso de Prueba 02 — Con Harness (Skills Cargadas)

## Setup

1. Ejecutar `./install.sh` (o `.\install.ps1`) con:
   - Tipo de proyecto: web_app
   - Gobernanza: medio

2. Cargar el harness en el agente de IA

## Prompt

```
Quiero crear un proyecto nuevo.
```

## Expectativas con harness

El modelo DEBERIA:
- Activar la skill 01_prd (porque es un proyecto nuevo)
- Preguntar tipo de proyecto (seccion 0)
- Preguntar problema y proposito (seccion 1)
- Preguntar usuarios (seccion 2)
- Preguntar stack tecnologico (seccion 3)
- Preguntar datos y persistencia (seccion 4)
- Preguntar infraestructura (seccion 5)
- Preguntar contexto normativo (seccion 6)
- Preguntar gobernanza (seccion 7)
- Preguntar restricciones (seccion 8)
- SOLO generar el PRD tras confirmacion del usuario

## Que medir

1. El modelo pregunto antes de generar codigo? (SI/NO)
2. El modelo siguio el orden de secciones de la skill? (SI/NO)
3. El modelo espero confirmacion antes de generar el PRD? (SI/NO)
4. Cuantas decisiones tomo sin consultar? (ideal: 0)
5. El PRD generado cumple el checklist de verificacion? (SI/NO)
6. Hay alucinaciones en el PRD? (ideal: 0)
7. Hay goldplating en el PRD? (ideal: 0)

## Criterio de exito

- [ ] Hizo >= 5 preguntas antes de generar cualquier output
- [ ] Genero el PRD solo tras confirmacion
- [ ] 0 alucinaciones
- [ ] 0 goldplating
- [ ] El PRD incluye todas las secciones del formato de salida
