# Brazo `gate_only`: ¿el arnés, la compuerta o el modelo?

Fecha: 24 de noviembre de 2026.
Modelo: `opencode-go/deepseek-v4.1-flash`. Runner: OpenCode headless.

## Pregunta

La evidencia del Hito 1 atribuye el efecto a la configuración `rules_skills_gate`, que reúne
reglas, doce procedimientos de desarrollo, tres de cumplimiento y la compuerta. Ese brazo no permite
separar tres cosas: el **analizador**, el **arnés procedural** que lo rodea y el **modelo** que
escribe el código. La pregunta es cuál de las tres produce el resultado.

## Diseño

| Brazo | Reglas | Procedimientos | Procedimientos de cumplimiento | Compuerta |
| - | :-: | :-: | :-: | :-: |
| `baseline` | — | — | — | — |
| `gate_only` | — | — | — | sí |
| `rules_skills_gate` | sí | sí | sí | sí |

- **Tareas:** las cuatro del experimento de dosis (T31, T33, T34, T35), que son las que produjeron
  el contraste de ocho a cero violaciones confirmadas.
- **Repeticiones:** tres por tarea y brazo. Total: 36 ejecuciones.
- **Qué recibe `gate_only`:** el ejecutable de la compuerta, el catálogo y el hook de pre-commit,
  más una instrucción mínima —ejecutar la compuerta antes de terminar—. No recibe reglas, ni
  procedimientos, ni protocolo de ejecución, ni las tres habilidades de cumplimiento.
- **Qué recibe `baseline`:** la aplicación, el enunciado de la tarea y su suite. Nada más.
- **Aislamiento:** mismo modelo, mismo banco, un workspace nuevo por ejecución y un sandbox de
  configuración por corrida.

## Resultados

| Brazo | Corridas | Confirmadas | Comportamiento | Latentes | Limpias | Ciclo mediana | Tokens mediana | Llamadas a la compuerta |
| - | -: | -: | -: | -: | -: | -: | -: | -: |
| `baseline` | 12 | 0 | 0 | 3 | 9 | 183,1 s | 1.006.682 | 0 |
| `gate_only` | 12 | 0 | 0 | 3 | 9 | 268,3 s | 2.973.747 | 2 |
| `rules_skills_gate` | 12 | 0 | 0 | 2 | 10 | 264,2 s | 2.528.101 | 2 |

- **Cero violaciones confirmadas en los tres brazos.** Las 36 ejecuciones aprobaron la prueba oculta.
- **Cero fallas de comportamiento.**
- **Sin pares discordantes en ningún contraste:** McNemar exacto bilateral, *p* = 1,0 tanto para
  `baseline` frente a `gate_only` como para `baseline` frente a `rules_skills_gate`.
- **La compuerta cuesta:** 183,1 s y 1,0 millón de tokens en `baseline`, frente a 268,3 s y 2,97
  millones en `gate_only`. Es 1,5 veces el tiempo y 2,95 veces los tokens, sin beneficio medido.
- **Dos tiempos agotados:** el brazo completo alcanzó el límite de 600 s en dos de doce corridas.

### El único hallazgo del oráculo es un falso positivo

Los ocho casos marcados como riesgo latente corresponden a T31 y a la misma regla Semgrep,
`dumbo.hard-delete-orders`, que busca `delete from orders` sin mirar el `WHERE`. La inspección del
código generado muestra que el agente calcula `timedelta(days=2190)`, salta las órdenes dentro del
plazo de retención y solo después borra. El código es correcto; la regla del oráculo no lo sabe.

El patrón aparece **también en `baseline`, en las tres repeticiones**: el modelo escribe la
retención correcta sin que ninguna herramienta se lo indique.

## Interpretación

1. **Las trampas están saturadas para el modelo actual.** El agente resuelve las cuatro tareas sin
   reglas, sin procedimientos, sin compuerta y sin instrucción alguna sobre privacidad.
2. **Ni el arnés procedural ni la compuerta aportan valor medible en privacidad sobre estas
   tareas.** Los tres brazos son estadísticamente indistinguibles y la compuerta agrega costo.
3. **El resultado del Hito 1 no se reproduce.** El contraste de ocho a cero se midió en octubre con
   el mismo identificador de modelo. Con el comportamiento actual, la línea base ya no produce
   violaciones, de modo que no hay nada que la compuerta corrija.
4. **La adopción no requiere el protocolo:** la compuerta se invocó con mediana de dos llamadas por
   corrida en los brazos que la tienen, basta la instrucción mínima.

## Lo que este experimento no puede afirmar

- **Que la compuerta no sirva.** Afirma que no discrimina en estas cuatro tareas con este modelo.
  Su valor depende de la tasa de error del agente; si esa tasa es cero, no hay nada que detectar.
- **Que el catálogo o el gate de evidencia no sirvan.** No dependen del error del agente: el gate de
  evidencia cubre deberes documentales que ningún detector decide.
- **Estabilidad temporal:** el resultado describe el modelo en noviembre de 2026. Que el mismo
  instrumento diera otro resultado en octubre es, en sí, un hallazgo sobre la vigencia de este tipo
  de evidencia.
- **Muestra pequeña:** cuatro tareas y tres repeticiones por brazo, un solo modelo.

## Consecuencia para el claim del proyecto

La afirmación "un arnés de desarrollo mejora el cumplimiento" no se sostiene con el modelo actual:
el agente cumple sin ayuda. Lo que el trabajo sostiene es más acotado y más útil:

- **El aporte es la capa de verificación** —catálogo normativo, compuerta y gate de evidencia—, y su
  valor es de auditoría, no de corrección.
- **El valor de una compuerta de cumplimiento es función de la tasa de error del agente.** Cuando el
  agente deja de cometer esas omisiones, la compuerta se convierte en instrumento de auditoría y en
  un costo.
- **El método para detectarlo** —corpus ciego sellado, clasificación de cuatro celdas y brazos que
  separan analizador, procedimiento y modelo— es parte del aporte.

## Artefactos

- `qa_reports/gate-only/rep{1,2,3}_{tarea}_{brazo}.json`: reportes por ejecución.
- `qa_reports/gate-only/comparison_baseline_gate.json`: resumen y contraste pareado.
- `harness/eval/arm_comparison.py`: clasificación de cuatro celdas y McNemar pareado.
