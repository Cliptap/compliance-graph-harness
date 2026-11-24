# TODO: validar el harness para desarrollo

La calibración ciega midió el **detector**. Este TODO cubre las tres validaciones que faltan para
responder si el harness sirve **para desarrollo**. Cada punto tiene tareas, criterio de aceptación y
estado.

Estado: `[ ]` pendiente · `[~]` en curso · `[x]` hecho · `[!]` bloqueado.

## Punto 1 — Código real con adjudicación

**Pregunta:** ¿el detector se comporta igual sobre una aplicación real, multi-archivo, que sobre
casos de 20–55 líneas?

| # | Tarea | Estado |
|---|---|---|
| 1.1 | Herramienta de triage: corre el engine sobre un directorio y emite una planilla con archivo, línea, control, evidencia y veredicto en blanco (`harness/eval/triage.py`) | `[x]` |
| 1.2 | Correr sobre una app real multi-archivo del repo (`experiments/supermercado/app`, 9 módulos, ~61 KB) | `[x]` |
| 1.3 | Adjudicar cada hallazgo con evidencia y calcular precisión sobre la app | `[x]` |
| 1.4 | Correr sobre los 13 variants del bloque D (10 con defecto sembrado, 3 limpios), multi-archivo | `[x]` |
| 1.5 | Repetir sobre PRs reales de la app objetivo (requiere acceso al repo y una persona que adjudique) | `[!]` |

**Resultado del piloto (1.2–1.4):**

- `experiments/supermercado/app`: **0 hallazgos**; verificado a mano, la app anonimiza en retención,
  filtra marketing por consentimiento y no loguea PII. Verdadero negativo, no un miss.
- 13 variants del bloque D: **13/13 OK** contra los detectores legacy (`build.py`).
- Controles v2 sobre los variants: **0 findings en las 3 apps limpias**; `v2.log_pii` en V01 y
  `v2.api_key`/`v2.credential_response`/`v2.reset_token` en V07. Los defectos legacy (tarjeta, CVV,
  consentimiento, biometría, rutas ausentes) no tienen control v2 y correctamente no disparan.
- **Un falso negativo confirmado en código real**: V02 (RUT que llega a un log vía
  `app.logging_helpers.log_value`, en otro módulo) no se detecta. Es el límite cross-module ya
  documentado, ahora con evidencia multi-archivo.

**Criterio de aceptación:** precisión medida sobre código real, con cada falso positivo identificado
y explicado. La adjudicación de 1.5 debe hacerla una persona; la de 1.3 la hizo el agente y se marca
como tal.

## Punto 2 — Repetir el bloque D con el detector actual

**Pregunta:** ¿el harness cambia el resultado funcional del desarrollo, o solo cuesta más?

| # | Tarea | Estado |
|---|---|---|
| 2.1 | Recuperar los fixtures del bloque D: están en `experiments/tasks` (tests ocultos D01–D10) y en `experiments/variants/manifest.json` (13 variantes multi-archivo con la mutación exacta) | `[x]` |
| 2.2 | Protocolo del piloto: 1 trampa × 2 brazos × 1 repetición, midiendo hidden pass, evidencia, ciclo, tokens y tool calls | `[x]` |
| 2.3 | Ejecutar el piloto con `experiments/tasks/formal_run.py` y los brazos de `arms.py` | `[!]` |
| 2.4 | Decidir qué problema resuelve el harness si el resultado se repite (auditoría vs. corrección) | `[ ]` |

**Criterio de aceptación:** un piloto con el mismo instrumento del bloque D, aunque sea de una sola
trampa, que confirme o desmienta el 30/30 con 2,5× costo.

**Bloqueo de 2.3:** el piloto consume ciclos de agente reales (dos brazos completos). Requiere una
sesión dedicada con presupuesto de tiempo; los fixtures y el runner ya están versionados.

## Punto 3 — Etiquetas independientes

**Pregunta:** ¿las etiquetas del autor LLM coinciden con un evaluador independiente?

| # | Tarea | Estado |
|---|---|---|
| 3.1 | Muestreo estratificado de 30 casos del corpus (15 violación / 15 limpio, 7 controles) | `[x]` |
| 3.2 | Planilla ciega: id, control, código; sin la etiqueta esperada | `[x]` |
| 3.3 | Calcular acuerdo (Cohen's kappa) entre la planilla y el corpus | `[x]` |
| 3.4 | Correr un evaluador independiente (subagente sin acceso al repo, sin ver las etiquetas) | `[x]` |
| 3.5 | Repetir con una persona experta | `[ ]` |

**Resultado del piloto (3.4):** 30/30, acuerdo **1.000**, Cohen's kappa **1.000** (15/15 en
violación, 15/15 en limpio). El evaluador fue un LLM con el mismo brief de controles y sin acceso al
corpus; es un proxy de independencia, no una adjudicación humana.

**Criterio de aceptación:** kappa medido. Un kappa bajo invalida los números de las 21 rondas; uno
alto los respalda. El evaluador de 3.4 es un LLM distinto en rol, no una persona: se reporta como
proxy, no como adjudicación humana.

## Orden de ejecución

1. Punto 1.1–1.4 (tooling + dos objetivos reales).
2. Punto 3.1–3.4 (muestreo + evaluador independiente + kappa).
3. Punto 2.2 (protocolo) y documentar el bloqueo de 2.1/2.3.
4. Punto 1.5 y 3.5 quedan para una persona con acceso a la app objetivo.
